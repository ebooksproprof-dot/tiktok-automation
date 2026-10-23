"""Prepare an in-memory approval only after explicit, hash-bound chat consent.

No CLI apply, filesystem writes, network calls, timestamp inference or publication.
The caller must supply actual human consent; selecting in the static UI is not consent.
"""
import copy
import datetime as dt

from batch_approval import approve, digest, identity, stamp
from review_batch44 import build_preview


def approve_preview(queue, state, archived, preview, selected_ids, consented_at, review,
                    *, authorized_manifest_sha256, approved=False, now=None):
    """Return a proposed queue; caller is responsible for authorized atomic persistence.

The authorization hash and IDs must come from the explicit user response. Never
populate them from an unchecked preview or infer consent from generating a preview.
"""
    now = now or dt.datetime.now(dt.timezone.utc)
    if approved is not True:
        raise ValueError('EXPLICIT_CHAT_CONSENT_REQUIRED')
    if not isinstance(review, str) or len(review.strip()) < 20:
        raise ValueError('EXPLICIT_EDITORIAL_REVIEW_REQUIRED')
    if not isinstance(selected_ids, list) or not selected_ids or any(not isinstance(x, str) for x in selected_ids):
        raise ValueError('EXPLICIT_SELECTED_IDS_REQUIRED')
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError('DUPLICATE_SELECTED_IDS')
    body = copy.deepcopy(preview)
    recorded_hash = body.pop('manifest_sha256', None)
    if (not isinstance(authorized_manifest_sha256, str) or not authorized_manifest_sha256
            or recorded_hash != authorized_manifest_sha256 or digest(body) != recorded_hash):
        raise ValueError('AUTHORIZED_PREVIEW_HASH_MISMATCH')
    if (preview.get('schema') != 'casasem-review-preview-4.4' or preview.get('approved') is not False
            or preview.get('consented_at') is not None or preview.get('submitted') is not False
            or preview.get('route') != 'buffer'):
        raise ValueError('INVALID_PREVIEW_STATE')
    if (preview.get('queue_snapshot_sha256') != digest(queue)
            or preview.get('state_snapshot_sha256') != digest(state)
            or preview.get('archived_history_sha256') != (digest(archived) if archived is not None else None)):
        raise ValueError('SNAPSHOT_CHANGED_REVIEW_AGAIN')
    generated = stamp(preview.get('generated_at'))
    consent = stamp(consented_at)
    if not generated <= consent <= now:
        raise ValueError('CONSENT_TIMESTAMP_OUTSIDE_REVIEW_WINDOW')
    if now >= stamp(preview.get('expires_at')):
        raise ValueError('PREVIEW_EXPIRED_REVIEW_AGAIN')
    # Recompute proposals at the original instant: even a rehashed edited slot
    # cannot silently replace the deterministic proposal shown in this preview.
    expected = build_preview(queue, state, generated, archived=archived)
    if preview.get('expires_at') != expected['expires_at']:
        raise ValueError('PREVIEW_EXPIRY_CHANGED')
    items = preview.get('items')
    if not isinstance(items, list) or [p.get('id') for p in items] != [p['id'] for p in expected['items']]:
        raise ValueError('PREVIEW_ITEMS_CHANGED')
    for item, original in zip(items, expected['items']):
        for key, value in original.items():
            if key != 'audit_notes' and item.get(key) != value:
                raise ValueError('PREVIEW_ITEM_CHANGED: ' + key)
    by_id = {p['id']: p for p in items}
    for key in selected_ids:
        if key not in by_id or by_id[key].get('selectable') is not True:
            raise ValueError('SELECTED_ITEM_NOT_ELIGIBLE')
    proposed = copy.deepcopy(queue)
    proposed_by_id = {p['id']: p for p in proposed['posts']}
    for key in selected_ids:
        post, item = proposed_by_id[key], by_id[key]
        original_identity = identity(post)
        for field in ('id', 'video_url', 'sha256', 'script_hash', 'post_snapshot_sha256'):
            if item.get(field) != original_identity[field]:
                raise ValueError('REVIEWED_IDENTITY_CHANGED')
        if item.get('original_scheduled_at') != post.get('scheduled_at'):
            raise ValueError('ORIGINAL_SCHEDULE_CHANGED')
        post['scheduled_at'] = item['proposed_scheduled_at']
    # Existing gates still validate hashes, novelty, credits, slots, collisions,
    # technical/editorial validation and already submitted IDs for the whole batch.
    manifest = dict(version=1, approved=True, route='buffer', consented_at=consented_at,
                    queue_snapshot_sha256=digest(proposed), state_snapshot_sha256=digest(state),
                    source_preview_sha256=recorded_hash,
                    items=[dict(**identity(proposed_by_id[key]), editorial_approved=True,
                                review=review.strip()) for key in selected_ids])
    return approve(proposed, state, manifest, now=now, legacy=archived)
