import copy
import datetime as dt
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import wan104_policy as policy
from semantic_review import MODEL, REVISION, assess_generated_organization
import buffer_runner as buffer
from daily_coverage import confirmed_live_tests


def quality_fixture():
    p = json.loads(policy.PROFILE.read_text())
    clips, reviews, visuals = [], [], []
    for slot, letter in enumerate('abc'):
        sha = letter*64
        evidence = {'source_sha256': sha, 'reviewed_at': '2026-11-07T00:00:00Z'}
        for component in ('model', 'derivative', 'reference', 'voice'):
            evidence[component] = {'revision': p['model_revision'], 'commercial_use': True, 'license_url': p['model_license_url']}
        url = 'https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/ai30-drafts-2026-W45/ai30-'+letter+'.mp4'
        clips.append({'slot': slot, 'sha256': sha, 'url': url, 'model': p['model'], 'model_revision': p['model_revision'],
            'space': p['space'], 'space_revision': p['space_revision'], 'reference_kind': 'authored_text_only',
            'generation_evidence': {'request_sha256': str(slot+1)*64, 'provider_job_id': 'real-id-'+str(slot)},
            'media': {'sha256': sha, 'duration_seconds': 5.041667}, 'commercial_license_clearance': True,
            'commercial_license_evidence': evidence})
        captions = [['glass jars on shelves']*3, ['folded towels']*3, ['kitchen utensils']*3][slot]
        reviews.append({'source_sha256': sha, 'accepted': True, 'policy': 'wan104_objects_v1',
                        'generated_slot': slot, 'model': MODEL, 'revision': REVISION, 'captions': captions})
        visuals.append({'source_id': url, 'sha256': sha, 'dhash': ['f'*16]*5})
    return {'wan104_licensed_profile': True, 'wan104_public_trial': True,
        'model': p['model'], 'model_revision': p['model_revision'], 'ai_generated_seconds': 15, 'duration': 15,
        'voice': 'kokoro-onnx-0.6.1-v1.0-int8-pf_dora-pt-br', 'technical_pass': True, 'editorial_approved': True,
        'commercial_license_clearance': True, 'freeze_intervals_over_1s': 0, 'sha256': 'd'*64,
        'licensed_sources': clips, 'semantic_reviews': reviews, 'visual_sources': visuals,
        'machine_checks_only': True}


def post_fixture():
    return {'id': 'casasem-2026-11-07-wan104', 'owner_mission': '10.4', 'wan104_first_public_test': True,
        'approval_scope': policy.SCOPE, 'video_origin': 'ai_only30', 'quality': quality_fixture(),
        'publication_provider': 'buffer', 'approved': True, 'consented_at': '2026-11-07T00:00:00Z',
        'scheduled_at': '2026-11-07T11:00:00-03:00', 'ai_disclosure_required': True,
        'video_url': 'https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-2026-11/trial.mp4',
        'title': 'Cenas geradas por IA. Organização ilustrativa, sem alegações sobre produtos.'}


class WanPublishingPolicyTests(unittest.TestCase):
    def test_only_exact_new_model_sources_and_bound_context_receipts_pass(self):
        valid = quality_fixture()
        policy.require_quality(valid)
        for mutation in ('old_model', 'false_rights', 'wrong_media_hash', 'wrong_context', 'wrong_review_model'):
            quality = copy.deepcopy(valid)
            if mutation == 'old_model': quality['licensed_sources'][0]['model'] = 'Wan-AI/Wan2.2-I2V-A14B-Diffusers'
            elif mutation == 'false_rights': quality['licensed_sources'][0]['commercial_license_clearance'] = False
            elif mutation == 'wrong_media_hash': quality['licensed_sources'][0]['media']['sha256'] = 'e'*64
            elif mutation == 'wrong_context': quality['semantic_reviews'][1]['captions'] = ['a mountain']*3
            else: quality['semantic_reviews'][1]['revision'] = 'unreviewed-model'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): policy.require_quality(quality)

    def test_safe_towel_contact_is_not_confused_with_harm_or_wrong_scene(self):
        self.assertTrue(assess_generated_organization(1, ['A hand places a folded towel on a shelf.', 'White towels.', 'Folded towels.']))
        self.assertFalse(assess_generated_organization(1, ['a river', 'towels', 'towels']))
        self.assertFalse(assess_generated_organization(1, ['kitchen utensils']*3))

    def test_only_one_explicit_trial_and_no_unknown_existing_submission(self):
        post = post_fixture()
        self.assertTrue(policy.require_trial_available(post, {'posts': [post]}, {'posts': {}}))
        for state in ({'posts': {'old-wan104': {'status': 'PUBLISH_COMPLETE'}}},
                      {'posts': {'other': {'provider': 'buffer', 'status': 'UNKNOWN'}}}):
            with self.assertRaises(ValueError): policy.require_trial_available(post, {'posts': [post]}, state)

    def test_extra_trial_preserves_regular_occupied_slots_and_ai_label(self):
        post = post_fixture()
        state = {'posts': {'morning': {'provider': 'buffer', 'status': 'PUBLISH_COMPLETE', 'scheduled_at': '2026-11-07T10:00:00-03:00'},
                           'evening': {'provider': 'buffer', 'status': 'SCHEDULED', 'scheduled_at': '2026-11-07T18:00:00-03:00'}}}
        date = dt.datetime(2026, 11, 7, 13, 30, tzinfo=dt.timezone.utc)
        with patch.object(buffer.common, 'utc_now', return_value=date), patch.object(buffer.common, 'load_json', return_value={'posts': [post]}), patch.object(buffer, 'require_evidence'):
            result = buffer.prepare(post, state, 'channel')
            self.assertTrue(result['metadata']['tiktok']['isAiGenerated'])
            unauthorized = copy.deepcopy(post); unauthorized['wan104_first_public_test'] = False
            with self.assertRaisesRegex(ValueError, 'Daily maximum'): buffer.prepare(unauthorized, state, 'channel')

    def test_trial_slot_collision_is_still_blocked(self):
        post = post_fixture()
        state = {'posts': {'occupied': {'provider': 'buffer', 'status': 'SCHEDULED', 'scheduled_at': post['scheduled_at']}}}
        date = dt.datetime(2026, 11, 7, 13, 30, tzinfo=dt.timezone.utc)
        with patch.object(buffer.common, 'utc_now', return_value=date), patch.object(buffer.common, 'load_json', return_value={'posts': [post]}), patch.object(buffer, 'require_evidence'), self.assertRaisesRegex(ValueError, 'slot already reserved'):
            buffer.prepare(post, state, 'channel')

    def test_no_exemption_for_scheduled_or_unverified_trial(self):
        post = post_fixture()
        entry = {'provider': 'buffer', 'status': 'SCHEDULED', 'sha256': post['quality']['sha256'],
                 'buffer_post_id': 'existing-id', 'publicly_verified': False}
        day = dt.date(2026, 11, 7)
        self.assertFalse(confirmed_live_tests({'posts': [post]}, {'posts': {post['id']: entry}}, day))
        entry.update(status='PUBLISH_COMPLETE', publicly_verified=True, public_urls=['https://www.tiktok.com/verified'],
                     public_visibility_evidence={'public_playback_verified': True})
        self.assertEqual(confirmed_live_tests({'posts': [post]}, {'posts': {post['id']: entry}}, day), {post['id']})


if __name__ == '__main__': unittest.main()
