"""Offline, secret-safe operational inventory; never treats diagnostics as publication."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def inspect(queue, state, concepts, media_bytes, environ):
    used = {p.get('concept') for p in queue.get('posts', [])}
    used.update(p.get('concept') for p in state.get('posts', {}).values())
    remaining = len(set(concepts) - used)
    blockers = []
    provider = environ.get('PUBLISHING_PROVIDER', '').strip()
    if not provider:
        blockers.append('PROVIDER_NOT_SELECTED: configure PUBLISHING_PROVIDER after a read-only connection test')
    if provider == 'buffer' or not provider:
        for name in ('BUFFER_API_KEY', 'BUFFER_CHANNEL_ID'):
            if not environ.get(name, '').strip():
                blockers.append(name + '_MISSING')
    if remaining < 2:
        blockers.append('CATALOG_EXHAUSTED: fewer than two unused concepts; do not recycle old scripts')
    pending = [p for p in queue.get('posts', []) if p.get('id') not in state.get('posts', {})]
    for p in pending:
        reasons = []
        if not p.get('quality', {}).get('editorial_approved'):
            reasons.append('EDITORIAL_REVIEW_REQUIRED')
        if not p.get('publication_provider'):
            reasons.append('POST_ROUTE_NOT_ASSIGNED')
        if reasons:
            blockers.append(str(p.get('id')) + ': ' + ', '.join(reasons))
    if environ.get('MEDIA_STORAGE') != 'release' and media_bytes + 40_000_000 > 200_000_000:
        blockers.append('MEDIA_BUDGET_LOW: next pair may exceed existing source-repository storage cap')
    return dict(checked_at=datetime.now(timezone.utc).isoformat(),
                status='BLOCKED' if blockers else 'LOCAL_CHECKS_ONLY',
                unused_concepts=remaining, media_bytes=media_bytes, blockers=blockers,
                note='No authentication, public publication, alert delivery or unlimited capacity is inferred.')


def main():
    from render_daily import IDEAS
    queue = json.loads((ROOT/'automation/queue.json').read_text())
    state = json.loads((ROOT/'automation/state.json').read_text())
    size = sum(p.stat().st_size for p in (ROOT/'public/rendered').rglob('*.mp4'))
    result = inspect(queue, state, [i[0] for i in IDEAS], size, os.environ)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as out:
            out.write('## Operational readiness: ' + result['status'] + '\n\n')
            out.write('\n'.join('- ' + reason for reason in result['blockers']) + '\n\n')
            out.write(result['note'] + '\n')
    # This diagnostic is informational; the real publishing step retains its failure status.


if __name__ == '__main__':
    main()
