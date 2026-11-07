"""Bounded read-only confirmation for the explicitly authorized near-term test.

Regular 10h/18h reconciliation retains the existing crons. No createPost here.
"""
import datetime as dt
import json
import time
import os
from zoneinfo import ZoneInfo

import buffer_runner as buffer


def candidate(queue, state, now):
    for post in queue.get('posts', []):
        if post.get('approval_scope') != 'mission102_owner_authorized_automated_quality_and_license_checks':
            continue
        entry = state.get('posts', {}).get(post['id'], {})
        try:
            due = buffer.common.parse_time(entry.get('scheduled_at'))
            submitted = buffer.common.parse_time(entry.get('submitted_at'))
        except (ValueError, TypeError):
            continue
        if not due:
            continue
        local = due.astimezone(ZoneInfo('America/Sao_Paulo'))
        regular = local.hour in (10, 18) and local.minute == local.second == local.microsecond == 0
        if post.get('first_test_outside_recurring_slots') is not True and regular:
            continue
        if (entry.get('provider') == 'buffer' and entry.get('buffer_post_id')
                and entry.get('publicly_verified') is not True
                and entry.get('status') in ('SCHEDULED', 'SENDING') and due and submitted
                and now-dt.timedelta(minutes=10) <= submitted <= now
                and now-dt.timedelta(minutes=2) <= due <= now+dt.timedelta(minutes=22)):
            return post['id'], due
    return None


def main():
    queue = buffer.common.load_json(buffer.common.QUEUE_PATH, {'posts': []})
    state = buffer.common.load_json(buffer.common.STATE_PATH, {'posts': {}})
    selected = candidate(queue, state, buffer.common.utc_now())
    if not selected:
        print('NO_NEAR_DUE_TEST; routine provider reconciliation remains scheduled')
        return 0
    post_id, due = selected
    target = due+dt.timedelta(seconds=90)
    print('READ_ONLY_CONFIRMATION_WAIT='+post_id+'; due='+due.isoformat(), flush=True)
    while buffer.common.utc_now() < target:
        time.sleep(min(30, max(0, (target-buffer.common.utc_now()).total_seconds())))
    code = buffer.confirm_post(post_id)
    current = buffer.common.load_json(buffer.common.STATE_PATH, {'posts': {}})['posts'][post_id]
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as out:
            out.write('\n## Public test confirmation (read-only)\n\n'+post_id+': '+current['status']+'\n')
            for url in current.get('public_urls', []):
                out.write(url+'\n')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
