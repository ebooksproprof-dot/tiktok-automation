import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import refresh_review44 as r

NOW=dt.datetime(2026,10,23,12,tzinfo=dt.timezone.utc)


class RefreshReviewTests(unittest.TestCase):
    def setup_root(self, path):
        root=Path(path);(root/'automation').mkdir();(root/'public').mkdir()
        for name, value in [('queue.json',{'posts':[]}),('state.json',{'posts':{}}),
                            ('visual_history.json',{}),('QUEUE-AUDIT-4.4.json',[])]:
            (root/'automation'/name).write_text(json.dumps(value))
        for name in ('review44.json','review44.html'):
            (root/'public'/name).write_text('previous')
        return root

    def test_refresh_replaces_only_derived_pages_and_never_approves(self):
        with tempfile.TemporaryDirectory() as directory:
            root=self.setup_root(directory);before=r.read_snapshot(root)
            result=r.refresh(root,NOW)
            self.assertEqual(r.read_snapshot(root),before)
            self.assertFalse(result['approved']);self.assertFalse(result['submitted'])
            manifest=json.loads((root/'public/review44.json').read_text())
            self.assertIn(manifest['manifest_sha256'],(root/'public/review44.html').read_text())
            self.assertEqual(set(p.name for p in (root/'public').iterdir()),{'review44.html','review44.json'})

    def test_changed_audit_aborts_without_replacing_either_page(self):
        with tempfile.TemporaryDirectory() as directory:
            root=self.setup_root(directory);original=r.render_html
            def concurrent_change(manifest):
                (root/'automation/QUEUE-AUDIT-4.4.json').write_text('[{"changed":true}]')
                return original(manifest)
            with patch.object(r,'render_html',side_effect=concurrent_change):
                with self.assertRaisesRegex(ValueError,'STATE_CHANGED'):
                    r.refresh(root,NOW)
            for name in ('review44.json','review44.html'):
                self.assertEqual((root/'public'/name).read_text(),'previous')
            self.assertEqual(set(p.name for p in (root/'public').iterdir()),{'review44.html','review44.json'})


if __name__=='__main__':unittest.main()
