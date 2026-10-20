import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import editorial_drafts as e


def media(number=1, tag='dish wash kitchen', bits='0000000000000000'):
    url=f'https://cdn.pixabay.com/video/{number}.mp4'
    return dict(provider='pixabay', provider_id=str(number), url=url, source_id=url,
                source_page=f'https://pixabay.com/videos/id-{number}/',
                license_url='https://pixabay.com/service/license-summary/', author='Creator',
                sha256=f'{number:064x}', dhash=[bits]*5, duration=30,
                status='pending_visual_review', selection_reason=tag)


class EditorialDraftTests(unittest.TestCase):
    def test_draft_does_not_approve_or_publish(self):
        result=e.generate({'items':[media()]}, {'version':1,'drafts':[]})
        draft=result['drafts'][0]
        for field in ('approved','editorial_approved','published'):
            self.assertIs(draft[field], False)
        self.assertEqual(draft['status'], 'pending_editorial_review')

    def test_same_footage_cannot_supply_second_hook(self):
        first=e.generate({'items':[media()]}, {'version':1,'drafts':[]})
        second=e.generate({'items':[media()]}, first)
        self.assertEqual(len(second['drafts']),1)
        self.assertEqual(second['last_run']['created'],0)

    def test_perceptual_reencode_rejected(self):
        first=e.generate({'items':[media()]}, {'version':1,'drafts':[]})
        second=e.generate({'items':[media(2)]}, first)
        self.assertEqual(second['last_run']['created'],0)

    def test_published_source_excluded(self):
        result=e.generate({'items':[media()]}, {'version':1,'drafts':[]},
                          [{'visual_sources':[media()]}])
        self.assertEqual(result['drafts'],[])

    def test_distinct_source_gets_distinct_fact_topic(self):
        first=e.generate({'items':[media()]}, {'version':1,'drafts':[]})
        second=e.generate({'items':[media(2,bits='ffffffffffffffff')]}, first)
        self.assertEqual(len(second['drafts']),2)
        self.assertNotEqual(second['drafts'][0]['topic'],second['drafts'][1]['topic'])
        self.assertNotEqual(second['drafts'][0]['body_sha256'],second['drafts'][1]['body_sha256'])

    def test_inappropriate_or_unmeasured_media_rejected(self):
        for change in [dict(selection_reason='bird washing'),dict(sha256='bad'),
                       dict(dhash=[]),dict(duration=5),dict(author=''),
                       dict(license_url='https://example.com/license')]:
            record=media();record.update(change)
            result=e.generate({'items':[record]}, {'version':1,'drafts':[]})
            self.assertEqual(result['drafts'],[])

    def test_ledger_persists_without_modifying_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'media_inbox.json').write_text(json.dumps({'items':[media()]}))
            (root/'queue.json').write_text('{"posts":[]}')
            original=(root/'queue.json').read_bytes()
            e.main(root);e.main(root)
            saved=json.loads((root/'editorial_drafts.json').read_text())
            self.assertEqual(len(saved['drafts']),1)
            self.assertEqual((root/'queue.json').read_bytes(),original)

    def test_script_normalization(self):
        self.assertEqual(e.digest('Texto,  igual!'), e.digest('texto igual'))

    def test_limit_is_bounded(self):
        with self.assertRaises(ValueError):
            e.generate({'items':[]},{'version':1,'drafts':[]},limit=3)
