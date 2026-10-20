import sys
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import buffer_runner as b


class BufferSafetyTests(unittest.TestCase):
    def setUp(self):
        self.state = {"posts": {}}
        self.post = {"id": "casasem-test", "publication_provider": "buffer",
                     "title": "Uma dica segura #CasaSemEsforco",
                     "scheduled_at": (b.common.utc_now() + timedelta(hours=1)).isoformat(),
                     "video_url": "https://ebooksproprof-dot.github.io/tiktok-automation/public/rendered/daily/test.mp4",
                     "quality": {"technical_pass": True, "editorial_approved": True, "sha256": "a" * 64,
                                 "visual_policy_version": 1, "visual_distinct": True,
                                 "visual_sources": [dict(source_id='test', sha256='b'*64, dhash=['0'*16]*5)]}}
        self.channel = {"id": "channel", "name": ".casasemesforo", "service": "tiktok",
                        "isDisconnected": False, "isLocked": False, "isQueuePaused": False,
                        "metadata": {"defaultToReminders": False}}

    def test_wrong_account_and_reminders_block(self):
        for fields in ({"name": "outra"}, {"isDisconnected": True},
                       {"metadata": {"defaultToReminders": True}}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                b.check_channel(dict(self.channel, **fields), "channel")

    def test_metricool_duplicate_hash_blocks_buffer(self):
        self.state["posts"]["old"] = {"provider": "metricool", "sha256": "a" * 64}
        with self.assertRaises(ValueError):
            b.prepare(self.post, self.state, "channel")

    def test_technical_pass_is_not_editorial_approval(self):
        self.post["quality"]["editorial_approved"] = False
        with self.assertRaises(ValueError):
            b.prepare(self.post, self.state, "channel")

    def test_expired_slot_does_not_publish_now(self):
        self.post["scheduled_at"] = (b.common.utc_now() - timedelta(minutes=1)).isoformat()
        with self.assertRaises(ValueError):
            b.prepare(self.post, self.state, "channel")

    def test_notification_or_wrong_url_is_not_public_evidence(self):
        base = {"id": "remote", "channelId": "channel", "status": "sent",
                "schedulingType": "automatic", "sentAt": b.common.iso_now(),
                "externalLink": "https://www.tiktok.com/@.casasemesforo/video/123"}
        for fields in ({"schedulingType": "notification"},
                       {"externalLink": "https://www.tiktok.com/@outra/video/123"},
                       {"externalLink": None}, {"status": "scheduled", "dueAt": self.post["scheduled_at"]}):
            entry = {"buffer_post_id": "remote", "scheduled_at": self.post["scheduled_at"]}
            b.record_remote(entry, dict(base, **fields), "channel")
            self.assertFalse(entry["publicly_verified"])

    def test_sent_with_correct_public_url_records_evidence(self):
        entry = {"buffer_post_id": "remote"}
        b.record_remote(entry, {"id": "remote", "channelId": "channel", "status": "sent",
            "schedulingType": "automatic", "sentAt": b.common.iso_now(),
            "externalLink": "https://www.tiktok.com/@.casasemesforo/video/123"}, "channel")
        self.assertTrue(entry["publicly_verified"])
        self.assertEqual(entry["status"], "PUBLISH_COMPLETE")

    def test_checkpoint_failure_prevents_write(self):
        client = Mock()
        with patch.object(b, "verify_hosted"), patch.object(b.common, "checkpoint", side_effect=RuntimeError("storage")):
            with self.assertRaises(RuntimeError):
                b.submit(client, self.post, self.state, "channel")
        client.call.assert_not_called()

    def test_timeout_cannot_be_resubmitted(self):
        client = Mock()
        client.call.side_effect = TimeoutError()
        with patch.object(b, "verify_hosted"), patch.object(b.common, "checkpoint"):
            with self.assertRaises(TimeoutError):
                b.submit(client, self.post, self.state, "channel")
            with self.assertRaises(ValueError):
                b.submit(client, self.post, self.state, "channel")
        self.assertEqual(client.call.call_count, 1)
        self.assertEqual(self.state["posts"][self.post["id"]]["status"], "SUBMISSION_UNKNOWN")

    def test_acceptance_requires_readback(self):
        client = Mock()
        remote = {"id": "remote", "channelId": "channel", "status": "scheduled",
                  "schedulingType": "automatic", "dueAt": self.post["scheduled_at"]}
        client.call.side_effect = [{"createPost": {"__typename": "PostActionSuccess", "post": remote}},
                                   {"post": remote}]
        with patch.object(b, "verify_hosted"), patch.object(b.common, "checkpoint"):
            b.submit(client, self.post, self.state, "channel")
        entry = self.state["posts"][self.post["id"]]
        self.assertEqual(client.call.call_count, 2)
        self.assertEqual(entry["status"], "SCHEDULED")
        self.assertFalse(entry["publicly_verified"])

    def test_free_request_budget_prevents_network_call(self):
        self.state["buffer_api_usage"] = [b.common.iso_now()] * 90
        with patch.dict(b.os.environ, {"BUFFER_API_KEY": "test-not-a-real-key"}):
            client = b.Client(self.state)
        with patch.object(b.urllib.request, "urlopen") as network:
            with self.assertRaises(RuntimeError):
                client.call("query { account { id } }", {})
        network.assert_not_called()

    def test_overdue_remote_post_alerts_without_resubmission(self):
        due = (b.common.utc_now() - timedelta(hours=3)).isoformat()
        for status in ('scheduled', 'sending'):
            entry = {'buffer_post_id': 'remote', 'scheduled_at': due}
            b.record_remote(entry, {'id': 'remote', 'channelId': 'channel',
                'status': status, 'schedulingType': 'automatic', 'dueAt': due}, 'channel')
            self.assertEqual(entry['status'], 'PUBLICATION_OVERDUE')
            self.assertFalse(entry['publicly_verified'])

    def test_foreign_queue_does_not_block_buffer(self):
        foreign = dict(self.post, publication_provider='metricool')
        client = Mock()
        client.call.return_value = {'channel': self.channel}
        with patch.object(b, 'Client', return_value=client), patch.dict(b.os.environ, {'BUFFER_CHANNEL_ID': 'channel'}), patch.object(b.common, 'load_json', side_effect=[self.state, {'posts': [foreign]}]), patch.object(b.common, 'save_json'), patch.object(b.common, 'summary'):
            self.assertEqual(b.main(), 0)
        self.assertEqual(client.call.call_count, 0)

    def test_insufficient_budget_leaves_no_submission_intent(self):
        self.state['buffer_api_usage'] = [b.common.iso_now()] * 89
        with patch.dict(b.os.environ, {'BUFFER_API_KEY': 'test-not-a-real-key'}):
            client = b.Client(self.state)
        with patch.object(b, 'verify_hosted'), patch.object(b.common, 'checkpoint') as checkpoint:
            with self.assertRaises(RuntimeError):
                b.submit(client, self.post, self.state, 'channel')
        checkpoint.assert_not_called()
        self.assertEqual(self.state['posts'], {})

    def test_missing_public_link_preserves_safe_diagnostic(self):
        entry = {'buffer_post_id': 'remote'}
        b.record_remote(entry, {'id': 'remote', 'channelId': 'channel', 'status': 'sent',
            'schedulingType': 'automatic', 'sentAt': b.common.iso_now(), 'externalLink': None}, 'channel')
        self.assertEqual(entry['evidence_pending_reason'], 'PUBLIC_LINK_MISSING')
        self.assertTrue(entry['buffer_sent_at_present'])
        self.assertIsNone(entry['buffer_external_link'])
        self.assertFalse(entry['publicly_verified'])

    def test_confirmed_evidence_clears_old_reason_and_query(self):
        entry = {'buffer_post_id': 'remote', 'evidence_pending_reason': 'PUBLIC_LINK_MISSING'}
        url = 'https://www.tiktok.com/@.casasemesforo/video/123'
        b.record_remote(entry, {'id': 'remote', 'channelId': 'channel', 'status': 'sent',
            'schedulingType': 'automatic', 'sentAt': b.common.iso_now(), 'externalLink': url.replace('www.', '') + '?tracking=example'}, 'channel')
        self.assertEqual(entry['public_urls'], [url])
        self.assertNotIn('evidence_pending_reason', entry)

    def test_full_run_reserves_budget_before_any_network(self):
        self.state['buffer_api_usage'] = [b.common.iso_now()] * 87
        with patch.dict(b.os.environ, {'BUFFER_API_KEY': 'test-not-real', 'BUFFER_CHANNEL_ID': 'channel'}), \
             patch.object(b.common, 'load_json', side_effect=[self.state, {'posts': [self.post]}]), \
             patch.object(b.common, 'save_json'), patch.object(b.common, 'summary'), \
             patch.object(b.urllib.request, 'urlopen') as network:
            with self.assertRaisesRegex(RuntimeError, 'budget'):
                b.main()
        network.assert_not_called()
        self.assertEqual(len(self.state['buffer_api_usage']), 87)


if __name__ == "__main__":
    unittest.main()
