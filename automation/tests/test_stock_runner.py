import copy
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import stock_runner as runner
import video_stock as stock


class StockRunnerTests(unittest.TestCase):
    def test_bootstrap_is_durable_without_generator_or_work(self):
        with tempfile.TemporaryDirectory() as directory:
            store = stock.LocalStore(Path(directory)/'stock.json')
            empty_scan = {'imported': [], 'skipped': [], 'errors': [], 'waiting_for_manifest': []}
            with patch.object(runner.stock_import, 'scan', return_value=empty_scan):
                report = runner.import_and_schedule(store, 'fake', {'posts': []}, {'posts': {}},
                    datetime(2026, 10, 28, tzinfo=timezone.utc))
            restarted, rev = stock.LocalStore(Path(directory)/'stock.json').load()
            self.assertTrue(rev)
            self.assertEqual(report, empty_scan)
            self.assertFalse(restarted['production']['enabled'])
            self.assertIsNone(restarted['production']['api_balance'])
            self.assertEqual(restarted['items'], [])

    def test_existing_external_schedule_shapes_reserved(self):
        result = runner.occupied_slots({'posts': [{'scheduled_at': '2026-10-29T13:00:00Z'}]},
            {'posts': {'one': {'scheduled_at': {'dateTime': '2026-10-28T18:00:00',
                                                 'timezone': 'America/Sao_Paulo'}}}})
        self.assertEqual([stock.stamp(x) for x in result],
                         ['2026-10-29T13:00:00Z', '2026-10-28T21:00:00Z'])

    def test_release_create_only_when_missing(self):
        release = {'id': 42, 'tag_name': 'stock-inbox', 'draft': False}
        with patch.object(runner, 'request', return_value=release) as req:
            self.assertEqual(runner.ensure_inbox('fake'), 42)
            self.assertEqual(req.call_count, 1)
        with patch.object(runner, 'request', side_effect=[None, release]) as req:
            self.assertEqual(runner.ensure_inbox('fake'), 42)
            self.assertEqual(req.call_args.args[2], 'POST')
            self.assertFalse(req.call_args.args[3]['draft'])

    def test_workflow_shared_lock_and_no_paid_runner(self):
        workflow = (Path(__file__).resolve().parents[2]/'.github/workflows/video-stock.yml').read_text()
        self.assertIn('group: casasemesforco-state', workflow)
        self.assertIn('cancel-in-progress: false', workflow)
        self.assertIn('runs-on: ubuntu-latest', workflow)
        self.assertNotIn('upload-artifact', workflow)
        self.assertIn('secrets.BUFFER_API_KEY', workflow)


if __name__ == '__main__':
    unittest.main()
