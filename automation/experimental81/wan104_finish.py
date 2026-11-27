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
            and review.get('editorial_id') == clip.get('editorial_id')
            and assess_generated_organization(clip['slot'], review.get('captions', []), clip.get('editorial_id')) else None)


def compose(inventory, folder, proof=None, source_folder=None, lines=None, on_review=None, on_reject=None, previous=None):
    profile = require_sources(inventory['clips'])
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    clips, visuals, reviews = [], [], []
    reviewer = None
    for clip in sorted(inventory['clips'], key=lambda c: c['slot']):
        path = Path(source_folder)/('new-clip-'+str(clip['slot'])+'.mp4') if source_folder else download(clip, folder)
        if render.sha(path) != clip['sha256']:
            raise ValueError('WAN_SOURCE_BYTES_DO_NOT_MATCH')
        try:
            source_visual = fingerprint(path, clip['url'])
            check_sources([source_visual], list(previous or [])+[{'visual_sources': visuals}])
            motion(path)
            review = cached_review(clip, proof or {})
            if not review:
                reviewer = reviewer or Reviewer(os.getenv('SEMANTIC_MODEL_CACHE'))
                review = reviewer.review(path, {'provider': 'wan104_generated', 'provider_id': clip['sha256'][:12],
                    'model': profile['model'], 'sha256': clip['sha256'], 'generated_slot': clip['slot'],
                    'editorial_id': clip.get('editorial_id'),
                    'frame_mode': 'reviewed_portrait'}, folder/('review-'+str(clip['slot'])))
                review.update(policy='wan104_objects_v1', generated_slot=clip['slot'])
        except ValueError as exc:
            if on_reject and (str(exc) in ('PORTRAIT_VISUAL_CONTEXT_REJECTED', 'SOURCE_FROZEN_OR_UNDECODABLE') or str(exc).startswith('VISUAL_')):
                review_path = folder/('review-'+str(clip['slot']))/'review.json'
                rejected_review = json.loads(review_path.read_text()) if review_path.exists() else {}
                on_reject(clip, str(exc), rejected_review)
            raise
        if on_review:
            on_review(clip, review)
        reviews.append(review)
        source_visual.update(semantic_context={'captions':review['captions'], 'editorial_id':clip.get('editorial_id'),
                                                   'motion':'camera_or_object_motion_checked'})
        visuals.append(source_visual)
        clips.append({'path': str(path), 'sha256': clip['sha256'], 'kind': 'ai', 'model': clip['model'],
            'source_url': clip['url'], 'license_url': profile['model_license_url'],
            'generation_evidence': clip['generation_evidence']['request_sha256'], 'visual_review_passed': True})
    check_sources(visuals, [])
    from framing import full_frame_filter
    for clip in inventory['clips']:
        full_frame_filter(clip['media']['width'], clip['media']['height'])
    lines = lines or wan104.SCRIPT
    reviewer = None
    import gc
    gc.collect()
    narration = render.synthesize(folder/'speech', lines, target_seconds=30)
    from chatterbox_v3 import NAME
    if narration['engine'] != NAME:
        raise ValueError('CHATTERBOX_V3_REQUIRED')
    manifest = {'experimental_only': True, 'script': lines, 'clips': clips, 'narration': narration}
    output = render.compose(manifest, folder/'render', 'AI_ONLY', target_seconds=30)
    quality = {**validate(output['video_path'], policy=Policy(target_seconds=30)), **motion(output['video_path'])}
    quality.update(mission='14.0', voice_reference_sha256=narration['voice_reference_sha256'],
        audio_content_verified=False, full_frame_reviewed=False, captions_reviewed=False, wan104_licensed_profile=True, model=profile['model'], model_revision=profile['model_revision'],
        ai_generated_seconds=30, real_video_seconds=0, voice=narration['engine'],
        machine_checks_only=True, human_perceptual_review=False, editorial_approved=True,
        commercial_license_clearance=True, licensed_sources=inventory['clips'], semantic_reviews=reviews,
        visual_sources=visuals, visual_policy_version=1, visual_distinct=True,
        source_urls=[c['url'] for c in inventory['clips']], scene_reuse_policy='sequential_distinct_AI_clips_no_loop',
        required_public_credits=[], caption_style='measured-v51')
    from output_review import review as review_output
    quality.update(review_output(folder/'speech', lines, narration['timings'], 30))
    require_quality(quality)
    return output, quality


