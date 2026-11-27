"""One explicit higher-definition Wan trial, sharing the existing durable quota.

No publishing, no paid hardware, no blind retry. Legacy clips remain intact.
"""
import json
import datetime as dt
import os
from pathlib import Path
import time
from experimental81 import wan104 as wan, auto_collect, hf_probe
from video_stock import GitHubStore

INVENTORY='automation/experimental81/wan16_inventory.json'
EPISODE='mission16-copos-secos-photoreal-v1'
PROMPTS=[
    'Professional photorealistic home kitchen close-up, a single clean transparent drinking tumbler standing upright on a real wooden countertop, a few tiny water droplets on its inner wall and base, soft daylight, detailed glass refraction. Slow continuous lateral camera slide, stable glass shape and base in contact with the counter. No people, no hands, no appearing or disappearing objects. No text or logos. One uninterrupted five-second shot.',
    'Professional photorealistic home kitchen close-up, three clean clear drinking tumblers inverted on the flat supported wire grid of a stainless steel dish drying rack, each glass separated by ample space, realistic glass and metal textures, stable geometry and natural daylight. Slow continuous lateral camera slide. No people, hands, wine glasses, stacking, floating objects, text or logos. One uninterrupted five-second shot.',
    'Photorealistic macro film of the inside bottom of one clear drinking tumbler, several clearly visible small water beads on the glass base, dry wooden kitchen worktop around the glass. Gentle continuous camera move, realistic transparent refraction, glass stays resting flat on the worktop. No water magically appearing, no people, hands, text or logos. Five seconds.',
    'Photorealistic close low-angle film of one upside-down clear drinking tumbler drying on a flat horizontal metal dish rack. Its open mouth rests flat on the supported grid; its closed circular bottom faces upward. Natural domestic window light, stable support and stable glass geometry, slow camera movement only. No hands, leaning glasses, floating objects, text or logos. Five seconds.',
    'Photorealistic overhead film of two upside-down clear drinking tumblers standing securely on a flat horizontal dish drying grid, widely separated with empty space between them. Both open circular mouths rest on the grid and both closed bottoms face up. Clear domestic kitchen materials and stable supports. Slow camera move, no object motion, no people, no hands, no text. Five seconds.',
    'Photorealistic close-up film of the smooth unbroken rim of a clear drinking tumbler standing on a kitchen table. Gentle continuous camera arc shows the complete rim and natural glass reflections for a careful inspection. Stable circular rim, realistic surface detail, no sharp edges, cracks, hands, text or logos. Five seconds.',
    'Photorealistic macro film of the closed circular base of one upside-down clear drinking tumbler resting securely with its open mouth on a flat dish rack. A few small remaining water droplets on the base are visible and remain physically stable. Gentle camera move in natural kitchen light. No people, hands, floating glass, shape changes, text or logos. Five seconds.',
    'Professional photorealistic domestic kitchen film of three completely dry clear drinking tumblers standing upright separately inside an open wooden cupboard. Each closed glass base rests flat on the same level shelf, no overlap, generous safe space between glasses. Slow continuous camera push, realistic wood grain and glass refraction, stable objects and natural light, no people, hands, text or logos. Five seconds.'
]


def spec(profile,slot):
    if type(slot) is not int or not 0<=slot<len(PROMPTS):raise ValueError('UNREVIEWED_MISSION16_SHOT')
    return dict(wan.request_spec(profile,16,slot),editorial_id='copos-secos',
        episode_id=EPISODE,prompt=PROMPTS[slot],height=1024,width=576,steps=8,
        seed=160001+slot,reference_kind='authored_text_only')


def next_unrequested(inventory):
    requested={r.get('spec',{}).get('seed') for r in inventory['requests'].values()}
    return next((i for i in range(len(PROMPTS)) if 160001+i not in requested),None)


