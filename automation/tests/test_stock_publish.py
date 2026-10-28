"""Mock official API tests. No real TikTok publication is performed."""
import copy
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import video_stock as stock
import stock_publish as p

NOW = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)


class MemoryStore:
    def __init__(self, state): self.state, self.revision = copy.deepcopy(state), 0
    def load(self): return copy.deepcopy(self.state), self.revision
    def save(self, state, revision):
        if self.revision != revision: raise stock.Conflict('stale')
        self.state = copy.deepcopy(state)
        self.revision += 1
        return self.revision


def inventory():
    state = stock.empty()
    item = stock.add_video(state, dict(stock.IDENTITY,
        sha256='a'*64, script='Uma dica original para deixar a cozinha organizada todos os dias.',
        filename='tip.mp4', subject='Organizacao', source_evidence='Studio export reviewed',
        storage_url='https://github.com/'+stock.REPO+'/releases/download/stock-inbox/tip.mp4',
        quality={'technical_pass': True, 'sha256': 'a'*64, 'duration': 20},
        identity_reviewed=True, rights_reviewed=True, editorial_reviewed=True,
        lip_sync_reviewed=True, subtitles_reviewed=True, commercial_content=False,
        reviewed_at='2026-10-27T12:00:00Z', caption='Uma dica para organizar sua casa.'), NOW)
    stock.schedule(state, NOW)
    return state, item['id']


