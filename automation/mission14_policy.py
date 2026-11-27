"""Current output contract; legacy history stays readable, new writes fail closed."""
import datetime as dt
from pathlib import Path
import json

# A ceiling, never a production/publication promise. No filler to meet it.
MAX_WEEKLY = 3
MIN_SPACING = dt.timedelta(hours=48)


def allowed_slot(when, reservations):
    return (all(abs(when-other) >= MIN_SPACING for other in reservations)
            and sum(when-dt.timedelta(days=7) < other <= when for other in reservations) < MAX_WEEKLY)


def require_output(quality):
    from chatterbox_v3 import NAME, IDENTITY
    identity = json.loads(IDENTITY.read_text())
    if identity.get('status') != 'APPROVED' or identity.get('perceptual_review_approved') is not True or identity.get('commercial_synthesis_authorized') is not True or not identity.get('rights_evidence') or not identity.get('holder'):
        raise ValueError('MISSION14_VOICE_IDENTITY_PENDING_NO_NEW_PUBLICATION')
    if (quality.get('mission') != '14.0' or quality.get('voice') != NAME
            or quality.get('voice_reference_sha256') != identity.get('reference_sha256')
            or quality.get('audio_content_verified') is not True
            or quality.get('full_frame_reviewed') is not True
            or quality.get('captions_reviewed') is not True
            or quality.get('technical_pass') is not True
            or abs(quality.get('duration', 0)-30) > .15):
        raise ValueError('MISSION14_30S_VOICE_FRAMING_CAPTIONS_REVIEW_REQUIRED')
