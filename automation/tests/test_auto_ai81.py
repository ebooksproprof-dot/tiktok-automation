"""Free collector/publishing handoff policy. No network and no social writes."""
from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import auto_collect, auto_finish, github_ledger


class CollectorTests(unittest.TestCase):
    def test_dry_run_never_touches_remote(self):
        with patch.object(auto_collect, 'content_get', side_effect=AssertionError('network')): 
            result=auto_collect.main(dry_run=True)
        self.assertEqual(result['status'],'DRY_RUN_NO_REMOTE_CALLS')
        self.assertEqual(result['clips_target'],6)
        self.assertFalse(result['quota']['guaranteed_production'])

    def test_cloud_guard_does_not_touch_remote(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'false'}), patch.object(auto_collect,'content_get') as remote:
            self.assertEqual(auto_collect.main()['status'],'SAFE_BLOCKED_INVALID_CLOUD_CONTEXT')
            remote.assert_not_called()

    def test_inventory_refuses_malformed_and_duplicates(self):
        value={'schema_version':1,'episode_sequence':1,'status':'COLLECTING',
               'clips':[{'sha256':'a'*64},{'sha256':'a'*64}]}
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):
            auto_collect.check_inventory(value)
        value['clips']=[{'sha256':'a'*64}]
        self.assertIs(auto_collect.check_inventory(value),value)
        value['clips']=[{}]*7
        with self.assertRaisesRegex(ValueError,'INVALID'):
            auto_collect.check_inventory(value)

    def test_missing_authorized_main_context_is_still_blocked(self):
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GITHUB_REF_NAME':'main',
              'GITHUB_WORKFLOW':'Some other workflow','AI30_MAIN_SCHEDULER_ALLOW':'true',
              'GITHUB_EVENT_NAME':'schedule','GH_TOKEN':'fake'}),patch.object(auto_collect,'content_get') as remote:
            self.assertEqual(auto_collect.main()['status'],'SAFE_BLOCKED_INVALID_CLOUD_CONTEXT')
            remote.assert_not_called()

    def test_remote_ledger_allows_only_dedicated_main_collector(self):
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GITHUB_REF_NAME':'main',
                'GITHUB_WORKFLOW':'CasaSemEsforco AI30 Free Collector',
                'AI30_MAIN_SCHEDULER_ALLOW':'true','GITHUB_EVENT_NAME':'schedule',
                'GITHUB_TOKEN':'fake'}):
            from experimental81 import daily_budget
            from unittest.mock import Mock
            state=daily_budget.fresh()
            class InMemory:
                def __init__(self):self.state=state
                def __call__(self, method,url,token,payload=None):
                    import base64,json
                    if method=='GET':
                        return {'sha':'current','encoding':'base64',
                         'content':base64.b64encode(json.dumps(self.state).encode()).decode()}
                    if method=='PUT':
                        self.state=json.loads(base64.b64decode(payload['content']))
                        return {'commit':{'sha':'b'*40}}
            fake=InMemory()
            record={'request_sha256':'2'*64,'request':{'space':github_ledger.SPACE,
                   'steps':4,'duration_seconds':5}}
            result=github_ledger.reserve_remote(record,transport=fake,now=datetime(2026,11,3,tzinfo=timezone.utc))
            self.assertTrue(result['reserved'])
            self.assertEqual(len(fake.state['claims']),1)


class FinishPolicyTests(unittest.TestCase):
    def test_no_direct_publisher_in_code(self):
        body=Path(auto_finish.__file__).read_text()
        for forbidden in ('api.buffer.com','BUFFER_API_KEY','TIKTOK_ACCESS_TOKEN','video/init'):
            self.assertNotIn(forbidden,body)

    def test_preferred_ten_oclock_and_existing_collision(self):
        zone=auto_finish.LOCAL
        now=datetime(2026,11,3,6,0,tzinfo=timezone.utc)
        chosen=auto_finish.choose_time({'posts':[]},{'posts':{}},now)
        self.assertEqual(chosen.hour,10)
        existing={'posts':[{'scheduled_at':chosen.isoformat()}]}
        next_date=auto_finish.choose_time(existing,{'posts':{}},now)
        self.assertEqual((next_date-chosen).days,1)

    def test_no_explicit_video_until_six(self):
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GITHUB_REF_NAME':'main',
            'GITHUB_WORKFLOW':'CasaSemEsforco AI30 Free Collector',
            'AI30_MAIN_SCHEDULER_ALLOW':'true'}),patch.object(auto_collect,'content_get',
                 return_value=('sha',{'schema_version':1,'episode_sequence':1,
                 'status':'COLLECTING','clips':[]})):
            self.assertEqual(auto_finish.main()['status'],'NOT_READY')


if __name__=='__main__':
    unittest.main()
