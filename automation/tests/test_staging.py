import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import stage_reviewed_preview as s

class StagingSafetyTests(unittest.TestCase):
    def test_invalid_slot_refuses(self):
        with self.assertRaisesRegex(ValueError, 'destination slot'):
            s.main(Path('/unused'), post_id='../escape')

    def test_invalid_expected_hash_refuses(self):
        with self.assertRaisesRegex(ValueError, 'reviewed fingerprint'):
            s.main(Path('/unused'), expected_sha='invalid')

    def test_existing_submission_refuses_before_upload(self):
        with patch.object(Path, 'read_text', side_effect=[json.dumps({'posts': []}),
                json.dumps({'posts': {s.POST_ID: {'status': 'SUBMISSION_UNKNOWN'}}})]), \
                patch.object(s, 'publish') as upload:
            with self.assertRaisesRegex(ValueError, 'Already submitted'):
                s.main(Path('/unused'))
            upload.assert_not_called()

    def test_existing_slot_never_overwritten(self):
        with patch.object(Path, 'read_text', side_effect=[json.dumps({'posts': [{'id': s.POST_ID}]}),
                json.dumps({'posts': {}})]), patch.object(s, 'publish') as upload:
            with self.assertRaisesRegex(ValueError, 'Slot already occupied'):
                s.main(Path('/unused'))
            upload.assert_not_called()

    def test_changed_cloud_bytes_refuse_upload(self):
        with patch.object(Path, 'read_text', side_effect=[json.dumps({'posts': []}),
                json.dumps({'posts': {}}), json.dumps([{'quality': {'sha256': s.EXPECTED_SHA}}])]), \
                patch.object(s, 'validate', return_value={'sha256': 'f'*64}), \
                patch.object(s, 'publish') as upload:
            with self.assertRaisesRegex(ValueError, 'fingerprint mismatch'):
                s.main(Path('/unused'))
            upload.assert_not_called()
