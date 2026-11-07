"""Licensed Wan 2.2 alternative in the existing collector, ledger and publisher.

Legacy A14B files stay untouched. Only this pinned, explicitly Apache-2.0 5B
profile can create new assets here. No paid endpoint, hardware request or retry.
"""
import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experimental81 import auto_collect as legacy, daily_budget, hf_probe
from video_stock import GitHubStore

PROFILE = Path(__file__).with_name('wan104_components.json')
INVENTORY = 'automation/experimental81/wan104_inventory.json'
LEDGER = 'automation/experimental81/ledger.json'
SCOPE = 'mission104_owner_authorized_first_licensed_wan_public_test'
NEGATIVE = 'text, watermark, logos, people, hands, distorted objects, flicker, frozen frames, impossible motion'
SCENES = [
    'Photorealistic kitchen pantry, three clear unlabelled glass storage jars on a clean wooden shelf. Gentle continuous camera slide reveals the organized shelf, realistic reflections and stable geometry. No people, no hands, no logos, no text. One calm uninterrupted shot.',
    'Photorealistic linen cupboard with neatly folded cotton towels on an open shelf, soft window light. Slow continuous camera push toward the towels, realistic fabric texture, stable objects and natural shadows. No people, no hands, no logos, no text. One uninterrupted shot.',
    'Photorealistic clean domestic kitchen, simple unbranded utensils hanging separately from a secure wall rail above an empty counter. A gentle continuous camera slide shows the easy access and organized space. Stable geometry and natural daylight. No people, no hands, no text, no logos.'
]
SCRIPT = ['Armário sem espaço? Separe os itens por categoria antes de organizar.',
          'Guarde somente os tecidos que já estão completamente secos e limpos.',
          'Deixe os utensílios de uso frequente bem visíveis e fáceis de alcançar.']
SCRIPT_BANKS = [
    [SCRIPT[0], 'Perde tempo procurando potes? Deixe os grupos visíveis na prateleira.',
     'Vai organizar a despensa? Reserve espaço para retirar os itens com segurança.',
     'Sua prateleira vive cheia? Organize uma categoria pequena antes de começar outra.',
     'Cada pote tem lugar? Mantenha os itens de uso frequente fáceis de pegar.',
     'Vai mexer no armário? Confira a estabilidade da prateleira antes de organizar.'],
    [SCRIPT[1], 'Guarde as toalhas sem apertar a pilha além do espaço disponível.',
     'Antes de guardar os panos, confira se precisam de lavagem ou reparo.',
     'Separe as toalhas por uso e deixe as mais usadas fáceis de retirar.',
     'Ajuste a dobra das peças ao espaço disponível, sem prender nas portas.',
     'Separe os tecidos limpos dos usados e termine uma pequena pilha por vez.'],
    [SCRIPT[2], 'Escolha um suporte firme para os utensílios e respeite a capacidade indicada.',
     'Organize os utensílios sem bloquear a área livre da bancada de trabalho.',
     'Agrupe os utensílios pelo uso e deixe espaço para retirar cada peça.',
     'Antes de guardar os utensílios, confira se estão limpos e completamente secos.',
     'Mantenha os utensílios de uso diário ao alcance sem formar uma pilha instável.']]


def script_variants(episode):
    if episode == 1:
        return [SCRIPT]
    rng = random.Random(104000+episode)
    return [[rng.choice(bank) for bank in SCRIPT_BANKS] for _ in range(36)]


def now():
    return dt.datetime.now(dt.timezone.utc)


def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'CasaSemEsforco/10.4'}), timeout=30) as response:
        return json.load(response)


def profile_check(profile, fetch=fetch_json):
    if (profile.get('additional_budget_brl') != 0 or profile.get('use_lora') is not False
            or profile.get('use_cbensimon_weights') is not False or profile.get('use_aoti_package') is not False
            or profile.get('model') != 'FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers'
            or profile.get('space') not in ('KingNish/wan2-2-fast', 'Upsampler/wan-2-2-5b-video')
            or profile.get('quota_estimate_per_clip_seconds') != (75 if profile.get('space') == 'KingNish/wan2-2-fast' else 60)
            or (profile.get('height'), profile.get('width'), profile.get('duration_seconds'), profile.get('steps')) != (832, 480, 5, 4)
            or profile.get('reference_kind') != 'authored_text_only'):
        raise ValueError('UNAPPROVED_WAN_PROFILE')
    for name, kind in [('model', 'models'), ('backbone', 'models'), ('voice', 'models'), ('space', 'spaces')]:
        data = fetch('https://huggingface.co/api/'+kind+'/'+profile[name])
        if data.get('sha') != profile[name+'_revision']:
            raise ValueError('PINNED_WAN_COMPONENT_CHANGED_'+name.upper())
        if name != 'space' and (data.get('cardData') or {}).get('license') != 'apache-2.0':
            raise ValueError('WAN_COMPONENT_LICENSE_NOT_CONFIRMED_'+name.upper())
        if name == 'space':
            runtime = data.get('runtime', {})
            if (runtime.get('stage') != 'RUNNING' or runtime.get('sha') != profile['space_revision']
                    or runtime.get('hardware', {}).get('current') != 'zero-a10g'):
                raise ValueError('PINNED_FREE_SPACE_NOT_RUNNING')
    return True


