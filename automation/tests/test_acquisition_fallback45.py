import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import media_acquisition as a
import media_providers as p
import editorial_drafts as e

class FallbackTests(unittest.TestCase):
    def exercise(self, error):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'automation';root.mkdir()
            records=[dict(provider='wikimedia',provider_id=str(i),url='https://upload.wikimedia.org/test.mp4') for i in range(8)]
            provider=MagicMock();provider.last_response_source='test';provider.search.return_value=records
            def measure(record,*args):
                if error or record['provider_id']=='0':
                    raise a.AcquisitionError(error or 'CANDIDATE_VALIDATION_REJECTED')
                return dict(record,status='pending_visual_review')
            with patch.object(a,'ROOT',root),patch.dict('os.environ',{'MEDIA_PROVIDER_ORDER':'wikimedia'}),patch.object(p,'WikimediaProvider',return_value=provider),patch.object(p,'credits',return_value=''),patch.object(a,'download_and_measure',side_effect=measure) as download,patch.object(a,'prepare_review_artifact'),patch.object(e,'main'):
                try:a.run()
                except a.AcquisitionError as exc:self.assertEqual(str(exc),'NO_NEW_REVIEWABLE_MEDIA')
            return download.call_count,json.loads((root/'media_inbox.json').read_text())
    def test_invalid_first_candidate_allows_distinct_second(self):
        count,result=self.exercise(None)
        self.assertEqual(count,3)
        self.assertEqual([x['provider_id'] for x in result['items']],['1','2'])
        self.assertEqual(result['last_run']['editorial_approved'],0)
    def test_four_download_budget_survives_validation_failures(self):
        count,result=self.exercise('CANDIDATE_VALIDATION_REJECTED')
        self.assertEqual(count,4);self.assertEqual(result['items'],[])
        self.assertEqual(result['last_run']['download_attempts'],4)
        self.assertGreater(result['last_run']['skipped_cooldown'],0)
    def test_provider_failures_stop_fallback_without_resetting_rejections(self):
        for code in ('PROVIDER_RATE_LIMITED','PROVIDER_SERVER_ERROR','PROVIDER_REQUEST_FAILED','PROVIDER_AUTH_REJECTED'):
            count,result=self.exercise(code)
            self.assertEqual(count,1)
            self.assertIn('wikimedia:0',result['rejected_until'])
