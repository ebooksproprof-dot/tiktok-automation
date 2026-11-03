"""Bounded, opt-in public Gradio experiment. Never publishes or buys capacity.

Uses no HF token, so cannot debit an authenticated prepaid account. An uncertain
submission is never repeated automatically. Persist the entire output directory
between runners; a missing durable directory is not an idempotency guarantee.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

SPACE = 'https://chopperblu-ltx-2-5-demo.hf.space'
MODEL = 'Lightricks/LTX-2.5-Diffusers'
PROMPTS = {
    'A': 'Photorealistic vertical close-up in a bright home kitchen. One adult carefully places stainless steel spoons into a wooden drawer organizer. Anatomically correct hands, stable utensil geometry, physically coherent slow movement, natural daylight, locked camera, no text, no logos.',
    'B': 'Photorealistic vertical close-up in a bright home kitchen. An adult places two small kitchen utensils into separate compartments of a plain wooden organizer. Keep the same organizer proportions and material throughout, realistic fingers and object contact, one slow continuous action, no text or logos.',
    'C': 'Photorealistic vertical close-up of an adult wiping a kitchen countertop with one blue microfiber cloth. The hand maintains natural pressure and contact with the cloth, coherent left-to-right motion, clean daylight, stable counter geometry, no text, no logos.'}


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    os.replace(temp, path)


def cached_record(path):
    record = json.loads(Path(path).read_text())
    if record.get('status') == 'GENERATED_PENDING_VISUAL_REVIEW':
        media = Path(path).parent / record.get('file', '')
        if (not media.is_file() or
                hashlib.sha256(media.read_bytes()).hexdigest() != record.get('media', {}).get('sha256')):
            return {**record, 'status': 'BLOCKED', 'error': 'GENERATED_FILE_MISSING_OR_CHANGED'}
    return record


def request_spec(case):
    if case not in PROMPTS:
        raise ValueError('Unknown test case')
    return {'case': case, 'space': SPACE, 'model': MODEL, 'prompt': PROMPTS[case],
            'width': 576, 'height': 1024, 'duration_seconds': 5,
            'seed': 8100 + ord(case) - ord('A') + 1, 'decoder': 'conv',
            'auto_length': False, 'randomize_seed': False, 'image_path': None}


def fingerprint(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def classify_error(exc):
    # Store a category, not an arbitrary exception body that might echo a token.
    text = str(exc).lower()
    if isinstance(exc, TimeoutError) or 'timeout' in text:
        return 'TIMEOUT_OUTCOME_UNKNOWN'
    if 'quota' in text or 'gpu duration' in text:
        return 'QUOTA_OR_GPU_BUDGET'
    if 'repositorynotfound' in text or 'model loading failed' in text:
        return 'SPACE_MODEL_UNAVAILABLE'
    if 'auth' in text or '401' in text or '403' in text or 'token' in text:
        return 'AUTHORIZATION_REQUIRED'
    return 'REMOTE_OR_TRANSPORT_FAILURE'


def video_path(output):
    first = output[0] if isinstance(output, (tuple, list)) else output
    if isinstance(first, dict):
        first = first.get('video') or first.get('path')
        if isinstance(first, dict):
            first = first.get('path')
    if not isinstance(first, str) or not Path(first).is_file():
        raise ValueError('No downloaded MP4 returned')
    path = Path(first)
    if path.suffix.lower() != '.mp4' or not 1000 <= path.stat().st_size <= 100_000_000:
        raise ValueError('Generated output outside MP4 size limits')
    return path


def inspect_clip(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                             '-of', 'json', str(path)], capture_output=True, text=True,
                            check=True, timeout=30)
    data = json.loads(result.stdout)
    streams = data.get('streams', [])
    video = next(s for s in streams if s['codec_type'] == 'video')
    duration = float(data['format']['duration'])
    if not 4.8 <= duration <= 5.3 or video.get('width') != 576 or video.get('height') != 1024:
        raise ValueError('Generated clip differs from requested dimensions/duration')
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'],
                   capture_output=True, check=True, timeout=60)
    return {'duration_seconds': duration, 'width': video['width'], 'height': video['height'],
            'video_codec': video.get('codec_name'),
            'audio_codecs': [s.get('codec_name') for s in streams if s['codec_type'] == 'audio'],
            'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def run(case, directory, enabled=False, client_factory=None, before_submit=None):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    spec = request_spec(case); digest = fingerprint(spec)
    path = directory / (digest + '.json')
    if not enabled:
        return {'status': 'DISABLED', 'generation_attempted': False, 'publication_allowed': False}
    if os.getenv('GITHUB_ACTIONS') == 'true' and before_submit is None:
        return {'status': 'BLOCKED', 'error': 'REMOTE_LEDGER_REQUIRED',
                'generation_attempted': False, 'publication_allowed': False}
    with (directory / (digest + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.exists():
            return cached_record(path)  # Never regenerate missing/changed media automatically.
        record = {'request': spec, 'request_sha256': digest, 'status': 'DISCOVERING',
                  'created_at': datetime.now(timezone.utc).isoformat(),
                  'generation_attempted': False, 'publication_allowed': False,
                  'gpu_seconds_requested': None, 'gpu_seconds_consumed': None,
                  'quota_consumed': None, 'queue_seconds': None, 'usable_video_seconds': 0,
                  'authenticated': False, 'billable_account_used': False}
        save(path, record); started = time.monotonic()
        try:
            if client_factory is None:
                from gradio_client import Client
                client_factory = Client
            # Explicit token=False prevents cached/environment HF authentication.
            client = client_factory(SPACE, token=False, verbose=False,
                                    download_files=str(directory / 'downloads'),
                                    httpx_kwargs={'timeout': 30})
            info = client.view_api(return_format='dict', print_info=False)
            endpoint = info.get('named_endpoints', {}).get('/generate_video')
            if not endpoint:
                raise ValueError('Published generation endpoint missing')
            names = [p.get('parameter_name') for p in endpoint.get('parameters', [])]
            required = ['prompt', 'image_path', 'width', 'height', 'duration_seconds',
                        'auto_length', 'seed', 'randomize_seed', 'decoder']
            if names != required:
                raise ValueError('Published generation schema changed')
            record.update(status='SUBMITTING', discovered_endpoint='/generate_video')
            save(path, record)
            if before_submit is not None:
                # Callback MUST atomically reserve request_sha256 remotely and reject
                # ANY previous reservation. It must not merely overwrite a ledger.
                before_submit(dict(record))
            record['generation_attempted'] = True
            save(path, record)  # Before submit. Lost response is never resubmitted.
            job = client.submit(*[spec[k] for k in required], api_name='/generate_video')
            result = job.result(timeout=180)
            source = video_path(result)
            quality = inspect_clip(source)
            target = directory / ('ai-' + case + '-' + quality['sha256'][:16] + '.mp4')
            if not target.exists():
                shutil.copyfile(source, target)
            if hashlib.sha256(target.read_bytes()).hexdigest() != quality['sha256']:
                raise ValueError('Persisted generated MP4 hash mismatch')
            record.update(status='GENERATED_PENDING_VISUAL_REVIEW', file=target.name,
                          media=quality, usable_video_seconds=None,
                          model_output_generated=True, visual_quality_approved=False)
        except Exception as exc:
            record.update(status='UNKNOWN' if record['generation_attempted'] else 'BLOCKED',
                          error=classify_error(exc), error_type=type(exc).__name__)
        record['wall_seconds'] = round(time.monotonic()-started, 3)
        save(path, record)
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=list(PROMPTS), default='A')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    enabled = os.getenv('AI_VIDEO_EXPERIMENTAL_ENABLED', 'false').lower() == 'true'
    print(json.dumps(run(args.case, args.output, enabled), indent=2))


if __name__ == '__main__':
    main()
