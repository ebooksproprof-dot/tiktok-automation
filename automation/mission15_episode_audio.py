"""Candidate narration for a complete editorial episode; approval stays separate."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import time
import wave
from voice_candidate_review import reference

LINES=[
    'Copo guardado com água no fundo? Confira antes de fechar o armário.',
    'Depois de lavar, apoie cada copo em um escorredor adequado ao material.',
    'Deixe espaço entre as peças, sem equilibrar uma sobre a outra.',
    'Observe a borda e o fundo. Se houver gotas, espere secar completamente.',
    'Só então guarde os copos estáveis e fáceis de retirar. Salve para lembrar.'
]


def run(cache,private,output):
    import numpy as np
    import torch
    import soundfile as sf
    from chatterbox_v3 import acquire,NAME,digest
    from narration import finish_30
    torch.set_num_threads(2);folder=Path(output);folder.mkdir(parents=True,exist_ok=True)
    cfg,c,path=reference('unmute-lara',private)
    model=acquire(cache);model.prepare_conditionals(str(path),exaggeration=.5)
    position=0;parts=[];timings=[];receipts=[]
    for i,text in enumerate(LINES):
        assert len(text)<=300
        key=hashlib.sha256((NAME+c['sha256']+text+'seed15-cfg.5-temp.65-exp.5').encode()).hexdigest()
        target=folder/f'utterance-{i}.wav';meta=target.with_suffix('.json')
        if not target.exists() or not meta.exists() or json.loads(meta.read_text()).get('key')!=key:
            random.seed(15);np.random.seed(15);torch.manual_seed(15);start=time.monotonic()
            audio=model.generate(text,language_id='pt',temperature=.65,cfg_weight=.5,exaggeration=.5)
            sf.write(target,audio.squeeze().cpu().numpy(),model.sr,subtype='PCM_16')
            meta.write_text(json.dumps({'key':key,'text':text,'sha256':digest(target),'inference_seconds':time.monotonic()-start}))
        receipt=json.loads(meta.read_text())
        if digest(target)!=receipt['sha256']:raise ValueError('CANDIDATE_UTTERANCE_HASH_MISMATCH')
        with wave.open(str(target),'rb') as inp:rate=inp.getframerate();pcm=inp.readframes(inp.getnframes());duration=inp.getnframes()/rate
        parts.append(pcm);timings.append((position,position+duration,text));position+=duration;receipts.append(receipt)
        (folder/'progress.json').write_text(json.dumps({'utterances':receipts,'source_seconds':position},ensure_ascii=False,indent=2))
        print('CANDIDATE_UTTERANCE_SAVED',i,duration,flush=True)
    engine=type('ReviewEngine',(),{'name':NAME})()
    actual,timings=finish_30(folder,parts,rate,position,timings,engine)
    result={'candidate_id':c['id'],'engine':NAME,'reference_sha256':c['sha256'],'source_seconds':position,
            'duration':actual,'lines':LINES,'timings':timings,'utterances':receipts,
            'voice_perceptual_review_approved':False,'publication_approved':False,'rights':cfg['rights_evidence']}
    (folder/'audio-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (folder/'script.json').write_text(json.dumps(LINES,ensure_ascii=False))
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);p.add_argument('--private',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.cache,a.private,a.output)
