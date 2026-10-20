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
    request = pending[0]  # maximum one extra proof per run
    if request['concept'] not in {i[0] for i in render_daily.IDEAS}:
        raise ValueError('Unknown review concept')
    preview_batch.main([request['concept']])
    report = json.loads((render_daily.ROOT/'tmp/review-v3/report.json').read_text())
    request.update(status='rendered_for_review', report=report, published=False)
    render_daily.atomic_json(PATH, data)
    print('QUALITY_PROOF_RENDERED_NOT_PUBLISHED=' + request['concept'])


if __name__ == '__main__':
    main()
