"""Conservative visual novelty gate. No paid API, no semantic-originality claims."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

POLICY_VERSION = 1


def fingerprint(path, source_id):
    path = Path(path)
    duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
        'format=duration', '-of', 'default=nw=1:nk=1', str(path)], text=True, timeout=30))
    frames = []
    for fraction in (.1, .3, .5, .7, .9):
        pixels = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(duration*fraction),
            '-i', str(path), '-frames:v', '1', '-vf', 'scale=9:8,format=gray',
            '-f', 'rawvideo', '-threads', '1', '-'], timeout=30)
        if len(pixels) != 72:
            raise ValueError('VISUAL_FINGERPRINT_INCOMPLETE')
        bits = 0
        for row in range(8):
            for col in range(8):
                bits = (bits << 1) | (pixels[row*9+col] > pixels[row*9+col+1])
        frames.append(f'{bits:016x}')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return dict(source_id=source_id, sha256=digest.hexdigest(), dhash=frames)


def similar(a, b):
    """Reject when >=60% of sampled frames have a close perceptual match."""
    left, right = a.get('dhash', []), b.get('dhash', [])
    if not left or not right:
        return False
    matches = sum(any((int(x, 16) ^ int(y, 16)).bit_count() <= 8 for y in right) for x in left)
    return matches / len(left) >= .6


def history(queue, state, exclude_id=None):
    entries = [(p.get('id'), p) for p in queue.get('posts', [])]
    entries += list(state.get('posts', {}).items())
    return [p.get('quality', p) for key, p in entries if key != exclude_id]


def check_sources(records, previous):
    if not records:
        raise ValueError('VISUAL_ASSETS_MISSING')
    for record in records:
        for old in previous:
            if record['source_id'] in old.get('source_urls', []):
                raise ValueError('VISUAL_SOURCE_REUSED: ' + record['source_id'])
            for existing in old.get('visual_sources', []):
                if record['source_id'] == existing['source_id'] or record['sha256'] == existing['sha256']:
                    raise ValueError('VISUAL_DUPLICATE_SOURCE')
                if similar(record, existing):
                    raise ValueError('VISUAL_NEAR_DUPLICATE')
    return dict(visual_policy_version=POLICY_VERSION, visual_distinct=True, visual_sources=records)


def preflight(source_ids, previous):
    used = {url for p in previous for url in p.get('source_urls', [])}
    used.update(r['source_id'] for p in previous for r in p.get('visual_sources', []))
    return not set(source_ids).intersection(used)


def require_evidence(post, previous=None):
    quality = post.get('quality') or {}
    if quality.get('visual_policy_version') != POLICY_VERSION or quality.get('visual_distinct') is not True:
        raise ValueError('VISUAL_REVIEW_REQUIRED: repeated or unmeasured scenes cannot be published')
    records = quality.get('visual_sources')
    if not isinstance(records, list) or not records:
        raise ValueError('VISUAL_FINGERPRINTS_REQUIRED')
    for record in records:
        if (not isinstance(record, dict) or not record.get('source_id')
            or not re.fullmatch(r'[0-9a-f]{64}', record.get('sha256', ''))
            or len(record.get('dhash', [])) != 5
            or any(not re.fullmatch(r'[0-9a-f]{16}', x) for x in record['dhash'])):
            raise ValueError('VISUAL_FINGERPRINTS_INVALID')
    if previous is not None:
        check_sources(records, previous)
