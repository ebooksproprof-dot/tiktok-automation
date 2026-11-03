from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import persist as p


class Persist81Tests(unittest.TestCase):
    def test_production_branch_refuses_network(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'true','GITHUB_REF_NAME':'main'}), patch.object(p,'request') as req:
            with self.assertRaises(ValueError):
                p.persist('/tmp/unused')
            req.assert_not_called()

    def test_empty_output_never_creates_release(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
            'GITHUB_ACTIONS':'true','GITHUB_REF_NAME':'feature/ai-video-hybrid-30s',
            'GH_TOKEN':'fake','GITHUB_SHA':'a'*40}), patch.object(p,'request') as req:
            self.assertEqual(p.persist(directory)['status'],'NO_OUTPUT_TO_PERSIST')
            req.assert_not_called()

    def test_asset_readback_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
            'GITHUB_ACTIONS':'true','GITHUB_REF_NAME':'feature/ai-video-hybrid-30s',
            'GH_TOKEN':'fake','GITHUB_SHA':'a'*40}):
            (Path(directory)/'cloud-result.json').write_text('{}')
            release = {'id':1,'html_url':'https://github.com/example'}
            with patch.object(p,'request',side_effect=[release,[],{'id':2},{'digest':'wrong'}]):
                with self.assertRaisesRegex(ValueError,'READBACK'):
                    p.persist(directory)


if __name__ == '__main__':
    unittest.main()
