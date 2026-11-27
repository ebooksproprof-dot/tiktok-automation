"""Independent visual-style gate. Technical validity never approves a style."""
import json
from pathlib import Path
import re

DECISIONS = Path(__file__).with_name('editorial_decisions.json')
REVIEWS = Path(__file__).with_name('photoreal_reviews.json')
CRITERIA=('photorealism','clarity','physical_coherence','motion','narrative','editing','variety','framing')
INCOMPATIBLE = {'authored_household_illustration', 'illustration', 'vector_animation',
                'procedural_animation', 'slideshow', 'static_image_pan_zoom'}


def reject_incompatible(quality):
    if (quality.get('video_origin') in INCOMPATIBLE or quality.get('visual_style') in INCOMPATIBLE
            or quality.get('visual_rejection_reason')=='VISUAL_STYLE_NOT_PHOTOREALISTIC'):
        raise ValueError('VISUAL_STYLE_NOT_PHOTOREALISTIC')
    decisions = json.loads(DECISIONS.read_text())
    if any((quality.get('sha256') in item.get('media_sha256', [])
            or item.get('episode_id') in (quality.get('episode_id'),quality.get('origin_draft_id')))
           for item in decisions['decisions'] if item['status'] == 'REJECTED'):
        raise ValueError('VISUAL_STYLE_NOT_PHOTOREALISTIC')


def definition(width,height,crop,upscale_review=None):
    """Native pixels in the actual portrait crop, never export dimensions.

    720x1280 is the default minimum. 576x1024 needs a recorded, source-bound
    before/after review of conventional resampling; below that is rejected.
    No generator or sharpening filter can assert that it created real detail.
    """
    if (any(type(x) is not int or x<=0 for x in (width,height)) or not isinstance(crop,(tuple,list)) or len(crop)!=4
            or any(type(x) is not int for x in crop)):
        raise ValueError('SOURCE_NATIVE_GEOMETRY_REQUIRED')
    x,y,w,h=crop
    if min(x,y)<0 or min(w,h)<=0 or x+w>width or y+h>height or abs(w/h-9/16)>.003:
        raise ValueError('SOURCE_PORTRAIT_CROP_INVALID')
    factor=max(1080/w,1920/h)
    if w<576 or h<1024:raise ValueError('SOURCE_NATIVE_DEFINITION_INSUFFICIENT')
    if w<720 or h<1280:
        review=upscale_review or {}
        if (factor>1.875+1e-6 or review.get('approved') is not True
                or not review.get('comparison_artifact') or not review.get('reviewer')
                or review.get('method') not in ('lanczos','bicubic')
                or review.get('invented_detail') is not False):
            raise ValueError('SOURCE_UPSCALE_COMPARISON_REVIEW_REQUIRED')
    return {'native_crop_width':w,'native_crop_height':h,'upscale_factor':factor,
            'native_full_hd':w>=1080 and h>=1920}


def require_source(source_sha256,registry=None):
    registry=registry if registry is not None else json.loads(REVIEWS.read_text())
    receipt=registry.get('sources',{}).get(source_sha256,{})
    if (receipt.get('source_sha256')!=source_sha256 or receipt.get('status')!='APPROVED'
            or receipt.get('style')!='photorealistic' or receipt.get('commercial_rights_verified') is not True
            or not receipt.get('reviewer') or type(receipt.get('human_review')) is not bool
            or not receipt.get('sequence_artifact') or not receipt.get('native_probe_artifact')
            or any(receipt.get('criteria',{}).get(k) is not True for k in ('photorealism','clarity','physical_coherence','motion'))):
        raise ValueError('PHOTOREAL_SOURCE_REVIEW_REQUIRED')
    definition(*receipt['native_dimensions'],receipt['portrait_crop'],receipt.get('upscale_review'))
    return receipt


def approved_crop_id(source_sha256):
    """Only an existing approved source may opt into its reviewed portrait crop."""
    if not source_sha256:return None
    data=json.loads(REVIEWS.read_text())
    return source_sha256 if data.get('sources',{}).get(source_sha256,{}).get('status')=='APPROVED' else None


def require_photoreal(quality,registry=None):
    reject_incompatible(quality)
    registry=registry if registry is not None else json.loads(REVIEWS.read_text())
    digest=quality.get('sha256')
    receipt=registry.get('videos',{}).get(digest,{})
    if (not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest)
            or receipt.get('video_sha256')!=digest or receipt.get('status')!='APPROVED'
            or receipt.get('policy_version')!=16 or receipt.get('id')!=quality.get('photorealistic_review_id')
            or quality.get('visual_editorial_approved') is not True or not receipt.get('reviewer')
            or type(receipt.get('human_review')) is not bool or not receipt.get('sequence_artifact')
            or receipt.get('method') not in ('human_audiovisual_review','assistant_sequence_review_with_decoded_motion')
            or any(receipt.get('criteria',{}).get(k) is not True for k in CRITERIA)):
        raise ValueError('PHOTOREAL_FINAL_VISUAL_REVIEW_REQUIRED')
    hashes={s.get('sha256') for s in quality.get('visual_sources',[])}
    if not hashes or hashes!=set(receipt.get('source_sha256',[])):
        raise ValueError('PHOTOREAL_REVIEW_SOURCE_BINDING_MISMATCH')
    for sha in hashes:require_source(sha,registry)
    return receipt
