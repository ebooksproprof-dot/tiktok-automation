import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import save_validation_v41 as saver


class SaveValidationV41Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'tmp/validation-v41'
        self.folder.mkdir(parents=True)
        self.report = [{'file': 'proof.mp4', 'approved': False, 'published': False}]
        (self.folder / 'report.json').write_text(json.dumps(self.report))
        (self.folder / 'proof.mp4').write_bytes(b'mocked-video-bytes')
        (self.folder / 'proof.jpg').write_bytes(b'mocked-contact-sheet')
        self.calls = []
        self.assets = {}
        self.release = {'id': 42, 'html_url': 'https://github.com/' + saver.REPO + '/releases/tag/test'}
        self.corrupt = False

    def request(self, url, token, method='GET', data=None, content_type=None):
        self.calls.append((url, method, data))
        if '/releases/tags/' in url:
            return None
        if url == saver.API + '/releases':
            return self.release
        if '?per_page=100' in url:
            return list(self.assets.values())
        if method == 'POST':
            name = url.split('?name=')[1]
            digest = hashlib.sha256(data).hexdigest()
            asset_id = len(self.assets) + 1
            self.assets[asset_id] = dict(id=asset_id, name=name, state='uploaded',
                size=len(data), digest='sha256:' + digest,
                browser_download_url='https://github.com/' + saver.REPO + '/releases/download/test/' + name)
            return {'id': asset_id}
        result = dict(self.assets[int(url.rsplit('/', 1)[1])])
        if self.corrupt:
            result['digest'] = 'sha256:wrong'
        return result

    def run_main(self):
        with patch.object(saver, '__file__', str(self.root / 'automation/save_validation_v41.py')), \
             patch.dict('os.environ', GITHUB_ACTIONS='true', GH_TOKEN='mock-only', GITHUB_SHA='source-sha'), \
             patch.object(saver, 'request', side_effect=self.request), \
             contextlib.redirect_stdout(io.StringIO()):
            saver.main()

    def test_main_target_preserves_source_sha_without_approval(self):
        self.run_main()
        creation = next(data for url, method, data in self.calls if url == saver.API + '/releases')
        self.assertEqual(creation['target_commitish'], 'main')
        self.assertIn('source-sha', creation['body'])
        self.assertIn('Not approved', creation['body'])
        result = json.loads((self.folder / 'release-links.json').read_text())
        self.assertFalse(result['published_to_tiktok'])
        self.assertFalse(result['batch_complete'])
        self.assertEqual(json.loads((self.folder / 'report.json').read_text()), self.report)
        self.assertTrue(all('github.com' in url for url, _, _ in self.calls))

    def test_upload_hash_names_and_independent_readback(self):
        self.run_main()
        self.assertEqual(len(self.assets), 3)
        for asset in self.assets.values():
            self.assertIn(asset['digest'][7:23], asset['name'])
            self.assertTrue(any(url == saver.API + '/releases/assets/' + str(asset['id'])
                                and method == 'GET' for url, method, _ in self.calls))

    def test_readback_digest_mismatch_prevents_success_manifest(self):
        self.corrupt = True
        with self.assertRaisesRegex(ValueError, 'digest'):
            self.run_main()
        self.assertFalse((self.folder / 'release-links.json').exists())

    def test_existing_hash_assets_are_reused_without_upload(self):
        self.run_main()
        self.calls.clear()
        self.run_main()
        self.assertFalse(any(method == 'POST' and 'uploads.github.com' in url
                             for url, method, _ in self.calls))


if __name__ == '__main__':
    unittest.main()
