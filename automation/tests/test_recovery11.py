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


class CommonsRecoveryTests(unittest.TestCase):
    def test_commons_hd_can_be_reviewed_without_crop_or_license_relaxation(self):
        from test_media_providers import commons
        page = commons(); page['imageinfo'][0].update(width=1920, height=1080)
        self.assertIsNone(providers.commons_record(page, 'kitchen', 'cleaning', ['cleaning']))
        record = providers.commons_record(page, 'kitchen', 'cleaning', ['cleaning'], allow_full_frame=True)
        self.assertEqual(record['frame_mode'], 'preserve_full')
        page['imageinfo'][0]['extmetadata']['LicenseUrl']['value'] = 'https://creativecommons.org/licenses/by-nc/4.0/'
        self.assertIsNone(providers.commons_record(page, 'kitchen', 'cleaning', ['cleaning'], allow_full_frame=True))

    def test_commons_rights_require_exact_asset_author_and_commercial_license(self):
        from test_media_providers import commons
        import source_license
        page = commons()
        record = providers.commons_record(page, 'kitchen', 'cleaning', ['cleaning'])
        record['sha256'] = 'f'*64
        def fetch(url):
            return json.dumps({'query': {'pages': {'42': page}}}).encode() if 'w/api.php' in url else b'official terms'
        proof = source_license.verify_commons(record, fetch)
        self.assertTrue(proof['commercial_use'])
        page['imageinfo'][0]['extmetadata']['Artist']['value'] = 'Different author'
        with self.assertRaisesRegex(ValueError, 'EXACT_ASSET'):
            source_license.verify_commons(record, fetch)

    def test_commons_candidates_reach_producer_not_just_inbox(self):
        from autonomous_production import candidate_records
        from test_media_providers import commons
        record = providers.commons_record(commons(), 'kitchen', 'cleaning', ['cleaning'])
        record['selection_reason'] = 'washing dishes in a kitchen sink'
        self.assertEqual(candidate_records({'items': [record]}, {}), [record])


class ContinuitySimulationTests(unittest.TestCase):
    def test_ten_days_refill_consumption_quota_outage_and_restart(self):
        import autonomous_production as production
        from experimental81 import daily_budget
        queue, state, budget = {'posts': []}, {'posts': {}}, daily_budget.fresh()
        begin = dt.datetime(2026, 11, 17, 7, tzinfo=dt.timezone.utc)
        partial, origins, consumed, slots = [], [], set(), set()
        for day in range(10):
            now = begin+dt.timedelta(days=day)
            # Recover JSON checkpoints as a new workflow process would.
            queue, state, budget, partial = json.loads(json.dumps([queue, state, budget, partial]))
            for p in queue['posts']:
                due = dt.datetime.fromisoformat(p['scheduled_at'])
                if due <= now and p['id'] not in consumed:
                    self.assertNotIn(p['quality']['sha256'], {state['posts'][i]['sha256'] for i in consumed})
                    state['posts'][p['id']] = {'status': 'PUBLISH_COMPLETE', 'sha256': p['quality']['sha256']}
                    consumed.add(p['id'])
            # A temporary free provider outage preserves partial source claims.
            if day != 2:
                for attempt in range(4):
                    ident = __import__('hashlib').sha256(f'{day}-{attempt}'.encode()).hexdigest()
                    try:
                        budget = daily_budget.reserve(budget, ident, now, tier='free', estimated_seconds=60)
                    except daily_budget.QuotaError:
                        break
                    partial.append(ident)
            def append(origin):
                ident, when = production.choose_slot(queue, state, now)
                self.assertEqual(when.minute, 0)
                self.assertIn(when.hour, (10, 18))
                self.assertGreater(when, now)
                self.assertNotIn(when.isoformat(), slots)
                slots.add(when.isoformat())
                digest = __import__('hashlib').sha256(ident.encode()).hexdigest()
                queue['posts'].append({'id': ident, 'scheduled_at': when.isoformat(), 'approved': True,
                    'consented_at': now.isoformat(), 'quality': {'technical_pass': True, 'sha256': digest}, 'origin': origin})
                origins.append(origin)
            # Existing AI gets the first production position, including overflow.
            if len(partial) >= 3 and production.stock_status(queue, state, now)['ready'] < 5:
                append('wan'); partial = partial[3:]
            # Two days of conventional unavailability do not fabricate outputs.
            if day not in (2, 3):
                for _ in range(2):
                    if not production.stock_status(queue, state, now)['refill_needed']: break
                    append('licensed')
            self.assertLessEqual(production.stock_status(queue, state, now)['ready'], 5)
            self.assertLessEqual(len(budget['window_claim_ids']), 4)
        self.assertIn('wan', origins); self.assertIn('licensed', origins)
        self.assertGreater(len(consumed), 12)
        self.assertEqual(len(queue['posts']), len({p['id'] for p in queue['posts']}))
        self.assertEqual(len(queue['posts']), len(slots))


