import copy
import datetime as dt
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import wan104 as wan, wan104_finish as finish, daily_budget
from test_wan104_policy import post_fixture
from content_catalog import novel_scripts


class Memory:
    def __init__(self, value, fail=False):
        self.value, self.fail, self.writes = copy.deepcopy(value), fail, 0

    def load(self): return copy.deepcopy(self.value), 'revision'

    def save(self, value, revision):
        self.writes += 1
        if self.fail: raise RuntimeError('uncertain inventory checkpoint')
        self.value = copy.deepcopy(value)
        return 'next'


class WanContinuityTests(unittest.TestCase):
    def test_activation_requires_public_playback_exact_media_and_provider_identity(self):
        post = post_fixture()
        entry = {'status': 'PUBLISH_COMPLETE', 'publicly_verified': True,
            'public_visibility_evidence': {'public_playback_verified': True}, 'sha256': post['quality']['sha256'],
            'buffer_post_id': 'real-buffer-id', 'public_urls': ['https://www.tiktok.com/verified']}
        profile = json.loads(wan.PROFILE.read_text())
        profile['activation_proof'] = {'post_id': post['id'], 'sha256': entry['sha256'],
                                     'provider_id': entry['buffer_post_id'], 'public_url': entry['public_urls'][0]}
        self.assertTrue(wan.require_public_activation(profile, {'posts': [post]}, {'posts': {post['id']: entry}}))
        for field, value in [('status', 'SCHEDULED'), ('publicly_verified', False), ('sha256', 'e'*64), ('buffer_post_id', 'different')]:
            bad = dict(entry, **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                wan.require_public_activation(profile, {'posts': [post]}, {'posts': {post['id']: bad}})

    def test_quota_wait_is_read_only_and_does_not_claim_another_request(self):
        date = dt.datetime(2026, 11, 7, 13, tzinfo=dt.timezone.utc)
        ledger = daily_budget.fresh()
        for letter, seconds in zip('abcd', [75, 60, 60, 60]):
            ledger = daily_budget.reserve(ledger, letter*64, date, tier='free', estimated_seconds=seconds)
        old = copy.deepcopy(ledger)
        profile = json.loads(wan.PROFILE.read_text())
        with patch.object(wan, 'now', return_value=date+dt.timedelta(hours=1)):
            result = wan.quota_wait(ledger, wan.request_spec(profile, 2, 0), 'free')
        self.assertEqual(result['status'], 'WAIT_FREE_QUOTA')
        self.assertEqual(result['new_gpu_calls'], 0)
        self.assertEqual(ledger, old)

    def test_next_episode_has_factual_scripts_distinct_from_first_publication(self):
        ideas = [('next', [], lines) for lines in wan.script_variants(2)]
        remaining = novel_scripts(ideas, {'posts': [{'script_lines': wan.SCRIPT}]}, {'posts': {}})
        self.assertTrue(remaining)
        self.assertTrue(any(lines[1:] != wan.SCRIPT[1:] for _, _, lines in remaining))

    def test_queue_committed_inventory_failed_recovers_without_overwriting_history(self):
        post = post_fixture(); post['concept'] = 'licensed-wan104-episode-1'
        inventory = {'episode': 1, 'clips': post['quality']['licensed_sources'], 'outputs': []}
        producer = Memory({'outputs': {'prior-publication': {'sha256': '9'*64, 'status': 'PUBLISH_COMPLETE'}}, 'candidates': {'preserved': {'status': 'REJECTED'}}})
        inv = Memory(inventory, fail=True)
        with self.assertRaises(RuntimeError): finish.complete_handoff(inv, copy.deepcopy(inventory), 'r', post, producer)
        self.assertEqual(producer.writes, 1)
        inv.fail = False
        finish.complete_handoff(inv, copy.deepcopy(inventory), 'r', post, producer)
        self.assertEqual(producer.writes, 1)
        self.assertEqual(inv.value['episode'], 2)
        self.assertEqual(inv.value['clips'], [])
        self.assertEqual(len(inv.value['outputs']), 1)
        self.assertEqual(producer.value['outputs']['prior-publication']['status'], 'PUBLISH_COMPLETE')
        self.assertEqual(producer.value['candidates']['preserved']['status'], 'REJECTED')

    def test_existing_queue_handoff_does_not_render_or_upload_again(self):
        post = post_fixture(); post['concept'] = 'licensed-wan104-episode-1'
        inventory = Memory({'episode': 1, 'clips': post['quality']['licensed_sources'], 'outputs': []})
        producer = Memory({'outputs': {}, 'candidates': {}})
        stores = {'automation/experimental81/wan104_inventory.json': inventory,
                  'automation/queue.json': Memory({'posts': [post]}), 'automation/state.json': Memory({'posts': {}}),
                  'automation/production_state.json': producer}
        with patch.dict('os.environ', {'GH_TOKEN': 'test-only'}), patch.object(finish, 'GitHubStore', side_effect=lambda token, path, validate=False: stores[path]), patch.object(finish, 'compose') as render, patch('release_media.publish') as upload:
            result = finish.stage(trial=True)
        self.assertEqual(result['status'], 'QUEUED_ALREADY_DO_NOT_REPEAT')
        render.assert_not_called(); upload.assert_not_called()
        self.assertEqual(inventory.value['episode'], 2)

    def test_existing_output_with_different_bytes_never_overwritten(self):
        post = post_fixture()
        producer = Memory({'outputs': {post['id']: {'sha256': 'f'*64}}})
        with self.assertRaisesRegex(ValueError, 'MUST_NOT_BE_OVERWRITTEN'):
            finish.register_production_output(producer, post)
        self.assertEqual(producer.writes, 0)


if __name__ == '__main__': unittest.main()
