"""Two proof-only videos: B framing correction and C washbasin selection illustration.

B/C are proof IDs, NOT avatar formats. Both use real stock footage and narration.
No publishing, approval, queue/history reset or baseline rerender.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time
import render_daily as r
import visual_library as visual
from female_narration import KokoroFemaleEngine
from framing import product_frame_filter, product_geometry
from validation_v4 import checks

BATCH = [
    ('B','37325','secador-visivel',[
        'Aqui, o secador aparece em uso.',
        'Observe como a pessoa movimenta o aparelho enquanto separa os fios com a mão.',
        'Esta é uma cena ilustrativa, sem comparação de resultados.',
        'Para usar o seu secador, siga as orientações do fabricante.',
        'Salve este lembrete para a sua rotina.']),
    ('C','38115','cuba-medidas',[
        'Escolhendo uma cuba? Olhe além da aparência.',
        'Nesta cena, veja o espaço disponível para lavar as mãos.',
        'Antes de comprar, confira as medidas, o local de instalação e a compatibilidade com a torneira.',
        'A filmagem ilustra o uso e não comprova a qualidade de um modelo.',
        'Salve para comparar suas opções.']),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out=r.ROOT/'tmp/validation-v43'; assets=out/'assets'
    assets.mkdir(parents=True,exist_ok=True)
    tracked=[r.QUEUE,r.ROOT/'automation/state.json',r.ROOT/'automation/visual_history.json']
    before={str(p):digest(p) for p in tracked if p.exists()}
    items={x['provider_id']:x for x in json.loads((r.ROOT/'automation/media_inbox.json').read_text())['items']}
    r.ASSETS,r.OUT=assets,out
    engine=KokoroFemaleEngine(Path(os.environ.get('KOKORO_CACHE',str(out/'voice-assets'))))
    previous,reports=[],[]
    for proof_id,source_id,concept,lines in BATCH:
        item=items[source_id]
        r.SOURCE[source_id],r.PROVENANCE[source_id]=item['url'],item
        source=r.get_clip(source_id)
        meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
            '-show_entries','stream=width,height','-of','json',str(source)],text=True,timeout=30))['streams'][0]
        width,height=meta['width'],meta['height']
        start=time.monotonic()
        original_run=r.run
        def framed_run(args,**kwargs):
            args=list(args)
            if '-vf' in args and '-an' in args:
                pos=args.index('-vf'); args[pos]='-filter_complex'
                args[pos+1]=product_frame_filter(width,height)
            return original_run(args,**kwargs)
        r.run=framed_run
        try:
            path,quality=r.render((concept,[source_id],lines),engine,f'validation-v43-{proof_id}-{concept}')
        finally:
            r.run=original_run
        elapsed=time.monotonic()-start
        visual.check_sources(quality['visual_sources'],previous);previous.append(quality)
        quality.update(voice=engine.name,approved=False,editorial_approved=False,proof_only=True,publication_allowed=False,
            graphics_style='full-frame-blurred-background',crop_shifts_pixels=[0]*quality['rendered_shots'])
        qa=checks(path)
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(path),'-vf',
            f"fps=6/{quality['duration']:.6f},scale=270:480,tile=3x2",'-frames:v','1',str(path.with_suffix('.jpg'))],check=True,timeout=90)
        after={str(p):digest(p) for p in tracked if p.exists()}
        if after!=before: raise RuntimeError('PROOF_STATE_CHANGED')
        record=dict(id=proof_id,file=path.name,script=lines,source=item,quality=quality,technical_checks=qa,
            render_seconds=round(elapsed,3),peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
            resource_note='Linux maxima per process, not aggregate; render time includes narration but not model init/download',
            source_dimensions=[width,height],foreground_box=product_geometry(width,height),
            source_frame_retained_percent=100,previous_center_crop_width_retained_percent=min(100,100*(1080*height/1920)/width),
            comparison='Whole source visible, smaller foreground; no claim of improved voice, efficacy or engagement.',
            audio_perceptual_review='Not listened; no naturalness/pronunciation claim',
            format='C_no_avatar',avatar_present=False,cost_added=0,approved=False,published=False,state_unchanged=True,
            limitations=['Licensed stock people are not avatars.','Illustrative use; no efficacy or specific model quality claim.',
                'B reuses source from earlier proof; not new publishable content.','Proof render is not sustained daily operation.'])
        r.atomic_json(path.with_suffix('.json'),record);reports.append(record);r.atomic_json(out/'report.json',reports)
        print('PROOF_READY='+str(path),flush=True)
    print('PROOFS_COMPLETE=2;PUBLISHED=0;APPROVED=0;STATE_UNCHANGED=1',flush=True)


if __name__=='__main__': main()
