"""Bounded, explicit cloud quality proofs using the existing production workflow."""
import json
from pathlib import Path
import preview_batch
import render_daily

PATH = Path(__file__).with_name('review_requests.json')


def main():
    data = json.loads(PATH.read_text())
    pending = [r for r in data['requests'] if r['status'] == 'pending']
    if not pending:
        print('PENDING_QUALITY_PROOFS=0')
        return
    selected = pending[:3]  # explicit requested batch, never public publishing
    concepts = [request['concept'] for request in selected]
    if len(set(concepts)) != len(concepts) or any(c not in {i[0] for i in render_daily.IDEAS} for c in concepts):
        raise ValueError('Unknown or duplicate review concept')
    report_path = render_daily.ROOT/'tmp/review-v3/report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    render_daily.atomic_json(report_path, [])
    try:
        preview_batch.main(concepts)
    finally:
        # Preserve completed proofs even when a later render fails.
        report = json.loads(report_path.read_text())
        for request in selected:
            matches = [r for r in report if r['concept'] == request['concept']]
            if matches:
                request.update(status='rendered_for_review', report=matches, published=False)
        render_daily.atomic_json(PATH, data)
    print('QUALITY_PROOFS_RENDERED_NOT_PUBLISHED=' + str(len(selected)))



if __name__ == '__main__':
    main()
