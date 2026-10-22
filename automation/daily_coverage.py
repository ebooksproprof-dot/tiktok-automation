"""Read-only daily delivery gate. Run AFTER reconciliation and state persistence."""
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo('America/Sao_Paulo')


def stamp(value):
    if isinstance(value, dict):
        result = dt.datetime.fromisoformat(value['dateTime'].replace('Z', '+00:00'))
        return result if result.tzinfo else result.replace(tzinfo=ZoneInfo(value['timezone']))
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if not result.tzinfo:
        raise ValueError('Timezone required')
    return result


def inspect(queue, state, now):
    day = now.astimezone(TZ).date()
    rows = []
    for hour in (10, 18):
        due = dt.datetime.combine(day, dt.time(hour), TZ)
        submitted, drafts = [], []
        for source, entries in ((submitted, state.get('posts', {}).values()),
                                (drafts, queue.get('posts', []))):
            for entry in entries:
                try:
                    if stamp(entry.get('scheduled_at')) == due:
                        source.append(entry)
                except (ValueError, TypeError, AttributeError, KeyError):
                    continue
        verified = [p for p in submitted if p.get('status') == 'PUBLISH_COMPLETE'
                    and p.get('publicly_verified') is True and p.get('public_urls')]
        if len(submitted) > 1:
            status = 'MULTIPLE_RESERVATIONS_REVIEW_REQUIRED'
        elif verified:
            status = 'PUBLISHED_PROVIDER_CONFIRMED'
        elif submitted:
            status = submitted[0].get('status', 'UNKNOWN')
            if status in ('SCHEDULED', 'SENDING') and now > due + dt.timedelta(hours=2):
                status = 'PUBLICATION_OVERDUE'
        elif drafts:
            status = 'NOT_SUBMITTED_REVIEW_ROUTE_OR_CONSENT_REQUIRED'
        else:
            status = 'NO_VIDEO'
        covered = status in ('PUBLISHED_PROVIDER_CONFIRMED', 'SCHEDULED', 'SENDING')
        # Before the lead window, report the gap without paging for unrendered future work.
        blocking = not covered and now >= due - dt.timedelta(hours=1)
        rows.append(dict(scheduled_at=due.isoformat(), status=status, blocking=blocking))
    return dict(day=str(day), slots=rows, blocked=any(r['blocking'] for r in rows),
                note='Provider evidence only; this does not prove sustained autonomous production.')


def main():
    root = Path(__file__).resolve().parent
    result = inspect(json.loads((root/'queue.json').read_text()),
                     json.loads((root/'state.json').read_text()), dt.datetime.now(dt.timezone.utc))
    print(json.dumps(result, indent=2))
    summary = os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as out:
            out.write('\n## Daily delivery coverage\n\n')
            for row in result['slots']:
                out.write('- ' + row['scheduled_at'] + ': ' + row['status'] + '\n')
    return 2 if result['blocked'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
