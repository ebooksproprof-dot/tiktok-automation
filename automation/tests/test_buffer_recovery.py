"""Independent recovery regressions. All provider traffic is mocked."""
import datetime as dt
import io
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import buffer_runner as b

NOW = dt.datetime(2026, 10, 21, 12, tzinfo=dt.timezone.utc)


class BufferRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch.object(b.common, 'utc_now', return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.state = {'posts': {}}
        self.post = dict(id='casasem-2026-10-21-1', publication_provider='buffer',
                         approved=True, consented_at='2026-10-20T12:00:00Z',
                         title='Uma dica segura.', scheduled_at=(NOW + dt.timedelta(hours=1)).isoformat(),
                         video_url='https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-2026-10/proof.mp4',
                         quality=dict(technical_pass=True, editorial_approved=True, sha256='a'*64,
                                      visual_policy_version=1, visual_distinct=True,
                                      visual_sources=[dict(source_id='source-new', sha256='b'*64,
                                                           dhash=['0'*16]*5)]))

    def entry(self, **overrides):
        value = dict(provider='buffer', buffer_post_id='remote', status='SCHEDULED',
                     scheduled_at=(NOW + dt.timedelta(hours=1)).isoformat(), publicly_verified=False)
        value.update(overrides)
        return value

    def main_no_network(self, expected):
        with patch.dict(b.os.environ, {'BUFFER_API_KEY': '', 'BUFFER_CHANNEL_ID': 'channel'}), \
                patch.object(b.common, 'load_json', side_effect=[self.state, {'posts': []}]), \
                patch.object(b.common, 'save_json'), patch.object(b.common, 'summary'), \
                patch.object(b.urllib.request, 'urlopen') as network:
            self.assertEqual(b.main(), expected)
        network.assert_not_called()

    def test_empty_work_is_noop_without_secret(self):
        self.main_no_network(0)

    def test_future_scheduled_is_noop_without_secret(self):
        self.state['posts']['existing'] = self.entry()
        self.main_no_network(0)

    def test_expired_unsent_queue_alerts_without_network(self):
        self.post['scheduled_at'] = (NOW-dt.timedelta(hours=1)).isoformat()
        with patch.dict(b.os.environ, {'BUFFER_API_KEY': '', 'BUFFER_CHANNEL_ID': 'channel'}), \
                patch.object(b.common, 'load_json', side_effect=[self.state, {'posts': [self.post]}]), \
                patch.object(b.common, 'save_json'), patch.object(b.common, 'summary'), \
                patch.object(b.urllib.request, 'urlopen') as network:
            self.assertEqual(b.main(), 2)
        network.assert_not_called()

    def test_unknown_without_remote_id_is_blocked_without_network(self):
        self.state['posts']['unknown'] = self.entry(status='SUBMISSION_UNKNOWN', buffer_post_id=None)
        self.assertEqual(b.pending_reconciliation(self.state), [])
        self.main_no_network(2)

    def test_unknown_with_remote_id_is_reconciled_before_due(self):
        entry = self.entry(status='SUBMISSION_UNKNOWN')
        self.state['posts']['unknown'] = entry
        self.assertEqual(b.pending_reconciliation(self.state), [entry])

    def test_due_reconciliation_obeys_thirty_minute_boundary(self):
        entry = self.entry(scheduled_at=(NOW-dt.timedelta(hours=1)).isoformat(),
                           last_checked_at=(NOW-dt.timedelta(minutes=29, seconds=59)).isoformat())
        self.state['posts']['existing'] = entry
        self.assertEqual(b.pending_reconciliation(self.state), [])
        entry['last_checked_at'] = (NOW-dt.timedelta(minutes=30)).isoformat()
        self.assertEqual(b.pending_reconciliation(self.state), [entry])

    def test_recent_failed_reconciliation_attempt_is_throttled(self):
        entry = self.entry(status='SUBMISSION_UNKNOWN',
                           last_reconcile_attempt_at=(NOW-dt.timedelta(minutes=5)).isoformat())
        self.state['posts']['existing'] = entry
        self.assertEqual(b.pending_reconciliation(self.state), [])

    def test_two_other_reservations_block_third_same_local_day(self):
        self.state['posts'] = {
            'confirmed': dict(status='PUBLISH_COMPLETE', scheduled_at='2026-10-21T08:00:00-03:00'),
            'ambiguous': dict(status='SUBMISSION_UNKNOWN', scheduled_at='2026-10-21T18:00:00-03:00')}
        with self.assertRaisesRegex(ValueError, 'Daily maximum'):
            b.prepare(self.post, self.state, 'channel')

    def test_same_slot_blocks_even_foreign_provider(self):
        self.state['posts']['metricool'] = dict(provider='metricool',
            scheduled_at={'dateTime': '2026-10-21T10:00:00', 'timezone': 'America/Fortaleza'})
        with self.assertRaisesRegex(ValueError, 'slot already reserved'):
            b.prepare(self.post, self.state, 'channel')

    def test_utc_day_does_not_replace_fortaleza_day(self):
        self.state['posts'] = {
            'previous-night': dict(scheduled_at='2026-10-21T01:00:00Z'),
            'today': dict(scheduled_at='2026-10-21T08:00:00-03:00')}
        self.assertEqual(b.prepare(self.post, self.state, 'channel')['channelId'], 'channel')

    def test_timeout_after_acceptance_keeps_remote_id_and_never_recreates(self):
        client = Mock()
        client.call.side_effect = [
            {'createPost': {'__typename': 'PostActionSuccess', 'post': {'id': 'accepted-id'}}},
            TimeoutError('readback failed')]
        with patch.object(b, 'verify_hosted'), patch.object(b.common, 'checkpoint') as checkpoint:
            with self.assertRaises(TimeoutError):
                b.submit(client, self.post, self.state, 'channel')
            stored = self.state['posts'][self.post['id']]
            self.assertEqual(stored['buffer_post_id'], 'accepted-id')
            self.assertEqual(stored['status'], 'SUBMISSION_UNKNOWN')
            self.assertFalse(stored['publicly_verified'])
            self.assertEqual(checkpoint.call_count, 2)
            with self.assertRaises(ValueError):
                b.submit(client, self.post, self.state, 'channel')
        self.assertEqual(client.call.call_count, 2)

    def test_malformed_response_never_looks_like_success(self):
        for payload in ([], {'data': []}, {'errors': [{'message': 'PRIVATE_PROVIDER_TEXT'}]}, None):
            with self.subTest(payload=payload):
                response = io.BytesIO(json.dumps(payload).encode())
                response.headers = {}
                with patch.dict(b.os.environ, {'BUFFER_API_KEY': 'mock-only'}), \
                        patch.object(b.common, 'save_json'), \
                        patch.object(b.urllib.request, 'urlopen', return_value=response), \
                        patch.object(b.buffer_quota, 'check'), \
                        patch.object(b.buffer_quota, 'record_attempt'), \
                        patch.object(b.buffer_quota, 'record_headers'), \
                        patch.object(b.buffer_quota, 'record_error') as failure, \
                        patch.object(b.buffer_quota, 'record_success') as success:
                    with self.assertRaises(RuntimeError) as error:
                        b.Client(self.state).call('query { account { id } }', {})
                self.assertNotIn('PRIVATE_PROVIDER_TEXT', str(error.exception))
                failure.assert_called_once()
                success.assert_not_called()
