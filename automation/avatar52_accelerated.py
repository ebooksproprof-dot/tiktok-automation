"""Isolated 5.2 accelerated avatar experiment. Never writes production or publishes."""
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
from avatar43_smoke import CODE_REV, WEIGHTS_REV, patch_checkpoint_loading_cpu, patch_reference_attention_device
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'avatar52-output'
CONTEXT = int(os.getenv('AVATAR_CONTEXT_FRAMES', '4'))
if CONTEXT not in (4, 12):
    raise ValueError('Only bounded context4 or upstream-default12 experiments allowed')
OVERLAP = {4: 1, 12: 3}[CONTEXT]

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
            if abs(duration - 5.0) > 0.3:
                raise ValueError(f'{stream.type} duration outside 5s ±0.3s: {duration}')
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
    report = dict(engine='EchoMimic V1 accelerated CPU', code_revision=CODE_REV,
                  weights_revision=WEIGHTS_REV, requested_seconds=5,
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

    report['hypothesis'] = 'Controlled comparison: context4 minimizes activation size; context12 restores upstream temporal window. Same portrait/audio/seed/CFG1/6steps; no quality guarantee.'
    report['settings'] = dict(width=256,height=256,frames=40,fps=8,steps=6,cfg=1.0,context_frames=CONTEXT,context_overlap=OVERLAP,inference_timeout_seconds=600,seed=420)
    report['cpu_count'] = os.cpu_count()
    report['available_cpu_affinity'] = len(os.sched_getaffinity(0))
    report['cgroup_memory_max'] = Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else None
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
        report['torch_cpu_threads'] = torch.get_num_threads()
        report['cpu_model'] = next((x.split(':',1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines() if x.startswith('model name')), 'unknown')
        stage('fetch_pinned_source')
        code = OUT / 'source'
        run(['git', 'clone', '--filter=blob:none', '--no-checkout',
             'https://github.com/antgroup/echomimic.git', str(code)])
        run(['git', 'checkout', CODE_REV], cwd=code)
        stage('bounded_weight_download')
        # Single pinned hub, explicit allowlist; no gated or authenticated requests.
        weights = code / 'pretrained_weights'
        patterns = ['LICENSE', 'denoising_unet_acc.pth', 'reference_unet.pth',
                    'motion_module_acc.pth', 'face_locator.pth',
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
        limit = report.get('cgroup_memory_max')
        report['effective_ram_bytes'] = min(report['physical_ram_bytes'], int(limit)) if limit and limit.isdigit() else report['physical_ram_bytes']
        save()
        if report['effective_ram_bytes'] < 12_000_000_000:
            raise RuntimeError('CPU experiment requires at least 12 GB RAM; inference needs remain unmeasured')
        snapshot_download('BadToBest/EchoMimic', revision=WEIGHTS_REV,
                          local_dir=weights, allow_patterns=patterns,
                          token=False, max_workers=4)
        report['downloaded_weight_bytes'] = sum(p.stat().st_size for p in weights.rglob('*') if p.is_file())
        license_path = weights/'LICENSE'
        license_text = license_path.read_text()
        if hashlib.sha256(license_path.read_bytes()).hexdigest() != '43070e2d4e532684de521b885f385d0841030efa2b1a20bafb76133a5e1379c1':
            raise RuntimeError('Unexpected weights license; inference blocked')
        report['weights_license_sha256'] = hashlib.sha256(license_path.read_bytes()).hexdigest()
        report['weights_license'] = 'Apache-2.0, pinned hub LICENSE checked before inference'
        stage('prepare_cpu_port_and_inputs')
        # Experimental modification explicitly recorded, not upstream behavior.
        entry = code / 'infer_audio2vid_acc.py'
        source = entry.read_text()
        report['original_entry_sha256'] = hashlib.sha256(source.encode()).hexdigest()
        source = source.replace('"cuda"', '"cpu"').replace("'cuda'", "'cpu'")
        source = patch_checkpoint_loading_cpu(source)
        entry.write_text(source)
        report['modified_entry_sha256'] = hashlib.sha256(source.encode()).hexdigest()
        attention = code / 'src/models/mutual_self_attention.py'
        original_attention = attention.read_text()
        report['original_attention_sha256'] = hashlib.sha256(original_attention.encode()).hexdigest()
        patched_attention = patch_reference_attention_device(original_attention)
        attention.write_text(patched_attention)
        report['modified_attention_sha256'] = hashlib.sha256(patched_attention.encode()).hexdigest()
        report['port_scope'] = 'entrypoint CPU; checkpoint CPU loading; internal reference attention device/dtype from UNet; fp32; remaining graph unproven'
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
        run(['ffmpeg', '-y', '-i', str(baseline), '-t', '5', '-ar', '16000',
             '-ac', '1', str(code / 'speech-5s.wav')])
        cfg_path = code / 'configs/prompts/animation_acc.yaml'
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg['weight_dtype'] = 'fp32'
        cfg['test_cases'] = {'presenter.jpg': ['speech-5s.wav']}
        cfg_path.write_text(yaml.safe_dump(cfg))
        stage('inference')
        report['inference_attempted'] = True
        report['inference_executed'] = None  # unknown until model output is evidenced
        save()
        # Official accelerated weights/pipeline: six steps, CFG1; smaller temporal windows bound activations.
        run([sys.executable, 'infer_audio2vid_acc.py', '--device', 'cpu', '-W', '256',
             '-H', '256', '-L', '40', '--fps', '8', '--steps', '6', '--cfg', '1.0',
             '--context_frames', str(CONTEXT), '--context_overlap', str(OVERLAP)], cwd=code, seconds=600)
        videos = list((code / 'output').rglob('*withaudio.mp4'))
        if not videos:
            raise RuntimeError('Inference returned without an audio/video artifact')
        target = OUT / 'avatar52-accelerated.mp4'
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
        # Emit only controlled metadata, not arbitrary subprocess output or URLs.
        failure = dict(stage=report['stage'], error_type=type(exc).__name__,
                       elapsed_seconds=report['elapsed_seconds'],
                       avatar_video_produced=False)
        if isinstance(exc, subprocess.CalledProcessError):
            failure['error'] = 'Experiment subprocess failed; inspect execution.log artifact'
            failure['returncode'] = exc.returncode
        elif isinstance(exc, subprocess.TimeoutExpired):
            failure['error'] = 'Experiment subprocess exceeded time budget'
        else:
            failure['error'] = 'Experiment failed; inspect report.json artifact'
        print(json.dumps(failure), flush=True)
        return 1
    finally:
        save()
        # Avoid uploading multi-GB weights/source in the evidence artifact.
        shutil.rmtree(OUT / 'source', ignore_errors=True)


if __name__ == '__main__':
    raise SystemExit(main())
