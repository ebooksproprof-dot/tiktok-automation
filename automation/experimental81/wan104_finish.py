"""Review/render licensed Wan clips and hand off to the existing Buffer queue.

No Buffer API here. Queue CAS and deterministic episode identity recover an
interrupted handoff. Sources and their model provenance remain immutable.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experimental81 import wan104, render
from experimental81.wan104_policy import require_sources, require_quality, require_trial_available, SCOPE
from semantic_review import Reviewer, REVISION, assess_generated_organization, motion
from experimental81.quality import validate, Policy
from visual_library import fingerprint, check_sources
from content_catalog import fingerprint as script_sha, novel_scripts
from video_stock import GitHubStore


def download(clip, folder):
    path = Path(folder)/('wan104-'+clip['sha256']+'.mp4')
    if not path.exists():
        if not clip['url'].startswith('https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/ai30-drafts-'):
            raise ValueError('WAN_SOURCE_HOST_NOT_TRUSTED')
        with urllib.request.urlopen(clip['url'], timeout=60) as response:
            body = response.read(20_000_001)
        if len(body) > 20_000_000 or hashlib.sha256(body).hexdigest() != clip['sha256']:
            raise ValueError('WAN_SOURCE_BYTES_DO_NOT_MATCH')
        path.write_bytes(body)
    if render.sha(path) != clip['sha256']:
        raise ValueError('WAN_SOURCE_BYTES_DO_NOT_MATCH')
    return path


def cached_review(clip, proof):
    review = proof.get(clip['sha256'], {})
    return (review if review.get('accepted') is True and review.get('source_sha256') == clip['sha256']
            and review.get('revision') == REVISION and review.get('policy') == 'wan104_objects_v1'
            and review.get('generated_slot') == clip['slot']
            and assess_generated_organization(clip['slot'], review.get('captions', [])) else None)


def compose(inventory, folder, proof=None, source_folder=None):
    profile = require_sources(inventory['clips'])
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    clips, visuals, reviews = [], [], []
    reviewer = None
    for clip in sorted(inventory['clips'], key=lambda c: c['slot']):
        path = Path(source_folder)/('new-clip-'+str(clip['slot'])+'.mp4') if source_folder else download(clip, folder)
        if render.sha(path) != clip['sha256']:
            raise ValueError('WAN_SOURCE_BYTES_DO_NOT_MATCH')
        motion(path)
        review = cached_review(clip, proof or {})
        if not review:
            reviewer = reviewer or Reviewer(os.getenv('SEMANTIC_MODEL_CACHE'))
            review = reviewer.review(path, {'provider': 'wan104_generated', 'provider_id': clip['sha256'][:12],
                'model': profile['model'], 'sha256': clip['sha256'], 'generated_slot': clip['slot'],
                'frame_mode': 'reviewed_portrait'}, folder/('review-'+str(clip['slot'])))
            review.update(policy='wan104_objects_v1', generated_slot=clip['slot'])
        reviews.append(review)
        visuals.append(fingerprint(path, clip['url']))
        clips.append({'path': str(path), 'sha256': clip['sha256'], 'kind': 'ai', 'model': clip['model'],
            'source_url': clip['url'], 'license_url': profile['model_license_url'],
            'generation_evidence': clip['generation_evidence']['request_sha256'], 'visual_review_passed': True})
    check_sources(visuals, [])
    lines = wan104.SCRIPT
    narration = render.synthesize(folder/'speech', lines, target_seconds=15)
    if narration['engine'] != 'kokoro-onnx-0.6.1-v1.0-int8-pf_dora-pt-br':
        raise ValueError('REQUESTED_PF_DORA_REQUIRED')
    manifest = {'experimental_only': True, 'script': lines, 'clips': clips, 'narration': narration}
    output = render.compose(manifest, folder/'render', 'AI_ONLY', target_seconds=15)
    quality = {**validate(output['video_path'], policy=Policy(target_seconds=15)), **motion(output['video_path'])}
    quality.update(wan104_licensed_profile=True, model=profile['model'], model_revision=profile['model_revision'],
        ai_generated_seconds=15, real_video_seconds=0, voice=narration['engine'],
        machine_checks_only=True, human_perceptual_review=False, editorial_approved=True,
        commercial_license_clearance=True, licensed_sources=inventory['clips'], semantic_reviews=reviews,
        visual_sources=visuals, visual_policy_version=1, visual_distinct=True,
        source_urls=[c['url'] for c in inventory['clips']], scene_reuse_policy='sequential_distinct_AI_clips_no_loop',
        required_public_credits=[], caption_style='measured-v51')
    require_quality(quality)
    return output, quality


def stage(trial=False):
    from autonomous_production import stock_status, choose_slot
    from release_media import publish
    from visual_library import history
    token = os.environ['GH_TOKEN']
    store = GitHubStore(token, path=wan104.INVENTORY, validate=False)
    inventory, revision = store.load()
    queue_store = GitHubStore(token, path='automation/queue.json', validate=False)
    state_store = GitHubStore(token, path='automation/state.json', validate=False)
    queue, queue_revision = queue_store.load()
    state, _ = state_store.load()
    concept = 'licensed-wan104-episode-'+str(inventory['episode'])
    existing = next((p for p in queue['posts'] if p.get('concept') == concept), None)
    if existing:
        return {'status': 'QUEUED_ALREADY_DO_NOT_REPEAT', 'post_id': existing['id'], 'publicly_verified': False}
    if len(inventory.get('clips', [])) != 3:
        return {'status': 'COLLECTING_NO_READY_AI_VIDEO', 'clips': len(inventory.get('clips', [])), 'publicly_verified': False}
    if not trial and not stock_status(queue, state, wan104.now())['refill_needed']:
        return {'status': 'LICENSED_AI_READY_HELD_STOCK_FULL', 'clips': 3, 'publicly_verified': False}
    require_sources(inventory['clips'])
    proof_path = Path(__file__).with_name('wan104_source_reviews.json')
    proof = json.loads(proof_path.read_text()) if proof_path.exists() else {}
    folder = ROOT.parent/'tmp'/'wan104-finish'/str(inventory['episode'])
    output, quality = compose(inventory, folder, proof)
    previous = history(queue, state)
    archive = ROOT/'visual_history.json'
    if archive.exists(): previous.append(json.loads(archive.read_text()))
    legacy, _ = GitHubStore(token, branch='feature/ai-video-hybrid-30s', path=legacy_inventory_path(), validate=False).load()
    previous.append({'visual_sources': [c['visual_source'] for c in legacy.get('clips', [])]})
    check_sources(quality['visual_sources'], previous)
    if not novel_scripts([(concept, [], wan104.SCRIPT)], queue, state):
        raise ValueError('WAN_SCRIPT_REPEATS_EXISTING_CONTENT')
    current = wan104.now()
    if trial:
        when = (current+dt.timedelta(minutes=12)).astimezone(ZoneInfo('America/Sao_Paulo')).replace(microsecond=0)
        post_id = 'casasem-'+str(when.date())+'-wan104'
        quality['wan104_public_trial'] = True
    else:
        post_id, when = choose_slot(queue, state, current)
    post = {'id': post_id, 'concept': concept, 'video_origin': 'ai_only30', 'quality': quality,
        'title': ' '.join(wan104.SCRIPT)+' Cenas geradas por IA: Wan 2.2, variante FastWan 5B. '
                 'Orientações ilustrativas; siga as instruções dos fabricantes. #CasaSemEsforco #OrganizacaoDaCasa #InteligenciaArtificial',
        'scheduled_at': when.isoformat(), 'approved': True, 'consented_at': current.isoformat(),
        'approval_scope': SCOPE, 'owner_mission': '10.4', 'wan104_first_public_test': trial,
        'first_test_outside_recurring_slots': trial, 'ai_disclosure_required': True,
        'publication_provider': 'buffer', 'media_storage': 'release', 'render_version': 3,
        'script_lines': wan104.SCRIPT, 'script_sha256': script_sha(wan104.SCRIPT),
        'publishing_status': 'VALIDATED_LICENSED_WAN_READY_FOR_EXISTING_BUFFER', 'video_url': ''}
    if trial: require_trial_available(post, queue, state)
    post['video_url'] = publish(output['video_path'], post_id, quality)
    queue['posts'].append(post)
    queue_store.save(queue, queue_revision)
    inventory.setdefault('outputs', []).append({'post_id': post_id, 'sha256': quality['sha256'],
        'video_url': post['video_url'], 'status': 'QUEUED_UNDER_EXISTING_BUFFER_CONTROLS',
        'publicly_verified': False, 'scheduled_at': when.isoformat(), 'clips': inventory['clips']})
    inventory.update(episode=inventory['episode']+1, clips=[], status='COLLECTING')
    store.save(inventory, revision)
    return {'status': 'QUEUED_UNDER_EXISTING_BUFFER_CONTROLS', 'post_id': post_id,
            'sha256': quality['sha256'], 'scheduled_at': when.isoformat(), 'publicly_verified': False}


def legacy_inventory_path():
    return 'automation/experimental81/auto_inventory.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial', action='store_true')
    args = parser.parse_args()
    if (os.getenv('GITHUB_ACTIONS') != 'true' or os.getenv('GITHUB_WORKFLOW') != 'CasaSemEsforco AI30 Free Collector'
            or os.getenv('GITHUB_REF_NAME') != 'main'):
        raise ValueError('AUTHORIZED_EXISTING_CLOUD_WORKFLOW_REQUIRED')
    return stage(args.trial)


if __name__ == '__main__':
    try:
        result = main()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result['status'] == 'COLLECTING_NO_READY_AI_VIDEO':
            raise SystemExit(2)
    except Exception as exc:
        print(json.dumps({'status': 'WAN104_ASSEMBLY_BLOCKED', 'error_type': type(exc).__name__,
                          'reason': str(exc) if isinstance(exc, ValueError) else 'SAFE_ERROR_BODY_OMITTED'}))
        raise SystemExit(2)
