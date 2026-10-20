"""Stage up to two explicitly SHA-approved proofs; never submit to Buffer here.

An upload intent is persisted before the remote write. Interrupted/ambiguous
intents are not retried or moved to another slot automatically.
"""
import copy
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import render_daily as r
import visual_library as visual
from content_catalog import category, fingerprint
from media_quality import validate
from release_media import publish

TZ = ZoneInfo('America/Fortaleza')
ID_PATTERN = re.compile(r'casasem-(\d{4}-\d{2}-\d{2})-([12])')


def read(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def next_slot(queue, state, now):
    planned = now.astimezone(TZ).replace(hour=10, minute=0, second=0, microsecond=0)
    entries = {p['id']: p for p in queue['posts']}
    entries.update(state.get('posts', {}))
    occupied_days = {}
    for identity, entry in entries.items():
        match = ID_PATTERN.fullmatch(identity)
        if match:
            occupied_days.setdefault(match[1], set()).add(identity)
        stamp = entry.get('scheduled_at')
        if isinstance(stamp, str):
            parsed = dt.datetime.fromisoformat(stamp.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                raise ValueError('SCHEDULE_TIMEZONE_REQUIRED')
            occupied_days.setdefault(parsed.astimezone(TZ).date().isoformat(), set()).add(identity)
        elif isinstance(stamp, dict):
            parsed = dt.datetime.fromisoformat(stamp['dateTime'].replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=ZoneInfo(stamp['timezone']))
            occupied_days.setdefault(parsed.astimezone(TZ).date().isoformat(), set()).add(identity)
    for _ in range(62):
        candidate = r.future_slot(planned, queue, state, '__new_requested_proof__', now=now)
        day = candidate.date().isoformat()
        identity = f'casasem-{day}-{1 if candidate.hour == 10 else 2}'
        if identity not in entries and len(occupied_days.get(day, ())) < 2:
            return identity, candidate
        planned = ((candidate + dt.timedelta(days=1)).replace(hour=10)
                   if candidate.hour == 18 or len(occupied_days.get(day, ())) >= 2
                   else candidate.replace(hour=18))
    raise ValueError('NO_SAFE_FUTURE_SLOT')


def approved_report(request, folder, now):
    approval = request['approval']
    expected = approval.get('sha256', '')
    if approval.get('route') != 'buffer' or not re.fullmatch(r'[a-f0-9]{64}', expected):
        raise ValueError('EXPLICIT_BUFFER_SHA_APPROVAL_REQUIRED')
    approved_at = dt.datetime.fromisoformat(approval.get('approved_at', '').replace('Z', '+00:00'))
    if approved_at.tzinfo is None or approved_at > now:
        raise ValueError('INVALID_APPROVAL_TIMESTAMP')
    matches = [x for x in request.get('report', []) if x.get('concept') == request['concept']]
    if len(matches) != 1:
        raise ValueError('PROOF_REPORT_NOT_UNIQUE')
    report = matches[0]
    name = report.get('file', '')
    if not name or Path(name).name != name or not name.endswith('.mp4'):
        raise ValueError('INVALID_PROOF_PATH')
    path = folder/name
    if path.is_symlink() or path.resolve().parent != folder.resolve():
        raise ValueError('INVALID_PROOF_PATH')
    quality = copy.deepcopy(report['quality'])
    if quality.get('sha256') != expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('APPROVED_PROOF_SHA_MISMATCH')
    measured = validate(path)
    if measured.get('technical_pass') is not True or measured.get('sha256') != expected:
        raise ValueError('PROOF_TECHNICAL_VALIDATION_FAILED')
    quality.update(measured)
    script = report.get('script')
    if not isinstance(script, list) or not script or any(not isinstance(x, str) or not x.strip() for x in script):
        raise ValueError('INVALID_PROOF_SCRIPT')
    credits = quality.get('required_public_credits', [])
    if not isinstance(credits, list) or any(not isinstance(x, str) or not x.strip() for x in credits):
        raise ValueError('INVALID_REQUIRED_CREDITS')
    title = ' '.join(script) + ' #CasaSemEsforco #OrganizacaoDaCasa'
    if credits:
        title += '\n\n' + '\n'.join(credits)
    if len(title) > 2200 or len(re.findall(r'(?<!\w)#\w+', title)) > 5:
        raise ValueError('CAPTION_LIMIT_EXCEEDED')
    return path, report, quality, title


def main(root=None, folder=None, now=None):
    root = Path(root) if root is not None else r.ROOT/'automation'
    folder = Path(folder) if folder is not None else r.ROOT/'tmp/review-v3'
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('NOW_TIMEZONE_REQUIRED')
    requests_path, queue_path = root/'review_requests.json', root/'queue.json'
    data = read(requests_path, {'requests': []})
    queue = read(queue_path, {'posts': []})
    state = read(root/'state.json', {'posts': {}})
    staged = 0
    for request in data['requests']:
        if staged >= 2:
            break
        if request.get('staged_post_id') or request.get('staging_post_id'):
            # A durable intent cannot silently receive a new ID after interruption.
            continue
        if request.get('status') != 'rendered_for_review' or not request.get('approval'):
            continue
        path, report, quality, title = approved_report(request, folder, now)
        previous = visual.history(queue, state)
        previous.append(read(root/'visual_history.json', {}))
        visual.require_evidence({'quality': quality, 'title': title}, previous)
        if any(p.get('concept') == report['concept'] or p.get('quality', p).get('sha256') == quality['sha256']
               for p in list(queue['posts']) + list(state.get('posts', {}).values())):
            raise ValueError('PROOF_CONCEPT_OR_MEDIA_ALREADY_QUEUED')
        post_id, scheduled = next_slot(queue, state, now)
        request.update(staging_post_id=post_id, staging_status='UPLOAD_INTENT',
                       staging_sha256=quality['sha256'])
        r.atomic_json(requests_path, data)
        try:
            video_url = publish(path, post_id, quality)
        except Exception:
            request['staging_status'] = 'UPLOAD_OUTCOME_UNKNOWN_RECONCILE_BEFORE_RETRY'
            r.atomic_json(requests_path, data)
            raise
        quality['editorial_approved'] = True
        entry = dict(id=post_id, concept=report['concept'], category=category(report['concept']),
                     script_lines=report['script'], script_sha256=fingerprint(report['script']),
                     title=title, quality=quality, video_url=video_url, media_storage='release',
                     scheduled_at=scheduled.isoformat(), render_version=2,
                     composition_revision=quality.get('composition_revision', r.COMPOSITION_REVISION),
                     approved=True, consented_at=request['approval']['approved_at'],
                     approved_provider='buffer', publication_provider='buffer',
                     publishing_status='APPROVED_FOR_BUFFER_NOT_SUBMITTED',
                     proof_request_concept=request['concept'])
        queue['posts'].append(entry)
        r.atomic_json(queue_path, queue)
        request.update(staged_post_id=post_id, staging_status='RELEASE_VERIFIED_QUEUE_PERSISTED',
                       status='staged_for_buffer', published=False)
        r.atomic_json(requests_path, data)
        staged += 1
    print(f'APPROVED_PROOFS_STAGED={staged}; PUBLICATION_CONFIRMED=false')
    return staged


if __name__ == '__main__':
    main()
