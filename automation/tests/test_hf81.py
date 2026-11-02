import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import hf_probe as hf

PARAMS = ['prompt','image_path','width','height','duration_seconds','auto_length','seed','randomize_seed','decoder']


def client():
    c=Mock()
    c.view_api.return_value={'named_endpoints': {'/generate_video': {'parameters': [{'parameter_name':x} for x in PARAMS]}}}
    return c


class HF81Tests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(hf.os.environ,{'GITHUB_ACTIONS':'false'})
        self.env.start();self.addCleanup(self.env.stop)

    def test_cloud_requires_remote_reservation(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(hf.os.environ,{'GITHUB_ACTIONS':'true'}):
            factory=Mock()
            r=hf.run('A',d,True,factory)
            self.assertEqual(r['error'],'REMOTE_LEDGER_REQUIRED');factory.assert_not_called()

    def test_remote_reservation_failure_prevents_submission(self):
        with tempfile.TemporaryDirectory() as d:
            c=client();reserve=Mock(side_effect=RuntimeError('CAS conflict'))
            r=hf.run('A',d,True,Mock(return_value=c),before_submit=reserve)
            self.assertEqual(r['status'],'BLOCKED');c.submit.assert_not_called()
            self.assertFalse(r['generation_attempted'])

    def test_disabled_no_network(self):
        with tempfile.TemporaryDirectory() as d:
            factory=Mock()
            self.assertEqual(hf.run('A',d,False,factory)['status'],'DISABLED')
            factory.assert_not_called()

    def test_request_fingerprints_separate_cases(self):
        self.assertEqual(len({hf.fingerprint(hf.request_spec(c)) for c in 'ABC'}),3)
        with self.assertRaises(ValueError):hf.request_spec('D')

    def test_missing_endpoint_blocks_without_submit(self):
        with tempfile.TemporaryDirectory() as d:
            c=client();c.view_api.return_value={'named_endpoints':{}}
            r=hf.run('A',d,True,Mock(return_value=c))
            self.assertEqual(r['status'],'BLOCKED');c.submit.assert_not_called()

    def test_changed_schema_blocks_without_submit(self):
        with tempfile.TemporaryDirectory() as d:
            c=client();c.view_api.return_value['named_endpoints']['/generate_video']['parameters'].pop()
            self.assertEqual(hf.run('A',d,True,Mock(return_value=c))['status'],'BLOCKED')
            c.submit.assert_not_called()

    def test_intent_persisted_before_submit_timeout_not_retried(self):
        with tempfile.TemporaryDirectory() as d:
            c=client();factory=Mock(return_value=c)
            def submit(*args,**kwargs):
                record=json.loads(next(Path(d).glob('*.json')).read_text())
                self.assertEqual(record['status'],'SUBMITTING')
                self.assertTrue(record['generation_attempted'])
                raise TimeoutError('secret-token-must-not-appear')
            c.submit.side_effect=submit
            r=hf.run('A',d,True,factory)
            self.assertEqual(r['status'],'UNKNOWN');self.assertIsNone(r['quota_consumed'])
            self.assertEqual(r['error'],'TIMEOUT_OUTCOME_UNKNOWN')
            self.assertNotIn('secret-token',json.dumps(r))
            again=hf.run('A',d,True,factory)
            self.assertEqual(r,again);self.assertEqual(c.submit.call_count,1)
            self.assertIs(factory.call_args.kwargs['token'],False)

    def test_quota_failure_stops_no_retry(self):
        with tempfile.TemporaryDirectory() as d:
            c=client();c.submit.return_value.result.side_effect=RuntimeError('GPU quota exhausted')
            r=hf.run('B',d,True,Mock(return_value=c))
            self.assertEqual(r['error'],'QUOTA_OR_GPU_BUDGET')
            self.assertFalse(r['publication_allowed'])
            self.assertEqual(hf.run('B',d,True,Mock()),r)

    def test_downloaded_file_persisted_by_hash_without_approval(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source.mp4';source.write_bytes(b'x'*2000)
            output=Path(d)/'output';c=client();c.submit.return_value.result.return_value=({'video':str(source)},8101,'fake fixture')
            import hashlib
            quality={'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'duration_seconds':5.04,'width':576,'height':1024}
            with patch.object(hf,'inspect_clip',return_value=quality):
                r=hf.run('A',output,True,Mock(return_value=c))
            self.assertEqual(r['status'],'GENERATED_PENDING_VISUAL_REVIEW')
            self.assertTrue((output/r['file']).exists())
            self.assertFalse(r['visual_quality_approved']);self.assertFalse(r['publication_allowed'])
            self.assertIsNone(r['usable_video_seconds'])

    def test_error_classification_does_not_expose_body(self):
        self.assertEqual(hf.classify_error(Exception('Model loading failed (RepositoryNotFoundError)')),'SPACE_MODEL_UNAVAILABLE')
        self.assertEqual(hf.classify_error(Exception('401 secret')),'AUTHORIZATION_REQUIRED')


if __name__=='__main__':unittest.main()