def require_public_activation(profile, queue, state):
    from experimental81.wan104_policy import is_trial, require_quality
    proof = profile.get('activation_proof') or {}
    post = next((p for p in queue.get('posts', []) if p.get('id') == proof.get('post_id')), None)
    entry = state.get('posts', {}).get(proof.get('post_id'), {})
    if not post or not is_trial(post):
        raise ValueError('VERIFIED_FIRST_WAN_PUBLICATION_REQUIRED')
    require_quality(post['quality'])
    if (entry.get('status') != 'PUBLISH_COMPLETE' or entry.get('publicly_verified') is not True
            or entry.get('public_visibility_evidence', {}).get('public_playback_verified') is not True
            or entry.get('sha256') != post['quality']['sha256'] or entry['sha256'] != proof.get('sha256')
            or entry.get('buffer_post_id') != proof.get('provider_id')
            or proof.get('public_url') not in entry.get('public_urls', [])):
        raise ValueError('VERIFIED_FIRST_WAN_PUBLICATION_REQUIRED')
    return True


def quota_wait(ledger, spec, tier):
    try:
        daily_budget.reserve(ledger, hf_probe.fingerprint(spec), now(), tier=tier,
                             estimated_seconds=60 if spec['space'] == 'Upsampler/wan-2-2-5b-video' else 75)
    except daily_budget.QuotaError as exc:
        if str(exc) != 'DAILY_QUOTA_ESTIMATE_EXCEEDED':
            raise
        return {'status': 'WAIT_FREE_QUOTA', 'new_gpu_calls': 0, 'publicly_verified': False,
                'not_before': (dt.datetime.fromisoformat(ledger['window_start'])+dt.timedelta(days=1)).isoformat()}
    return None


def stores():
    token = os.environ['GH_TOKEN']
    return (GitHubStore(token, path=INVENTORY, validate=False),
            GitHubStore(token, branch='feature/ai-video-hybrid-30s', path=LEDGER, validate=False))


def request_spec(profile, episode, slot):
    # The episode changes the actual seed and an explicitly described scene.
    # Source and final perceptual comparisons still reject similar results.
    surfaces = ['light oak', 'warm walnut', 'pale beech', 'white painted wood']
    prompt = SCENES[slot]+' Setting detail: '+surfaces[(episode-1) % len(surfaces)]+'.'
    return {'space': profile['space'], 'space_revision': profile['space_revision'],
            'model': profile['model'], 'model_revision': profile['model_revision'],
            'prompt': prompt, 'reference_kind': 'authored_text_only',
            'height': profile['height'], 'width': profile['width'],
            'duration_seconds': 5, 'negative_prompt': NEGATIVE, 'steps': 4,
            'guidance_scale': 0, 'seed': 104000+episode*101+slot,
            'randomize_seed': False}


def reserve(inventory_store, budget_store, inventory, revision, spec, tier, estimated_seconds=75):
    digest = hf_probe.fingerprint(spec)
    if digest in inventory['requests']:
        raise ValueError('KNOWN_OR_UNCERTAIN_WAN_REQUEST_NO_RETRY')
    ledger, budget_revision = budget_store.load()
    updated = daily_budget.reserve(ledger, digest, now(), tier=tier, estimated_seconds=estimated_seconds)
    updated['claims'][-1].update(profile='wan104_licensed_fastwan5b', space=spec['space'])
    budget_store.save(updated, budget_revision)  # Includes old A14B claims; never reset or replace.
    inventory['requests'][digest] = {'status': 'INTENT_RECORDED_NO_RETRY', 'at': now().isoformat(), 'spec': spec}
    revision = inventory_store.save(inventory, revision)
    return digest, revision


def provider_failure(exc):
    # gradio_client raises AppError only after a completed server response with
    # an explicit error. Timeout/transport errors provide no such evidence.
    from gradio_client.exceptions import AppError
    if isinstance(exc, AppError):
        return 'FAILED_PROVIDER_NO_OUTPUT', 'GRADIO_COMPLETED_WITH_SERVER_ERROR'
    return 'UNKNOWN_NO_RETRY', hf_probe.classify_error(exc)