def register_production_output(producer_store, post):
    ledger, ledger_revision = producer_store.load()
    if not isinstance(ledger.get('outputs'), dict):
        raise ValueError('EXISTING_PRODUCTION_HISTORY_REQUIRED')
    existing = ledger['outputs'].get(post['id'])
    if existing and existing.get('sha256') != post['quality']['sha256']:
        raise ValueError('EXISTING_OUTPUT_MUST_NOT_BE_OVERWRITTEN')
    if not existing:
        require_quality(post.get('quality', {}))
        ledger['outputs'][post['id']] = {'post_id': post['id'], 'sha256': post['quality']['sha256'],
            'video_url': post['video_url'], 'status': 'QUEUED', 'origin': 'licensed_wan104',
            'scheduled_at': post['scheduled_at'], 'publicly_verified': False}
        producer_store.save(ledger, ledger_revision)


def complete_handoff(store, inventory, revision, post, producer_store):
    """Queue is already durable. Repair either later checkpoint without resubmission."""
    source_hashes = {c['sha256'] for c in post['quality']['licensed_sources']}
    if source_hashes != {c['sha256'] for c in inventory['clips']}:
        raise ValueError('WAN_RECOVERY_SOURCE_IDENTITY_MISMATCH')
    register_production_output(producer_store, post)
    receipt = {'post_id': post['id'], 'sha256': post['quality']['sha256'], 'video_url': post['video_url'],
        'status': 'QUEUED_UNDER_EXISTING_BUFFER_CONTROLS', 'publicly_verified': False,
        'scheduled_at': post['scheduled_at'], 'clips': inventory['clips']}
    if not any(o.get('post_id') == post['id'] for o in inventory.setdefault('outputs', [])):
        inventory['outputs'].append(receipt)
    for c in inventory.get('scene_bank', []):
        if c['sha256'] in source_hashes: c['consumed_by'] = post['id']
    inventory.pop('editorial_id', None)
    inventory.pop('script_lines', None)
    inventory.update(episode=inventory['episode']+1, clips=[], status='COLLECTING')
    store.save(inventory, revision)
    return receipt


