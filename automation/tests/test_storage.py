import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_media as r

class ReleaseStorageTests(unittest.TestCase):
    def test_third_daily_id_never_bypasses_proof_authorization(self):
        with patch('daily_coverage.confirmed_live_tests', return_value=set()), patch.object(r, 'request') as api:
            with self.assertRaisesRegex(ValueError, 'Third ID requires'):
                r.publish('/not-read.mp4', 'casasem-2026-11-07-3', {})
            api.assert_not_called()
    def setUp(self):
        self.content = b'validated-media-test'
        self.digest = hashlib.sha256(self.content).hexdigest()
        self.name = 'casasem-2026-10-18-1-' + self.digest[:16] + '.mp4'
        self.asset = dict(id=12,name=self.name,state='uploaded',size=len(self.content),digest='sha256:'+self.digest,
                         browser_download_url='https://github.com/'+r.REPO+'/releases/download/media-2026-10/'+self.name)
        self.env = patch.dict(os.environ, {'GH_TOKEN':'dummy','GITHUB_ACTIONS':'true'})
        self.env.start();self.addCleanup(self.env.stop)

    def call_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'video.mp4';p.write_bytes(self.content)
            return r.publish(p, 'casasem-2026-10-18-1',dict(technical_pass=True,sha256=self.digest))

    def test_existing_verified_asset_is_reused_without_write(self):
        with patch.object(r,'request',side_effect=[{'id':1},[self.asset]]) as api:
            self.assertEqual(self.call_publish(),self.asset['browser_download_url'])
            self.assertEqual(api.call_count,2)
            self.assertTrue(all(len(c.args)==2 for c in api.call_args_list))

    def test_upload_requires_readback(self):
        with patch.object(r,'request',side_effect=[{'id':1},[],{'id':12},self.asset]) as api:
            self.assertEqual(self.call_publish(),self.asset['browser_download_url'])
            self.assertEqual(api.call_count,4)
            self.assertIn('/releases/assets/12',api.call_args.args[0])

    def test_digest_mismatch_blocks_reuse(self):
        with patch.object(r,'request',side_effect=[{'id':1},[dict(self.asset,digest='sha256:wrong')]]):
            with self.assertRaises(ValueError):self.call_publish()

    def test_budget_blocks_upload(self):
        with patch.object(r,'request',side_effect=[{'id':1},[{'name':str(i)} for i in range(64)]]) as api:
            with self.assertRaises(RuntimeError):self.call_publish()
            self.assertEqual(api.call_count,2)

    def test_unknown_upload_is_not_retried(self):
        with patch.object(r,'request',side_effect=[{'id':1},[],RuntimeError('unknown')]) as api:
            with self.assertRaises(RuntimeError):self.call_publish()
            self.assertEqual(api.call_count,3)

    def test_new_month_preserves_history_and_needs_verified_upload(self):
        with patch.object(r, 'request', side_effect=[None, {'id': 1}, [], {'id': 12}, self.asset]) as api:
            self.assertEqual(self.call_publish(), self.asset['browser_download_url'])
            self.assertEqual(api.call_count, 5)
            self.assertTrue(api.call_args_list[0].args[0].endswith('/releases/tags/media-2026-10'))
            self.assertEqual(api.call_args_list[1].args[2], 'POST')
            self.assertFalse(any('DELETE' in call.args for call in api.call_args_list))
