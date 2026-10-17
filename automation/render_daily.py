#!/usr/bin/env python3
"""Render a bounded, non-repeating editorial catalog. Never fabricate publishing consent."""
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import time
import urllib.request
import wave
from zoneinfo import ZoneInfo
from media_quality import validate
from content_catalog import TOPICS, script, category, fingerprint, rotate

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / ('tmp/daily/release-output' if os.getenv('MEDIA_STORAGE') == 'release' else 'public/rendered/daily')
QUEUE = ROOT / 'automation/queue.json'
ASSETS = ROOT / 'tmp/daily'
VERSION = 2
COMPOSITION_REVISION = 3
VOICE = 'pt_BR-faber-medium'
VOICE_SHA = '858555e3a064209c57088fe6bd70c4c3dc54d03eaa00c45d5ecaf43a33f95aa7'
MAX_MEDIA_BYTES = 200_000_000
SOURCE = {
 'piso': 'https://videos.pexels.com/video-files/9473227/9473227-uhd_2160_3840_24fps.mp4',
 'pia': 'https://videos.pexels.com/video-files/9472849/9472849-uhd_2160_3840_24fps.mp4',
 'espelho': 'https://videos.pexels.com/video-files/9462884/9462884-uhd_2160_3840_24fps.mp4',
}
# Finite catalog, deliberately no random recycling. Stock scenes are illustrative.
IDEAS = [
 ('panos-por-area', ['pia','piso'], ['Um pano para tudo?', 'Separe os panos por área.', 'Banheiro de um lado.', 'Outros ambientes do outro.', 'Assim, você evita levar', 'sujeira de um lugar', 'para outro. Depois do uso,', 'lave e deixe secar.', 'Use cores diferentes.', 'Fica fácil de identificar.', 'Salve para lembrar.']),
 ('ordem-da-faxina', ['espelho','pia','piso'], ['Limpou o chão primeiro?', 'Experimente mudar a ordem.', 'Comece pelas partes altas.', 'Depois, limpe as bancadas.', 'Deixe o piso por último.', 'Assim, a sujeira que cai', 'não estraga o trabalho', 'que você já terminou.', 'Siga de cima para baixo.', 'E termine uma área por vez.', 'Salve esta sequência.']),
 ('pano-lado-limpo', ['pia','espelho'], ['Seu pano já está sujo?', 'Não espalhe a sujeira.', 'Dobre para usar', 'uma parte limpa.', 'Troque o lado conforme limpa.', 'Quando todos estiverem sujos,', 'pegue outro pano limpo.', 'É um cuidado simples.', 'Na próxima superfície,', 'comece com o pano limpo.', 'Salve para a faxina.']),
 ('rotulo-primeiro', ['pia','piso'], ['Mais produto não é melhor.', 'Antes de limpar,', 'confira o rótulo.', 'Respeite a diluição indicada.', 'E confirme se o produto', 'serve para aquela superfície.', 'Cada acabamento pede cuidado.', 'Evite improvisar misturas.', 'Na dúvida, consulte', 'a orientação do fabricante.', 'Salve este lembrete.']),
 ('sem-misturas', ['pia','espelho'], ['Misturar não limpa melhor.', 'Use cada produto', 'conforme o rótulo.', 'Não improvise misturas', 'com produtos de limpeza.', 'Mantenha a área ventilada.', 'Guarde na embalagem original,', 'longe de crianças e animais.', 'Nunca use garrafas de bebida', 'para guardar esses produtos.', 'Compartilhe este cuidado.']),
 ('planejar-por-area', ['pia','piso'], ['Faxina sem saber por onde?', 'Escolha uma área pequena.', 'Separe o que vai usar.', 'Retire os objetos soltos.', 'Limpe uma superfície', 'antes de passar à próxima.', 'No final, guarde os materiais.', 'Uma tarefa de cada vez.', 'Não precisa começar', 'pela casa inteira de uma vez.', 'Salve para organizar.']),
]

IDEAS.extend(script(topic) for topic in TOPICS)


def run(args, **kwargs):
    return subprocess.run(args, check=True, timeout=240, **kwargs)