def stage(trial=False):
    from autonomous_production import stock_status, choose_slot
    from release_media import publish
    from visual_library import history
    token = os.environ['GH_TOKEN']
    if not trial and not json.loads(wan104.PROFILE.read_text())['activated_after_public_trial']:
        return {'status': 'WAN104_NOT_ACTIVE_FIRST_PUBLIC_PROOF_PENDING', 'publicly_verified': False}
    store = GitHubStore(token, path=wan104.INVENTORY, validate=False)
    inventory, revision = store.load()
    queue_store = GitHubStore(token, path='automation/queue.json', validate=False)
    state_store = GitHubStore(token, path='automation/state.json', validate=False)
    producer_store = GitHubStore(token, path='automation/production_state.json', validate=False)
    queue, queue_revision = queue_store.load()
    state, _ = state_store.load()
    # Recover a queue write acknowledged before a later checkpoint failed.
    hashes = {c['sha256'] for c in inventory['clips']}
    for prior in queue['posts']:
        if hashes and hashes == {c.get('sha256') for c in prior.get('quality', {}).get('licensed_sources', [])}:
            complete_handoff(store, inventory, revision, prior, producer_store)
            return {'status': 'QUEUED_ALREADY_DO_NOT_REPEAT', 'post_id': prior['id'], 'publicly_verified': False}
    from editorial_topics import BY_ID
    if inventory.get('editorial_id'):
        tip = BY_ID[inventory['editorial_id']]
        choices = novel_scripts([('tip12-'+tip['id'], [], tip['script_lines'])], queue, state)
    else:
        choices = wan104.script_choices(inventory['episode'], queue, state)
    if not choices:
        return {'status': 'EDITORIAL_HOLD_PRESERVED_CLIPS', 'clips': len(inventory['clips']),
                'reason': 'LEGACY_TOPIC_REPEATED_REPLAN_ON_NEXT_COLLECTION', 'publicly_verified': False}
    concept, _, lines = choices[0]
    if len(inventory['clips']) != 6:
        return {'status': 'COLLECTING_NO_READY_AI_VIDEO', 'clips': len(inventory['clips']), 'publicly_verified': False}
    # The first public trial may have been staged by an earlier tested revision.
    # Import only its exact existing queue entry; never create a replacement.
    for receipt in inventory.get('outputs', []):
        old = next((p for p in queue['posts'] if p.get('id') == receipt['post_id']), None)
        if not old or old['quality']['sha256'] != receipt['sha256']:
            raise ValueError('DURABLE_WAN_OUTPUT_HISTORY_MISSING_OR_CHANGED')
        register_production_output(producer_store, old)
    # One overflow position gives completed AI priority without cancelling slots.
    demand = stock_status(queue, state, wan104.now())
    if not trial and demand['ready']+demand['held_uncertain'] >= demand['target_max']+1:
        return {'status': 'LICENSED_AI_OVERFLOW_RESERVED', 'clips': 3, 'publicly_verified': False}
    require_sources(inventory['clips'])
    proof_path = Path(__file__).with_name('wan104_source_reviews.json')
    proof = json.loads(proof_path.read_text()) if proof_path.exists() else {}
    proof.update(inventory.get('source_reviews', {}))
    folder = ROOT.parent/'tmp'/'wan104-finish'/str(inventory['episode'])
    def checkpoint_review(clip, review):
        nonlocal revision
        reviews = inventory.setdefault('source_reviews', {})
        if reviews.get(clip['sha256']) != review:
            reviews[clip['sha256']] = review
            revision = store.save(inventory, revision)
    def reject_source(clip, reason, review):
        nonlocal revision
        inventory.setdefault('rejected_clips', []).append(dict(clip, rejection_reason=reason,
            rejected_at=wan104.now().isoformat(), rejected_review=review))
        inventory['clips'] = [c for c in inventory['clips'] if c['sha256'] != clip['sha256']]
        for source in inventory.get('scene_bank', []):
            if source['sha256'] == clip['sha256']:
                if reason == 'PORTRAIT_VISUAL_CONTEXT_REJECTED':
                    source.setdefault('editorial_holds', []).append(clip.get('editorial_id'))
                else: source['consumed_by'] = 'REJECTED'
        inventory['status'] = 'REPLACING_REJECTED_SCENE'
        revision = store.save(inventory, revision)
    previous = history(queue, state)
    archive = ROOT/'visual_history.json'
    if archive.exists(): previous.append(json.loads(archive.read_text()))
    output, quality = compose(inventory, folder, proof, lines=lines,
                              on_review=checkpoint_review, on_reject=reject_source, previous=previous)
    check_sources(quality['visual_sources'], previous)
    current = wan104.now()
    if trial:
        when = (current+dt.timedelta(minutes=12)).astimezone(ZoneInfo('America/Sao_Paulo')).replace(microsecond=0)
        post_id = 'casasem-'+str(when.date())+'-wan104'
        quality['wan104_public_trial'] = True
    else:
        post_id, when = choose_slot(queue, state, current)
    post = {'id': post_id, 'concept': concept, 'video_origin': 'ai_only30', 'quality': quality,
        'title': ' '.join(lines)+' Cenas ilustrativas geradas por inteligência artificial. '
                 'Orientações ilustrativas; siga as instruções dos fabricantes. #CasaSemEsforco #OrganizacaoDaCasa #InteligenciaArtificial',
        'scheduled_at': when.isoformat(), 'approved': True, 'consented_at': current.isoformat(),
        'approval_scope': SCOPE, 'owner_mission': '10.4', 'wan104_first_public_test': trial,
        'first_test_outside_recurring_slots': trial, 'ai_disclosure_required': True,
        'publication_provider': 'buffer', 'media_storage': 'release', 'render_version': 3,
        'script_lines': lines, 'script_sha256': script_sha(lines),
        'publishing_status': 'VALIDATED_LICENSED_WAN_READY_FOR_EXISTING_BUFFER', 'video_url': ''}
    from editorial_policy import require as require_editorial
    post['editorial'] = require_editorial(post, queue, state)
    if trial: require_trial_available(post, queue, state)
    from mission14_policy import require_output
    require_output(quality)
    post['video_url'] = publish(output['video_path'], post_id, quality)
    queue['posts'].append(post)
    queue_store.save(queue, queue_revision)
    complete_handoff(store, inventory, revision, post, producer_store)
    return {'status': 'QUEUED_UNDER_EXISTING_BUFFER_CONTROLS', 'post_id': post_id,
            'sha256': quality['sha256'], 'scheduled_at': when.isoformat(), 'publicly_verified': False}


