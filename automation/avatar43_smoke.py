"""Bounded isolated EchoMimic CPU experiment; never used by production.

Outputs are technical proofs only, not commercial-quality or approved content.
No credentials, gated models, paid APIs, queue writes, or publication.
"""
import hashlib
import fnmatch
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time
import urllib.request

CODE_REV = 'c32b3a557003f84ead1483a2d2386035685d984d'
WEIGHTS_REV = '987c98d1d00a5fd062c5f087719af663fa90bc53'
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'avatar43-output'


def validate_mp4(path):
    """Decode both complete streams and validate the requested proof geometry/time."""
    import av
    with av.open(str(path)) as container:
        videos, audios = list(container.streams.video), list(container.streams.audio)
        if len(videos) != 1 or len(audios) != 1:
            raise ValueError('Proof must contain exactly one video and one audio stream')
        video, audio = videos[0], audios[0]
        if (video.width, video.height) != (256, 256):
            raise ValueError('Unexpected proof resolution')
        durations = {}
        for stream in (video, audio):
            if stream.duration is None or stream.time_base is None:
                raise ValueError('Missing stream duration')
            duration = float(stream.duration * stream.time_base)
            if abs(duration - 3.0) > 0.3:
                raise ValueError(f'{stream.type} duration outside 3s ±0.3s: {duration}')
            durations[stream.type] = duration
        counts = {'video': 0, 'audio': 0}
        for packet in container.demux(video, audio):
            for frame in packet.decode():
                counts[packet.stream.type] += 1
                if packet.stream.type == 'video' and (frame.width, frame.height) != (256, 256):
                    raise ValueError('Decoded frame resolution changed')
        if not counts['video'] or not counts['audio']:
            raise ValueError('Empty or undecodable stream')
        return dict(resolution=[256, 256], stream_durations=durations,
                    decoded_frames=counts, full_decode_passed=True)


