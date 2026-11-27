"""Independent visual-style gate. Technical validity never approves a style."""
import json
from pathlib import Path

DECISIONS = Path(__file__).with_name('editorial_decisions.json')
INCOMPATIBLE = {'authored_household_illustration', 'illustration', 'vector_animation',
                'procedural_animation', 'slideshow', 'static_image_pan_zoom'}


def reject_incompatible(quality):
    if quality.get('video_origin') in INCOMPATIBLE or quality.get('visual_style') in INCOMPATIBLE:
        raise ValueError('VISUAL_STYLE_NOT_PHOTOREALISTIC')
    decisions = json.loads(DECISIONS.read_text())
    if any(quality.get('sha256') in item.get('media_sha256', [])
           for item in decisions['decisions'] if item['status'] == 'REJECTED'):
        raise ValueError('VISUAL_STYLE_NOT_PHOTOREALISTIC')
