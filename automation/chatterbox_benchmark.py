"""Real CPU feasibility probe. Built-in conditioning is NOT a brand voice approval."""
import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

from chatterbox_v3 import acquire, NAME, MODEL, MODEL_REVISION

SCRIPT = [
    'Sua gaveta de cozinha prende toda vez que você tenta abrir?',
    'Antes de organizar, retire os utensílios e observe o espaço disponível.',
    'Separe as peças por uso e deixe as que você usa todos os dias na frente.',
    'Acomode cada grupo sem empilhar acima da altura da gaveta.',
    'Abra e feche devagar para conferir se nada ficou preso.',
    'Uma divisão simples facilita encontrar cada utensílio. Salve para organizar depois.',
    'Confira também se os cabos ficaram livres, sem impedir o movimento da gaveta ao abrir e fechar.',
    'Reserve outro espaço para as peças que não cabem nesse compartimento.'
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=Path, default=Path('tmp/mission14/cpu'))
    args = parser.parse_args(); args.folder.mkdir(parents=True, exist_ok=True)
    report = {'model':MODEL, 'revision':MODEL_REVISION, 'real_inference':False,
        'brand_voice_approved':False, 'female_identity_verified':False,
        'conditioning':'built-in conds.pt from MIT base checkpoint; no public demo audio downloaded',
        'additional_cost_brl':0, 'device':'cpu', 'publication_attempted':False}
    prior_path=args.folder/'report.json'
    prior=json.loads(prior_path.read_text()) if prior_path.exists() else {}
    start = time.monotonic()
    try:
        import torch
        import soundfile as sf
        import numpy as np
        torch.set_num_threads(2)
        print('Loading pinned CPU model',flush=True)
        model = acquire(args.folder/'cache')
        report['load_seconds'] = round(time.monotonic()-start,3)
        report['sample_rate'] = model.sr
        import random
        total = 0
        for i, text in enumerate(SCRIPT):
            old=prior.get('utterances',[])
            if i < len(old) and old[i]['text']==text and (args.folder/f'cpu-{i}.wav').exists():
                report.setdefault('utterances',[]).append(old[i])
                total+=old[i]['audio_seconds']
                report.update(real_inference=True,audio_seconds=total)
                continue
            random.seed(14); np.random.seed(14); torch.manual_seed(14)
            t = time.monotonic()
            wav = model.generate(text, language_id='pt', exaggeration=.5, cfg_weight=.5, temperature=.8)
            sf.write(args.folder/f'cpu-{i}.wav',wav.squeeze().cpu().numpy(),model.sr,subtype='PCM_16')
            seconds = wav.numel()/model.sr; total += seconds
            report.setdefault('utterances',[]).append({'text':text,'audio_seconds':seconds,'inference_seconds':round(time.monotonic()-t,3)})
            report.update(real_inference=True, audio_seconds=total)
            (args.folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
            print('CPU_UTTERANCE',i,report['utterances'][-1],flush=True)
        report['status']='TECHNICAL_AUDIO_GENERATED_NOT_IDENTITY_APPROVAL'
    except Exception as exc:
        report.update(status='CPU_PROBE_FAILED', error_type=type(exc).__name__,error=str(exc)[:1500])
        traceback.print_exc()
    finally:
        report.update(inference_seconds=sum(x['inference_seconds'] for x in report.get('utterances',[])),
            wall_seconds=round(time.monotonic()-start,3),peak_rss_mib=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1))
        (args.folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    return 0 if report['real_inference'] and len(report.get('utterances',[]))==len(SCRIPT) else 2

if __name__ == '__main__':
    raise SystemExit(main())
