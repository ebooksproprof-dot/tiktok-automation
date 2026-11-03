"""Scheduled, nonpaid Wan clip collector. NO publication or claim of video quality.

Runs from an isolated checkout; every GPU attempt must first reserve a durable
request SHA via GitHub CAS. Stores each real MP4 as a verified Release asset and
tracks it in the branch inventory. Failed/uncertain calls are never auto-retried.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen

AUTOMATION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUTOMATION))
from experimental81 import daily_budget, github_ledger, wan_probe
from release_media import API, REPO, request as github_request
from visual_library import fingerprint, similar

INVENTORY = 'automation/experimental81/auto_inventory.json'
INV_API = API + '/contents/' + INVENTORY
MAX_CLIPS_PER_RUN = 2
# These are only input-image references from separately licensed Pexels footage.
# The final video will use only actual AI-generated motion, not these videos.
REFERENCE = [
    ('02_pia_limpa.mp4', '9472849', 1.0),
    ('02_pia_limpa.mp4', '9472849', 4.5),
    ('03_espelho_limpo.mp4', '9462884', 1.0),
    ('03_espelho_limpo.mp4', '9462884', 4.5),
    ('01_piso_opaco.mp4', '9473227', 1.0),
    ('01_piso_opaco.mp4', '9473227', 4.5),
]
SCENES = [
    'Photorealistic household cleaning demonstration. A pink gloved adult hand gently wipes ceramic countertop with microfiber cloth near steel faucet, stable sink geometry, consistent natural lighting, clear realistic contact, single unhurried action, no logos and no text.',
    'Photorealistic close-up of a kitchen faucet and countertop. A gloved hand folds a microfiber cloth, slowly cleans the area directly beside the faucet, consistent sink and cloth, no extra fingers, no camera shake, no logos and no text.',
    'Photorealistic home cleaning. An adult hand uses a clean microfiber cloth to wipe one section of a bathroom mirror, natural continuous movement, reflections consistent with the real room, no added objects, no logos or text.',
    'Photorealistic bathroom mirror. The same realistic person carefully buffs one visible smudge on a mirror using a dry microfiber cloth, gentle contact and physically consistent reflections, stable camera and geometry, no text or logos.',
    'Photorealistic floor cleaning. A person moves a cleaning cloth gently over a small section of floor, clearly visible contact, no disappearing items, correct hand anatomy, natural daylight, one coherent action, no text or logos.',
    'Photorealistic household clean floor after wiping. Adult hand makes a final gentle wiping pass with cloth and moves away leaving floor visibly tidy, consistent surface and natural shadows, no deformation, no text or logos.'
]
SCRIPT = [
    'Sua casa parece difícil de manter limpa? Comece por partes pequenas.',
    'Na pia, retire resíduos e use um pano adequado para a superfície.',
    'No espelho, cuide das marcas com movimentos leves e sem exagerar nos produtos.',
    'Depois, seque com um pano limpo, evitando novas manchas e riscos.',
    'No piso, siga as instruções do fabricante e deixe os produtos longe das crianças.',
    'No fim, guarde os materiais e aproveite o ambiente organizado. Salve esta dica.'
]


def now_utc():
    return datetime.now(timezone.utc)

def free_hf_identity():
    """Only permit optional user-owned non-PRO Free account, never auto-bill."""
    token=os.getenv('HF_FREE_TOKEN','').strip()
    if not token:
        return 'anonymous',None
    request=Request('https://huggingface.co/api/whoami-v2',
            headers={'Authorization':'Bearer '+token,
                     'Accept':'application/json','User-Agent':'CasaSemEsforco-AI30/1.0'})
    try:
        with urlopen(request,timeout=20) as response:
            data=json.load(response)
    except Exception:
        raise RuntimeError('HF_FREE_ACCOUNT_VERIFICATION_FAILED_NO_AUTH_CALL') from None
    if not isinstance(data,dict) or data.get('isPro') is not False or data.get('type')!='user':
        raise RuntimeError('HF_FREE_ONLY_NO_PRO_OR_UNKNOWN_TIER')
    return 'free',token




def content_get(path, ref='feature/ai-video-hybrid-30s'):
    token = os.environ['GH_TOKEN']
    response = github_ledger.request_json(
        'GET', API+'/contents/'+path+'?ref='+ref.replace('/','%2F'), token)
    sha, data = github_ledger.parse_file(response)
    return sha, data


def content_put(path, sha, value, ref='feature/ai-video-hybrid-30s', message='Update AI30 durable state'):
    token = os.environ['GH_TOKEN']
    body = {'message': message, 'sha': sha, 'branch': ref,
            'content': base64.b64encode((json.dumps(value, ensure_ascii=False,
                                  indent=2, sort_keys=True)+'\n').encode()).decode()}
    response = github_ledger.request_json('PUT', API+'/contents/'+path, token, body)
    if not response.get('commit',{}).get('sha'):
        raise RuntimeError('INVENTORY_WRITE_UNCONFIRMED_NO_RETRY')
    _, checked = content_get(path,ref)
    if checked != value:
        raise RuntimeError('INVENTORY_READBACK_MISMATCH_NO_RETRY')
    return response['commit']['sha']


def check_inventory(value):
    if (not isinstance(value, dict) or value.get('schema_version') != 1
            or type(value.get('episode_sequence')) is not int
            or not 1 <= value['episode_sequence'] <= 9999
            or value.get('status') not in ('COLLECTING','READY','BLOCKED')
            or not isinstance(value.get('clips'), list)
            or len(value['clips']) > 6):
        raise ValueError('INVALID_INVENTORY')
    hashes = [x.get('sha256') for x in value['clips']]
    if len(set(hashes)) != len(hashes):
        raise ValueError('DUPLICATE_INVENTORY_HASH')
    return value


def extract_reference(slot, folder):
    if not 0 <= slot < 6: raise ValueError('SLOT_OUT_OF_RANGE')
    name, pexels_id, second = REFERENCE[slot]
    source = AUTOMATION.parent/'public/rendered'/name
    if not source.is_file(): raise ValueError('PINNED_REFERENCE_VIDEO_MISSING')
    image = Path(folder)/('reference-'+str(slot)+'.png')
    # Crops the prior editing frame; source has existing Pexels provenance.
    command = ['ffmpeg','-nostdin','-hide_banner','-loglevel','error',
        '-ss',str(second),'-i',str(source),'-frames:v','1',
        '-vf','crop=630:1090:224:560,scale=480:832:flags=lanczos',
        '-y',str(image)]
    subprocess.run(command,check=True,capture_output=True,timeout=45)
    if image.stat().st_size < 1000: raise ValueError('REFERENCE_EXTRACTION_INVALID')
    return image,{'reference_video':str(source.relative_to(AUTOMATION.parent)),
                  'reference_video_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                  'pexels_id':pexels_id, 'pexels_license':'https://www.pexels.com/license/'}


def upload_clip(path, digest, date):
    token = os.environ['GH_TOKEN']
    tag='ai30-drafts-'+date.strftime('%Y-%m')
    name='ai30-'+digest[:24]+'.mp4'
    release = github_request(API+'/releases/tags/'+tag,token)
    if release is None:
        release=github_request(API+'/releases',token,'POST',{
            'tag_name':tag,'target_commitish':'main','name':'CasaSemEsforco IA experimental '+date.strftime('%Y-%m'),
            'draft':False,'prerelease':True,'make_latest':'false',
            'body':'AI clips for experimental pipeline only; no public TikTok publication approved by this upload.'})
    assets=github_request(API+'/releases/'+str(release['id'])+'/assets?per_page=100',token)
    if not isinstance(assets,list) or len(assets)>=95:
        raise RuntimeError('RELEASE_ASSET_LIMIT_UNKNOWN')
    found=next((x for x in assets if x.get('name')==name),None)
    data=Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest or not 1000<len(data)<=20_000_000:
        raise ValueError('MP4_HASH_OR_SIZE_MISMATCH')
    if found is None:
        found=github_request('https://uploads.github.com/repos/'+REPO+
                    '/releases/'+str(release['id'])+'/assets?name='+name,
                    token,'POST',data,'video/mp4')
    verified=github_request(API+'/releases/assets/'+str(found['id']),token)
    url='https://github.com/'+REPO+'/releases/download/'+tag+'/'+name
    if (verified.get('name')!=name or verified.get('state')!='uploaded'
            or verified.get('size')!=len(data)
            or verified.get('digest')!='sha256:'+digest
            or verified.get('browser_download_url')!=url):
        raise RuntimeError('RELEASE_ASSET_READBACK_FAILED')
    return url


def collect_one(folder):
    sha, state=content_get(INVENTORY)
    state=check_inventory(state)
    if state['status']!='COLLECTING' or len(state['clips'])>=6:
        return {'status':state['status'],'clips':len(state['clips'])}
    slot=len(state['clips'])
    image, provenance=extract_reference(slot,folder)
    case='ABC'[slot%3]
    episode=state['episode_sequence']
    variant=int(state.get('retry_variant',0))
    if not 0<=variant<=50:raise ValueError('INVALID_RETRY_VARIANT')
    description=SCENES[slot]+f' Original episode {episode}, single distinctive scene {slot+1} of six. Variation {variant}: preserve the same visible action with natural physically coherent micro-movement.'
    # Check the LOCAL conservative quota model before opening the Space.
    # This is NOT a check of actual HF credits, which the public endpoint
    # does not expose. A denied estimate should simply wait for renewal.
    from experimental81 import hf_probe as common
    request_spec={'case':case,'space':wan_probe.SPACE,'model':wan_probe.MODEL,
        'reference_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
        'prompt':description,'steps':4,
        'negative_prompt':'warped objects, deformed hands, duplicate objects, text, logos',
        'duration_seconds':5,'guidance_scale':1,'guidance_scale_2':1,
        'seed':8100+ord(case)-ord('A')+1,'randomize_seed':False}
    request_sha=common.fingerprint(request_spec)
    tier,hf_token=free_hf_identity()
    _, ledger=content_get('automation/experimental81/ledger.json')
    # A new Free token is not a way to reset an in-progress anonymous
    # 24-hour window; wait until its original start time has elapsed.
    started=ledger.get('window_start')
    if started and ledger.get('tier') and ledger['tier']!=tier:
        from datetime import timedelta
        try: first=datetime.fromisoformat(started)
        except (ValueError,TypeError):
            raise ValueError('INVALID_LEDGER_WINDOW_START') from None
        if now_utc()<first+timedelta(hours=24):
            return {'status':'WAIT_CREDITS','clips':slot,'reason':'FREE_TIER_CHANGE_NEXT_WINDOW_ONLY'}
    try:
        daily_budget.reserve(ledger,request_sha,now_utc(),tier=tier)
    except daily_budget.QuotaError as exc:
        if str(exc)=='DAILY_QUOTA_ESTIMATE_EXCEEDED':
            return {'status':'WAIT_CREDITS','clips':slot,
                    'reason':'CONSERVATIVE_WINDOW_ESTIMATE_FULL',
                    'not_before':ledger.get('window_start')}
        raise
    output=Path(folder)/'generation'
    output.mkdir(exist_ok=True)
    result=wan_probe.run(image,case,output,enabled=True,
                         before_submit=lambda record: github_ledger.reserve_remote(record,tier=tier),
                         prompt=description,hf_token=hf_token)
    if result.get('status')!='GENERATED_PENDING_VISUAL_REVIEW':
        # Known quota exhaustion is safe to reattempt only NEXT quota window
        # with a different fingerprint; an unknown transport result is NOT.
        reason=result.get('error')
        recoverable=(reason in ('QUOTA_OR_GPU_BUDGET','SPACE_MODEL_UNAVAILABLE'))
        state['status']='COLLECTING' if recoverable else 'BLOCKED'
        if recoverable: state['retry_variant']=variant+1
        state['last_attempt']={'slot':slot,'result':result.get('status'),
                               'error':reason,'at':now_utc().isoformat(),
                               'request_sha256':result.get('request_sha256')}
        content_put(INVENTORY,sha,state,message='Preserve AI30 failed request; guard uncertain retries')
        return {'status':'WAIT_CREDITS' if recoverable else 'BLOCKED',
                'reason':reason or result.get('status'),'clips':slot}
    source=output/result['file']
    digest=result['media']['sha256']
    key='https://huggingface.co/spaces/zerogpu-aoti/wan2-2-fp8da-aoti-faster'
    visual=fingerprint(source,key+'#'+digest)
    if any(similar(visual,previous.get('visual_source',{})) for previous in state['clips']):
        state['status']='BLOCKED'
        state['last_attempt']={'slot':slot,'result':'VISUAL_NEAR_DUPLICATE',
                                'request_sha256':result['request_sha256']}
        content_put(INVENTORY,sha,state,message='Pause AI30: generated scene perceptually duplicated')
        return {'status':'BLOCKED','reason':'VISUAL_NEAR_DUPLICATE','clips':slot}
    asset_url=upload_clip(source,digest,now_utc())
    entry={'slot':slot,'episode':episode,'sha256':digest,'url':asset_url,
           'media':result['media'],'model':wan_probe.MODEL,'reference':provenance,
           'generation_evidence':{'request_sha256':result['request_sha256'],
               'wall_seconds':result.get('wall_seconds'),'gpu_seconds_consumed':None},
           'prompt':description,'visual_source':visual,
           'visual_check':'automatic_fingerprint_only; no semantic/human review',
           'owner_test_publication_consent':True,'commercial_license_clearance':False}
    state['clips'].append(entry)
    state['retry_variant']=0
    state['last_attempt']={'slot':slot,'result':'ASSET_VERIFIED','at':now_utc().isoformat()}
    if len(state['clips'])==6:state['status']='READY'
    content_put(INVENTORY,sha,state,message='Persist validated real AI30 clip '+str(slot+1)+' of 6')
    return {'status':state['status'],'clips':len(state['clips']),'sha256':digest,'url':asset_url}


def main(dry_run=False):
    if dry_run:
        return {'status':'DRY_RUN_NO_REMOTE_CALLS',
                'quota':daily_budget.estimate_full_video(tier='anonymous'),
                'clips_target':6,'new_clips_max_per_run':MAX_CLIPS_PER_RUN}
    if (os.getenv('GITHUB_ACTIONS')!='true'
        or os.getenv('GITHUB_WORKFLOW')!='CasaSemEsforco AI30 Free Collector'
        or os.getenv('GITHUB_REF_NAME')!='main'
        or os.getenv('AI30_MAIN_SCHEDULER_ALLOW')!='true'
        or not os.getenv('GH_TOKEN')):
        return {'status':'SAFE_BLOCKED_INVALID_CLOUD_CONTEXT'}
    events=[]
    with tempfile.TemporaryDirectory(prefix='ai30-') as folder:
        for _ in range(MAX_CLIPS_PER_RUN):
            record=collect_one(folder)
            events.append(record)
            if record['status']!='COLLECTING':break
    return {'status':events[-1]['status'] if events else 'NO_ACTION',
            'attempts':events,'new_video_posted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    try:
        result=main(args.dry_run)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if result['status'] in ('SAFE_BLOCKED_INVALID_CLOUD_CONTEXT','BLOCKED'):
            sys.exit(2)
    except Exception as exc:
        # Never dump error bodies from remote services or possibly secret tokens.
        print(json.dumps({'status':'BLOCKED_UNEXPECTED','exception_type':type(exc).__name__,
            'message':'inspect safe private logs, no blind repeat of remote submissions'}))
        sys.exit(2)
