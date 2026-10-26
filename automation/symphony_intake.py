"""Offline Symphony intake. No generation, API calls, approval or publication.

The Studio IDs are user-selected requirements, not verified API identifiers.
Queue edits require the same serialized GitHub state concurrency as production.
Imported files remain pending human review of identity, voice, lip-sync and rights.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

from media_quality import validate

ROOT = Path(__file__).resolve().parents[1]


def load_config(path):
    config = json.loads(Path(path).read_text())
    expected = dict(provider='tiktok_symphony', avatar_id='7616458821397659655',
                    voice_name='Keren', locale='pt-BR', width=1080, height=1920,
                    timezone='America/Sao_Paulo', publication_hours=[10, 18],
                    additional_budget_brl=0, fallback_voice_allowed=False,
                    fallback_avatar_allowed=False)
    for key, value in expected.items():
        if config.get(key) != value or type(config.get(key)) is not type(value):
            raise ValueError('Official configuration mismatch: ' + key)
    if config.get('generation_enabled') is not False:
        raise ValueError('No verified API adapter installed; generation must remain disabled')
    return config


def save_queue(path, queue):
    """Atomic replace; callers must serialize concurrent writers."""
    path = Path(path)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        json.dump(queue, f, ensure_ascii=False, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def enqueue(queue, script, config):
    script = ' '.join(script.split())
    if not 40 <= len(script) <= 2000:
        raise ValueError('Expected an original pt-BR script between 40 and 2000 characters')
    digest = hashlib.sha256(script.casefold().encode()).hexdigest()
    if any(x['script_sha256'] == digest for x in queue['items']):
        raise ValueError('Duplicate script')
    if len(queue['items']) >= 60:
        raise ValueError('Intake limit reached; review existing queue first')
    item = dict(id='symphony-' + digest[:16], script=script, script_sha256=digest,
                requested_identity={k: config[k] for k in ('avatar_id', 'voice_name', 'locale')},
                status='BLOCKED_API_ACCESS', approved=False)
    queue['items'].append(item)
    return item


def attach(queue, item_id, video, manifest, config):
    item = next(x for x in queue['items'] if x['id'] == item_id)
    if item['status'] != 'BLOCKED_API_ACCESS':
        raise ValueError('Item already has a candidate; do not overwrite evidence')
    for key in ('avatar_id', 'voice_name', 'locale'):
        if manifest.get(key) != config[key]:
            raise ValueError('Candidate identity mismatch: ' + key)
    if manifest.get('script_sha256') != item['script_sha256']:
        raise ValueError('Candidate script mismatch')
    if not isinstance(manifest.get('source_evidence'), str) or not manifest['source_evidence'].strip():
        raise ValueError('Studio export evidence reference required')
    video = Path(video)
    if not video.is_file() or video.suffix.lower() != '.mp4':
        raise ValueError('A real local MP4 is required')
    if not 100_000 <= video.stat().st_size <= 20_000_000:
        raise ValueError('Candidate outside existing media size limits')
    digest = hashlib.sha256(video.read_bytes()).hexdigest()
    if manifest.get('sha256') != digest:
        raise ValueError('Candidate hash mismatch')
    if any(x.get('media_sha256') == digest for x in queue['items']):
        raise ValueError('Duplicate video')
    quality = validate(video)  # Existing real FFmpeg/ffprobe validator, never a mock in CLI.
    item.update(status='PENDING_IDENTITY_AND_EDITORIAL_REVIEW', media_sha256=digest,
                local_media_path=str(video.resolve()), media_persisted=False,
                technical_validation=quality,
                declared_identity={k: manifest[k] for k in ('avatar_id', 'voice_name', 'locale')},
                source_evidence=manifest['source_evidence'], identity_verified=False,
                lip_sync_verified=False, approved=False)
    return item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'automation/symphony.json')
    parser.add_argument('--queue', type=Path, default=ROOT/'automation/symphony_queue.json')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    add = commands.add_parser('enqueue')
    add.add_argument('--script-file', type=Path, required=True)
    imp = commands.add_parser('import')
    imp.add_argument('--id', required=True)
    imp.add_argument('--video', type=Path, required=True)
    imp.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    queue = json.loads(args.queue.read_text())
    if args.command == 'status':
        result = dict(generation_enabled=False, api_adapter_installed=False,
                      blocked_reason=config['blocked_reason'], queue_items=len(queue['items']),
                      imported_candidates=sum('media_sha256' in x for x in queue['items']),
                      api_capacity=config['api_capacity'], publication_enabled=False)
    elif args.command == 'enqueue':
        result = enqueue(queue, args.script_file.read_text(), config)
        save_queue(args.queue, queue)
    else:
        result = attach(queue, args.id, args.video, json.loads(args.manifest.read_text()), config)
        save_queue(args.queue, queue)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