def reconcile_initial_app_failure(inventory):
    """One evidenced migration of the first trial; never clear transport unknowns."""
    changed = False
    for digest, entry in inventory['requests'].items():
        if (digest == 'a2b7465b46cf7160c40b732012e532ca44ff05d710095d1afedc3b9c0661f9bc'
                and entry.get('status') == 'UNKNOWN_NO_RETRY' and entry.get('error_type') == 'AppError'
                and entry.get('reason') == 'REMOTE_OR_TRANSPORT_FAILURE' and not entry.get('media')
                and entry.get('spec', {}).get('space') == 'KingNish/wan2-2-fast'):
            entry['prior_classification'] = dict(status=entry['status'], reason=entry['reason'])
            entry.update(status='FAILED_PROVIDER_NO_OUTPUT', reason='GRADIO_COMPLETED_WITH_SERVER_ERROR',
                         reconciled_at=now().isoformat(), quota_claim_preserved=True,
                         evidence='Actions 42375392951 AppError; gradio_client emits it only for explicit server error response')
            changed = True
    return changed


def inspect_clip(path):
    from experimental81.wan_probe import inspect_clip as inspect
    from semantic_review import motion
    import subprocess
    info = inspect(path)
    if (info['width'], info['height']) != (480, 832):
        raise ValueError('WAN_PROFILE_SHAPE_MISMATCH')
    motion(path)
    check = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-xerror', '-i', str(path),
        '-vf', 'blackdetect=d=0.3:pix_th=0.10:pic_th=0.98', '-an', '-f', 'null', '-'],
        capture_output=True, text=True, timeout=60)
    if check.returncode or 'black_start:' in check.stderr:
        raise ValueError('WAN_SOURCE_BLACK_OR_INVALID')
    return info


