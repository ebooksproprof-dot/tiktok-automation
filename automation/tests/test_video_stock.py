"""Simulated persistence/provider tests; never claims real TikTok publication."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import video_stock as s

NOW = datetime(2026, 10, 28, 11, tzinfo=timezone.utc)


def metadata(n=0):
    digest = hashlib.sha256(str(n).encode()).hexdigest()
    return dict(filename=f'{n}.mp4', storage_url=f'https://github.com/{s.REPO}/releases/download/stock-inbox/{n}.mp4',
        sha256=digest, script=f'Organize os seus utensílios todos os dias sem esforço. Ideia original {n}.',
        subject='Organização', **s.IDENTITY, quality={'technical_pass': True, 'sha256': digest, 'duration': 20},
        source_evidence='Studio export declared by owner', identity_reviewed=True,
        rights_reviewed=True, editorial_reviewed=True)


class VideoStockTests(unittest.TestCase):
    def stock(self):
        state = s.empty()
        item = s.add_video(state, metadata(), NOW)
        s.schedule(state, NOW)
        return state, item

    def test_import_schedule_and_restart(self):
        state, item = self.stock()
        self.assertEqual(item['scheduled_at'], '2026-10-28T13:00:00Z')
        with tempfile.TemporaryDirectory() as folder:
            store = s.LocalStore(Path(folder)/'stock.json')
            rev = store.save(state, None)
            recovered, rev2 = s.LocalStore(store.path).load()
            self.assertEqual(recovered, state)
            self.assertEqual(rev, rev2)
            with self.assertRaises(ValueError):
                s.add_video(recovered, metadata(), NOW)

    def test_duplicate_normalized_script_even_different_file(self):
        state = s.empty()
        s.add_video(state, metadata(), NOW)
        other = metadata(1)
        other['script'] = '  ' + metadata()['script'].upper() + '\n'
        with self.assertRaises(ValueError):
            s.add_video(state, other, NOW)

    def test_official_identity_and_review_required(self):
        for key in s.IDENTITY:
            with self.subTest(key=key), self.assertRaises(ValueError):
                s.add_video(s.empty(), dict(metadata(), **{key:'other'}), NOW)
        item = s.add_video(s.empty(), dict(metadata(), rights_reviewed=False), NOW)
        self.assertEqual(item['status'], 'REJECTED')

    def test_quality_and_persistent_media_required(self):
        for change in ({'storage_url':'/tmp/a.mp4'}, {'quality':{}}, {'sha256':'bad'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                s.add_video(s.empty(), dict(metadata(), **change), NOW)

    def test_slots_include_legacy_and_timezone(self):
        state = s.empty()
        for n in range(4):
            s.add_video(state, metadata(n), NOW)
        s.schedule(state, NOW, ['2026-10-28T10:00:00-03:00'])
        self.assertEqual([i['scheduled_at'] for i in state['items']], [
            '2026-10-28T21:00:00Z', '2026-10-29T13:00:00Z',
            '2026-10-29T21:00:00Z', '2026-10-30T13:00:00Z'])

    def test_two_cas_writers_one_wins(self):
        with tempfile.TemporaryDirectory() as folder:
            store = s.LocalStore(Path(folder)/'stock.json')
            a, rev_a = store.load()
            b, rev_b = store.load()
            s.add_video(a, metadata(), NOW)
            s.add_video(b, metadata(1), NOW)
            store.save(a, rev_a)
            with self.assertRaises(s.Conflict):
                store.save(b, rev_b)
            self.assertEqual(len(store.load()[0]['items']), 1)

    def test_durable_claim_precedes_external_mutation_and_blocks_second(self):
        state, item = self.stock()
        with tempfile.TemporaryDirectory() as folder:
            store = s.LocalStore(Path(folder)/'stock.json')
            store.save(state, None)
            claimed, rev, result = s.durable_claim(store, item['id'], NOW)
            self.assertEqual(store.load()[0]['items'][0]['status'], 'PUBLISHING')
            with self.assertRaises(ValueError):
                s.durable_claim(store, item['id'], NOW)
            s.recover_interrupted(claimed, NOW)
            store.save(claimed, rev)
            self.assertEqual(store.load()[0]['items'][0]['status'], 'UNKNOWN')
            with self.assertRaises(ValueError):
                s.durable_claim(store, item['id'], NOW)

    def test_failed_checkpoint_raises_before_claim_is_returned(self):
        state, item = self.stock()
        with tempfile.TemporaryDirectory() as folder:
            store = s.LocalStore(Path(folder)/'stock.json')
            store.save(state, None)
            with patch.object(store, 'save', side_effect=s.Conflict('concurrent')):
                with self.assertRaises(s.Conflict):
                    s.durable_claim(store, item['id'], NOW)
            self.assertEqual(store.load()[0]['items'][0]['status'], 'SCHEDULED')

    def test_confirmation_requires_ids_and_evidence(self):
        state, item = self.stock()
        s.claim(state, item['id'], NOW)
        with self.assertRaises(ValueError):
            s.resolve(state, item['id'], 'PUBLISHED', NOW)
        s.resolve(state, item['id'], 'SCHEDULED', NOW, remote_id='remote-test')
        with self.assertRaises(ValueError):
            s.claim(state, item['id'], NOW)
        with self.assertRaises(ValueError):
            s.resolve(state, item['id'], 'PUBLISHED', NOW, remote_id='different', publication_id='x', evidence='test')
        s.resolve(state, item['id'], 'PUBLISHED', NOW, publication_id='test-id', evidence='SIMULATED')
        self.assertEqual(item['publication_id'], 'test-id')
        with self.assertRaises(ValueError):
            s.add_video(state, metadata(), NOW)

    def test_unknown_and_failed_never_reset_attempt(self):
        for status in ('UNKNOWN', 'FAILED'):
            state, item = self.stock()
            s.claim(state, item['id'], NOW)
            s.resolve(state, item['id'], status, NOW)
            with self.assertRaises(ValueError):
                s.claim(state, item['id'], NOW)
            self.assertEqual(item['attempts'], 1)

    def test_missed_slots_reported_and_never_submitted_late(self):
        state, item = self.stock()
        later = datetime(2026, 10, 29, tzinfo=timezone.utc)
        self.assertEqual(s.stock_report(state, later)['missed_slots'], [item['id']])
        with self.assertRaises(ValueError):
            s.claim(state, item['id'], later)

    def test_cloud_store_serializes_expected_sha_and_refuses_missing_response(self):
        store = s.GitHubStore('unit-test-token')
        with patch.object(store, 'request', return_value={'content': {'sha': 'new'}}) as request:
            self.assertEqual(store.save(s.empty(), 'old'), 'new')
            payload = request.call_args.args[1]
            self.assertEqual(payload['sha'], 'old')
            self.assertEqual(payload['branch'], 'main')
        with patch.object(store, 'request', return_value={}):
            with self.assertRaises(RuntimeError):
                store.save(s.empty(), 'old')

    def test_import_preserves_safe_publication_metadata(self):
        values = dict(metadata(), caption='Organize a bancada.', commercial_content=False,
                      reviewed_at='2026-10-28T08:00:00-03:00', source_asset_id=42,
                      review={'publication_approved': True}, media_persisted=True,
                      secret_token='never persisted')
        item = s.add_video(s.empty(), values, NOW)
        self.assertEqual(item['caption'], values['caption'])
        self.assertEqual(item['reviewed_at'], '2026-10-28T11:00:00Z')
        self.assertFalse(item['commercial_content'])
        self.assertNotIn('secret_token', item)
        with self.assertRaises(ValueError):
            s.add_video(s.empty(), dict(values, commercial_content='false'), NOW)

    def test_low_stock_and_refill_target(self):
        state = s.empty()
        self.assertEqual(s.stock_report(state, NOW)['refill_needed'], 14)
        for n in range(14):
            s.add_video(state, metadata(n), NOW)
        self.assertFalse(s.stock_report(state, NOW)['low_stock'])
        self.assertEqual(s.stock_report(state, NOW)['refill_needed'], 0)


if __name__ == '__main__':
    unittest.main()
