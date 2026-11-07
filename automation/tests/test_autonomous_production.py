import datetime as dt
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import autonomous_production as production
import semantic_review as semantic
import source_license
import public_visibility
import confirm_near_due
import autonomous_stock


class PolicyTests(unittest.TestCase):
    def test_ironing_ski_lift_is_not_a_clothes_candidate(self):
        self.assertIsNone(semantic.nominate({'selection_reason': 'ironing lift, ski, tractor, winter sports'}))
        self.assertIsNone(semantic.nominate({'selection_reason': 'iron bridge, architecture'}))
        self.assertEqual(semantic.nominate({'selection_reason': 'books, shelves, library, closet'}), 'books')
        self.assertIsNone(semantic.nominate({'selection_reason': 'plate, pizza, meal, restaurant, tree'}))

    def test_api_evidence_binds_same_id_author_file_and_keeps_credentials_private(self):
        record = {'provider_id': '1', 'url': 'https://cdn.pixabay.com/video/a.mp4',
                  'source_page': 'https://pixabay.com/videos/id-1/', 'author': 'Author',
                  'sha256': 'a'*64, 'license_url': 'https://pixabay.com/service/license-summary/'}
        data = {'hits': [{'id': 1, 'pageURL': record['source_page'], 'user': 'Author',
                         'videos': {'large': {'url': record['url']}}}]}
        policy = {'terms_url': 'https://pixabay.com/service/terms/', 'terms_sha256': 'b'*64}
        with patch.object(source_license, 'API_CHECKS', 0):
            evidence = source_license.verify_api(record, 'not-a-real-secret',
                transport=lambda u: json.dumps(data).encode(), policy=policy)
            self.assertTrue(evidence['commercial_use'])
            self.assertNotIn('not-a-real-secret', json.dumps(evidence))
            data['hits'][0]['user'] = 'Different author'
            with self.assertRaisesRegex(ValueError, 'IDENTITY_AND_FILE'):
                source_license.verify_api(record, 'not-a-real-secret',
                    transport=lambda u: json.dumps(data).encode(), policy=policy)

    def test_refill_intent_is_durable_before_dispatch_and_never_repeated_after_timeout(self):
        class Memory:
            def __init__(self):
                self.value = {'outputs': {'post': {'sha256': 'a'*64}}}
            def load(self):
                import copy
                return copy.deepcopy(self.value), 'revision'
            def save(self, value, revision):
                import copy
                self.value = copy.deepcopy(value)
                return 'revision'
        store = Memory()
        state = {'posts': {'post': {'sha256': 'a'*64, 'status': 'PUBLISH_COMPLETE',
                 'publicly_verified': True, 'public_visibility_evidence': {'public_playback_verified': True}}}}
        now = dt.datetime.now(dt.timezone.utc)
        def sender():
            self.assertIn('post', store.value['refill_events'])
            raise TimeoutError()
        with self.assertRaises(TimeoutError):
            autonomous_stock.request_refill(store, state, now, sender)
        self.assertEqual(store.value['refill_events']['post']['status'], 'UNKNOWN_WORKFLOW_DISPATCH')
        self.assertEqual(autonomous_stock.newly_published(store.value, state), [])
        # A provider's sent flag without public playback never triggers refill.
        state['posts']['post']['public_visibility_evidence'] = {'public_playback_verified': False}
        self.assertEqual(autonomous_stock.newly_published({'outputs': {'post': {'sha256': 'a'*64}}}, state), [])
    def test_near_due_confirmation_never_waits_for_unsubmitted_or_regular_slots(self):
        now = dt.datetime(2026, 11, 7, 4, tzinfo=dt.timezone.utc)
        post = {'id': 'p', 'approval_scope': 'mission102_owner_authorized_automated_quality_and_license_checks',
                'first_test_outside_recurring_slots': True}
        self.assertIsNone(confirm_near_due.candidate({'posts': [post]}, {'posts': {}}, now))
        entry = {'provider': 'buffer', 'buffer_post_id': 'known', 'status': 'SCHEDULED',
                 'submitted_at': now.isoformat(), 'scheduled_at': (now+dt.timedelta(minutes=20)).isoformat()}
        self.assertEqual(confirm_near_due.candidate({'posts': [post]}, {'posts': {'p': entry}}, now)[0], 'p')
        entry['status'] = 'SUBMISSION_UNKNOWN'
        self.assertIsNone(confirm_near_due.candidate({'posts': [post]}, {'posts': {'p': entry}}, now))
    def test_provider_sent_without_public_playback_stays_unverified_and_reserved(self):
        entry = dict(status='PUBLISH_COMPLETE', publicly_verified=True, buffer_post_id='existing-id',
                     public_urls=['https://www.tiktok.com/@.casasemesforo/video/123'],
                     publicly_available_post_id=['123'], verification_source='Buffer sent')
        public_visibility.require(entry, verifier=lambda p: {'public_playback_verified': False})
        self.assertFalse(entry['publicly_verified'])
        self.assertEqual(entry['status'], 'AWAITING_PUBLIC_VERIFICATION')
        self.assertEqual(entry['buffer_post_id'], 'existing-id')
        self.assertNotIn('publicly_available_post_id', entry)

    def test_real_public_playback_is_a_distinct_required_evidence(self):
        entry = dict(status='PUBLISH_COMPLETE', publicly_verified=True, verification_source='Buffer sent')
        public_visibility.require(entry, verifier=lambda p: {'public_playback_verified': True})
        self.assertTrue(entry['publicly_verified'])
        self.assertIn('public_visibility_evidence', entry)
    def test_stream_bed_and_botanical_broom_never_become_housekeeping(self):
        for text in ('mountain stream bed river watercourse', 'broom rain blossoms',
                     'ai generated clothes laundry', 'woman portrait cigarette'):
            self.assertIsNone(semantic.nominate({'selection_reason': text}))

    def test_tags_alone_cannot_approve_a_source(self):
        self.assertFalse(semantic.assess('clothes', ['A lake and mountain.']*3))
        self.assertFalse(semantic.assess('sweeping', ['Pink flowers in sunlight.']*3))
        self.assertFalse(semantic.assess('dishes', ['A person holding a phone.']*3))

    def test_unsafe_sample_overrides_two_positive_samples(self):
        self.assertFalse(semantic.assess('clothes', ['An iron over a shirt.',
            'Clothes on a rack.', 'A gun beside clothing.']))
        self.assertTrue(semantic.assess('clothes', ['An iron over a shirt.',
            'Clothes on a rack.', 'A folded shirt.']))

    def test_unknown_reservations_and_two_identical_timestamps_still_consume_daily_cap(self):
        now = dt.datetime(2026, 11, 7, 8, tzinfo=dt.timezone.utc)
        state = {'posts': {str(i): {'scheduled_at': '2026-11-07T10:00:00-03:00',
                                    'status': 'SUBMISSION_UNKNOWN'} for i in (1, 2)}}
        _, chosen = production.choose_slot({'posts': []}, state, now)
        self.assertEqual(chosen.date(), dt.date(2026, 11, 8))
        self.assertEqual(chosen.hour, 10)

    def test_a_scheduled_video_counts_as_stock_until_actual_publication(self):
        now = dt.datetime(2026, 11, 7, 8, tzinfo=dt.timezone.utc)
        post = {'id': 'p', 'approved': True, 'consented_at': now.isoformat(),
                'scheduled_at': (now+dt.timedelta(hours=1)).isoformat(),
                'quality': {'technical_pass': True}}
        state = {'posts': {'p': {'status': 'SCHEDULED'}}}
        self.assertEqual(len(production.ready({'posts': [post]}, state, now)), 1)
        state['posts']['p']['status'] = 'PUBLISH_COMPLETE'
        self.assertEqual(production.ready({'posts': [post]}, state, now), [])

    def test_license_must_bind_exact_file_author_and_commercial_terms(self):
        record = {'provider': 'pixabay', 'url': 'https://cdn.pixabay.com/video/a.mp4',
                  'source_page': 'https://pixabay.com/videos/id-1/', 'author': 'Creator',
                  'license_url': 'https://pixabay.com/service/license-summary/', 'sha256': 'a'*64}
        def page(author='Creator', url=record['url']):
            return ('<script type="application/ld+json">'+json.dumps({
                '@type': 'VideoObject', 'contentUrl': url, 'license': record['license_url'],
                'author': {'name': author}})+'</script>').encode()
        terms = b'royalty-free use for commercial or non-commercial purposes'
        def fetch(url):
            return terms if url.endswith('/terms/') else page()
        proof = source_license.verify(record, fetch)
        self.assertEqual(proof['source_sha256'], record['sha256'])
        for invalid in (page('Other author'), page(url='https://cdn.pixabay.com/video/b.mp4')):
            with self.assertRaisesRegex(ValueError, 'DOES_NOT_CONFIRM'):
                source_license.verify(record, lambda url: terms if url.endswith('/terms/') else invalid)
        with self.assertRaisesRegex(ValueError, 'COMMERCIAL_LICENSE'):
            source_license.verify(record, lambda url: b'Non-commercial use only' if url.endswith('/terms/') else page())

    @unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg integration requires installed validator')
    def test_real_freeze_detector_rejects_still_and_accepts_motion(self):
        with tempfile.TemporaryDirectory() as folder:
            for name, source, accepted in (('still', 'color=c=blue:s=96x160:r=15', False),
                                           ('motion', 'testsrc2=s=96x160:r=15', True)):
                path = Path(folder)/(name+'.mp4')
                subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', source,
                                '-t', '2', '-c:v', 'libx264', '-threads', '1', '-y', str(path)], check=True)
                if accepted:
                    self.assertEqual(semantic.motion(path)['freeze_intervals_over_1s'], 0)
                else:
                    with self.assertRaisesRegex(ValueError, 'FROZEN'):
                        semantic.motion(path)

    def test_primary_voice_is_pf_dora_and_media_error_does_not_switch_voice(self):
        engine = Mock(name='kokoro')
        engine.name = 'kokoro-pf_dora'
        with patch('narration.load_engine', return_value=engine) as load, \
             patch.object(production.render, 'render', side_effect=RuntimeError('media download failed')):
            with self.assertRaisesRegex(RuntimeError, 'media download'):
                production.render_with_voice_fallback(('idea', [], []), 'post')
            self.assertEqual(load.call_count, 1)
            self.assertEqual(load.call_args.args[1], 'kokoro-female')

    def test_real_primary_synthesis_failure_restarts_whole_narration_with_piper(self):
        primary, fallback = Mock(), Mock()
        primary.name, fallback.name = 'kokoro-pf_dora', 'piper-faber'
        primary.speak.side_effect = RuntimeError('CPU runtime failed')
        def render(idea, voice, post_id):
            voice.speak('Uma frase.', 'unused.wav')
            return 'video.mp4', {'voice': voice.name}
        with patch('narration.load_engine', side_effect=[primary, fallback]) as load, \
             patch.object(production.render, 'render', side_effect=render) as renderer:
            _, quality = production.render_with_voice_fallback(('idea', [], []), 'post')
            self.assertEqual(quality['voice'], 'piper-faber')
            self.assertIn('PRIMARY_SYNTHESIS', quality['voice_fallback_reason'])
            self.assertEqual(renderer.call_count, 2)
            self.assertEqual(load.call_args.args[1], 'piper')


if __name__ == '__main__':
    unittest.main()