def main():
    OUT.mkdir(exist_ok=True)
    started = time.monotonic()
    report = dict(engine='EchoMimic V1', code_revision=CODE_REV,
                  weights_revision=WEIGHTS_REV, requested_seconds=3,
                  inference_attempted=False, inference_executed=False, avatar_video_produced=False,
                  approved_for_publication=False, production_integrated=False,
                  voice='Kokoro reused from verified validation-v41-C3; no new synthesis or listening review',
                  additional_paid_cost_brl=0, stage='initialization')
    evidence = OUT / 'report.json'

    def save():
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        report['max_child_rss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        evidence.write_text(json.dumps(report, indent=2) + '\n')

    def stage(name):
        report['stage'] = name
        save()

    def run(args, cwd=None, seconds=90):
        with (OUT / 'execution.log').open('a') as log:
            subprocess.run(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=seconds)

    save()
    try:
        import torch
        import yaml
        import imageio_ffmpeg
        from huggingface_hub import HfApi, snapshot_download
        torch.set_num_threads(2)
        # Wheel includes FFmpeg; avoid apt repository downloads entirely.
        bin_dir = OUT / 'bin'
        bin_dir.mkdir(exist_ok=True)
        ffmpeg = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
        link = bin_dir / 'ffmpeg'
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(ffmpeg)
        os.environ['PATH'] = str(bin_dir) + os.pathsep + os.environ.get('PATH', '')
        os.environ['IMAGEIO_FFMPEG_EXE'] = str(ffmpeg)
        os.environ['FFMPEG_PATH'] = str(bin_dir)
        report['ffmpeg_source'] = 'imageio-ffmpeg wheel'
        report['torch_version'] = torch.__version__
        report['cuda_available'] = torch.cuda.is_available()
        stage('fetch_pinned_source')
        code = OUT / 'source'
        run(['git', 'clone', '--filter=blob:none', '--no-checkout',
             'https://github.com/antgroup/echomimic.git', str(code)])
        run(['git', 'checkout', CODE_REV], cwd=code)
        stage('bounded_weight_download')
        # Single pinned hub, explicit allowlist; no gated or authenticated requests.
        weights = code / 'pretrained_weights'
        patterns = ['LICENSE', 'denoising_unet.pth', 'reference_unet.pth',
                    'motion_module.pth', 'face_locator.pth',
                    'audio_processor/whisper_tiny.pt',
                    'sd-vae-ft-mse/config.json', 'sd-vae-ft-mse/diffusion_pytorch_model.bin',
                    'sd-image-variations-diffusers/unet/config.json',
                    'sd-image-variations-diffusers/unet/diffusion_pytorch_model.bin']
        info = HfApi(token=False).model_info('BadToBest/EchoMimic',
                                          revision=WEIGHTS_REV, files_metadata=True)
        selected = [s for s in info.siblings if any(fnmatch.fnmatch(s.rfilename, p) for p in patterns)]
        if len(selected) != len(patterns) or any(s.size is None for s in selected):
            raise RuntimeError('Exact download inventory could not be verified')
        total = sum(s.size for s in selected)
        report['planned_download_bytes'] = total
        report['free_disk_bytes'] = shutil.disk_usage(OUT).free
        report['physical_ram_bytes'] = os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')
        report['weight_manifest'] = [dict(path=s.rfilename, bytes=s.size) for s in selected]
        save()
        if total > 13_000_000_000:
            raise RuntimeError('Download budget of 13 GB exceeded')
        # local_dir avoids a second full snapshot; reserve largest download + output.
        if report['free_disk_bytes'] < total + max(s.size for s in selected) + 1_000_000_000:
            raise RuntimeError('Insufficient disk for weights and cache reserve')
        if report['physical_ram_bytes'] < 12_000_000_000:
            raise RuntimeError('CPU experiment requires at least 12 GB RAM; inference needs remain unmeasured')
        snapshot_download('BadToBest/EchoMimic', revision=WEIGHTS_REV,
                          local_dir=weights, allow_patterns=patterns,
                          token=False, max_workers=4)
        report['downloaded_weight_bytes'] = sum(p.stat().st_size for p in weights.rglob('*') if p.is_file())
        stage('prepare_cpu_port_and_inputs')
        # Experimental modification explicitly recorded, not upstream behavior.
        entry = code / 'infer_audio2vid.py'
        source = entry.read_text()
        report['original_entry_sha256'] = hashlib.sha256(source.encode()).hexdigest()
        source = source.replace('"cuda"', '"cpu"').replace("'cuda'", "'cpu'")
        entry.write_text(source)
        report['modified_entry_sha256'] = hashlib.sha256(source.encode()).hexdigest()
        report['port_scope'] = 'entrypoint literal cuda→cpu, fp32 config; deeper CPU compatibility unproven'
        shutil.copy2(ROOT / 'automation/avatar/presenter-v1.jpg', code / 'presenter.jpg')
        baseline = code / 'baseline-kokoro.mp4'
        baseline_url = ('https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/'
                        'validation-v41-2026-10-22/validation-v41-C3-secador-guardar-depois-v2-ba6632efac13a27e.mp4')
        baseline_sha = 'ba6632efac13a27e72af60d467f5a4f7f52f4d48aaa1d38e560025923ad59b87'
        download_start = time.monotonic()
        with urllib.request.urlopen(baseline_url, timeout=15) as response, baseline.open('wb') as handle:
            count = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > 20_000_000 or time.monotonic() - download_start > 90:
                    raise RuntimeError('Voice baseline download exceeded 20MB/90s budget')
                handle.write(chunk)
        if hashlib.sha256(baseline.read_bytes()).hexdigest() != baseline_sha:
            raise RuntimeError('Voice baseline SHA256 mismatch')
        report['voice_source_sha256'] = baseline_sha
        run(['ffmpeg', '-y', '-i', str(baseline), '-t', '3', '-ar', '16000',
             '-ac', '1', str(code / 'speech-3s.wav')])
        cfg_path = code / 'configs/prompts/animation.yaml'
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg['weight_dtype'] = 'fp32'
        cfg['test_cases'] = {'presenter.jpg': ['speech-3s.wav']}
        cfg_path.write_text(yaml.safe_dump(cfg))
        stage('inference')
        report['inference_attempted'] = True
        report['inference_executed'] = None  # unknown until model output is evidenced
        save()
        # 36 frames at 12fps: 3 seconds; few steps are diagnostic, not quality proof.
        run([sys.executable, 'infer_audio2vid.py', '--device', 'cpu', '-W', '256',
             '-H', '256', '-L', '36', '--fps', '12', '--steps', '4',
             '--context_frames', '12', '--context_overlap', '3'], cwd=code, seconds=180)
        videos = list((code / 'output').rglob('*withaudio.mp4'))
        if not videos:
            raise RuntimeError('Inference returned without an audio/video artifact')
        target = OUT / 'avatar43-diagnostic.mp4'
        shutil.copy2(videos[-1], target)
        stage('validate_decoded_output')
        report['technical_validation'] = validate_mp4(target)
        report['avatar_video_produced'] = True
        report['inference_executed'] = True
        report['video_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        report['quality_review'] = 'pending; no lip-sync or realism claim'
        stage('diagnostic_video_available_for_review')
        return 0
    except Exception as exc:
        report['error_type'] = type(exc).__name__
        report['error'] = str(exc)
        save()
        return 1
    finally:
        save()
        # Avoid uploading multi-GB weights/source in the evidence artifact.
        shutil.rmtree(OUT / 'source', ignore_errors=True)


if __name__ == '__main__':
    raise SystemExit(main())
