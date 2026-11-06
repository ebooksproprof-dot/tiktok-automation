"""Commercial clearance is independent of owner consent and media validation."""
import re
from datetime import datetime
from urllib.parse import urlsplit


def require_clearance(clips):
    if not clips:
        raise ValueError('AI_COMMERCIAL_CLEARANCE_REQUIRED')
    for clip in clips:
        evidence = clip.get('commercial_license_evidence') or {}
        if (clip.get('commercial_license_clearance') is not True
                or not re.fullmatch(r'[0-9a-f]{64}', clip.get('sha256', ''))
                or evidence.get('source_sha256') != clip['sha256']):
            raise ValueError('AI_COMMERCIAL_CLEARANCE_REQUIRED')
        try:
            reviewed = datetime.fromisoformat(evidence['reviewed_at'].replace('Z', '+00:00'))
            if reviewed.tzinfo is None:
                raise ValueError()
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ValueError('AI_LICENSE_REVIEW_DATE_REQUIRED') from None
        for component in ('model', 'derivative', 'reference', 'voice'):
            item = evidence.get(component) or {}
            url = urlsplit(item.get('license_url', ''))
            if (item.get('commercial_use') is not True or not item.get('revision')
                    or url.scheme != 'https' or not url.hostname or url.username):
                raise ValueError('AI_LICENSE_COMPONENT_UNCONFIRMED_' + component.upper())
    return clips
