import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import media_acquisition as m
import editorial_drafts as e
from test_editorial_drafts import media


class Renewal44Tests(unittest.TestCase):
    def test_six_days_cover_bank_without_more_than_four_queries(self):
        plans = [m.daily_topics(day * 86400) for day in range(6)]
        self.assertTrue(all(len(plan) == 4 for plan in plans))
        queries = [query for plan in plans for _, query, _ in plan]
        self.assertEqual(len(queries), 24)
        self.assertEqual(len(set(queries)), 24)
        self.assertEqual(set(queries), {query for _, query, _ in m.TOPICS})

    def test_retry_on_same_day_reuses_plan_next_day_changes(self):
        self.assertEqual(m.daily_topics(100 * 86400), m.daily_topics(100 * 86400 + 86399))
        self.assertNotEqual(m.daily_topics(100 * 86400), m.daily_topics(101 * 86400))

    def test_pexels_budget_cache_does_not_spend_or_reset_counter(self):
        cache = {'cached': {'at': 100, 'videos': []}}
        provider = m.PexelsProvider('unit-test-placeholder', cache, now=101)
        with patch.object(m, 'request', side_effect=lambda *args: io.BytesIO(b'{"videos":[]}')) as req:
            for index in range(4):
                provider.search('query-' + str(index))
            self.assertEqual(provider.search('cached'), [])
            self.assertEqual(provider.last_response_source, 'cache')
            with self.assertRaisesRegex(m.AcquisitionError, 'PROVIDER_REQUEST_BUDGET_REACHED'):
                provider.search('fifth')
            self.assertEqual(provider.requests, 4)
            self.assertEqual(req.call_count, 4)
            self.assertIn('cached', cache)

    def test_failed_pexels_requests_still_consume_run_budget(self):
        provider = m.PexelsProvider('unit-test-placeholder', {}, now=100)
        with patch.object(m, 'request', side_effect=m.AcquisitionError('PROVIDER_SERVER_ERROR')) as req:
            for _ in range(4):
                with self.assertRaisesRegex(m.AcquisitionError, 'PROVIDER_SERVER_ERROR'):
                    provider.search('query')
            with self.assertRaisesRegex(m.AcquisitionError, 'PROVIDER_REQUEST_BUDGET_REACHED'):
                provider.search('query')
            self.assertEqual(req.call_count, 4)

    def test_new_templates_have_distinct_bodies_and_product_contexts(self):
        self.assertEqual(len({t[0] for t in e.TEMPLATES}), len(e.TEMPLATES))
        self.assertEqual(len({e.digest(t[4]) for t in e.TEMPLATES}), len(e.TEMPLATES))
        self.assertGreaterEqual(len({t[1] for t in e.TEMPLATES}), 15)

    def test_new_context_draft_is_never_approval_or_reserve(self):
        result = e.generate({'items': [media(tag='kitchen food containers')]}, {'version': 1, 'drafts': []})
        self.assertEqual(result['drafts'][0]['topic'], 'potes-conferir-tampas')
        self.assertFalse(result['drafts'][0]['approved'])
        self.assertFalse(result['drafts'][0]['editorial_approved'])
        self.assertFalse(result['drafts'][0]['published'])
        self.assertIsNone(result['last_run']['approved_reserve_days'])
        self.assertEqual(result['last_run']['pending_review'], 1)

    def test_expanded_bank_does_not_recycle_known_source(self):
        source = media(tag='kitchen food containers')
        first = e.generate({'items': [source]}, {'version': 1, 'drafts': []})
        again = e.generate({'items': [source]}, first)
        self.assertEqual(again['last_run']['created'], 0)
        self.assertEqual(again['drafts'], first['drafts'])

    def test_incidental_container_word_is_not_food_context(self):
        result = e.generate({'items': [media(tag='shipping container port')]}, {'version': 1, 'drafts': []})
        self.assertEqual(result['last_run']['created'], 0)


if __name__ == '__main__':
    unittest.main()
