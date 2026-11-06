"""Live-runner guards: offline tests, never provider writes or quota resets."""
from datetime import timedelta
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import buffer_runner as b
from experimental81.rights import require_clearance


class LiveGuardTests(unittest.TestCase):
    def test_cancelled_posts_are_not_reconciled_again(self):
        entry=dict(provider='buffer',status='CANCELLED_EDITORIAL',buffer_post_id='deleted')
        self.assertEqual(b.pending_reconciliation({'posts':{'cancelled':entry}}),[])
        self.assertEqual(b.unresolved_count({'posts':{'cancelled':entry}}),0)

    def test_unconfirmed_post_still_fails_during_readback_throttle(self):
        entry=dict(provider='buffer',status='AWAITING_PUBLIC_EVIDENCE',
                   buffer_post_id='remote',last_checked_at=b.common.iso_now())
        self.assertEqual(b.pending_reconciliation({'posts':{'pending':entry}}),[])
        self.assertEqual(b.unresolved_count({'posts':{'pending':entry}}),1)

    def test_invalid_timestamp_does_not_confirm_and_clears_stale_url(self):
        entry=dict(buffer_post_id='remote',public_urls=['stale'],publicly_available_post_id=['123'])
        b.record_remote(entry,dict(id='remote',channelId='channel',status='sent',
                        schedulingType='automatic',sentAt='invalid',
                        externalLink='https://www.tiktok.com/@.casasemesforo/video/123'),'channel')
        self.assertFalse(entry['publicly_verified'])
        self.assertNotIn('public_urls',entry)
        self.assertNotIn('publicly_available_post_id',entry)

    def test_commercial_consent_is_not_license_clearance(self):
        with self.assertRaisesRegex(ValueError,'AI_COMMERCIAL_CLEARANCE_REQUIRED'):
            require_clearance([dict(sha256='a'*64,owner_test_publication_consent=True,
                                    commercial_license_clearance=False)])

    def test_graphql_error_codes_are_safe_but_provider_messages_are_omitted(self):
        payload=dict(errors=[dict(message='PRIVATE_PROVIDER_MESSAGE',
                                 extensions={'code':'UNAUTHENTICATED'}),
                             dict(message='other',extensions={'code':'PRIVATE_UNKNOWN_CODE'})])
        response=io.BytesIO(json.dumps(payload).encode());response.headers={}
        state={'posts':{}}
        with patch.dict(b.os.environ,{'BUFFER_API_KEY':'mock-only'}),\
             patch.object(b.common,'save_json'),patch.object(b.buffer_quota,'check'),\
             patch.object(b.urllib.request,'urlopen',return_value=response):
            with self.assertRaises(RuntimeError) as error:b.Client(state).call('mock',{})
        self.assertIn('UNAUTHENTICATED',str(error.exception))
        self.assertNotIn('PRIVATE_PROVIDER_MESSAGE',str(error.exception))
        self.assertNotIn('PRIVATE_UNKNOWN_CODE',str(error.exception))


if __name__=='__main__':unittest.main()