def verify_existing(post_id):
    """Recompose one approved historical input set; no queue/Release/Buffer write."""
    queue, _ = GitHubStore(os.environ['GH_TOKEN'], path='automation/queue.json', validate=False).load()
    post = next((p for p in queue['posts'] if p.get('id') == post_id), None)
    if not post or post.get('approved') is not True:
        raise ValueError('EXISTING_APPROVED_WAN_REQUIRED')
    quality = post.get('quality', {})
    require_quality(quality)
    proof = {r['source_sha256']: r for r in quality['semantic_reviews']}
    output, measured = compose({'clips':quality['licensed_sources']},
        ROOT.parent/'tmp'/'wan104-finish'/'assembly-verification', proof, lines=post['script_lines'])
    result = {'status':'EXISTING_WAN_RECOMPOSED_VALIDATED_NO_PUBLICATION', 'post_id':post_id,
              'quality':measured, 'video_path':output['video_path'],
              'new_gpu_calls':0, 'queue_mutated':False, 'publication_attempted':False}
    (ROOT.parent/'tmp'/'wan104-finish'/'assembly-verification'/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


def legacy_inventory_path():
    return 'automation/experimental81/auto_inventory.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial', action='store_true')
    parser.add_argument('--verify-existing', default='')
    parser.add_argument('--optional-ai', action='store_true', help='Ordinary producer may use existing licensed-stock fallback; never applies to public trial')
    args = parser.parse_args()
    allowed_workflow = (os.getenv('GITHUB_WORKFLOW') == 'CasaSemEsforco AI30 Free Collector'
                        or (args.optional_ai and not args.trial and os.getenv('GITHUB_WORKFLOW') == 'CasaSemEsforco Daily Video Creation'))
    if (os.getenv('GITHUB_ACTIONS') != 'true' or not allowed_workflow
            or os.getenv('GITHUB_REF_NAME') != 'main'):
        raise ValueError('AUTHORIZED_EXISTING_CLOUD_WORKFLOW_REQUIRED')
    if args.optional_ai and args.trial:
        raise ValueError('PUBLIC_TRIAL_MUST_NOT_BE_OPTIONAL')
    try:
        if args.verify_existing:
            if args.trial or args.optional_ai: raise ValueError('VERIFICATION_MUST_NOT_STAGE')
            return verify_existing(args.verify_existing)
        return stage(args.trial)
    except Exception as exc:
        from operational_errors import evidence
        diagnostic = evidence(exc, 'wan_assembly')
        print('WAN_ASSEMBLY_CAUSE='+json.dumps(diagnostic), flush=True)
        if not args.optional_ai:
            raise
        # The following conventional production is still mandatory. This is
        # not an AI success or a claim that any video was published.
        return {'status': 'AI_HELD_CONVENTIONAL_FALLBACK_REQUIRED', 'error_type': type(exc).__name__, 'cause': diagnostic, 'publicly_verified': False}


if __name__ == '__main__':
    try:
        result = main()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result['status'] == 'COLLECTING_NO_READY_AI_VIDEO' and '--optional-ai' not in sys.argv:
            raise SystemExit(2)
    except Exception as exc:
        print(json.dumps({'status': 'WAN104_ASSEMBLY_BLOCKED', 'error_type': type(exc).__name__,
                          'reason': str(exc) if isinstance(exc, ValueError) else 'SAFE_ERROR_BODY_OMITTED'}))
        raise SystemExit(2)
