"""Explicit, bounded 4.0 A/B proofs. Never writes queue/state or approves publication.

Source crops were inspected on 2026-10-22. These are illustrative routines, not
product demonstrations. Only this manually selected batch is supported; no
keyword-based editorial approval. FFmpeg/Piper production defaults are unchanged.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import render_daily as r
import visual_library as visual
from media_quality import validate

BATCH = [
    ('34818', 'sabonete-com-lugar', 'UM LUGAR PARA O SABONETE', [
        'Seu sabonete fica escorregando na pia?',
        'Escolha um apoio estável e fácil de alcançar.',
        'Deixe livre a área que você usa para lavar as mãos.',
        'Ao terminar, devolva o sabonete ao apoio.',
        'Confira se precisa limpar e secar esse espaço.',
        'Salve para ajustar sua rotina.']),
    ('140587', 'livros-devolver-por-grupo', 'ENCONTRE E DEVOLVA', [
        'Encontrou o livro, mas não sabe onde devolver?',
        'Organize sua estante em grupos que façam sentido para você.',
        'Pode ser por assunto ou por autor.',
        'Mantenha as lombadas visíveis e a mesma regra em cada grupo.',
        'Depois da leitura, devolva ao lugar escolhido.',
        'Salve esta ideia.']),
    ('37325', 'secador-guardar-depois', 'TERMINOU DE USAR?', [
        'Terminou de usar o secador?',
        'Desligue da tomada e espere esfriar antes de guardar.',
        'Escolha um lugar seco, longe da água.',
        'Deixe os acessórios juntos, sem apertar o cabo ao redor do aparelho.',
        'Confira também as orientações do fabricante.',
        'Salve para organizar seus acessórios.']),
]
CONTEXT = {
    '34818': 'Close-up of hands washing with a bar of soap; central crop preserves tap and soap. Does not show a soap holder or organization steps.',
    '140587': 'People reading beside bookshop shelves. Illustrates books and reading, not a home organization demonstration.',
    '37325': 'Person drying hair; central crop shows hair and parts of dryer. Illustrates use only, not storage or unplugging steps.',
}


def checks(path):
    result = subprocess.run(['ffmpeg', '-hide_banner', '-v', 'info', '-i', str(path),
        '-vf', 'blackdetect=d=0.3:pix_th=0.10:pic_th=0.98',
        '-af', 'silencedetect=n=-45dB:d=0.8', '-f', 'null', '-'],
        capture_output=True, text=True, timeout=180, check=True)
    black = len(re.findall(r'black_start:', result.stderr))
    silence = len(re.findall(r'silence_start:', result.stderr))
    if black or silence:
        raise ValueError(f'PROOF_FAILED: black={black};silence={silence}')
    return dict(full_decode=True, black_intervals_ge_0_3s=black,
                silence_intervals_ge_0_8s= silence,
                thresholds=dict(black_pixel=.10, black_picture=.98, silence_db=-45))


def main():
    out = r.ROOT/'tmp/validation-v4'
    assets = out/'assets'
    out.mkdir(parents=True, exist_ok=True); assets.mkdir(exist_ok=True)
    original_queue = hashlib.sha256(r.QUEUE.read_bytes()).hexdigest()
    state_path = r.ROOT/'automation/state.json'
    original_state = hashlib.sha256(state_path.read_bytes()).hexdigest()
    inbox = json.loads((r.ROOT/'automation/media_inbox.json').read_text())
    by_id = {item['provider_id']: item for item in inbox['items']}
    r.ASSETS = assets
    r.OUT = out
    engine = r.load_voice()
    previous, reports = [], []
    for source_id, concept, headline, lines in BATCH:
        item = by_id[source_id]
        # Bound the proof to measured, licensed inbox bytes. No provider API calls.
        item = dict(item, id='pixabay-'+source_id, context=CONTEXT[source_id])
        r.SOURCE[source_id] = item['url']; r.PROVENANCE[source_id] = item
        source = assets/(source_id+'.mp4')
        if not source.exists():
            subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                '--max-time', '120', '--max-filesize', '250000000',
                '-A', 'CasaSemEsforco/4.0', item['url'], '-o', str(source)], check=True, timeout=130)
        r.verify_source(source_id, source)
        started = time.monotonic()
        baseline, base_quality = r.render((concept, [source_id], lines), engine,
                                         'validation-v4-'+concept+'-base')
        base_seconds = time.monotonic()-started
        visual.check_sources(base_quality['visual_sources'], previous)
        previous.append(base_quality)
        duration = base_quality['duration']
        title = out/(concept+'-headline.txt'); title.write_text(headline, encoding='utf8')
        # Original compact top strap; caption at y=1320 stays unobstructed.
        font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        vf = (f'drawbox=x=54:y=265:w=972:h=114:color=black@0.70:t=fill:enable=lt(t\\,3),'
              f'drawtext=fontfile={font}:textfile={title}:fontsize=43:fontcolor=0x8EF0D0:'
              f'x=(w-text_w)/2:y=300:enable=lt(t\\,3),'
              'drawbox=x=54:y=1480:w=972:h=8:color=white@0.28:t=fill,'
              f'drawbox=x=54:y=1480:w=972:h=8:color=0x8EF0D0:t=fill:enable=gte(t\\,{duration*.75:.4f})')
        enhanced = out/('validation-v4-'+concept+'.mp4')
        start = time.monotonic()
        original_run = r.run
        shot_index = [0]
        base_crop = 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30'
        def variant_run(args, **kwargs):
            args = list(args)
            if '-vf' in args:
                index = args.index('-vf') + 1
                if args[index] == base_crop:
                    # Horizontal crop shift uses source pixels; no zoom/upscale.
                    shift = -60 if shot_index[0] % 2 == 0 else 60
                    args[index] = ('scale=1080:1920:force_original_aspect_ratio=increase,'
                                   f'crop=1080:1920:x=(iw-ow)/2+{shift}:y=(ih-oh)/2,fps=30')
                    shot_index[0] += 1
                elif 'drawtext=' in args[index]:
                    args[index] += ',' + vf
            return original_run(args, **kwargs)
        r.run = variant_run
        try:
            enhanced_raw, _ = r.render((concept, [source_id], lines), engine,
                                       'validation-v4-'+concept+'-variant')
        finally:
            r.run = original_run
        enhanced_raw.replace(enhanced)
        enhanced_seconds = time.monotonic()-start
        quality = validate(enhanced)
        quality.update({k:v for k,v in base_quality.items() if k.startswith('visual_') or k in
                        ('source_urls','source_licenses','required_public_credits','voice')})
        quality.update(editorial_approved=False, approved=False, proof_only=True)
        tech = checks(enhanced)
        base_tech = checks(baseline)
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(enhanced),'-vf',
            f'fps=6/{duration:.6f},scale=270:480,tile=3x2','-frames:v','1',str(enhanced.with_suffix('.jpg'))],check=True,timeout=90)
        record = dict(concept=concept, file=enhanced.name, baseline_file=baseline.name,
            source_context=CONTEXT[source_id], script=lines, source=item,
            quality=quality, technical_checks=tech, baseline_quality=base_quality,
            baseline_technical_checks=base_tech,
            comparison=dict(baseline_render_seconds=round(base_seconds,2),
                variant_render_seconds=round(enhanced_seconds,2),
                first_three_second_headline=True, final_quarter_visual_marker=True,
                voice_engine_unchanged=True, source_footage_unchanged=True,
                alternating_horizontal_crop_pixels=120, rendered_shots=shot_index[0],
                retention_improvement_measured=False, naturalness_improvement_measured=False,
                note='Controlled crop/graphics A/B; no claimed narration-naturalness or audience-retention gain.'),
            published=False, approved=False)
        reports.append(record)
        r.atomic_json(out/'report.json',reports)
        print('VALIDATION_COMPLETE='+enhanced.name,flush=True)
    if hashlib.sha256(r.QUEUE.read_bytes()).hexdigest()!=original_queue or hashlib.sha256(state_path.read_bytes()).hexdigest()!=original_state:
        raise RuntimeError('QUEUE_OR_STATE_CHANGED_DURING_PROOF')
    print('VALIDATION_BATCH_COMPLETE=3;PUBLISHED=0;APPROVED=0',flush=True)


if __name__ == '__main__':
    main()
