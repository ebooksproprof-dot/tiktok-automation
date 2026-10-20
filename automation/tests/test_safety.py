import copy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tiktok_runner as r


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.creator = dict(creator_username='.casasemesforo', max_video_post_duration_sec=60,
                            privacy_level_options=['PUBLIC_TO_EVERYONE'])
        self.post = dict(id='test', video_url='https://example.com/videos/test.mp4',
                         scheduled_at=r.iso_now(), privacy_level='PUBLIC_TO_EVERYONE',
                         approved=True, consented_at='2026-10-15T12:00:00Z', official_posting_consent=True,
                         quality=dict(technical_pass=True,editorial_approved=True,duration=20,sha256='a'*64,
                                      visual_policy_version=1,visual_distinct=True,
                                      visual_sources=[dict(source_id='test',sha256='b'*64,dhash=['0'*16]*5)]))
        self.env = patch.dict(os.environ, {'TIKTOK_VERIFIED_VIDEO_PREFIX':'https://example.com/videos/'})
        self.env.start();self.addCleanup(self.env.stop)

    def test_valid_reviewed_post(self):
        r.validate_post(self.post,self.creator)

    def test_wrong_account_blocked(self):
        self.creator['creator_username']='other'
        with self.assertRaises(ValueError):r.validate_post(self.post,self.creator)

    def test_technical_pass_does_not_approve_editorial(self):
        self.post['quality']['editorial_approved']=False
        with self.assertRaises(ValueError):r.validate_post(self.post,self.creator)

    def test_unverified_url_blocked(self):
        self.post['video_url']='https://example.com.attacker.test/videos/file.mp4'
        with self.assertRaises(ValueError):r.validate_post(self.post,self.creator)

    def test_creator_duration_respected(self):
        self.creator['max_video_post_duration_sec']=10
        with self.assertRaises(ValueError):r.validate_post(self.post,self.creator)

    def test_platform_consent_cannot_be_inferred(self):
        self.post.pop('official_posting_consent')
        with self.assertRaises(ValueError):r.validate_post(self.post,self.creator)

    def test_private_completion_not_public_success(self):
        state={'posts':{'test':dict(publish_id='123',status='PROCESSING_DOWNLOAD',privacy_level='SELF_ONLY')}}
        with tempfile.TemporaryDirectory() as folder, patch.object(r,'STATE_PATH',Path(folder)/'state.json'), patch.object(r,'api_post',return_value={'data':{'status':'PUBLISH_COMPLETE'}}):
            r.poll_existing('not-a-token',state)
        self.assertFalse(state['posts']['test']['publicly_verified'])

    def test_unknown_submission_never_resubmitted(self):
        state={'posts':{'test':dict(status='SUBMISSION_UNKNOWN')}}
        with patch.object(r,'load_json',side_effect=[{'posts':[self.post]},state]), patch.object(r,'fetch_token_from_broker') as token:
            self.assertEqual(r.main(),2)
            token.assert_not_called()

    def test_blocked_queue_is_not_success(self):
        self.post['approved']=False
        with patch.object(r,'load_json',side_effect=[{'posts':[self.post]},{'posts':{}}]), patch.object(r,'fetch_token_from_broker') as token:
            self.assertEqual(r.main(),2)
            token.assert_not_called()

    def test_checkpoint_failure_prevents_api_submission(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(r,'STATE_PATH',Path(folder)/'state.json'), patch.object(r,'load_json',side_effect=[{'posts':[self.post]},{'posts':{}}]), patch.object(r,'fetch_token_from_broker',return_value='not-a-token'), patch.object(r,'get_creator_info',return_value=self.creator), patch.object(r,'checkpoint',side_effect=RuntimeError('persistence failed')), patch.object(r,'submit_post') as submit:
            with self.assertRaises(RuntimeError):r.main()
            submit.assert_not_called()

if __name__=='__main__': unittest.main()
