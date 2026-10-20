import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import catalog_extension as c
import media_rights as r
import visual_library as v


class RightsTests(unittest.TestCase):
    def asset(self, provider='wikimedia'):
        return dict(provider=provider, author='Author', title='Kitchen organization',
            source_page='https://commons.wikimedia.org/wiki/File:Kitchen.webm',
            url='https://upload.wikimedia.org/wikipedia/commons/a/ab/Kitchen.webm',
            license_url='https://creativecommons.org/licenses/by/4.0/')

    def test_caption_carries_attribution_and_adaptation_notice(self):
        caption, credits = r.caption_with_credits('Organize a cozinha.', [self.asset()])
        self.assertIn(credits[0], caption)
        self.assertIn('Adaptacoes:', caption)
        self.assertIn('Author', caption)

    def test_missing_public_credit_blocks_publish(self):
        with self.assertRaisesRegex(ValueError, 'REQUIRED_PUBLIC_CREDIT_MISSING'):
            v.require_evidence({'title': 'No attribution', 'quality': {'required_public_credits': ['Author credit']}})

    def test_oversized_caption_rejected_without_truncating_credit(self):
        with self.assertRaises(ValueError): r.caption_with_credits('x'*2150, [self.asset()])

    def test_restrictive_license_and_wrong_origin_rejected(self):
        for changes in [dict(license_url='https://creativecommons.org/licenses/by-nc/4.0/'),
                        dict(provider='pixabay'), dict(restrictions='personality rights')]:
            asset = dict(self.asset(), **changes)
            self.assertFalse(r.valid_source(asset))

    def test_reviewed_pack_accepts_commons_and_preserves_provenance(self):
        data = json.loads(c.PATH.read_text())
        item = data['items'][0]
        asset = dict(item['media'][0], **self.asset())
        item['media'] = [asset]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'pack.json'; path.write_text(json.dumps(data))
            sources, topics, provenance = c.load(path)
        self.assertEqual(provenance[asset['id']]['provider'], 'wikimedia')
        self.assertEqual(sources[asset['id']], asset['url'])

    def test_reviewed_pack_accepts_pixabay(self):
        asset = self.asset('pixabay')
        asset.update(url='https://cdn.pixabay.com/video/42.mp4',
                     source_page='https://pixabay.com/videos/id-42/',
                     license_url='https://pixabay.com/service/license-summary/')
        self.assertTrue(r.valid_source(asset))
