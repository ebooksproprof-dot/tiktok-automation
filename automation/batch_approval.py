"""Offline explicit batch consent. Export and dry-run do not approve or publish.

The complete queue/state snapshots bind the approval. Reviewers must inspect each
exact MP4 and attest editorial review. Hosted bytes are revalidated by the runner.
"""
import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from content_catalog import fingerprint
from visual_library import history, require_evidence

ROOT = Path(__file__).resolve().parent
TZ = ZoneInfo('America/Sao_Paulo')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def stamp(value):
    if not isinstance(value, str):
        raise ValueError('TIMESTAMP_REQUIRED')
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('TIMESTAMP_TIMEZONE_REQUIRED')
    return result


def identity(post):
    lines = post.get('script_lines')
    if not isinstance(lines, list) or not lines or any(not isinstance(x, str) for x in lines):
        raise ValueError('EXACT_SCRIPT_REQUIRED')
    script_hash = fingerprint(lines)
    if script_hash != post.get('script_sha256'):
        raise ValueError('SCRIPT_HASH_MISMATCH')
    sha = post.get('quality', {}).get('sha256', '')
    if not isinstance(sha, str) or not re.fullmatch(r'[a-f0-9]{64}', sha):
        raise ValueError('MEDIA_HASH_REQUIRED')
    return dict(id=post['id'], video_url=post['video_url'], sha256=sha,
                script_hash=script_hash, scheduled_at=post['scheduled_at'],
                post_snapshot_sha256=digest(post))


def export_manifest(queue, state):
    pending = [p for p in queue['posts'] if p.get('id') not in state.get('posts', {})
               and p.get('approved') is not True and p.get('quality', {}).get('technical_pass') is True]
    return dict(version=1, approved=False, consented_at=None, route='buffer',
                queue_snapshot_sha256=digest(queue), state_snapshot_sha256=digest(state),
                items=[dict(**identity(p), editorial_approved=False, review='') for p in pending],
                notice='Inspect every exact MP4 and script. Fill explicit consent and review; no publishing occurs here.')


