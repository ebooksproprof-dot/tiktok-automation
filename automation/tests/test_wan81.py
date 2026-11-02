from pathlib import Path
import sys,tempfile,unittest,json,hashlib
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experimental81 import wan_probe as wan

class Wan81Tests(unittest.TestCase):
    def setUp(self):
        env=patch.dict(wan.os.environ,{'GITHUB_ACTIONS':'false'});env.start();self.addCleanup(env.stop)
    def fixture(self,d):
        p=Path(d)/'licensed-reference.png';p.write_bytes(b'x'*2000)
        c=Mock();c.view_api.return_value={'named_endpoints':{'/generate_video':{'parameters':[{'parameter_name':x} for x in wan.ORDER]}}}
        return p,c
    def test_disabled_does_not_touch_network(self):
        c=Mock();self.assertEqual(wan.run('missing','C','unused',False,client_factory=c)['status'],'DISABLED');c.assert_not_called()
    def test_cloud_requires_remote_ledger(self):
        with patch.dict(wan.os.environ,{'GITHUB_ACTIONS':'true'}):
            self.assertEqual(wan.run('missing','C','unused',True)['error'],'REMOTE_LEDGER_REQUIRED')
    def test_schema_change_never_submits(self):
        with tempfile.TemporaryDirectory() as d:
            p,c=self.fixture(d);c.view_api.return_value={}
            r=wan.run(p,'C',Path(d)/'out',True,client_factory=Mock(return_value=c),file_handler=lambda x:x)
            self.assertEqual(r['status'],'BLOCKED');c.submit.assert_not_called()
    def test_remote_conflict_never_submits(self):
        with tempfile.TemporaryDirectory() as d:
            p,c=self.fixture(d)
            r=wan.run(p,'C',Path(d)/'out',True,before_submit=Mock(side_effect=RuntimeError('conflict')),
                      client_factory=Mock(return_value=c),file_handler=lambda x:x)
            self.assertEqual(r['status'],'BLOCKED');c.submit.assert_not_called()
    def test_quota_unknown_never_auto_retried(self):
        with tempfile.TemporaryDirectory() as d:
            p,c=self.fixture(d);c.submit.return_value.result.side_effect=RuntimeError('quota exceeded')
            out=Path(d)/'out';factory=Mock(return_value=c)
            r=wan.run(p,'C',out,True,client_factory=factory,file_handler=lambda x:x)
            self.assertEqual(r['status'],'UNKNOWN');self.assertEqual(r['error'],'QUOTA_OR_GPU_BUDGET')
            self.assertEqual(wan.run(p,'C',out,True,client_factory=factory,file_handler=lambda x:x),r)
            self.assertEqual(c.submit.call_count,1);self.assertIs(factory.call_args.kwargs['token'],False)
    def test_success_preserves_real_bytes_not_approval(self):
        with tempfile.TemporaryDirectory() as d:
            p,c=self.fixture(d);v=Path(d)/'mock.mp4';v.write_bytes(b'v'*2000)
            c.submit.return_value.result.return_value=(str(v),8103)
            sha=hashlib.sha256(v.read_bytes()).hexdigest()
            with patch.object(wan,'inspect_clip',return_value={'sha256':sha,'duration_seconds':5.0625}):
                r=wan.run(p,'C',Path(d)/'out',True,client_factory=Mock(return_value=c),file_handler=lambda x:x)
            self.assertEqual(r['status'],'GENERATED_PENDING_VISUAL_REVIEW')
            self.assertFalse(r['publication_allowed']);self.assertTrue(r['license_review_pending'])
            self.assertEqual((Path(d)/'out'/r['file']).read_bytes(),v.read_bytes())

if __name__=='__main__':unittest.main()
