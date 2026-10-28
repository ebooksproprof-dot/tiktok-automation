"""Durable, fail-closed inventory for manually exported Symphony videos.

Small metadata lives in GitHub; MP4 bytes live in immutable Release assets.
GitHub's contents SHA is the compare-and-swap token. A lost PUT response is
uncertain: reload, never send the external publication from that invocation.
All writers must use this module; never overwrite inventory via git push.
"""
import base64
import copy
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

UTC = timezone.utc
BRT = ZoneInfo('America/Sao_Paulo')
REPO = 'ebooksproprof-dot/tiktok-automation'
IDENTITY = {'avatar_id': '7616458821397659655', 'voice_name': 'Keren', 'locale': 'pt-BR'}
STATES = {'GENERATING', 'READY', 'SCHEDULED', 'PUBLISHING', 'PUBLISHED', 'FAILED', 'REJECTED', 'UNKNOWN'}


class Conflict(RuntimeError):
    """Another writer won; no external mutation may follow this failure."""


def instant(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError('Timezone-aware timestamp required')
    return value.astimezone(UTC)


def stamp(value):
    return instant(value).isoformat().replace('+00:00', 'Z')


def empty():
    return {'schema_version': 1, 'items': [], 'events': []}


def encode(state):
    validate_state(state)
    return (json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def validate_state(state):
    if state.get('schema_version') != 1 or not isinstance(state.get('items'), list):
        raise ValueError('Unsupported inventory schema')
    for field in ('id', 'sha256', 'script_sha256'):
        values = [item[field] for item in state['items']]
        if len(values) != len(set(values)):
            raise ValueError('Duplicate inventory ' + field)
    slots = [stamp(item['scheduled_at']) for item in state['items'] if item.get('scheduled_at')]
    if len(slots) != len(set(slots)):
        raise ValueError('Duplicate inventory slot')
    if any(item['status'] not in STATES for item in state['items']):
        raise ValueError('Unknown inventory status')


class LocalStore:
    """Restart/concurrency-safe local development store; not cloud persistence."""
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return empty(), None
        raw = self.path.read_bytes()
        state = json.loads(raw)
        validate_state(state)
        return state, hashlib.sha256(raw).hexdigest()

    def save(self, state, expected_revision):
        raw = encode(state)
        with self.path.with_suffix(self.path.suffix + '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            _, revision = self.load()
            if revision != expected_revision:
                raise Conflict('Inventory changed; reload before continuing')
            with tempfile.NamedTemporaryFile(dir=self.path.parent, delete=False) as f:
                temporary = Path(f.name)
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
            try:
                os.replace(temporary, self.path)
                directory = os.open(self.path.parent, os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            finally:
                temporary.unlink(missing_ok=True)
        return hashlib.sha256(raw).hexdigest()


class GitHubStore:
    """Metadata CAS through the official GitHub contents API, no paid services."""
    def __init__(self, token, branch='main', path='automation/video_stock.json', validate=True):
        if not token:
            raise ValueError('GitHub token required')
        if not re.fullmatch(r'[A-Za-z0-9_./-]+', path) or not re.fullmatch(r'[A-Za-z0-9_/-]+', branch):
            raise ValueError('Invalid inventory location')
        self.token, self.branch = token, branch
        self.validate = validate
        self.url = 'https://api.github.com/repos/' + REPO + '/contents/' + path

    def request(self, method, payload=None):
        url = self.url + ('?ref=' + self.branch if method == 'GET' else '')
        request = urllib.request.Request(url, method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={'Authorization': 'Bearer ' + self.token,
                     'Accept': 'application/vnd.github+json',
                     'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if method == 'GET' and exc.code == 404:
                return None
            if exc.code in (409, 422):
                raise Conflict('Inventory CAS rejected; reload before continuing') from None
            raise RuntimeError('Inventory GitHub HTTP ' + str(exc.code) + '; body omitted') from None
        except (urllib.error.URLError, TimeoutError, ValueError):
            raise RuntimeError('Inventory response uncertain; reload and stop external mutations') from None

    def load(self):
        result = self.request('GET')
        if result is None:
            return empty(), None
        if result.get('encoding') != 'base64':
            raise ValueError('Inventory content unavailable; refusing empty fallback')
        state = json.loads(base64.b64decode(result['content']))
        if self.validate:
            validate_state(state)
        return state, result['sha']

    def save(self, state, expected_revision):
        payload = {'message': 'Checkpoint durable video inventory', 'branch': self.branch,
                   'content': base64.b64encode(encode(state) if self.validate else
                       (json.dumps(state, ensure_ascii=False, indent=2) + '\n').encode()).decode()}
        if expected_revision:
            payload['sha'] = expected_revision
        result = self.request('PUT', payload)
        revision = result.get('content', {}).get('sha')
        if not revision:
            raise RuntimeError('Inventory checkpoint unconfirmed; do not publish')
        return revision


def script_hash(script):
    return hashlib.sha256(' '.join(script.split()).casefold().encode()).hexdigest()


def item_by_id(state, item_id):
    return next(item for item in state['items'] if item['id'] == item_id)


def event(item, action, now, **details):
    item['history'].append({'at': stamp(now), 'action': action, **details})


def add_video(state, metadata, now):
    """Import already durably hosted, technically validated media.

    Human declarations are recorded, never described as machine identity proof.
    Unreviewed media is REJECTED, kept for deduplication and later review.
    """
    for key, value in IDENTITY.items():
        if metadata.get(key) != value:
            raise ValueError('Official identity mismatch: ' + key)
    digest = metadata.get('sha256', '')
    if not re.fullmatch(r'[a-f0-9]{64}', digest):
        raise ValueError('SHA-256 required')
    script = metadata.get('script', '').strip()
    if not 40 <= len(script) <= 2000:
        raise ValueError('Script must contain 40–2000 characters')
    shash = script_hash(script)
    if any(i['sha256'] == digest or i['script_sha256'] == shash for i in state['items']):
        raise ValueError('Duplicate video or script')
    url = metadata.get('storage_url', '')
    if not url.startswith('https://github.com/' + REPO + '/releases/download/') or not url.endswith('.mp4') or '?' in url:
        raise ValueError('Persistent repository Release MP4 URL required')
    quality = metadata.get('quality', {})
    if quality.get('technical_pass') is not True or quality.get('sha256') != digest:
        raise ValueError('Matching technical validation required')
    duration = quality.get('duration')
    if not isinstance(duration, (int, float)) or not 15 <= duration <= 28:
        raise ValueError('Duration outside validated 15–28 second policy')
    for key in ('filename', 'subject', 'source_evidence'):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(key + ' required')
    reviews = {key: metadata.get(key) is True for key in
               ('identity_reviewed', 'rights_reviewed', 'editorial_reviewed')}
    ready = all(reviews.values())
    item = dict(id='stock-' + digest, filename=metadata['filename'], storage_url=url,
                sha256=digest, created_at=stamp(now), script=script, script_sha256=shash,
                subject=metadata['subject'], **IDENTITY, duration=duration,
                validation_status='PASSED' if ready else 'REVIEW_REQUIRED',
                quality=copy.deepcopy(quality), **reviews,
                source_evidence=metadata['source_evidence'],
                status='READY' if ready else 'REJECTED', scheduled_at=None,
                remote_id=None, publication_id=None, history=[], attempts=0)
    # Keep provenance and explicit editorial decisions for the publishing adapter.
    # Unknown manifest keys are intentionally discarded (including credentials).
    for key in ('caption', 'commercial_content', 'reviewed_at', 'consented_at',
                'source_asset_id', 'source_asset_updated_at', 'source_created_at',
                'review', 'lip_sync_reviewed', 'subtitles_reviewed', 'media_persisted'):
        if key not in metadata:
            continue
        value = metadata[key]
        if key in ('commercial_content', 'lip_sync_reviewed', 'subtitles_reviewed', 'media_persisted'):
            if type(value) is not bool:
                raise ValueError(key + ' must be boolean')
        elif key == 'review':
            if not isinstance(value, dict) or any(type(v) is not bool for v in value.values()):
                raise ValueError('Review must contain boolean decisions')
        elif key in ('reviewed_at', 'consented_at', 'source_asset_updated_at', 'source_created_at'):
            value = stamp(value)
        elif key == 'caption':
            if not isinstance(value, str) or not value.strip() or len(value) > 2200:
                raise ValueError('Caption must contain 1–2200 characters')
        elif key == 'source_asset_id':
            if type(value) is not int or value <= 0:
                raise ValueError('Positive source asset ID required')
        item[key] = copy.deepcopy(value)
    event(item, 'IMPORTED', now, reviewed=ready)
    state['items'].append(item)
    validate_state(state)
    return item


def schedule(state, now, occupied_slots=()):
    """Reserve future 10h/18h local slots; retain past reservations for audit."""
    now = instant(now)
    occupied = {stamp(value) for value in occupied_slots if value}
    occupied.update(stamp(i['scheduled_at']) for i in state['items'] if i.get('scheduled_at'))
    day = now.astimezone(BRT).date()
    ready = [item for item in state['items'] if item['status'] == 'READY']
    for offset in range(366):
        date = day + timedelta(days=offset)
        for hour in (10, 18):
            slot = datetime(date.year, date.month, date.day, hour, tzinfo=BRT)
            if slot <= now + timedelta(minutes=10) or stamp(slot) in occupied:
                continue
            if not ready:
                return
            item = ready.pop(0)
            item.update(status='SCHEDULED', scheduled_at=stamp(slot))
            event(item, 'SLOT_RESERVED', now, slot=stamp(slot))
            occupied.add(stamp(slot))
    if ready:
        raise ValueError('Schedule horizon exhausted')


def claim(state, item_id, now):
    """Reserve once. Caller MUST save successfully before external HTTP."""
    item = item_by_id(state, item_id)
    if item['status'] != 'SCHEDULED' or item.get('remote_id') or item['attempts'] != 0:
        raise ValueError('Already attempted or not scheduled; no resubmission')
    if instant(item['scheduled_at']) <= instant(now) + timedelta(minutes=5):
        raise ValueError('Slot missed or too close; do not publish late')
    item.update(status='PUBLISHING', attempts=1)
    event(item, 'SUBMISSION_INTENT', now)
    return item


def durable_claim(store, item_id, now):
    state, revision = store.load()
    item = claim(state, item_id, now)
    revision = store.save(state, revision)
    return state, revision, item


def resolve(state, item_id, status, now, remote_id=None, publication_id=None, evidence=None, error=None):
    """Reconcile an attempted item; UNKNOWN never resets attempts or permits retry."""
    item = item_by_id(state, item_id)
    if item['status'] not in ('PUBLISHING', 'UNKNOWN', 'SCHEDULED', 'FAILED') or item['attempts'] != 1:
        raise ValueError('No attempted publication to reconcile')
    if status not in ('SCHEDULED', 'PUBLISHED', 'FAILED', 'UNKNOWN'):
        raise ValueError('Invalid remote resolution')
    if remote_id and item.get('remote_id') not in (None, remote_id):
        raise ValueError('Remote identity mismatch')
    if status == 'SCHEDULED' and not (remote_id or item.get('remote_id')):
        raise ValueError('Remote scheduling ID required')
    if status == 'PUBLISHED' and not (publication_id and evidence and (remote_id or item.get('remote_id'))):
        raise ValueError('Remote ID, publication ID and verification evidence required')
    item['status'] = status
    if remote_id:
        item['remote_id'] = remote_id
    if publication_id:
        item['publication_id'] = publication_id
    if status == 'PUBLISHED':
        item['publication_evidence'] = evidence
        item['published_at'] = stamp(now)
    event(item, 'RECONCILED', now, status=status, error=error)


def recover_interrupted(state, now):
    """Call only inside the cloud runner's shared concurrency lock."""
    for item in state['items']:
        if item['status'] == 'PUBLISHING':
            resolve(state, item['id'], 'UNKNOWN', now, error='INTERRUPTED_SUBMISSION_DO_NOT_RETRY')


def stock_report(state, now):
    available = sum(i['status'] in ('READY', 'SCHEDULED') for i in state['items'])
    return {'available': available, 'low_stock': available < 7, 'target_min': 14,
            'target_max': 28, 'refill_needed': max(0, 14 - available),
            'unknown': sum(i['status'] == 'UNKNOWN' for i in state['items']),
            'missed_slots': [i['id'] for i in state['items'] if i['status'] == 'SCHEDULED'
                             and instant(i['scheduled_at']) < instant(now)],
            'published': sum(i['status'] == 'PUBLISHED' for i in state['items'])}