def collect(trial=False, client_factory=None, reconcile_app_failure=False):
    profile = json.loads(PROFILE.read_text())
    if not trial and not profile['activated_after_public_trial']:
        raise ValueError('WAN_PUBLIC_TRIAL_NOT_CONFIRMED')
    inventory_store, budget_store = stores()
    if not trial:
        token = os.environ['GH_TOKEN']
        queue, _ = GitHubStore(token, path='automation/queue.json', validate=False).load()
        state, _ = GitHubStore(token, path='automation/state.json', validate=False).load()
        require_public_activation(profile, queue, state)
    inventory, revision = inventory_store.load()
    if inventory.get('version') != 1 or not isinstance(inventory.get('clips'), list):
        raise ValueError('WAN104_INVENTORY_REQUIRED')
    if reconcile_app_failure and reconcile_initial_app_failure(inventory):
        revision = inventory_store.save(inventory, revision)
    if any(r['status'] in ('INTENT_RECORDED_NO_RETRY', 'UNKNOWN_NO_RETRY') for r in inventory['requests'].values()):
        raise ValueError('UNCERTAIN_WAN_GENERATION_REQUIRES_RECONCILIATION')
    if len(inventory['clips']) >= 3:
        return {'status': 'READY_PRESERVED_NO_GPU_CALL', 'clips': len(inventory['clips'])}
    profile_check(profile)
    tier, token = legacy.free_hf_identity()
    ledger, _ = budget_store.load()
    waiting = quota_wait(ledger, request_spec(profile, inventory['episode'], len(inventory['clips'])), tier)
    if waiting:
        inventory['last_wait'] = dict(waiting, at=now().isoformat())
        inventory_store.save(inventory, revision)
        return waiting
    if client_factory is None:
        from gradio_client import Client
        client_factory = Client
    # Keep every returned file for the workflow's failure artifact as well as
    # the immutable Release. A failed upload must not delete a useful clip.
    with contextlib.nullcontext(ROOT.parent/'tmp'/'wan104') as folder:
        folder.mkdir(parents=True, exist_ok=True)
        client = client_factory(profile['space'], token=token or False, verbose=False,
            download_files=folder, httpx_kwargs={'timeout': 30})
        api = client.view_api(return_format='dict', print_info=False)
        if [x['parameter_name'] for x in api.get('named_endpoints', {}).get('/generate_video', {}).get('parameters', [])] != profile['order']:
            raise ValueError('PINNED_WAN_API_SCHEMA_CHANGED')
        for _ in range(profile['max_clips_per_run']):
            slot = len(inventory['clips'])
            if slot >= 3:
                break
            spec = request_spec(profile, inventory['episode'], slot)
            estimate = profile['quota_estimate_per_clip_seconds']
            digest, revision = reserve(inventory_store, budget_store, inventory, revision, spec, tier, estimate)
            entry = inventory['requests'][digest]
            try:
                values = [None]+[spec[key] for key in profile['order'][1:]]
                job = client.submit(*values, api_name='/generate_video')
                deadline = time.monotonic()+10
                while not getattr(getattr(job, 'communicator', None), 'event_id', None) and not job.done() and time.monotonic() < deadline:
                    time.sleep(.1)
                entry['provider_job_id'] = getattr(getattr(job, 'communicator', None), 'event_id', None)
                revision = inventory_store.save(inventory, revision)
                result = job.result(timeout=180)
                path = Path(hf_probe.video_path(result))
                media = inspect_clip(path)
                entry.update(status='GENERATED_AWAITING_STORAGE', media=media)
                revision = inventory_store.save(inventory, revision)
                url = legacy.upload_clip(path, media['sha256'], now())
                from visual_library import fingerprint
                visual = fingerprint(path, url)
                clip = {'slot': slot, 'episode': inventory['episode'], 'sha256': media['sha256'],
                    'url': url, 'media': media, 'model': profile['model'], 'model_revision': profile['model_revision'],
                    'space': profile['space'], 'space_revision': profile['space_revision'], 'prompt': spec['prompt'],
                    'reference_kind': 'authored_text_only', 'generation_evidence': {'request_sha256': digest,
                    'provider_job_id': entry['provider_job_id'], 'gpu_seconds_consumed': None,
                    'estimated_reserved_seconds': estimate, 'tier': tier, 'paid_endpoint_used': False},
                    'visual_source': visual, 'commercial_license_clearance': True,
                    'commercial_license_evidence': {'source_sha256': media['sha256'], 'reviewed_at': now().isoformat(),
                        'model': {'revision': profile['model_revision'], 'commercial_use': True, 'license_url': profile['model_license_url']},
                        'derivative': {'revision': profile['model_revision'], 'commercial_use': True, 'license_url': profile['model_license_url']},
                        'voice': {'revision': profile['voice_revision'], 'commercial_use': True, 'license_url': profile['voice_license_url']},
                        'reference': {'revision': digest, 'commercial_use': True, 'basis': 'original authored text; no third-party image',
                            'license_url': 'https://github.com/ebooksproprof-dot/tiktok-automation/blob/main/automation/WAN-10.4.md'}}}
                inventory['clips'].append(clip)
                entry.update(status='GENERATED_DURABLE_PENDING_VISUAL_REVIEW', sha256=media['sha256'], url=url)
                inventory['status'] = 'READY_FOR_REVIEW' if len(inventory['clips']) == 3 else 'COLLECTING'
                revision = inventory_store.save(inventory, revision)
            except Exception as exc:
                # A lost reply cannot grant permission to submit the same scene again.
                status, reason = provider_failure(exc)
                entry.update(status=status, error_type=type(exc).__name__, reason=reason)
                inventory['status'] = 'GENERATION_HELD'
                inventory_store.save(inventory, revision)
                raise RuntimeError('WAN_GENERATION_HELD_NO_BLIND_RETRY') from None
    return {'status': inventory['status'], 'clips': len(inventory['clips']), 'model': profile['model'], 'additional_cost_brl': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--reconcile-app-failure', action='store_true')
    args = parser.parse_args()
    if args.dry_run:
        return {'status': 'OFFLINE_PROFILE_ONLY', 'new_gpu_calls': 0, 'published': False}
    if (os.getenv('GITHUB_ACTIONS') != 'true' or os.getenv('GITHUB_WORKFLOW') != 'CasaSemEsforco AI30 Free Collector'
            or os.getenv('GITHUB_REF_NAME') != 'main'):
        raise ValueError('AUTHORIZED_EXISTING_CLOUD_WORKFLOW_REQUIRED')
    return collect(args.trial, reconcile_app_failure=args.reconcile_app_failure)


if __name__ == '__main__':
    try:
        result = main()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if os.getenv('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
                out.write('collection_status='+result['status']+'\n')
                out.write('ready='+str(result['status'] in ('READY_FOR_REVIEW', 'READY_PRESERVED_NO_GPU_CALL')).lower()+'\n')
    except Exception as exc:
        print(json.dumps({'status': 'WAN104_BLOCKED', 'error_type': type(exc).__name__,
                          'reason': str(exc) if isinstance(exc, (ValueError, daily_budget.QuotaError)) else 'SAFE_ERROR_BODY_OMITTED'}))
        raise SystemExit(2)
