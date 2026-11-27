"""Generate licensed candidate samples for listening. Never approves a voice."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
import wave

CANDIDATES=Path(__file__).with_name('voice_candidates.json')
TEXT='Uma rotina simples ajuda a cuidar da casa. Separe os utensílios por uso e deixe espaço para retirar cada peça com facilidade.'


def reference(candidate_id, folder):
    import urllib.request
    from chatterbox_v3 import digest
    cfg=json.loads(CANDIDATES.read_text());c=next(c for c in cfg['candidates'] if c['id']==candidate_id)
    if c['commercial_synthesis_authorized'] is not True or cfg['license']!='CC0-1.0' or len(cfg['rights_evidence'])<2:
        raise ValueError('CANDIDATE_REFERENCE_RIGHTS_NOT_VERIFIED')
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);folder.chmod(0o700)
    path=folder/(candidate_id+'.wav')
    if not path.exists():
        url=f"https://huggingface.co/{cfg['source_repository']}/resolve/{cfg['source_revision']}/{c['path']}"
        data=urllib.request.urlopen(url,timeout=30).read(2_000_001)
        if hashlib.sha256(data).hexdigest()!=c['sha256']:raise ValueError('REFERENCE_HASH_MISMATCH')
        path.write_bytes(data);path.chmod(0o600)
    if digest(path)!=c['sha256']:raise ValueError('REFERENCE_HASH_MISMATCH')
    with wave.open(str(path),'rb') as w:
        if w.getnchannels()!=1 or w.getsampwidth()!=2 or not 5<=w.getnframes()/w.getframerate()<=12:
            raise ValueError('REFERENCE_PCM16_MONO_DURATION_REQUIRED')
    return cfg,c,path


def generate(ids,cache,private,output,text=TEXT,temperature=.65):
    import numpy as np
    import soundfile as sf
    import torch
    from chatterbox_v3 import acquire,NAME,digest
    torch.set_num_threads(2)
    model=acquire(cache);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    results=[]
    for candidate_id in ids:
        cfg,c,path=reference(candidate_id,private)
        model.prepare_conditionals(str(path),exaggeration=.5)
        random.seed(15);np.random.seed(15);torch.manual_seed(15)
        start=time.monotonic()
        wav=model.generate(text,language_id='pt',exaggeration=.5,cfg_weight=.5,temperature=temperature)
        target=output/(candidate_id+'.wav');sf.write(target,wav.squeeze().cpu().numpy(),model.sr,subtype='PCM_16')
        result={'candidate_id':candidate_id,'reference_sha256':c['sha256'],'audio_sha256':digest(target),
            'engine':NAME,'text':text,'seconds':wav.numel()/model.sr,'inference_seconds':time.monotonic()-start,
            'temperature':temperature,'cfg_weight':.5,'seed':15,'perceptual_review_approved':False,
            'publication_approved':False,'rights_evidence':cfg['rights_evidence']}
        target.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');results.append(result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',action='append',required=True);p.add_argument('--text',default=TEXT)
    p.add_argument('--cache',type=Path,required=True);p.add_argument('--private',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();generate(args.candidate,args.cache,args.private,args.output,args.text)
