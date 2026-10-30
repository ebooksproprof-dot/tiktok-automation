import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tiktok_runner as t
import render_daily as render
import readiness


class RegressionTests(unittest.TestCase):
    def test_other_provider_is_never_polled(self):
        state = {'posts': {'buffer': {'provider': 'buffer', 'status': 'SCHEDULED', 'publish_id': 'foreign'}}}
        with patch.object(t, 'api_post') as api:
            self.assertFalse(t.needs_token({'posts': []}, state))
            self.assertFalse(t.poll_existing('dummy', state))
            api.assert_not_called()

    def test_other_provider_candidate_never_calls_tiktok(self):
        post = dict(id='buffer', publication_provider='buffer', approved=True,
                    consented_at=t.iso_now(), scheduled_at=t.iso_now())
        with patch.object(t, 'load_json', side_effect=[{'posts': [post]}, {'posts': {}}]), patch.object(t, 'fetch_token_from_broker') as token:
            self.assertEqual(t.main(), 0)
            token.assert_not_called()
        with self.assertRaises(ValueError):
            t.validate_post(post, {})

    def test_public_completion_without_ids_is_reconciled(self):
        state = {'posts': {'test': dict(provider='tiktok', publish_id='p',
                    status='PUBLISH_COMPLETE', privacy_level='PUBLIC_TO_EVERYONE')}}
        self.assertTrue(t.needs_poll(state['posts']['test']))
        with tempfile.TemporaryDirectory() as directory, patch.object(t, 'STATE_PATH', Path(directory)/'state.json'), patch.object(t, 'api_post', return_value={'data': {'status': 'PUBLISH_COMPLETE', 'publicaly_available_post_id': ['123']}}):
            t.poll_existing('dummy', state)
        self.assertTrue(state['posts']['test']['publicly_verified'])
        self.assertFalse(t.needs_poll(state['posts']['test']))

    def test_single_remaining_render_failure_cannot_create_queue_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'automation').mkdir()
            queue = root/'automation/queue.json'
            queue.write_text('{"posts": []}')
            (root/'automation/state.json').write_text('{"posts": {}}')
            with patch.object(render, 'ROOT', root), patch.object(render, 'QUEUE', queue), patch.object(render, 'ASSETS', root/'tmp'), patch.object(render, 'OUT', root/'public/rendered'), patch.object(render, 'IDEAS', [('only', [], [])]), patch.object(render, 'load_voice', return_value=object()), patch.object(render, 'render', side_effect=ValueError('invalid audio')):
                with self.assertRaisesRegex(RuntimeError, 'no validated output'):
                    render.main()
            self.assertEqual(json.loads(queue.read_text()), {'posts': []})

    def test_renderer_prioritizes_measured_sufficient_real_footage(self):
        ideas = [
            ('unknown', ['unknown-src'], ['New original script']),
            ('too-short', ['short-src'], ['Short actual video']),
            ('valid', ['full-src'], ['Sufficient real video']),
        ]
        with patch.object(render, 'PROVENANCE', {
            'short-src': {'duration': 4.36},
            'full-src': {'duration': 25.0},
        }):
            ranked = render.ranked_render_candidates(ideas)
        self.assertEqual([idea[0] for idea in ranked], ['valid', 'unknown'])

    def test_render_retries_distinct_short_sources_before_succeeding(self):
        """A too-short clip must not prevent the next viable original concept."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'automation').mkdir()
            queue = root/'automation/queue.json'
            queue.write_text('{"posts": []}')
            (root/'automation/state.json').write_text('{"posts": {}}')
            ideas = [
                ('short-first', [], ['First short source']),
                ('short-second', [], ['Second short source']),
                ('valid-third', [], ['Distinct verified original footage']),
            ]
            quality = dict(duration=20, technical_pass=True, editorial_approved=False)
            future_day = render.dt.date(2030, 1, 1)
            with (patch.object(render, 'ROOT', root),
                  patch.object(render, 'QUEUE', queue),
                  patch.object(render, 'ASSETS', root/'tmp'),
                  patch.object(render, 'OUT', root/'public/rendered'),
                  patch.object(render, 'IDEAS', ideas),
                  patch.object(render, 'load_voice', return_value=object()),
                  patch.object(render, 'planned_reserve_slots', return_value=[(future_day, 1, 10)]),
                  patch.object(render, 'render', side_effect=[
                      ValueError('SOURCE_TOO_SHORT_WITHOUT_REPEATING: 4.31s available'),
                      ValueError('SOURCE_TOO_SHORT_WITHOUT_REPEATING: choose more adequate footage'),
                      (Path('valid-third.mp4'), quality),
                  ]) as renderer,
                  patch.dict(os.environ, {'MEDIA_STORAGE': 'git', 'EDITORIAL_RESERVE_DAYS': '1'})):
                render.main()
            posts = json.loads(queue.read_text())['posts']
            self.assertEqual(renderer.call_count, 3)
            self.assertEqual(len(posts), 1)
            self.assertEqual(posts[0]['concept'], 'valid-third')
            self.assertFalse(posts[0]['approved'])
            self.assertIsNone(posts[0]['consented_at'])
            self.assertFalse(posts[0]['quality']['editorial_approved'])

    def test_second_slot_failure_does_not_reuse_first_video(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'automation').mkdir()
            queue = root/'automation/queue.json'
            queue.write_text('{"posts": []}')
            (root/'automation/state.json').write_text('{"posts": {}}')
            quality = dict(duration=20, technical_pass=True, editorial_approved=False)
            with patch.object(render, 'ROOT', root), patch.object(render, 'QUEUE', queue), patch.object(render, 'ASSETS', root/'tmp'), patch.object(render, 'OUT', root/'public/rendered'), patch.object(render, 'IDEAS', [('first', [], ['First']), ('second', [], ['Second'])]), patch.object(render, 'load_voice', return_value=object()), patch.object(render, 'render', side_effect=[(Path('first.mp4'), quality), ValueError('invalid audio')]):
                with self.assertRaisesRegex(RuntimeError, 'no validated output'):
                    render.main()
            posts = json.loads(queue.read_text())['posts']
            self.assertEqual(len(posts), 1)
            self.assertEqual(posts[0]['concept'], 'first')

    def test_inventory_is_secret_safe_and_flags_exhaustion(self):
        result = readiness.inspect({'posts': [{'id':'old','concept':'one'}]}, {'posts':{}}, ['one'], 100,
                                   {'BUFFER_API_KEY':'SENSITIVE_TEST_VALUE'})
        serialized = json.dumps(result)
        self.assertNotIn('SENSITIVE_TEST_VALUE', serialized)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['unused_concepts'], 0)
        self.assertTrue(any(x.startswith('CATALOG_EXHAUSTED') for x in result['blockers']))

    def test_archived_topics_are_not_reported_as_available(self):
        result = readiness.inspect({'posts': []}, {'posts': {'archived': {'concept': 'one'}}}, ['one'], 0, {})
        self.assertEqual(result['unused_concepts'], 0)

    def test_late_render_moves_to_free_future_slot(self):
        planned = render.dt.datetime(2026, 10, 17, 10, tzinfo=render.ZoneInfo('America/Sao_Paulo'))
        now = planned.replace(hour=19)
        occupied = planned + render.dt.timedelta(days=1)
        queue = {'posts': [{'id': 'other', 'scheduled_at': occupied.isoformat()}]}
        result = render.future_slot(planned, queue, {'posts': {}}, 'new', now)
        self.assertEqual(result, occupied.replace(hour=18))

    def test_future_slot_preserves_free_plan(self):
        planned = render.dt.datetime(2026, 10, 17, 10, tzinfo=render.ZoneInfo('America/Sao_Paulo'))
        self.assertEqual(render.future_slot(planned, {'posts': []}, {'posts': {}}, 'new', planned.replace(hour=8)), planned)

    def test_future_slot_understands_metricool_history_timezone(self):
        planned = render.dt.datetime(2026, 10, 17, 10, tzinfo=render.ZoneInfo('America/Sao_Paulo'))
        state = {'posts': {'metricool': {'scheduled_at': {'dateTime': '2026-10-17T10:00:00', 'timezone': 'America/Sao_Paulo'}}}}
        self.assertEqual(render.future_slot(planned, {'posts': []}, state, 'new', planned.replace(hour=8)), planned.replace(hour=18))