def atomic_json(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    temp.replace(path)


def get_clip(key):
    target = ASSETS / (key+'.mp4')
    if target.exists() and target.stat().st_size > 100000:
        return target
    for attempt in range(3):
        temp = target.with_suffix('.part')
        try:
            req = urllib.request.Request(SOURCE[key], headers={'User-Agent': 'CasaSemEsforco/2.0'})
            with urllib.request.urlopen(req, timeout=45) as response, temp.open('wb') as out:
                total = 0
                while chunk := response.read(1024*1024):
                    total += len(chunk)
                    if total > 250_000_000:
                        raise ValueError('Source exceeds download budget')
                    out.write(chunk)
            run(['ffprobe','-v','error',str(temp)], capture_output=True)
            temp.replace(target)
            return target
        except Exception:
            temp.unlink(missing_ok=True)
            if attempt == 2:
                raise RuntimeError('Licensed footage download failed: '+key) from None
            time.sleep(2**attempt)


def load_voice():
    # Disable optional external telemetry before ONNX initializes, including child downloads.
    os.environ["ORT_DISABLE_TELEMETRY"] = "1"
    from piper import PiperVoice
    model = ASSETS / (VOICE+'.onnx')
    if not model.exists() or not model.with_suffix(".onnx.json").exists():
        run(['python3','-m','piper.download_voices','--data-dir',str(ASSETS),VOICE])
    if hashlib.sha256(model.read_bytes()).hexdigest() != VOICE_SHA:
        raise ValueError('Voice model checksum mismatch')
    return PiperVoice.load(str(model))


def narration(voice, lines, folder):
    from piper import SynthesisConfig
    parts, timings, position = [], [], 0.0
    for i, line in enumerate(lines):
        path = folder / f'line-{i}.wav'
        with wave.open(str(path),'wb') as out:
            voice.synthesize_wav(line, out, syn_config=SynthesisConfig(length_scale=1.2))
        with wave.open(str(path),'rb') as inp:
            rate = inp.getframerate()
            pcm = inp.readframes(inp.getnframes())
            duration = inp.getnframes()/rate
        timings.append((position,position+duration,line))
        parts.append(pcm + bytes(int(rate*.08)*2))
        position += duration + .08
    if not 15 <= position <= 27.7:
        raise ValueError(f'Narration length out of range: {position:.2f}')
    with wave.open(str(folder/'voice.wav'),'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(rate)
        out.writeframes(b''.join(parts))
    return position, timings


def render(idea, voice, post_id):
    concept, keys, lines = idea
    folder = ASSETS / post_id
    folder.mkdir(exist_ok=True)
    duration, timings = narration(voice, lines, folder)
    clips = [get_clip(k) for k in keys]
    segments = []
    # Each shot follows the spoken instruction. Never show the floor as a high surface.
    shot_keys = {
        'panos-por-area': ['pia','pia','pia','piso','pia','piso','pia','pia','pia','pia','pia'],
        'ordem-da-faxina': ['piso','espelho','espelho','pia','piso','espelho','pia','piso','espelho','piso','piso'],
    }.get(concept)
    for i,(start,end,line) in enumerate(timings):
        length = (timings[i+1][0] if i+1 < len(timings) else duration) - start
        source = get_clip(shot_keys[i]) if shot_keys else clips[min(i * len(clips) // len(timings), len(clips)-1)]
        segment = folder/f'shot-{i}.mp4'
        # Moving footage only; no still zoom, no fabricated before/after.
        run(['ffmpeg','-v','error','-y','-stream_loop','-1','-ss',str((i//len(clips))*2),
             '-i',str(source),'-t',str(length),'-an','-vf',
             'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30',
             '-c:v','libx264','-threads','2','-preset','veryfast','-crf','23','-pix_fmt','yuv420p',str(segment)])
        segments.append(segment)
    (folder/'concat.txt').write_text(''.join(f"file '{p.name}'\n" for p in segments))
    filters = []
    font = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    for i,(start,end,line) in enumerate(timings):
        txt = folder/f'caption-{i}.txt'; txt.write_text(line, encoding='utf8')
        filters.append(f"drawtext=fontfile={font}:textfile={txt}:fontsize=58:fontcolor=white:box=1:boxcolor=black@0.70:boxborderw=18:x=(w-text_w)/2:y=1320:enable='between(t,{start:.3f},{end:.3f})'")
    label=folder/'label.txt';label.write_text('CENAS ILUSTRATIVAS',encoding='utf8')
    filters.append(f'drawtext=fontfile={font}:textfile={label}:fontsize=24:fontcolor=white:borderw=2:x=70:y=200')
    output = OUT / (post_id+'-v2.mp4')
    run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(folder/'concat.txt'),
         '-i',str(folder/'voice.wav'),'-vf',','.join(filters),'-af','loudnorm=I=-16:TP=-1.5:LRA=11',
         '-t',str(duration),'-c:v','libx264','-threads','2','-preset','veryfast','-crf','23','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','128k','-movflags','+faststart',str(output)])
    quality=validate(output)
    quality.update(concept=concept,source_urls=[SOURCE[k] for k in keys],
                   source_license='https://www.pexels.com/license/',voice=VOICE,render_version=VERSION,composition_revision=COMPOSITION_REVISION)
    atomic_json(output.with_suffix('.json'),quality)
    return output,quality


def future_slot(planned, queue, state, post_id, now=None):
    """Move only a new/unsubmitted render to an unoccupied Brazilian slot."""
    now = now or dt.datetime.now(dt.timezone.utc)
    occupied = set()
    for p in list(queue.get('posts', [])) + list(state.get('posts', {}).values()):
        value = p.get('scheduled_at')
        if not value or p.get('id') == post_id:
            continue
        if isinstance(value, dict):  # Persisted Metricool provider evidence.
            stamp = dt.datetime.fromisoformat(value['dateTime'].replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=ZoneInfo(value['timezone']))
        else:
            stamp = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValueError('Persisted schedule must include a timezone')
        occupied.add(stamp)
    candidate = planned
    for _ in range(62):
        if candidate >= now + dt.timedelta(minutes=10) and candidate not in occupied:
            return candidate
        if candidate.hour == 10:
            candidate = candidate.replace(hour=18)
        else:
            candidate = (candidate + dt.timedelta(days=1)).replace(hour=10)
    raise RuntimeError('SCHEDULE_BACKLOG: no free slot within 31 days')


def main():
    ASSETS.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    today=dt.datetime.now(ZoneInfo('America/Sao_Paulo')).date()
    queue=json.loads(QUEUE.read_text(encoding='utf8'))
    state=json.loads((ROOT/'automation/state.json').read_text(encoding='utf8'))
    available=rotate(IDEAS, queue, state)
    count=0; voice=None
    for slot,hour in enumerate([10,18],1):
        post_id=f'casasem-{today}-{slot}'
        old=next((p for p in queue['posts'] if p['id']==post_id),None)
        if post_id in state.get('posts',{}) or (old and (old.get('approved') or old.get('composition_revision')==COMPOSITION_REVISION)):
            continue
        media_total=sum(p.stat().st_size for p in (ROOT/'public/rendered').rglob('*.mp4'))
        release_storage = os.getenv('MEDIA_STORAGE') == 'release'
        if not release_storage and media_total+20_000_000>MAX_MEDIA_BYTES:
            raise RuntimeError('STORAGE_BUDGET: stop before adding media beyond 200 MB; no paid storage')
        if old and old.get('concept'):
            repair = next((idea for idea in IDEAS if idea[0] == old['concept']), None)
            if repair and repair not in available:
                available.insert(0, repair)
        if not available:
            raise RuntimeError('CATALOG_EXHAUSTED: reviewed original scripts needed; refusing repeated videos')
        voice=voice or load_voice()
        # Try another licensed composition if an asset/quality check fails.
        failures=[]
        rendered = False
        for idea in list(available):
            try:
                output,quality=render(idea,voice,post_id)
                available.remove(idea)
                rendered = True
                break
            except Exception as exc:
                failures.append(type(exc).__name__+': '+str(exc))
                if len(failures)>=2: raise RuntimeError('Render failed after two compositions: '+'; '.join(failures)) from None
        if not rendered:
            raise RuntimeError("Render failed; no validated output: " + "; ".join(failures))
        scheduled=dt.datetime.combine(today,dt.time(hour),ZoneInfo('America/Sao_Paulo'))
        original_scheduled = scheduled
        scheduled = future_slot(scheduled, queue, state, post_id)
        video_url = f'https://ebooksproprof-dot.github.io/tiktok-automation/public/rendered/daily/{output.name}'
        if release_storage:
            from release_media import publish
            video_url = publish(output, post_id, quality)
        entry=dict(id=post_id,video_url=video_url,
                   title=' '.join(idea[2])+' #CasaSemEsforco #OrganizacaoDaCasa',
                   scheduled_at=scheduled.astimezone(dt.timezone.utc).isoformat(),
                   approved=False,consented_at=None,quality=quality,concept=idea[0],
                   category=category(idea[0]),script_lines=idea[2],script_sha256=fingerprint(idea[2]),render_version=VERSION,composition_revision=COMPOSITION_REVISION,
                   publishing_status='AWAITING_EDITORIAL_REVIEW_AND_VALID_PUBLISHING_ROUTE',
                   media_storage='release' if release_storage else 'git')
        if scheduled != original_scheduled:
            entry.update(original_scheduled_at=original_scheduled.isoformat(),
                         schedule_recovery='MISSED_OR_OCCUPIED_SLOT_MOVED_BEFORE_SUBMISSION')
        if old: queue['posts'][queue['posts'].index(old)]=entry
        else: queue['posts'].append(entry)
        atomic_json(QUEUE,queue); count+=1
        print(f'RENDERED {post_id}: {quality["duration"]:.2f}s; technical pass; NOT PUBLISHED',flush=True)
    print(f'NEW_VIDEO_COUNT={count}; PUBLICATION_CONFIRMED=false',flush=True)


if __name__=='__main__':
    main()
