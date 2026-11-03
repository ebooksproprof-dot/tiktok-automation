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
    def test_known_visual_duplicate_is_rejected_and_new_seed_allowed_next_run(self):
        import tempfile
        from unittest.mock import Mock
        state={'schema_version':1,'episode_sequence':1,'status':'COLLECTING',
               'clips':[{'sha256':'a'*64,'visual_source':{'dhash':['a'*16]*5}}],
               'retry_variant':0,'last_attempt':None}
        ledger={'schema_version':1,'window_start':None,'tier':None,
                'claims':[],'window_claim_ids':[]}
        with tempfile.TemporaryDirectory() as folder:
            image=Path(folder)/'ref.png'
            image.write_bytes(b'fake image bytes for controlled unit test')
            generated={'status':'GENERATED_PENDING_VISUAL_REVIEW',
                       'file':'test.mp4','request_sha256':'c'*64,
                       'media':{'sha256':'b'*64}}
            with patch.object(auto_collect,'content_get',side_effect=[('sha',state),('ls',ledger)]),\
                 patch.object(auto_collect,'content_put',return_value='committed') as save,\
                 patch.object(auto_collect,'extract_reference',return_value=(image,{})),\
                 patch.object(auto_collect,'free_hf_identity',return_value=('free','test')),\
                 patch.object(auto_collect.daily_budget,'reserve',return_value=ledger),\
                 patch.object(auto_collect.wan_probe,'run',return_value=generated),\
                 patch.object(auto_collect,'fingerprint',return_value={'dhash':['a'*16]*5}),\
                 patch.object(auto_collect,'similar',return_value=True),\
                 patch.object(auto_collect,'upload_clip',side_effect=AssertionError('should not upload')):
                result=auto_collect.collect_one(folder)
            self.assertEqual(result['status'],'WAIT_VARIANT')
            self.assertEqual(state['status'],'COLLECTING')
            self.assertEqual(state['retry_variant'],1)
            self.assertEqual(len(state['clips']),1)
            self.assertEqual(state['last_attempt']['result'],'VISUAL_NEAR_DUPLICATE')
            save.assert_called_once()

    def test_optional_free_token_verified_without_billing(self):
        import io
        from unittest.mock import Mock
        response=io.BytesIO(b'{"type":"user","isPro":false}')
        with patch.dict(os.environ,{'HF_FREE_TOKEN':'fake-read-token'}),\
             patch.object(auto_collect,'urlopen',return_value=response):
            self.assertEqual(auto_collect.free_hf_identity(),('free','fake-read-token'))

    def test_paid_pro_token_never_reaches_generator(self):
        import io
        response=io.BytesIO(b'{"type":"user","isPro":true}')
        with patch.dict(os.environ,{'HF_FREE_TOKEN':'fake-pro-token'}),\
             patch.object(auto_collect,'urlopen',return_value=response):
            with self.assertRaisesRegex(RuntimeError,'NO_PRO'):
                auto_collect.free_hf_identity()

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
        now=datetime(2026,11,3,12,0,tzinfo=timezone.utc)
        chosen=auto_finish.choose_time({'posts':[]},{'posts':{}},now)
        self.assertEqual(chosen.hour,10)
        existing={'posts':[{'scheduled_at':chosen.isoformat()}]}
        next_date=auto_finish.choose_time(existing,{'posts':{}},now)
        self.assertEqual((next_date-chosen).days,1)

    def test_recover_existing_post_after_inventory_checkpoint_failure(self):
        urls=['https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/ai30-drafts-2026-11/clip-'+str(i)+'.mp4' for i in range(6)]
        inventory={'schema_version':1,'episode_sequence':5,'status':'READY',
                   'clips':[{'url':u,'sha256':f'{i:064x}'} for i,u in enumerate(urls)],
                   'publish_history':[],'last_output':None}
        queued={'id':'casasem-2026-11-04-1','video_origin':'ai_only30',
                'concept':'faxina-ia30-5','scheduled_at':'2026-11-04T10:00:00-03:00',
                'video_url':'https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-2026-11/test.mp4',
                'quality':{'source_urls':urls,'sha256':'a'*64}}
        with patch.object(auto_collect,'content_get',side_effect=[
            ('old-inventory-sha',inventory),('queue-sha',{'posts':[queued]})]),\
             patch.object(auto_collect,'content_put',return_value='saved') as commit,\
             patch.object(auto_finish,'download',side_effect=AssertionError('must not redownload')):
            result=auto_finish.finish()
        self.assertEqual(result['status'],'QUEUED_ALREADY_RECOVERED')
        self.assertEqual(inventory['status'],'COLLECTING')
        self.assertEqual(inventory['episode_sequence'],6)
        self.assertEqual(inventory['clips'],[])
        commit.assert_called_once()

    def test_no_explicit_video_until_six(self):
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GITHUB_REF_NAME':'main',
            'GITHUB_WORKFLOW':'CasaSemEsforco AI30 Free Collector',
            'AI30_MAIN_SCHEDULER_ALLOW':'true'}),patch.object(auto_collect,'content_get',
                 return_value=('sha',{'schema_version':1,'episode_sequence':1,
                 'status':'COLLECTING','clips':[]})):
            self.assertEqual(auto_finish.main()['status'],'NOT_READY')


if __name__=='__main__':
    unittest.main()
