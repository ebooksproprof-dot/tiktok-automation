"""Finish a complete six-scene AI-only episode and enqueue through EXISTING Buffer runner.

Never call Buffer here. It stages ONE fully checked, owner-authorized AI30 post
in main's existing queue; the preexisting TikTok Online Runner remains the sole
publication path. No queue entry is created from fewer than six real AI assets.
"""
import argparse
import json
import hashlib
from datetime import datetime,timedelta
from pathlib import Path
import re
import sys
import tempfile
import urllib.request
from zoneinfo import ZoneInfo

AUTOMATION=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(AUTOMATION))
from experimental81 import auto_collect as collector
from experimental81 import render
from experimental81.quality import validate as validate_ai30
from release_media import publish as publish_existing_release
from visual_library import similar, fingerprint, require_evidence

LOCAL=ZoneInfo('America/Sao_Paulo')


def download(entry, folder):
    path=Path(folder)/('ai-shot-'+str(entry['slot'])+'.mp4')
    url=entry['url']
    if not url.startswith('https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/ai30-drafts-'):
        raise ValueError('UNTRUSTED_MEDIA_URL')
    request=urllib.request.Request(url,headers={'User-Agent':'CasaSemEsforco-AI30/1.0'})
    with urllib.request.urlopen(request,timeout=75) as response,path.open('wb') as out:
        size=0
        while True:
            chunk=response.read(512*1024)
            if not chunk:break
            size+=len(chunk)
            if size>20_000_000:raise ValueError('AI30_SOURCE_TOO_LARGE')
            out.write(chunk)
    if render.sha(path)!=entry['sha256']:
        raise ValueError('AI30_SOURCE_HASH_MISMATCH')
    return path


def choose_time(queue,state,now):
    def matches(item,stamp):
        value=item.get('scheduled_at')
        if not isinstance(value,str):return False
        try:t=datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError:return False
        if t.tzinfo is None:return False
        return t.astimezone(LOCAL)==stamp
    # Buffer requires >5 minutes in the future and <=26h.
    local=now.astimezone(LOCAL)
    for days in (0,1):
        chosen=(local+timedelta(days=days)).replace(hour=10,minute=0,second=0,microsecond=0)
        if not timedelta(minutes=20)<chosen-local<timedelta(hours=26):
            continue
        if any(matches(item,chosen) for item in queue.get('posts',[])):
            continue
        if any(matches(item,chosen) for item in state.get('posts',{}).values()):
            continue
        return chosen
    raise ValueError('NO_FREE_BUFFER_10H_SLOT_IN_NEXT_26H')


def build_post(state,video,quality,source_visuals,now):
    queue_sha,queue=collector.content_get('automation/queue.json','main')
    _,existing_state=collector.content_get('automation/state.json','main')
    when=choose_time(queue,existing_state,now)
    candidate_ids=['casasem-'+when.strftime('%Y-%m-%d')+'-'+n for n in ('1','2')]
    existing_ids={p.get('id') for p in queue['posts']}
    existing_ids|=set(existing_state.get('posts',{}))
    chosen_id=next((x for x in candidate_ids if x not in existing_ids),None)
    if chosen_id is None:raise ValueError('POST_IDS_OCCUPIED')
    if len({x['sha256'] for x in state['clips']})!=6:
        raise ValueError('SIX_UNIQUE_GENERATED_SOURCES_REQUIRED')
    prior_quality=[p.get('quality',{}) for p in queue['posts']]
    prior_quality+=list(existing_state.get('posts',{}).values())
    # All sources were genuine model video outputs, not reference stock.
    quality.update(visual_policy_version=1,visual_distinct=True,
                   visual_sources=source_visuals,
                   source_urls=[x['url'] for x in state['clips']],
                   scene_reuse_policy='six_distinct_AI_generated_clips_no_loop',
                   ai_generated_seconds=30,
                   model=state['clips'][0]['model'],
                   voice='kokoro-onnx-0.6.1-v1.0-int8-pf_dora-pt-br',
                   required_public_credits=[],
                   # The owner explicitly authorized the first fully AI video
                   # as a real publication test without separate preview.
                   editorial_approved=True,
                   editorial_basis='Owner authorized live AI30 test on 2026-11-03; no human visual quality certification',
                   machine_checks_only=True,
                   professional_quality_certified=False)
    post={'id':chosen_id,
          'video_origin':'ai_only30',
          'video_url':video,
          'title':'Uma casa mais prática começa com pequenas atitudes. Veja seis momentos de limpeza e organização gerados com inteligência artificial. Dicas ilustrativas: siga as instruções dos fabricantes dos produtos e superfícies. #CasaSemEsforco #OrganizacaoDaCasa #InteligenciaArtificial',
          'scheduled_at':when.isoformat(),
          'approved':True,'consented_at':now.isoformat(),
          'approval_scope':'owner_authorized_ai30_first_live_test_and_ongoing_automation',
          'quality':quality,
          'publishing_status':'OWNER_AUTHORIZED_AI30_EXPERIMENT_SCHEDULED',
          'publication_provider':'buffer',
          'media_storage':'release',
          'render_version':3,
          'concept':'faxina-ia30-'+str(state['episode_sequence']),
          'script_lines':collector.SCRIPT,
          'script_sha256':hashlib.sha256('\n'.join(collector.SCRIPT).encode()).hexdigest(),
          'editorial_review':{'type':'owner_waived_preview',
             'owner_consent_reference':'automation/experimental81/FIRST-PUBLICATION-CONSENT.md',
             'verified':'technical+duplicate+scene_heuristics',
             'not_verified':'human_perceptual_scene_review; commercial derivative licensing'},
          'ai_disclosure_required':True}
    # Reuse project's duplicate/visual fingerprints gate before remotely staging.
    require_evidence(post,prior_quality)
    return queue_sha,queue,post