class PublishTests(unittest.TestCase):
    def client(self, store):
        client = Mock()
        client.state = {'posts': {}}
        def call(query, variables):
            self.assertEqual(store.state['items'][0]['attempts'], 1)
            if query == p.buffer.CREATE_QUERY:
                self.assertEqual(store.state['items'][0]['status'], 'PUBLISHING')
                return {'createPost': {'__typename':'PostActionSuccess', 'post': {'id':'remote'}}}
            return {'post': {'id':'remote','channelId':'channel','status':'sent',
                'schedulingType':'automatic','sentAt':'2026-10-28T13:00:00Z',
                'externalLink':'https://www.tiktok.com/@.casasemesforo/video/123'}}
        client.call.side_effect = call
        return client

    def test_claim_and_legacy_intent_before_http_and_real_readback_required(self):
        state, ident = inventory(); store = MemoryStore(state); client = self.client(store)
        with patch.object(p.buffer, 'verify_hosted'):
            p.submit_one(store, client, ident, 'channel', {'posts': []}, NOW)
        item = store.state['items'][0]
        self.assertEqual(item['status'], 'PUBLISHED')
        self.assertEqual(item['publication_id'], '123')
        self.assertEqual(client.call.call_count, 2)
        self.assertIn(ident, client.state['posts'])
        with self.assertRaises(ValueError):
            p.submit_one(store, client, ident, 'channel', {'posts': []}, NOW)
        self.assertEqual(client.call.call_count, 2)

    def test_failed_durable_claim_never_calls_api(self):
        state, ident = inventory(); store = MemoryStore(state); client = self.client(store)
        store.save = Mock(side_effect=stock.Conflict('conflict'))
        with patch.object(p.buffer, 'verify_hosted'), self.assertRaises(stock.Conflict):
            p.submit_one(store, client, ident, 'channel', {'posts': []}, NOW)
        client.call.assert_not_called()

    def test_timeout_is_unknown_and_cannot_retry(self):
        state, ident = inventory(); store = MemoryStore(state); client = self.client(store)
        client.call.side_effect = TimeoutError('simulated')
        with patch.object(p.buffer, 'verify_hosted'), self.assertRaises(TimeoutError):
            p.submit_one(store, client, ident, 'channel', {'posts': []}, NOW)
        self.assertEqual(store.state['items'][0]['status'], 'UNKNOWN')
        with self.assertRaises(ValueError):
            p.submit_one(store, client, ident, 'channel', {'posts': []}, NOW)
        self.assertEqual(client.call.call_count, 1)

    def test_affiliate_requires_supported_disclosure(self):
        state, _ = inventory(); item = state['items'][0]
        for value in (True, None):
            item['commercial_content'] = value
            with self.assertRaisesRegex(ValueError, 'Commercial'):
                p.check_item(item, {'posts': {}}, {'posts': []}, NOW)

    def test_legacy_duplicates_and_timezone_dict(self):
        state, _ = inventory(); item = state['items'][0]
        for legacy in ({'sha256':item['sha256']}, {'script_sha256':item['script_sha256']},
                       {'scheduled_at':{'dateTime':'2026-10-28T10:00:00','timezone':'America/Sao_Paulo'}}):
            with self.assertRaises(ValueError):
                p.check_item(item, {'posts': {'old':legacy}}, {'posts': []}, NOW)
        p.check_item(item, {'posts': {'old':{'scheduled_at':{'dateTime':'2026-10-20T10:00:00','timezone':'America/Sao_Paulo'}}}}, {'posts': []}, NOW)

    def test_no_external_link_never_published(self):
        state, ident = inventory(); stock.claim(state, ident, NOW)
        stock.resolve(state, ident, 'UNKNOWN', NOW, remote_id='remote')
        store = MemoryStore(state); client = Mock(state={'posts':{}})
        client.call.return_value = {'post': {'id':'remote','channelId':'channel','status':'sent',
            'schedulingType':'automatic','sentAt':'2026-10-28T13:00:00Z','externalLink':None}}
        p.reconcile_one(store, client, ident, 'channel', NOW)
        self.assertEqual(store.state['items'][0]['status'], 'UNKNOWN')

    def test_quota_checkpoint_failure_blocks_even_read_request(self):
        legacy = MemoryStore({'posts':{}})
        client = p.DurableClient(legacy, token='not-real', now=lambda:NOW)
        legacy.save = Mock(side_effect=stock.Conflict('conflict'))
        with patch.object(p.urllib.request, 'urlopen') as network, self.assertRaises(stock.Conflict):
            client.call('query { example }', {})
        network.assert_not_called()

    def test_empty_stock_zero_provider_calls(self):
        with patch.object(p, 'DurableClient') as client:
            result = p.run(MemoryStore(stock.empty()), MemoryStore({'posts':{}}), {'posts':[]}, 'channel', NOW)
        self.assertEqual(result['api_calls'], 0)
        client.assert_not_called()

    def test_remote_free_queue_full_keeps_stock_unattempted(self):
        state, _ = inventory(); store = MemoryStore(state)
        fake = Mock()
        fake.calls = 2
        fake.call.side_effect = [
            {'channel': {'organizationId':'org'}},
            {'posts': {'edges':[{'node':{'channelId':'channel'}}]*10,
                       'pageInfo':{'hasNextPage':False}}}]
        with patch.object(p, 'DurableClient', return_value=fake), \
             patch.object(p.buffer, 'check_channel'), patch.object(p, 'submit_one') as submit:
            result = p.run(store, MemoryStore({'posts':{}}), {'posts':[]}, 'channel', NOW)
        submit.assert_not_called()
        self.assertEqual(result['submitted'], 0)
        self.assertEqual(store.state['items'][0]['attempts'], 0)

    def test_check_only_never_submits(self):
        state, _ = inventory()
        fake = Mock(); fake.calls = 1
        fake.call.return_value = {'channel': {}}
        with patch.object(p, 'DurableClient', return_value=fake), \
             patch.object(p.buffer, 'check_channel'), patch.object(p, 'submit_one') as submit:
            result = p.run(MemoryStore(state), MemoryStore({'posts':{}}), {'posts':[]}, 'channel', NOW, check_only=True)
        self.assertTrue(result['channel_verified'])
        submit.assert_not_called()

    def test_commercial_hold_requires_zero_api_calls(self):
        state, _ = inventory(); state['items'][0]['commercial_content'] = True
        with patch.object(p, 'DurableClient') as client:
            result = p.run(MemoryStore(state), MemoryStore({'posts':{}}), {'posts':[]}, 'channel', NOW)
        client.assert_not_called()
        self.assertEqual(len(result['held']), 1)
        self.assertEqual(result['submitted'], 0)

    def test_http_timeout_persists_quota_without_token_in_error(self):
        legacy = MemoryStore({'posts':{}})
        client = p.DurableClient(legacy, token='secret-test-token', now=lambda:NOW)
        def fail(request, timeout):
            self.assertEqual(len(legacy.state['buffer_api_usage']), 1)
            raise TimeoutError('secret-test-token must not escape transport')
        with patch.object(p.urllib.request, 'urlopen', side_effect=fail), \
             patch.object(p.buffer.common, 'save_json'), self.assertRaises(RuntimeError) as caught:
            client.call('query { example }', {})
        self.assertNotIn('secret-test-token', str(caught.exception))
        self.assertEqual(len(legacy.state['buffer_api_usage']), 1)
        self.assertEqual(legacy.state['buffer_quota']['last_error_code'], 'TRANSPORT_OR_RESPONSE')
        restored = p.DurableClient(legacy, token='secret-test-token', now=lambda:NOW)
        with self.assertRaises(p.buffer_quota.BudgetExceeded): restored.check_budget()

    def test_payload_ai_labeled(self):
        state, _ = inventory()
        result = p.payload(state['items'][0], 'channel')
        self.assertTrue(result['metadata']['tiktok']['isAiGenerated'])
        self.assertEqual(result['dueAt'], '2026-10-28T13:00:00Z')


if __name__ == '__main__': unittest.main()