class WanRecoveryBoundsTests(unittest.TestCase):
    def test_neutral_second_look_never_erases_unsafe_context_or_accepts_books(self):
        from semantic_review import needs_textile_disambiguation, assess_generated_organization
        self.assertTrue(needs_textile_disambiguation(1, ['white books on shelves']*3))
        self.assertFalse(needs_textile_disambiguation(1, ['a child holding white books']*3))
        self.assertFalse(needs_textile_disambiguation(0, ['white books on shelves']*3))
        self.assertFalse(needs_textile_disambiguation(1, ['folded towels']*3))
        self.assertFalse(assess_generated_organization(1, ['stacked books with paper pages']*3))

    def test_replacement_targets_missing_slot_with_new_request_and_bounded_attempts(self):
        from experimental81 import wan104 as wan
        profile = json.loads(wan.PROFILE.read_text())
        inventory = {'episode': 3, 'clips': [{'slot': 0}, {'slot': 2}], 'rejected_clips': []}
        slot, first = wan.next_scene(inventory, profile)
        self.assertEqual(slot, 1)
        inventory['rejected_clips'].append({'episode': 3, 'slot': 1, 'sha256': 'a'*64})
        slot, second = wan.next_scene(inventory, profile)
        self.assertEqual(slot, 1)
        self.assertNotEqual(first['seed'], second['seed'])
        self.assertNotEqual(first['prompt'], second['prompt'])
        self.assertEqual(inventory['clips'], [{'slot': 0}, {'slot': 2}])
        inventory['rejected_clips'].append({'episode': 3, 'slot': 1, 'sha256': 'b'*64})
        with self.assertRaisesRegex(ValueError, 'REPLACEMENT_LIMIT'):
            wan.next_scene(inventory, profile)
        inventory['episode'] = 4  # Earlier episode's rejected clips stay archived.
        self.assertEqual(wan.next_scene(inventory, profile)[1]['seed'], wan.request_spec(profile, 4, 1)['seed'])

    def test_failed_scene_preserves_previous_review_without_starting_narration(self):
        import tempfile
        from experimental81 import wan104_finish as finish
        from test_wan104_policy import quality_fixture
        q = quality_fixture(); reviewed, rejected = [], []
        def moving(path):
            if str(path) == 'b'*64: raise ValueError('SOURCE_FROZEN_OR_UNDECODABLE')
            return {}
        proof = {r['source_sha256']: r for r in q['semantic_reviews']}
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(finish, 'download', side_effect=lambda clip, folder: clip['sha256']), \
             patch.object(finish.render, 'sha', side_effect=lambda path: str(path)), \
             patch.object(finish, 'motion', side_effect=moving), \
             patch.object(finish, 'fingerprint', return_value={}), \
             patch.object(finish.render, 'synthesize') as speech:
            with self.assertRaisesRegex(ValueError, 'FROZEN'):
                finish.compose({'clips': q['licensed_sources']}, tmp, proof,
                    on_review=lambda clip, review: reviewed.append(clip['slot']),
                    on_reject=lambda clip, reason, review: rejected.append(clip['slot']))
        self.assertEqual(reviewed, [0]); self.assertEqual(rejected, [1])
        speech.assert_not_called()


class LicenseRefreshTests(unittest.TestCase):
    def test_current_official_positive_grant_required_not_just_http_200(self):
        import source_license
        policy = {'terms_url': 'https://pixabay.com/service/terms/'}
        terms = b'<p>royalty-free commercial or non-commercial purposes</p>'
        docs = b'images and videos released by Pixabay under the Content License'
        at = dt.datetime(2026, 11, 17, tzinfo=dt.timezone.utc)
        refreshed = source_license.refreshed_policy(policy, terms, docs, at)
        self.assertEqual(refreshed['retrieved_at'], at.isoformat())
        self.assertEqual(len(refreshed['terms_sha256']), 64)
        for changed_terms, changed_docs in [(b'Just a moment', docs), (terms, b'Access denied'),
                                             (b'Non-commercial only', docs)]:
            with self.assertRaisesRegex(ValueError, 'CURRENT_OFFICIAL'):
                source_license.refreshed_policy(policy, changed_terms, changed_docs, at)


class CaptionCompatibilityTests(unittest.TestCase):
    def test_portuguese_multiline_text_disables_newline_glyph_shaping(self):
        import tempfile
        from caption_layout import filters
        with tempfile.TemporaryDirectory() as tmp, patch('caption_layout.layout', return_value=(
                'Armário sem espaço? Separe os\nitens por categoria antes de', 46)):
            result = filters(Path(tmp), [[0, 5, 'Armário sem espaço? Separe os itens por categoria antes de']])
            self.assertIn('text_shaping=0', result[0])
            text = (Path(tmp)/'caption-v51-0.txt').read_text()
            self.assertIn('\n', text)
            self.assertIn('Armário', text)


class HouseholdContextTests(unittest.TestCase):
    def test_industrial_iron_does_not_consume_household_review_capacity(self):
        from semantic_review import nominate
        for text in ['soldering iron electrical circuit wire', 'gate iron metal cemetery entrance',
                     'iron cast iron craft product', 'building factory iron chimney']:
            self.assertIsNone(nominate({'selection_reason': text}))
        self.assertEqual(nominate({'selection_reason': 'iron ironing shirt clothes'}), 'clothes')

    def test_sewing_fabric_is_not_a_wiping_demonstration(self):
        from semantic_review import nominate
        self.assertIsNone(nominate({'selection_reason': 'sewing machine fabric cloth tailor sew stitch'}))
        self.assertEqual(nominate({'selection_reason': 'cleaning cloth microfiber wiping kitchen'}), 'wiping')