def finish():
    sha,state=collector.content_get(collector.INVENTORY)
    collector.check_inventory(state)
    if state['status']!='READY' or len(state['clips'])!=6:
        return {'status':'NOT_READY','clips':len(state['clips'])}
    with tempfile.TemporaryDirectory(prefix='ai30-final-') as folder:
        out=Path(folder)
        sources=[]
        visuals=[]
        for item in state['clips']:
            src=download(item,out)
            visual=fingerprint(src,item['url'])
            if any(similar(visual,v) for v in visuals):
                raise ValueError('AI30_VISUAL_REPETITION')
            visuals.append(visual)
            sources.append({'path':str(src),'sha256':item['sha256'],'kind':'ai',
                'model':item['model'],'source_url':item['url'],
                'license_url':'https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B-Diffusers',
                'generation_evidence':item['generation_evidence']['request_sha256'],
                'visual_review_passed':True,
                'review_method':'automated distinctness, decode and owner waived preview; not human perceptual approval',
                'derivative_license_status':'unconfirmed'})
        narration=render.synthesize(out/'speech',collector.SCRIPT)
        manifest={'experimental_only':True,'script':collector.SCRIPT,
                  'clips':sources,'narration':narration}
        output=render.compose(manifest,out/'render','AI_ONLY')
        quality=validate_ai30(output['video_path'])
        if (quality.get('technical_pass') is not True
                or output.get('ai_seconds')!=30 or output.get('real_seconds')!=0
                or len(output['shots'])!=6):
            raise ValueError('AI30_FULL_VIDEO_NOT_VERIFIED')
        now=collector.now_utc()
        # The only publication route is the existing Buffer queue; no other
        # API publisher, no new TikTok credentials, and no direct TikTok calls.
        # Publishing is committed LAST, only after release readback.
        existing_sha,existing_queue=collector.content_get('automation/queue.json','main')
        _,existing_state=collector.content_get('automation/state.json','main')
        when=choose_time(existing_queue,existing_state,now)
        post_id=next((f"casasem-{when:%Y-%m-%d}-{n}"
                      for n in (1,2)
                      if all(p.get('id')!=f"casasem-{when:%Y-%m-%d}-{n}"
                             for p in existing_queue['posts'])
                      and f"casasem-{when:%Y-%m-%d}-{n}" not in existing_state.get('posts',{})),None)
        if post_id is None:raise ValueError('NO_POST_ID_AVAILABLE')
        video_url=publish_existing_release(output['video_path'],post_id,quality)
        qsha,q,post=build_post(state,video_url,quality,visuals,now)
        if qsha!=existing_sha:
            raise ValueError('QUEUE_CHANGED_DURING_MEDIA_UPLOAD_RECHECK')
        if any(p.get('video_url')==video_url or p.get('quality',{}).get('sha256')==quality['sha256']
               for p in q['posts']):
            raise ValueError('DUPLICATE_FINAL_POST_BLOCKED')
        q['posts'].append(post)
        staged=collector.content_put('automation/queue.json',qsha,q,ref='main',
                   message='Queue owner-authorized 30s all-AI trial via existing Buffer runner')
        # Queue is durable; if this checkpoint fails, NEVER stage again blindly.
        completion={'status':'QUEUED_UNDER_BUFFER_CONTROLS',
            'episode_sequence':state['episode_sequence'],'post_id':post['id'],
            'queue_commit':staged,'video_sha256':quality['sha256'],
            'video_url':video_url,'scheduled_at':post['scheduled_at'],
            'publication_verified':False}
        state['publish_history'].append(completion)
        # Preserve the queued output and allow future episodes without losing
        # already consumed request fingerprints in the separate quota ledger.
        state['last_output']=completion
        state['episode_sequence']+=1
        state['clips']=[]
        state['status']='COLLECTING'
        collector.content_put(collector.INVENTORY,sha,state,
                   message='Record AI30 queue handoff and advance episode without duplicate posting')
        return {'status':'QUEUED_FOR_BUFFER','post_id':post['id'],
                'scheduled_at':post['scheduled_at'],'video_url':video_url,
                'queue_commit':staged,'publication_verified':False}


def main():
    if collector.now_utc().tzinfo is None:raise RuntimeError('TIMEZONE_MISSING')
    if (collector.os.getenv('GITHUB_ACTIONS')!='true'
            or collector.os.getenv('GITHUB_WORKFLOW')!='CasaSemEsforco AI30 Free Collector'
            or collector.os.getenv('GITHUB_REF_NAME')!='main'
            or collector.os.getenv('AI30_MAIN_SCHEDULER_ALLOW')!='true'):
        return {'status':'SAFE_BLOCKED_INVALID_CLOUD_CONTEXT'}
    return finish()


if __name__=='__main__':
    try:
        print(json.dumps(main(),ensure_ascii=False,indent=2))
    except Exception as exc:
        print(json.dumps({'status':'FINISH_BLOCKED','error_type':type(exc).__name__,
                          'reason':'No unverified output was staged; inspect safe local logs'}))
        sys.exit(2)
