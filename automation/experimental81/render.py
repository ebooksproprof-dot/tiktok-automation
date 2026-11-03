"""Experimental 30-second composer. Never edits a production queue or publishes.

Inputs carry explicit provenance. Without usable AI this produces REFERENCE_ONLY,
not a purported hybrid. Repeated files/overlapping source intervals are forbidden.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import wave

AUTOMATION = Path(__file__).resolve().parents[1]
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

PROFILES = {'AI_ONLY': (30, 0), 'A': (10, 20), 'B': (15, 15), 'C': (5, 25), 'REFERENCE_ONLY': (0, 30)}
SCRIPT = [
    'Sua casa vive desorganizada? Comece por uma pequena área.',
    'No armário, mantenha os potes que você usa ao alcance das mãos.',
    'Antes de guardar roupas, espere as peças secarem completamente.',
    'Dobre cada peça e organize sem apertar demais a caixa.',
    'Separe poucos minutos para devolver cada coisa ao seu lugar.',
    'Uma rotina simples ajuda a manter tudo organizado. Salve esta dica.'
]
DEMO_KEYS = ['pexels-8580892-full', 'pixabay-165820-full', 'pexels-8938252-full']


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def call(args, timeout=180):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('Media process failed: ' + Path(args[0]).name)
    return result.stdout


def probe(path):
    return json.loads(call(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], 30))


def inspect_clips(clips):
    seen, result = set(), []
    for entry in clips:
        item = dict(entry)
        path = Path(item['path']).resolve()
        if not path.is_file() or path.stat().st_size > 250_000_000:
            raise ValueError('Source missing or over 250 MB')
        digest = sha(path)
        if item.get('sha256') != digest or digest in seen:
            raise ValueError('Source hash mismatch or duplicate file')
        seen.add(digest)
        if item.get('kind') not in ('ai', 'real', 'reference'):
            raise ValueError('Explicit media origin required')
        if item['kind'] == 'ai':
            if not item.get('model') or not item.get('generation_evidence') or item.get('visual_review_passed') is not True:
                raise ValueError('AI model, generation evidence and visual review required')
        if not item.get('source_url') or not item.get('license_url'):
            raise ValueError('Source and license provenance required')
        meta = probe(path)
        video = next((x for x in meta['streams'] if x['codec_type'] == 'video'), None)
        duration = float(meta['format']['duration'])
        if not video or not math.isfinite(duration) or duration <= 0:
            raise ValueError('Invalid video source')
        offset = item.get('source_offset', 0.0)
        if not isinstance(offset, (int,float)) or not math.isfinite(offset) or not 0 <= offset < duration:
            raise ValueError('Invalid source offset')
        item.update(path=str(path), duration=duration-offset, source_offset=offset, width=video['width'], height=video['height'])
        result.append(item)
    return result


def select_profile(clips, requested='auto'):
    totals = {'ai': 0.0, 'real': 0.0}
    for clip in clips:
        totals['ai' if clip['kind'] == 'ai' else 'real'] += clip['duration']
    options = ['AI_ONLY', 'A', 'B', 'C', 'REFERENCE_ONLY'] if requested == 'auto' else [requested]
    for name in options:
        if name not in PROFILES:
            raise ValueError('Unknown mix configuration')
        ai, real = PROFILES[name]
        if totals['ai'] + 1e-6 >= ai and totals['real'] + 1e-6 >= real:
            return name
    raise ValueError('Insufficient unique clip duration; no looping fallback')


def plan(clips, profile):
    ai_seconds, real_seconds = PROFILES[profile]
    remaining = {'ai': float(ai_seconds), 'real': float(real_seconds)}
    used = [0.0] * len(clips)
    shots = []
    # Use bounded non-overlapping shots, rotate sources within a category.
    indices = {'ai': [i for i,c in enumerate(clips) if c['kind'] == 'ai'],
               'real': [i for i,c in enumerate(clips) if c['kind'] != 'ai']}
    turn = {'ai': 0, 'real': 0}
    while sum(remaining.values()) > 1e-6:
        category = 'ai' if remaining['ai'] > 1e-6 else 'real'
        choices = indices[category]
        if not choices:
            raise ValueError('No source in required category')
        selected = None
        for offset in range(len(choices)):
            position = (turn[category] + offset) % len(choices)
            index = choices[position]
            capacity = clips[index]['duration'] - used[index]
            if capacity > .05:
                selected = index
                turn[category] = (position + 1) % len(choices)
                break
        if selected is None:
            raise ValueError('Insufficient non-repeated footage')
        length = min(5.0, remaining[category], clips[selected]['duration'] - used[selected])
        shots.append({'source_index': selected, 'start': round(clips[selected].get('source_offset',0) + used[selected], 6), 'duration': round(length, 6)})
        used[selected] += length
        remaining[category] -= length
    if abs(sum(s['duration'] for s in shots) - 30) > .001:
        raise ValueError('Plan must total 30 seconds')
    return shots


def synthesize(folder, lines=SCRIPT):
    """Existing licensed Kokoro voice, measured sentence boundaries, modest tempo."""
    from narration import load_engine
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    engine = load_engine(folder/'voice-cache', 'kokoro-female')
    pcm_parts, segments, position, expected = [], [], 0.0, None
    for index, sentence in enumerate(lines):
        path = folder/f'utterance-{index}.wav'
        engine.speak(sentence, path)
        with wave.open(str(path), 'rb') as inp:
            shape = (inp.getnchannels(), inp.getsampwidth(), inp.getframerate())
            if shape[:2] != (1, 2) or (expected is not None and shape != expected):
                raise ValueError('Narration PCM shape changed')
            expected = shape
            rate = shape[2]
            data = inp.readframes(inp.getnframes())
            duration = len(data)/2/rate
        # Caption spans exactly the measured utterance; no word alignment claimed.
        segments.append([position, position + duration, sentence])
        gap = .08 if index < len(lines)-1 else 0
        pcm_parts.append(data + bytes(int(rate*gap)*2))
        position += duration+gap
    tempo = position / 30
    if not .75 <= tempo <= 1.35:
        raise ValueError(f'Narration requires excessive speed change ({tempo:.3f}); edit script')
    source = folder/'narration-source.wav'
    with wave.open(str(source), 'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(rate)
        out.writeframes(b''.join(pcm_parts))
    target = folder/'narration.wav'
    call(['ffmpeg','-v','error','-y','-i',str(source),'-af',f'atempo={tempo:.9f},loudnorm=I=-16:TP=-1.5:LRA=9,apad',
          '-t','30','-ar','48000','-ac','1',str(target)])
    return {'path': str(target.resolve()), 'sha256': sha(target), 'engine': engine.name, 'language': 'pt-BR',
            'tempo': tempo, 'timing_method': 'Measured utterance boundaries; sentence-level synchronization, not word-level forced alignment',
            'timings': [[start/tempo, min(30,end/tempo), text] for start,end,text in segments]}


def fetch_demo_sources(folder):
    from catalog_extension import PROVENANCE
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    result = []
    for key in DEMO_KEYS:
        origin = PROVENANCE[key]
        path = folder/(key+'.mp4')
        if not path.exists():
            temporary = path.with_suffix('.part')
            try:
                with urllib.request.urlopen(origin['url'],timeout=45) as response, temporary.open('wb') as out:
                    count = 0
                    while chunk := response.read(1024*1024):
                        count += len(chunk)
                        if count > 250_000_000:
                            raise ValueError('Source download size exceeded')
                        out.write(chunk)
                if sha(temporary) != origin['sha256']:
                    raise ValueError('Reviewed source hash changed')
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
        result.append({'path': str(path.resolve()), 'kind': 'real', 'sha256': origin['sha256'],
                       'source_url': origin['source_page'], 'download_url': origin['url'],
                       'license_url': origin['license_url'], 'author': origin['author'], 'context': origin['context']})
    return result



def write_srt(path, timings):
    def timestamp(value):
        ms = round(value*1000)
        hours, ms = divmod(ms,3600000); minutes,ms=divmod(ms,60000);seconds,ms=divmod(ms,1000)
        return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'
    rows = [f'{i+1}\n{timestamp(start)} --> {timestamp(end)}\n{text}\n' for i,(start,end,text) in enumerate(timings)]
    Path(path).write_text('\n'.join(rows),encoding='utf8')


def input_identity(manifest, profile):
    identity_manifest = json.loads(json.dumps(manifest))
    for source in identity_manifest['clips']:
        source.pop('path', None)
    identity_manifest['narration'].pop('path', None)
    return hashlib.sha256(json.dumps({'manifest':identity_manifest,'profile':profile,'renderer':1},sort_keys=True).encode()).hexdigest()

def compose(manifest, folder, requested='auto'):
    import fcntl
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/'.render.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _compose_locked(manifest, folder, requested)


def _compose_locked(manifest, folder, requested='auto'):
    """Render one experimental output; reuse a verified matching output on rerun."""
    from experimental81.quality import validate
    from caption_layout import filters
    from framing import product_frame_filter
    if manifest.get('experimental_only') is not True:
        raise ValueError('Explicit experimental-only manifest required')
    folder = Path(folder).resolve(); folder.mkdir(parents=True, exist_ok=True)
    clips = inspect_clips(manifest['clips'])
    narration = manifest['narration']
    audio = Path(narration['path']).resolve()
    if narration.get('language') != 'pt-BR' or sha(audio) != narration['sha256']:
        raise ValueError('PT-BR narration and matching hash required')
    timings = narration['timings']
    if not timings or timings[0][0] > .2 or timings[-1][1] < 29:
        raise ValueError('Narration captions must cover the full video')
    profile = select_profile(clips, requested)
    shots = plan(clips, profile)
    identity = input_identity(manifest, profile)
    output = folder/('experimental81-'+identity[:16]+'.mp4')
    record_path = output.with_suffix('.json')
    if output.exists() or record_path.exists():
        if not output.exists() or not record_path.exists():
            raise ValueError('Incomplete previous render; inspect before rerender')
        record = json.loads(record_path.read_text())
        if record.get('input_sha256') != identity or record['quality']['sha256'] != sha(output):
            raise ValueError('Existing render identity/hash mismatch')
        validate(output)
        return record
    start = time.monotonic()
    inputs = []
    graph = []
    for number, shot in enumerate(shots):
        clip = clips[shot['source_index']]
        inputs.extend(['-ss',str(shot['start']),'-t',str(shot['duration']),'-i',clip['path']])
        if abs(clip['width']/clip['height'] - 9/16) < .04:
            graph.append(f'[{number}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,setpts=PTS-STARTPTS[v{number}]')
        else:
            frame = product_frame_filter(clip['width'],clip['height']).replace('[0:v]',f'[{number}:v]')
            for label_name in ('background','foreground','blur','full'):
                frame = frame.replace('['+label_name+']',f'[{label_name}{number}]')
            graph.append(frame+f',setpts=PTS-STARTPTS[v{number}]')
    graph.append(''.join(f'[v{i}]' for i in range(len(shots))) + f'concat=n={len(shots)}:v=1:a=0[sequence]')
    caption_filters = filters(folder, timings)
    # Disclosure prevents reference footage being mistaken for generated IA.
    label = folder/'origin-label.txt'
    label.write_text('CONTEÚDO GERADO POR IA' if profile == 'AI_ONLY' else
                     'ESTUDO • SEM PUBLICAÇÃO' if profile != 'REFERENCE_ONLY' else
                     'ESTUDO • FILMAGENS REAIS • 0 IA')
    caption_filters.append(f'drawtext=textfile={label}:expansion=none:fontsize=25:fontcolor=white:box=1:boxcolor=black@0.6:x=40:y=100')
    temporary = output.with_name(output.stem+'.partial.mp4')
    try:
        graph.append('[sequence]'+','.join(caption_filters)+'[final]')
        call(['ffmpeg','-v','error','-nostdin','-y','-filter_complex_threads','1',*inputs,'-i',str(audio),
              '-filter_complex',';'.join(graph),'-map','[final]','-map',f'{len(shots)}:a:0','-t','30','-c:v','libx264',
              '-preset','veryfast','-crf','22','-maxrate','3M','-bufsize','6M','-threads','2','-pix_fmt','yuv420p',
              '-c:a','aac','-b:a','128k','-ar','48000','-movflags','+faststart',str(temporary)],240)
        quality = validate(temporary)
        record = {'schema_version':1,'experimental_only':True,'publication_enabled':False,'approved':False,
            'input_sha256':identity,'profile':profile,'ai_seconds':PROFILES[profile][0],'real_seconds':PROFILES[profile][1],
            'video_path':str(output),'quality':quality,'sources':clips,'shots':shots,'narration':narration,
            'script':manifest.get('script'), 'render_seconds':round(time.monotonic()-start,3),
            'created_at':datetime.now(timezone.utc).isoformat(),
            'creative_quality':'UNREVIEWED; technical validation is not visual/editorial approval'}
        temporary.replace(output)
        write_srt(output.with_suffix('.srt'), timings)
        record_temp = record_path.with_suffix('.json.partial')
        record_temp.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
        record_temp.replace(record_path)
        return record
    finally:
        temporary.unlink(missing_ok=True)


def demo(folder):
    folder = Path(folder).resolve(); folder.mkdir(parents=True,exist_ok=True)
    if (Path(__file__).parent/'fixtures/wan-C-631e17ed61f5a53a.mp4').exists():
        return reference_demo(folder)
    clips = fetch_demo_sources(folder/'sources')
    narration = synthesize(folder/'speech')
    manifest = {'experimental_only':True,'script':SCRIPT,'clips':clips,'narration':narration}
    (folder/'input-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return compose(manifest,folder/'render')



def reference_demo(folder):
    """Honest contingency from three different existing licensed reference clips.

    Original renders are reused only as experimental inputs, never new stock.
    Crop removes this project's old text wrapper, not source watermarks.
    """
    folder = Path(folder).resolve(); folder.mkdir(parents=True, exist_ok=True)
    files = [('01_piso_opaco.mp4','9473227'),('02_pia_limpa.mp4','9472849'),('03_espelho_limpo.mp4','9462884')]
    clips = []
    for name, provider_id in files:
        source = AUTOMATION.parent/'public/rendered'/name
        target = folder/('reference-'+name)
        if not target.exists():
            call(['ffmpeg','-v','error','-y','-i',str(source),'-an','-vf','crop=630:1090:224:560',
                  '-c:v','libx264','-preset','veryfast','-crf','19','-threads','2','-pix_fmt','yuv420p',str(target)])
        clips.append({'path':str(target),'sha256':sha(target),'kind':'reference',
            'source_url':'https://www.pexels.com/video/'+provider_id+'/',
            'license_url':'https://www.pexels.com/license/',
            'origin_repository_file':str(source.relative_to(AUTOMATION.parent)),
            'origin_sha256':sha(source),'context':'Previously rendered licensed reference; not new footage or AI. Existing wrapper cropped.'})
    lines = [
        'Quer facilitar a faxina? Organize uma pequena tarefa por vez.',
        'Separe os materiais antes de começar a limpar cada ambiente.',
        'Use o produto indicado no rótulo para aquela superfície.',
        'Troque o lado do pano quando ele estiver sujo.',
        'Deixe o piso por último e guarde os materiais depois do uso.',
        'Faça uma área por vez, sem pressa. Salve para lembrar depois.'
    ]
    narration = synthesize(folder/'speech', lines)
    fixture = Path(__file__).parent/'fixtures/wan-C-631e17ed61f5a53a.mp4'
    profile = 'REFERENCE_ONLY'
    disclosure = 'REFERENCE_ONLY; reused licensed project footage; zero generated AI frames; not approved for publication'
    if fixture.exists():
        expected = '631e17ed61f5a53a2c07b248be01992ce9ff7704efdda2ecbf40498db0ee0239'
        if sha(fixture) != expected:
            raise ValueError('AI fixture hash mismatch')
        evidence_path = Path(__file__).parent/'evidence/wan-attempt-C.json'
        evidence = json.loads(evidence_path.read_text())
        if (evidence.get('visual_review') or {}).get('experimental_use_approved') is not True:
            raise ValueError('AI fixture lacks explicit experimental visual review')
        clips[1]['source_offset'] = 5
        clips.append({'path':str(fixture.resolve()),'sha256':expected,'kind':'ai',
            'model':'Wan-AI/Wan2.2-I2V-A14B-Diffusers + Lightx2v LoRA',
            'generation_evidence':'automation/experimental81/evidence/wan-attempt-C.json',
            'visual_review_passed':True,'professional_quality':False,
            'source_url':'https://huggingface.co/spaces/zerogpu-aoti/wan2-2-fp8da-aoti-faster',
            'license_url':'https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B-Diffusers',
            'license_status':'derivative_review_pending'})
        profile = 'C'
        disclosure = 'C:5seconds real AI+25seconds reused licensed reference footage; experimental only, derivative commercial clearance pending'
    manifest = {'experimental_only':True,'script':lines,'clips':clips,'narration':narration,'disclosure':disclosure}
    (folder/'input-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return compose(manifest, folder/'render', profile)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--demo',action='store_true')
    parser.add_argument('--reference-demo',action='store_true')
    parser.add_argument('--profile',default='auto',choices=['auto',*PROFILES])
    args = parser.parse_args()
    if sum([bool(args.manifest), args.demo, args.reference_demo]) != 1:
        parser.error('Choose exactly one of --manifest, --demo or --reference-demo')
    result = reference_demo(args.output) if args.reference_demo else demo(args.output) if args.demo else compose(json.loads(args.manifest.read_text()),args.output,args.profile)
    print(json.dumps({key:result[key] for key in ('video_path','profile','ai_seconds','quality','render_seconds')},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
