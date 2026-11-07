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
import sys
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
SCRIPT = ['Armário sem espaço? Separe os itens por categoria.',
          'Guarde somente os tecidos que já estão bem secos.',
          'Deixe o que você usa sempre fácil de alcançar.']


def now():
    return dt.datetime.now(dt.timezone.utc)


def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'CasaSemEsforco/10.4'}), timeout=30) as response:
        return json.load(response)


def profile_check(profile, fetch=fetch_json):
    if (profile.get('additional_budget_brl') != 0 or profile.get('use_lora') is not False
            or profile.get('use_cbensimon_weights') is not False or profile.get('use_aoti_package') is not False
            or profile.get('model') != 'FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers'
            or profile.get('space') != 'KingNish/wan2-2-fast'
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


def reserve(inventory_store, budget_store, inventory, revision, spec, tier):
    digest = hf_probe.fingerprint(spec)
    if digest in inventory['requests']:
        raise ValueError('KNOWN_OR_UNCERTAIN_WAN_REQUEST_NO_RETRY')
    ledger, budget_revision = budget_store.load()
    updated = daily_budget.reserve(ledger, digest, now(), tier=tier, estimated_seconds=75)
    updated['claims'][-1].update(profile='wan104_licensed_fastwan5b', space=spec['space'])
    budget_store.save(updated, budget_revision)  # Includes old A14B claims; never reset or replace.
    inventory['requests'][digest] = {'status': 'INTENT_RECORDED_NO_RETRY', 'at': now().isoformat(), 'spec': spec}
    revision = inventory_store.save(inventory, revision)
    return digest, revision


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


def collect(trial=False, client_factory=None):
    profile = json.loads(PROFILE.read_text())
    if not trial and not profile['activated_after_public_trial']:
        raise ValueError('WAN_PUBLIC_TRIAL_NOT_CONFIRMED')
    inventory_store, budget_store = stores()
    inventory, revision = inventory_store.load()
    if inventory.get('version') != 1 or not isinstance(inventory.get('clips'), list):
        raise ValueError('WAN104_INVENTORY_REQUIRED')
    if any(r['status'] in ('INTENT_RECORDED_NO_RETRY', 'UNKNOWN_NO_RETRY') for r in inventory['requests'].values()):
        raise ValueError('UNCERTAIN_WAN_GENERATION_REQUIRES_RECONCILIATION')
    if len(inventory['clips']) >= 3:
        return {'status': 'READY_PRESERVED_NO_GPU_CALL', 'clips': len(inventory['clips'])}
    profile_check(profile)
    tier, token = legacy.free_hf_identity()
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
            digest, revision = reserve(inventory_store, budget_store, inventory, revision, spec, tier)
            entry = inventory['requests'][digest]
            try:
                values = [None]+[spec[key] for key in profile['order'][1:]]
                job = client.submit(*values, api_name='/generate_video')
                entry['provider_job_id'] = getattr(job, 'event_id', None)
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
                    'estimated_reserved_seconds': 75, 'tier': tier, 'paid_endpoint_used': False},
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
                entry.update(status='UNKNOWN_NO_RETRY', error_type=type(exc).__name__, reason=hf_probe.classify_error(exc))
                inventory['status'] = 'GENERATION_HELD'
                inventory_store.save(inventory, revision)
                raise RuntimeError('WAN_GENERATION_HELD_NO_BLIND_RETRY') from None
    return {'status': inventory['status'], 'clips': len(inventory['clips']), 'model': profile['model'], 'additional_cost_brl': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.dry_run:
        return {'status': 'OFFLINE_PROFILE_ONLY', 'new_gpu_calls': 0, 'published': False}
    if (os.getenv('GITHUB_ACTIONS') != 'true' or os.getenv('GITHUB_WORKFLOW') != 'CasaSemEsforco AI30 Free Collector'
            or os.getenv('GITHUB_REF_NAME') != 'main'):
        raise ValueError('AUTHORIZED_EXISTING_CLOUD_WORKFLOW_REQUIRED')
    return collect(args.trial)


if __name__ == '__main__':
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({'status': 'WAN104_BLOCKED', 'error_type': type(exc).__name__,
                          'reason': str(exc) if isinstance(exc, (ValueError, daily_budget.QuotaError)) else 'SAFE_ERROR_BODY_OMITTED'}))
        raise SystemExit(2)
