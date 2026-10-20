import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review_requested as review
import preview_batch as preview
import render_daily as render


class ReviewCheckpointTests(unittest.TestCase):
    def test_stale_report_cannot_complete_a_failed_new_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            requests = root / 'requests.json'
            requests.write_text(json.dumps({'requests': [{'concept': 'first', 'status': 'pending'}]}))
            report = root / 'tmp/review-v3/report.json'
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps([{'concept': 'first', 'file': 'stale.mp4'}]))
            with patch.object(review, 'PATH', requests), patch.object(render, 'ROOT', root), \
                    patch.object(render, 'IDEAS', [('first', [], [])]), \
                    patch.object(preview, 'main', side_effect=RuntimeError('render failed')):
                with self.assertRaisesRegex(RuntimeError, 'render failed'):
                    review.main()
            self.assertEqual(json.loads(report.read_text()), [])
            saved = json.loads(requests.read_text())['requests'][0]
            self.assertEqual(saved['status'], 'pending')
            self.assertNotIn('report', saved)

    def test_later_render_failure_preserves_completed_proof_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            requests = root / 'requests.json'
            requests.write_text(json.dumps({'requests': [
                {'concept': 'first', 'status': 'pending'},
                {'concept': 'second', 'status': 'pending'}]}))
            quality = {'visual_sources': [{'source_id': 'first'}]}
            with patch.object(review, 'PATH', requests), patch.object(render, 'ROOT', root), \
                    patch.object(render, 'ASSETS', root / 'assets'), patch.object(render, 'OUT', root / 'out'), \
                    patch.object(render, 'IDEAS', [('first', [], ['one']), ('second', [], ['two'])]), \
                    patch.object(render, 'load_voice', return_value=object()), \
                    patch.object(render, 'render', side_effect=[(Path('first.mp4'), quality), RuntimeError('second failed')]), \
                    patch.object(preview.visual, 'check_sources'), patch.object(render, 'run'):
                with self.assertRaisesRegex(RuntimeError, 'second failed'):
                    review.main()
            saved = json.loads(requests.read_text())['requests']
            self.assertEqual(saved[0]['status'], 'rendered_for_review')
            self.assertEqual(saved[0]['report'][0]['file'], 'first.mp4')
            self.assertIs(saved[0]['published'], False)
            self.assertEqual(saved[1]['status'], 'pending')
            self.assertNotIn('report', saved[1])
            report = json.loads((root / 'tmp/review-v3/report.json').read_text())
            self.assertEqual([r['concept'] for r in report], ['first'])
