"""Apply an explicit owner's listening receipt, never an automatic ASR approval."""
import hashlib
import json
from pathlib import Path


def profile_digest(profile):return hashlib.sha256(json.dumps(profile,sort_keys=True).encode()).hexdigest()


def approve(data,receipt,candidates):
    if (receipt.get('actor')!='ebooksproprof-dot' or receipt.get('source')!='owner_workflow_dispatch'
            or not receipt.get('run_id') or receipt.get('approved') is not True):
        raise ValueError('EXPLICIT_OWNER_LISTENING_APPROVAL_REQUIRED')
    candidate=next(c for c in candidates['candidates'] if c['id']==data['selected_candidate_id'])
    if (receipt.get('candidate_id')!=candidate['id'] or receipt.get('reference_sha256')!=candidate['sha256']
            or data.get('reference_sha256')!=candidate['sha256'] or candidate['commercial_synthesis_authorized'] is not True
            or data.get('commercial_synthesis_authorized') is not True):
        raise ValueError('VOICE_APPROVAL_REFERENCE_OR_RIGHTS_MISMATCH')
    sample=Path(__file__).with_name('mission15-evidence')/(candidate['id']+'.wav')
    if receipt.get('sample_sha256')!=hashlib.sha256(sample.read_bytes()).hexdigest():
        raise ValueError('LISTENED_SAMPLE_HASH_MISMATCH')
    result=dict(data,status='APPROVED',gender='female',locale='pt-BR',perceptual_review_approved=True)
    from chatterbox_v3 import NAME
    result['review_receipt']={**receipt,'engine_name':NAME,'inference_sha256':profile_digest(data['inference']),
        'scope':'Female Brazilian identity, naturalness and clarity; episode content still independently validated'}
    return result


if __name__=='__main__':
    import os
    root=Path(__file__).parent;data=json.loads((root/'voice_identity.json').read_text())
    sample=root/'mission15-evidence/unmute-lara.wav'
    receipt={'actor':os.environ['GITHUB_ACTOR'],'source':'owner_workflow_dispatch','run_id':os.environ['GITHUB_RUN_ID'],
        'approved':os.getenv('APPROVE_IDENTITY')=='true','candidate_id':'unmute-lara',
        'reference_sha256':os.environ['REVIEWED_REFERENCE_SHA256'],'sample_sha256':hashlib.sha256(sample.read_bytes()).hexdigest()}
    result=approve(data,receipt,json.loads((root/'voice_candidates.json').read_text()))
    temporary=root/'voice_identity.json.partial';temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');temporary.replace(root/'voice_identity.json')
