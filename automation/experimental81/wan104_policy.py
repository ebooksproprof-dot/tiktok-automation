"""Exact-source gates for the new licensed profile and one off-slot owner test."""
import json
from pathlib import Path
import re

from experimental81.rights import require_clearance

PROFILE = Path(__file__).with_name('wan104_components.json')
SCOPE = 'owner_authorized_ai30_first_live_test_and_ongoing_automation'


def require_sources(clips):
    profile = json.loads(PROFILE.read_text())
    require_clearance(clips)
    if len(clips) != 3 or {c.get('slot') for c in clips} != {0, 1, 2}:
        raise ValueError('WAN104_THREE_DISTINCT_NATIVE_SOURCES_REQUIRED')
    if len({c.get('sha256') for c in clips}) != 3:
        raise ValueError('WAN104_SOURCE_DUPLICATION')
    for clip in clips:
        if (clip.get('model') != profile['model'] or clip.get('model_revision') != profile['model_revision']
                or clip.get('space') != profile['space'] or clip.get('space_revision') != profile['space_revision']
                or clip.get('reference_kind') != 'authored_text_only'
                or not re.fullmatch('[a-f0-9]{64}', clip.get('generation_evidence', {}).get('request_sha256', ''))
                or not clip.get('generation_evidence', {}).get('provider_job_id')
                or not clip.get('url', '').startswith('https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/ai30-drafts-')
                or clip['commercial_license_evidence']['model'].get('license_url') != profile['model_license_url']
                or clip['commercial_license_evidence']['model'].get('revision') != profile['model_revision']
                or clip.get('media', {}).get('sha256') != clip['sha256']
                or not 4.8 <= clip.get('media', {}).get('duration_seconds', 0) <= 5.3):
            raise ValueError('WAN104_PINNED_LICENSE_AND_GENERATION_PROOF_REQUIRED')
    return profile


def require_quality(quality):
    profile = require_sources(quality.get('licensed_sources') or [])
    if (quality.get('wan104_licensed_profile') is not True or quality.get('model') != profile['model']
            or quality.get('model_revision') != profile['model_revision']
            or quality.get('ai_generated_seconds') != 15 or abs(quality.get('duration', 0)-15) > .15
            or quality.get('voice') != 'kokoro-onnx-0.6.1-v1.0-int8-pf_dora-pt-br'
            or quality.get('technical_pass') is not True or quality.get('editorial_approved') is not True
            or quality.get('commercial_license_clearance') is not True
            or quality.get('freeze_intervals_over_1s') != 0
            or not re.fullmatch('[a-f0-9]{64}', quality.get('sha256', ''))):
        raise ValueError('WAN104_VALIDATED_OUTPUT_REQUIRED')
    reviews = quality.get('semantic_reviews') or []
    from semantic_review import MODEL, REVISION, assess_generated_organization
    sources = {c['sha256']: c for c in quality['licensed_sources']}
    if (len(reviews) != 3 or {r.get('source_sha256') for r in reviews} != {c['sha256'] for c in quality['licensed_sources']}
            or any(r.get('accepted') is not True or r.get('policy') != 'wan104_objects_v1'
                   or r.get('revision') != REVISION or r.get('model') != MODEL
                   or r.get('generated_slot') != sources[r['source_sha256']]['slot']
                   or not assess_generated_organization(r.get('generated_slot'), r.get('captions', [])) for r in reviews)):
        raise ValueError('WAN104_PER_SOURCE_CONTEXT_REVIEW_REQUIRED')
    return profile


def is_trial(post):
    return (post.get('owner_mission') == '10.4' and post.get('wan104_first_public_test') is True
            and post.get('approval_scope') == SCOPE and post.get('video_origin') == 'ai_only30'
            and post.get('quality', {}).get('wan104_public_trial') is True
            and re.fullmatch(r'casasem-\d{4}-\d{2}-\d{2}-wan104', post.get('id', '')) is not None)


def require_trial_available(post, queue, state):
    if not is_trial(post):
        raise ValueError('WAN104_EXPLICIT_FIRST_TEST_AUTHORIZATION_REQUIRED')
    require_quality(post.get('quality', {}))
    if any(p.get('id') != post['id'] and (is_trial(p) or str(p.get('id', '')).endswith('-wan104')) for p in queue.get('posts', [])):
        raise ValueError('WAN104_FIRST_TEST_ALREADY_RESERVED')
    if any(key.endswith('-wan104') for key in state.get('posts', {})):
        raise ValueError('WAN104_FIRST_TEST_ALREADY_ATTEMPTED_NO_REPEAT')
    if any(p.get('provider') == 'buffer' and p.get('status') not in
           ('PUBLISH_COMPLETE', 'SCHEDULED', 'SENDING', 'FAILED', 'CANCELLED_EDITORIAL') for p in state.get('posts', {}).values()):
        raise ValueError('UNCERTAIN_EXISTING_PUBLICATION_BLOCKS_EXTRA_TEST')
    return True
