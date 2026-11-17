"""Mission 11 regressions: discovery progress, bounded budgets and stock recovery."""
import copy
import datetime as dt
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import media_acquisition as acquisition
import media_providers as providers
from test_media_providers import pixabay


class DiscoveryRecoveryTests(unittest.TestCase):
    def test_discovery_expands_supported_contexts_and_leaves_recent_searches(self):
        bank = acquisition.discovery_bank()
        self.assertGreater(len(bank), 100)
        cache = {}
        seen = set()
        for window in range(20):
            plan = acquisition.discovery_topics(window*43200+100, cache)
            self.assertEqual(len(plan), 4)
            for _, query, _ in plan:
                self.assertNotIn(query, seen)
                seen.add(query)
                cache['pixabay:'+query+'|native-full-v1'] = {'at': window*43200+100, 'data': {'hits': []}}
        self.assertEqual(len(seen), 80)
        self.assertEqual(len(bank), len({q for _, q, _ in bank}))

    def test_empty_context_pages_progress_beyond_third_without_crawl(self):
        hits = [dict(pixabay(), tags='mountain landscape') for _ in range(15)]
        cache = {'pixabay:cleaning|native-full-v1'+('' if n == 1 else '|page='+str(n)):
                 {'at': 100, 'data': {'totalHits': 150, 'hits': hits}} for n in range(1, 5)}
        p = providers.PixabayProvider('test-key', cache, now=101)
        p.allow_full_frame = True; p.known_urls = set()
        with patch.object(providers, 'request', return_value=io.BytesIO(b'{"hits": [], "totalHits": 150}')) as network:
            p.search('cleaning', 'cleaning', ['cleaning'])
        self.assertEqual(network.call_count, 1)
        self.assertIn('page=5', network.call_args.args[0])
        self.assertEqual(p.requests, 1)

    def test_new_reviewable_candidate_prevents_skipping_a_page(self):
        hit = pixabay()
        cache = {'pixabay:cleaning|native-full-v1': {'at': 100, 'data': {'hits': [hit]*15, 'totalHits': 150}}}
        p = providers.PixabayProvider('test-key', cache, now=101)
        p.allow_full_frame = True; p.known_urls = set()
        with patch.object(providers, 'request', side_effect=AssertionError('unexpected HTTP')):
            self.assertTrue(p.search('cleaning', 'cleaning', ['cleaning']))
        self.assertEqual(p.last_diagnostics['page'], 1)

    def test_filter_diagnostics_explain_zero_candidates(self):
        p = providers.PixabayProvider('test-key', {}, now=101)
        hit = pixabay(); hit['duration'] = 1
        with patch.object(p, 'json', return_value={'hits': [hit], 'totalHits': 1}):
            self.assertEqual(p.search('cleaning', 'cleaning', ['cleaning']), [])
        self.assertEqual(p.last_diagnostics['duration_rejected'], 1)