def run(slot=None):
    profile=json.loads(wan.PROFILE.read_text());wan.profile_check(profile)
    # Verified public UI at the pinned revision exposes 256..1024, modulus32,
    # steps1..8 and five seconds. Do not exceed its controls or billing policy.
    tier,token=auto_collect.free_hf_identity()
    store=GitHubStore(os.environ['GH_TOKEN'],path=INVENTORY,validate=False)
    budget=GitHubStore(os.environ['GH_TOKEN'],branch='feature/ai-video-hybrid-30s',path=wan.LEDGER,validate=False)
    inventory,revision=store.load()
    wait=inventory.get('last_wait',{})
    if wait.get('provider_quota_rejected') and dt.datetime.fromisoformat(wait['not_before'])>wan.now():
        return {'status':'BLOQUEADO POR LIMITAÇÃO GRATUITA','new_gpu_calls':0,'not_before':wait['not_before']}
    if slot is None:slot=next_unrequested(inventory)
    if slot is None:return {'status':'SHOT_PLAN_EXHAUSTED_REVIEW_REQUIRED','new_gpu_calls':0}
    request=spec(profile,slot);fingerprint=hf_probe.fingerprint(request)
    if fingerprint in inventory['requests']:
        return {'status':'PRESERVED_RESULT_OR_UNCERTAIN_NO_RESUBMISSION','request_sha256':fingerprint,'new_gpu_calls':0}
    ledger,_=budget.load()
    from experimental81 import daily_budget
    try:daily_budget.reserve(ledger,fingerprint,wan.now(),tier=tier,estimated_seconds=110)
    except daily_budget.QuotaError as exc:
        if str(exc)!='DAILY_QUOTA_ESTIMATE_EXCEEDED':raise
        result={'status':'BLOQUEADO POR LIMITAÇÃO GRATUITA','reason':str(exc),'new_gpu_calls':0,
            'not_before':(dt.datetime.fromisoformat(ledger['window_start'])+dt.timedelta(days=1)).isoformat()}
        inventory['last_wait']=result;store.save(inventory,revision)
        return result
    from gradio_client import Client
    folder=Path('tmp/mission16/wan-new');folder.mkdir(parents=True,exist_ok=True)
    client=Client(profile['space'],token=token or False,verbose=False,download_files=folder,httpx_kwargs={'timeout':30})
    api=client.view_api(return_format='dict',print_info=False)
    if [p['parameter_name'] for p in api['named_endpoints']['/generate_video']['parameters']]!=profile['order']:
        raise ValueError('PINNED_WAN_API_SCHEMA_CHANGED')
    fingerprint,revision=wan.reserve(store,budget,inventory,revision,request,tier,110,
        claim_profile='wan16_576x1024_8steps_quality_trial')
    entry=inventory['requests'][fingerprint]
    try:
        job=client.submit(*([None]+[request[key] for key in profile['order'][1:]]),api_name='/generate_video')
        deadline=time.monotonic()+10
        while not getattr(getattr(job,'communicator',None),'event_id',None) and not job.done() and time.monotonic()<deadline:time.sleep(.1)
        entry['provider_job_id']=getattr(getattr(job,'communicator',None),'event_id',None)
        revision=store.save(inventory,revision)
        path=Path(hf_probe.video_path(job.result(timeout=240)))
        media=hf_probe.inspect_clip(path)
        if (media['width'],media['height'])!=(576,1024):raise ValueError('QUALITY_TRIAL_NATIVE_SHAPE_MISMATCH')
        entry.update(status='GENERATED_AWAITING_STORAGE',media=media);revision=store.save(inventory,revision)
        url=auto_collect.upload_clip(path,media['sha256'],wan.now())
        clip={'slot':slot,'episode_id':EPISODE,'sha256':media['sha256'],'url':url,'media':media,
            'prompt':request['prompt'],'model':profile['model'],'model_revision':profile['model_revision'],
            'space':profile['space'],'space_revision':profile['space_revision'],'reference_kind':'authored_text_only',
            'visual_status':'GERAÇÃO CONCLUÍDA — AGUARDANDO REVISÃO','publication_approved':False,
            'license_url':profile['model_license_url'],'commercial_license_clearance':True,
            'generation_evidence':{'request_sha256':fingerprint,'provider_job_id':entry['provider_job_id'],
                'estimated_reserved_seconds':110,'observed_gpu_seconds':None,'tier':tier,'paid_endpoint_used':False}}
        inventory['clips'].append(clip);entry.update(status='GENERATED_DURABLE_PENDING_VISUAL_REVIEW',sha256=media['sha256'],url=url)
        inventory['status']='GERAÇÃO CONCLUÍDA — AGUARDANDO REVISÃO';store.save(inventory,revision)
        return {'status':inventory['status'],'clip':clip,'new_gpu_calls':1}
    except Exception as exc:
        status,reason=wan.provider_failure(exc)
        if hf_probe.classify_error(exc)=='QUOTA_OR_GPU_BUDGET':
            reason='QUOTA_OR_GPU_BUDGET'
            inventory['last_wait']={'provider_quota_rejected':True,'not_before':(wan.now()+dt.timedelta(days=1)).isoformat()}
        entry.update(status=status,reason=reason,error_type=type(exc).__name__)
        inventory['status']='BLOQUEADO POR LIMITAÇÃO GRATUITA' if reason=='QUOTA_OR_GPU_BUDGET' else 'GENERATION_HELD_NO_BLIND_RETRY'
        store.save(inventory,revision)
        return {'status':inventory['status'],'request_status':status,'reason':reason,'error_type':type(exc).__name__,'new_gpu_calls':1,'publication_approved':False}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--slot',choices=['auto']+[str(i) for i in range(len(PROMPTS))],default='auto');a=p.parse_args()
    result=run(None if a.slot=='auto' else int(a.slot));Path('tmp/mission16').mkdir(parents=True,exist_ok=True)
    Path('tmp/mission16/wan-trial-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
