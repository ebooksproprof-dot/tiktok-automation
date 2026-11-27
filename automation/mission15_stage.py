"""Idempotent handoff of the reviewed editorial episode to the existing queue.

No Buffer creation here. A real owner's voice approval is mandatory. All media
and observed content hashes are rechecked before existing release/queue writes.
"""
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).parent
PACK=ROOT/'mission15-evidence/episode'
VIDEO=ROOT.parent/'public/rendered/mission15/casasem-copos-secos-review.mp4'
DRAFT_ID='mission15-copos-secos'


def finalized_quality(voice,quality,audio,manifest,video_sha,wav_sha):
    if voice.get('status')!='APPROVED' or voice.get('perceptual_review_approved') is not True:
        raise ValueError('VOICE_LISTENING_APPROVAL_PENDING')
    if (not voice.get('commercial_synthesis_authorized') or not voice.get('rights_evidence')
            or voice.get('reference_sha256')!=manifest.get('reference_sha256')):
        raise ValueError('EPISODE_VOICE_RIGHTS_OR_IDENTITY_MISMATCH')
    if (video_sha!=quality.get('sha256') or wav_sha!=manifest.get('wav_sha256')
            or wav_sha!=audio.get('audio_sha256') or audio.get('audio_content_verified') is not True
            or quality.get('visual_editorial_approved') is not True
            or quality.get('captions_reviewed') is not True or quality.get('full_frame_reviewed') is not True
            or quality.get('technical_pass') is not True or quality.get('freeze_intervals_over_1s')!=0):
        raise ValueError('EPISODE_AUDIO_VISUAL_EVIDENCE_INCOMPLETE')
    from voice_approval import profile_digest
    if (voice.get('inference')!=manifest.get('inference')
            or voice.get('review_receipt',{}).get('inference_sha256')!=profile_digest(manifest['inference'])):
        raise ValueError('REVIEWED_VOICE_INFERENCE_SETTINGS_CHANGED')
    result=copy.deepcopy(quality);result.update(editorial_approved=True,publication_approved=True,
        editorial_review_status='ALL_GATES_VERIFIED',voice_profile_sha256=profile_digest(manifest['inference']),
        voice_identity_approval_receipt=voice['review_receipt'])
    from mission14_policy import require_output
    require_output(result)
    return result


def stage():
    from media_quality import validate
    from chatterbox_v3 import digest,IDENTITY
    from audio_review import compare
    from video_stock import GitHubStore
    from autonomous_production import choose_slot
    from editorial_policy import require as require_editorial
    from visual_library import require_evidence,history
    from release_media import publish
    from content_catalog import fingerprint as script_sha
    voice=json.loads(IDENTITY.read_text());quality=json.loads((PACK/'video-review.json').read_text())
    audio=json.loads((PACK/'asr.json').read_text());manifest=json.loads((PACK/'audio-manifest.json').read_text())
    if not compare(' '.join(manifest['lines']),audio['transcript'])['audio_content_verified']:
        raise ValueError('OBSERVED_TRANSCRIPT_DOES_NOT_MATCH_EPISODE')
    from authored_motion import validate as action_motion
    actual=validate(VIDEO,ai_only30=True);action_motion(VIDEO)
    quality=finalized_quality(voice,quality,audio,manifest,actual['sha256'],digest(PACK/'voice.wav'))
    token=os.environ['GH_TOKEN'];queue_store=GitHubStore(token,path='automation/queue.json',validate=False)
    state_store=GitHubStore(token,path='automation/state.json',validate=False)
    queue,revision=queue_store.load();state,_=state_store.load()
    existing=next((p for p in queue['posts'] if p.get('origin_draft_id')==DRAFT_ID),None)
    if existing:
        if existing['quality']['sha256']!=quality['sha256']:raise ValueError('EXISTING_DRAFT_MEDIA_CHANGED')
        register_output(existing,token)
        return {'status':'ALREADY_QUEUED_DO_NOT_REPEAT','post_id':existing['id'],'publication_confirmed':False}
    now=dt.datetime.now(dt.timezone.utc);post_id,when=choose_slot(queue,state,now)
    post={'id':post_id,'origin_draft_id':DRAFT_ID,'concept':'tip12-copos-secos','owner_mission':'15.0',
        'video_origin':'authored_household_illustration','publication_provider':'buffer','render_version':15,
        'title':'Copo guardado com água no fundo? Veja o cuidado antes de guardar. Ilustração autoral; siga as instruções do fabricante. #CasaSemEsforco #OrganizacaoDaCasa',
        'scheduled_at':when.isoformat(),'approved':True,'consented_at':now.isoformat(),
        'approval_scope':'mission15_owner_authorized_automated_editorial_checks_after_explicit_voice_approval',
        'script_lines':manifest['lines'],'script_sha256':script_sha(manifest['lines']),
        'quality':quality,'media_storage':'release','publishing_status':'READY_FOR_EXISTING_BUFFER_RUNNER'}
    post['editorial']=require_editorial(post,queue,state)
    previous=history(queue,state)+[json.loads((ROOT/'visual_history.json').read_text())]
    require_evidence(post,previous)
    post['video_url']=publish(VIDEO,post_id,quality)
    queue['posts'].append(post);queue_store.save(queue,revision)
    register_output(post,token)
    return {'status':'QUEUED','post_id':post_id,'scheduled_at':when.isoformat(),'publication_confirmed':False}

def register_output(post,token):
    from video_stock import GitHubStore
    store=GitHubStore(token,path='automation/production_state.json',validate=False)
    ledger,revision=store.load();outputs=ledger.get('outputs')
    if not isinstance(outputs,dict):raise ValueError('EXISTING_PRODUCTION_HISTORY_REQUIRED')
    old=outputs.get(post['id'])
    if old:
        if old['sha256']!=post['quality']['sha256']:raise ValueError('DURABLE_EPISODE_HASH_CHANGED')
        return  # Never downgrade an already reconciled publication receipt.
    outputs[post['id']]={'status':'QUEUED','sha256':post['quality']['sha256'],
        'scheduled_at':post['scheduled_at'],'origin_draft_id':DRAFT_ID,'publicly_verified':False}
    ledger['last_run']={'status':'MISSION15_EPISODE_QUEUED','created':1,'publication_confirmed':False}
    store.save(ledger,revision)


if __name__=='__main__':print(json.dumps(stage(),ensure_ascii=False,indent=2))
