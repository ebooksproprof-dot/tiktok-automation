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
        hit = pixabay(); hit['tags'] = 'cleaning window cloth'
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


class WanSourceCorrectionTests(unittest.TestCase):
    def test_towel_false_positive_is_bound_to_exact_source_and_slot(self):
        from experimental81 import wan104_finish as finish
        inventory = json.loads((acquisition.ROOT/'experimental81/wan104_inventory.json').read_text())
        proof = json.loads((acquisition.ROOT/'experimental81/wan104_source_reviews.json').read_text())
        sha = 'c270d7a327a0f994b06da1401e695a3c53d1e56f863d58475a63b5a1e8e661cc'
        clip = {'sha256': sha, 'slot': 1}
        r = finish.cached_review(clip, proof)
        self.assertTrue(r['accepted'])
        self.assertFalse(r['original_automated_review']['accepted'])
        self.assertIsNone(finish.cached_review(dict(clip, slot=0), proof))
        self.assertIsNone(finish.cached_review(dict(clip, sha256='e'*64), proof))
        from semantic_review import assess_generated_organization
        self.assertFalse(assess_generated_organization(1, ['Four white books on a shelf.']*3))
        self.assertFalse(assess_generated_organization(1, ['A person with towels.']*3))
        import hashlib
        self.assertEqual(hashlib.sha256((acquisition.ROOT.parent/r['correction']['evidence_path']).read_bytes()).hexdigest(),
                         r['correction']['evidence_sha256'])

    def test_four_fallback_reservations_cannot_starve_wan_assembly(self):
        from experimental81 import wan104_finish as finish
        from test_wan104_continuity import Memory
        from test_wan104_policy import post_fixture
        post = post_fixture()
        stores = {'automation/experimental81/wan104_inventory.json': Memory({'episode': 2, 'clips': post['quality']['licensed_sources'], 'outputs': []}),
                  'automation/queue.json': Memory({'posts': []}), 'automation/state.json': Memory({'posts': {}}),
                  'automation/production_state.json': Memory({'outputs': {}, 'candidates': {}})}
        with patch.dict('os.environ', {'GH_TOKEN': 'test-only'}), \
             patch.object(finish, 'GitHubStore', side_effect=lambda token, path, validate=False: stores[path]), \
             patch('autonomous_production.stock_status', return_value={'ready': 4, 'held_uncertain': 0, 'target_max': 4}), \
             patch.object(finish.wan104, 'script_choices', return_value=[('new', [], ['new script'])]), \
             patch.object(finish, 'compose', side_effect=ValueError('REACHED_REAL_ASSEMBLY')):
            with self.assertRaisesRegex(ValueError, 'REACHED_REAL_ASSEMBLY'):
                finish.stage()

    def test_failed_acquisition_still_triggers_independent_production(self):
        workflow = (acquisition.ROOT.parent/'.github/workflows/casasemesforco-daily.yml').read_text()
        self.assertIn("github.event.workflow_run.conclusion == 'failure'", workflow)
        self.assertIn("len(wan.get('clips', [])) == 3", workflow)