def approve(queue, state, manifest, now=None, legacy=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    if (manifest.get('version') != 1 or manifest.get('approved') is not True
            or manifest.get('route') != 'buffer'):
        raise ValueError('EXPLICIT_BUFFER_BATCH_APPROVAL_REQUIRED')
    consent = stamp(manifest.get('consented_at'))
    if consent > now:
        raise ValueError('FUTURE_CONSENT_REJECTED')
    if manifest.get('queue_snapshot_sha256') != digest(queue) or manifest.get('state_snapshot_sha256') != digest(state):
        raise ValueError('SNAPSHOT_CHANGED_EXPORT_AND_REVIEW_AGAIN')
    items = manifest.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= 14:
        raise ValueError('APPROVAL_BATCH_REQUIRES_ONE_TO_FOURTEEN_ITEMS')
    ids = [p.get('id') for p in queue['posts']]
    requested = [item.get('id') for item in items]
    if len(ids) != len(set(ids)) or len(requested) != len(set(requested)):
        raise ValueError('DUPLICATE_POST_ID')
    proposed = copy.deepcopy(queue)
    by_id = {p['id']: p for p in proposed['posts']}
    for item in items:
        post = by_id.get(item.get('id'))
        if post is None or post['id'] in state.get('posts', {}) or any(post.get(key) for key in
                ('public_url', 'metricool_post_id', 'buffer_post_id', 'publish_id')):
            raise ValueError('UNKNOWN_OR_ALREADY_SUBMITTED_POST')
        if post.get('approved') is True:
            raise ValueError('POST_ALREADY_APPROVED')
        for key, value in identity(post).items():
            if item.get(key) != value:
                raise ValueError('REVIEWED_POST_CHANGED: ' + key)
        if item.get('editorial_approved') is not True or not isinstance(item.get('review'), str) or len(item['review'].strip()) < 20:
            raise ValueError('EXPLICIT_EDITORIAL_REVIEW_REQUIRED')
        if post.get('quality', {}).get('technical_pass') is not True:
            raise ValueError('TECHNICAL_VALIDATION_REQUIRED')
        due = stamp(post['scheduled_at'])
        local = due.astimezone(TZ)
        if due < now + dt.timedelta(minutes=5) or due > now + dt.timedelta(days=7):
            raise ValueError('SLOT_EXPIRED_OR_OUTSIDE_SEVEN_DAY_BATCH_WINDOW')
        if (local.hour not in (10, 18) or local.minute or local.second or local.microsecond):
            raise ValueError('ONLY_10H_OR_18H_SLOTS_ALLOWED')
        sha = item['sha256']
        other_posts = [p for p in queue['posts'] if p['id'] != post['id']]
        other_posts += list(state.get('posts', {}).values())
        occupied = set()
        for previous in other_posts:
            previous_sha = previous.get('quality', previous).get('sha256')
            if previous_sha == sha:
                raise ValueError('DUPLICATE_MEDIA_HASH')
            previous_due = previous.get('scheduled_at')
            if isinstance(previous_due, dict):
                value = dt.datetime.fromisoformat(previous_due['dateTime'].replace('Z', '+00:00'))
                prior = value if value.tzinfo else value.replace(tzinfo=ZoneInfo(previous_due['timezone']))
            elif previous_due:
                prior = stamp(previous_due)
            else:
                continue
            if prior == due:
                raise ValueError('SLOT_ALREADY_RESERVED')
            if prior.astimezone(TZ).date() == local.date():
                occupied.add(prior)
        if len(occupied) >= 2:
            raise ValueError('TWO_DAILY_SLOTS_ALREADY_RESERVED')
        previous = history(queue, state, exclude_id=post['id'])
        if legacy:
            previous.append(legacy)
        require_evidence(post, previous)
        if not post['video_url'].startswith(('https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-',
                                             'https://ebooksproprof-dot.github.io/tiktok-automation/public/rendered/daily/',
                                             'https://raw.githubusercontent.com/ebooksproprof-dot/tiktok-automation/')) or not post['video_url'].endswith('.mp4'):
            raise ValueError('EXISTING_APPROVED_MEDIA_HOST_REQUIRED')
        post.update(approved=True, consented_at=manifest['consented_at'],
                    publication_provider='buffer', approved_provider='buffer',
                    editorial_review=item['review'].strip(),
                    batch_approval_sha256=digest(manifest),
                    publishing_status='APPROVED_FOR_BUFFER_NOT_SUBMITTED')
        post['quality']['editorial_approved'] = True
    return proposed


def run(root, manifest_path=None, export_path=None, apply=False, now=None):
    root = Path(root)
    queue_path, state_path = root/'queue.json', root/'state.json'
    queue_bytes, state_bytes = queue_path.read_bytes(), state_path.read_bytes()
    queue, state = json.loads(queue_bytes), json.loads(state_bytes)
    if export_path:
        if apply or manifest_path:
            raise ValueError('EXPORT_IS_SEPARATE_FROM_APPROVAL')
        destination = Path(export_path)
        if destination.resolve() in (queue_path.resolve(), state_path.resolve()):
            raise ValueError('EXPORT_MUST_NOT_OVERWRITE_OPERATIONAL_FILES')
        with destination.open('x', encoding='utf8') as out:
            json.dump(export_manifest(queue, state), out, ensure_ascii=False, indent=2)
        return dict(exported=str(destination), applied=False, published=False)
    if manifest_path is None:
        raise ValueError('MANIFEST_OR_EXPORT_REQUIRED')
    manifest = json.loads(Path(manifest_path).read_text())
    legacy_path = root/'visual_history.json'
    legacy = json.loads(legacy_path.read_text()) if legacy_path.exists() else None
    proposed = approve(queue, state, manifest, now, legacy)
    if apply:
        if queue_bytes != queue_path.read_bytes() or state_bytes != state_path.read_bytes():
            raise ValueError('CONCURRENT_STATE_CHANGE')
        import tempfile
        with tempfile.NamedTemporaryFile('w', encoding='utf8', dir=root, delete=False) as out:
            target = Path(out.name)
            json.dump(proposed, out, ensure_ascii=False, indent=2)
            out.write('\n')
        target.replace(queue_path)
    return dict(validated=len(manifest['items']), applied=apply, published=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--export', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.manifest, args.export, args.apply), indent=2))
