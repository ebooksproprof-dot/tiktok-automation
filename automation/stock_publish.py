"""Official Buffer adapter for durable stock; no generation or UI automation.

All cloud invocations share casasemesforco-state with legacy publishing. Every
request is counted remotely BEFORE HTTP. A claim and legacy reservation are
persisted before createPost. Uncertain writes are never automatically repeated.
"""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import timedelta

import buffer_quota
from daily_coverage import stamp as legacy_stamp
import buffer_runner as buffer
import video_stock as stock


class DurableClient:
    def __init__(self, legacy_store, token=None, now=None):
        self.store = legacy_store
        self.state, self.revision = legacy_store.load()
        if not isinstance(self.state.get('posts'), dict):
            raise ValueError('Existing legacy state unavailable; refusing empty fallback')
        self.token = token if token is not None else os.getenv('BUFFER_API_KEY', '').strip()
        if not self.token:
            raise RuntimeError('BUFFER_API_KEY missing')
        self.calls = 0
        self.now = now or buffer.common.utc_now

    def persist(self):
        self.revision = self.store.save(self.state, self.revision)
        # The legacy workflow may later persist this checkout; keep it current.
        buffer.common.save_json(buffer.common.STATE_PATH, self.state)

    def check_budget(self, required=1):
        buffer_quota.check(self.state, self.now(), required, self.calls)

    def call(self, query, variables):
        self.check_budget()
        self.calls += 1
        buffer_quota.record_attempt(self.state, self.now())
        self.persist()  # Remote commit, not merely runner disk.
        request = urllib.request.Request('https://api.buffer.com', method='POST',
            data=json.dumps({'query': query, 'variables': variables}).encode(),
            headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                buffer_quota.record_headers(self.state, response.headers, self.now())
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            buffer_quota.record_error(self.state, exc.code, exc.headers, self.now())
            self.persist()
            raise RuntimeError('Buffer HTTP ' + str(exc.code) + '; body omitted') from None
        except (urllib.error.URLError, TimeoutError, ValueError):
            buffer_quota.record_error(self.state, None, {}, self.now())
            self.persist()
            raise RuntimeError('Buffer outcome uncertain; do not resubmit') from None
        if not isinstance(result, dict) or result.get('errors') or not isinstance(result.get('data'), dict):
            buffer_quota.record_error(self.state, None, {}, self.now())
            self.persist()
            raise RuntimeError('Buffer response invalid; body omitted; do not resubmit')
        buffer_quota.record_success(self.state)
        self.persist()
        return result['data']


def legacy_records(legacy, legacy_queue):
    return list(legacy.get('posts', {}).values()) + list(legacy_queue.get('posts', []))


def check_item(item, legacy, legacy_queue, now):
    if item.get('status') != 'SCHEDULED' or item.get('attempts') != 0 or item.get('remote_id'):
        raise ValueError('Video already attempted or not scheduled')
    for field, expected in stock.IDENTITY.items():
        if item.get(field) != expected:
            raise ValueError('Official identity mismatch')
    for field in ('identity_reviewed', 'rights_reviewed', 'editorial_reviewed',
                  'lip_sync_reviewed', 'subtitles_reviewed'):
        if item.get(field) is not True:
            raise ValueError('Human audiovisual review required')
    if item.get('commercial_content') is not False:
        raise ValueError('Commercial disclosure unsupported by verified adapter; hold video')
    consent = stock.instant(item['reviewed_at'])
    if consent > now:
        raise ValueError('Future consent timestamp')
    quality = item.get('quality') or {}
    if quality.get('technical_pass') is not True or quality.get('sha256') != item.get('sha256'):
        raise ValueError('Matching technical validation required')
    when = stock.instant(item['scheduled_at'])
    if not now + timedelta(minutes=5) < when <= now + timedelta(hours=26):
        raise ValueError('Outside scheduling window')
    local = when.astimezone(stock.BRT)
    if local.hour not in (10, 18) or local.minute or local.second or local.microsecond:
        raise ValueError('Publication must be 10h or 18h Sao Paulo')
    for record in legacy_records(legacy, legacy_queue):
        sha = record.get('sha256') or (record.get('quality') or {}).get('sha256')
        if sha == item['sha256'] or record.get('script_sha256') == item['script_sha256']:
            raise ValueError('Video/script already in legacy pipeline')
        previous = record.get('scheduled_at')
        if previous is not None and legacy_stamp(previous) == when:
            raise ValueError('Slot reserved by legacy pipeline')
    caption = item.get('caption', '').strip()
    if not caption or len(caption) > 2200 or len(re.findall(r'(?<!\w)#\w+', caption)) > 5:
        raise ValueError('Caption empty or exceeds TikTok limits')
    return when


def payload(item, channel_id):
    return {'channelId': channel_id, 'text': item['caption'], 'schedulingType': 'automatic',
            'mode': 'customScheduled', 'dueAt': item['scheduled_at'], 'needsApproval': False,
            'saveToDraft': False, 'aiAssisted': True,
            'metadata': {'tiktok': {'isAiGenerated': True}},
            'assets': [{'video': {'url': item['storage_url']}}]}


def reconcile_one(store, client, item_id, channel_id, now):
    state, revision = store.load()
    item = stock.item_by_id(state, item_id)
    if not item.get('remote_id') or item['status'] == 'PUBLISHED':
        return
    remote = client.call('query($input: PostInput!) { post(input: $input) { ' +
                         buffer.POST_FIELDS + ' } }', {'input': {'id': item['remote_id']}})['post']
    entry = {'buffer_post_id': item['remote_id'], 'scheduled_at': item['scheduled_at']}
    buffer.record_remote(entry, remote, channel_id)
    result = 'PUBLISHED' if entry.get('publicly_verified') else (
        'FAILED' if entry['status'] == 'FAILED' else
        'SCHEDULED' if entry['status'] in ('SCHEDULED', 'SENDING') else 'UNKNOWN')
    publication_id = (entry.get('publicly_available_post_id') or [None])[0]
    stock.resolve(state, item_id, result, now, publication_id=publication_id,
                  evidence=entry.get('public_urls'), error=None if result != 'UNKNOWN' else 'REMOTE_EVIDENCE_PENDING')
    item['last_checked_at'] = stock.stamp(now)
    store.save(state, revision)
    client.state['posts'].setdefault(item_id, {}).update(entry)
    client.persist()


def submit_one(store, client, item_id, channel_id, legacy_queue, now):
    current, _ = store.load()
    candidate = stock.item_by_id(current, item_id)
    check_item(candidate, client.state, legacy_queue, now)
    # Re-read and decode hosted bytes immediately before reservation.
    buffer.verify_hosted({'video_url': candidate['storage_url'], 'quality': candidate['quality']})
    client.check_budget(required=2)
    state, revision, item = stock.durable_claim(store, item_id, now)
    entry = {'provider': 'buffer', 'status': 'SUBMISSION_UNKNOWN', 'sha256': item['sha256'],
             'script_sha256': item['script_sha256'], 'scheduled_at': item['scheduled_at'],
             'video_url': item['storage_url'], 'publicly_verified': False,
             'submitted_at': stock.stamp(now), 'stock_item_id': item_id}
    client.state['posts'][item_id] = entry
    client.persist()  # Also blocks legacy publication of this hash/script/slot.
    try:
        result = client.call(buffer.CREATE_QUERY, {'input': payload(item, channel_id)})['createPost']
        remote = result.get('post') or {}
        if result.get('__typename') != 'PostActionSuccess' or not remote.get('id'):
            raise RuntimeError('No confirmed remote ID')
        stock.resolve(state, item_id, 'UNKNOWN', now, remote_id=remote['id'])
        revision = store.save(state, revision)
        entry['buffer_post_id'] = remote['id']
        client.persist()
    except Exception:
        # If a checkpoint itself failed, this write may also fail; durable PUBLISHING
        # is already enough to prevent another create and recovery freezes UNKNOWN.
        stock.resolve(state, item_id, 'UNKNOWN', now, error='CREATE_OR_CHECKPOINT_UNCERTAIN')
        store.save(state, revision)
        raise
    reconcile_one(store, client, item_id, channel_id, now)


def run(store, legacy_store, legacy_queue, channel_id, now=None, check_only=False):
    now = stock.instant(now or buffer.common.utc_now())
    state, revision = store.load()
    stock.recover_interrupted(state, now)
    revision = store.save(state, revision)
    candidates = [i for i in state['items'] if i['status'] == 'SCHEDULED' and i['attempts'] == 0
                  and now + timedelta(minutes=5) < stock.instant(i['scheduled_at']) <= now + timedelta(hours=26)]
    pending = [i for i in state['items'] if i.get('remote_id') and i['status'] not in ('PUBLISHED', 'FAILED')
               and (i['status'] != 'SCHEDULED' or stock.instant(i['scheduled_at']) <= now)]
    legacy, _ = legacy_store.load()
    if not isinstance(legacy.get('posts'), dict):
        raise ValueError('Existing legacy state unavailable')
    eligible, held = [], []
    for candidate in candidates:
        try:
            check_item(candidate, legacy, legacy_queue, now)
            eligible.append(candidate)
        except (ValueError, KeyError) as exc:
            held.append({'id': candidate['id'], 'reason': str(exc)})
    candidates = eligible
    if not candidates and not pending and not check_only:
        return {'submitted': 0, 'reconciled': 0, 'api_calls': 0, 'held': held}
    client = DurableClient(legacy_store)
    channel = client.call(buffer.CHANNEL_QUERY, {'input': {'id': channel_id}})['channel']
    buffer.check_channel(channel, channel_id)
    if check_only:
        return {'channel_verified': True, 'submitted': 0, 'api_calls': client.calls, 'held': held}
    reconciled = submitted = 0
    for item in pending[:2]:
        reconcile_one(store, client, item['id'], channel_id, now)
        reconciled += 1
    if candidates:
        remote = client.call('query($input: PostsInput!) { posts(input: $input) { edges { node { channelId } } pageInfo { hasNextPage } } }',
            {'input': {'organizationId': channel['organizationId'], 'filter': {'status': ['scheduled', 'sending']}}})['posts']
        if remote['pageInfo']['hasNextPage']:
            raise RuntimeError('Remote queue truncated; free capacity unknown')
        occupied = sum(e['node']['channelId'] == channel_id for e in remote.get('edges') or [])
        for item in sorted(candidates, key=lambda i: i['scheduled_at'])[:min(2, max(0, 10 - occupied))]:
            submit_one(store, client, item['id'], channel_id, legacy_queue, now)
            submitted += 1
    return {'submitted': submitted, 'reconciled': reconciled, 'api_calls': client.calls, 'held': held}
