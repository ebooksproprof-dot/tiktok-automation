"""Current output contract; legacy history stays readable, new writes fail closed."""
import datetime as dt
from pathlib import Path
import json

# A ceiling, never a production/publication promise. No filler to meet it.
MAX_WEEKLY = 3
MIN_SPACING = dt.timedelta(hours=48)


def allowed_slot(when, reservations):
    if not all(abs(when-other) >= MIN_SPACING for other in reservations):
        return False
    times=[when,*reservations]
    # Inserting before existing future reservations must also respect their
    # rolling windows, not only the seven days preceding the candidate.
    return all(sum(end-dt.timedelta(days=7)<other<=end for other in times)<=MAX_WEEKLY
               for end in times if when<=end<when+dt.timedelta(days=7))


def require_output(quality):
    from photoreal_policy import reject_incompatible
    reject_incompatible(quality)
    from chatterbox_v3 import NAME, IDENTITY
    identity = json.loads(IDENTITY.read_text())
    if identity.get('status') != 'APPROVED' or identity.get('perceptual_review_approved') is not True or identity.get('commercial_synthesis_authorized') is not True or not identity.get('rights_evidence') or not identity.get('holder'):
        raise ValueError('MISSION14_VOICE_IDENTITY_PENDING_NO_NEW_PUBLICATION')
    if identity.get('reference_source',{}).get('kind')=='kyutai_donation':
        from voice_approval import profile_digest
        receipt=identity.get('review_receipt',{})
        profile_hash=profile_digest(identity.get('inference',{}))
        if receipt.get('engine_name')!=NAME or receipt.get('inference_sha256')!=profile_hash or quality.get('voice_profile_sha256')!=profile_hash:
            raise ValueError('APPROVED_VOICE_MODEL_OR_PARAMETERS_CHANGED')
    if (quality.get('mission') not in ('14.0','15.0') or quality.get('voice') != NAME
            or quality.get('voice_reference_sha256') != identity.get('reference_sha256')
            or quality.get('audio_content_verified') is not True
            or quality.get('full_frame_reviewed') is not True
            or quality.get('captions_reviewed') is not True
            or quality.get('technical_pass') is not True
            or abs(quality.get('duration', 0)-30) > .15):
        raise ValueError('MISSION14_30S_VOICE_FRAMING_CAPTIONS_REVIEW_REQUIRED')


def require_schedule(post, queue, state):
    from daily_coverage import stamp
    merged={p.get('id'):p for p in queue.get('posts',[])}
    merged.update({key:dict(value,id=key) for key,value in state.get('posts',{}).items()})
    reservations=[]
    for key,p in merged.items():
        if key==post.get('id') or not p.get('scheduled_at'):continue
        if p.get('status')=='CANCELLED_EDITORIAL' and p.get('buffer_status')=='deleted':continue
        reservations.append(stamp(p['scheduled_at']))
    when=stamp(post['scheduled_at'])
    if not allowed_slot(when,reservations):
        raise ValueError('MISSION14_48H_SPACING_AND_WEEKLY_LIMIT_REQUIRED')
