"""Controlled caption comparison; no queue, consent or publisher writes."""
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import time
import urllib.request
from caption_layout import filters as measured, FONT
from composition_style import overlay
from framing import product_frame_filter
from female_narration import KokoroFemaleEngine
from narration import synthesize
from media_quality import validate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'tmp/validation-v51'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args): subprocess.run(args, check=True, timeout=240)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    tracked=[ROOT/'automation'/x for x in ('queue.json','state.json','visual_history.json')]
    before={str(p):sha(p) for p in tracked}
    item=next(x for x in json.loads((ROOT/'automation/catalog_extension.json').read_text())['items'] if x['id']=='mesa-caneca-afastada')
    source=item['media'][0]
    clip=OUT/'source.mp4'
    if not clip.exists():
        with urllib.request.urlopen(urllib.request.Request(source['url'], headers={'User-Agent': 'CasaSemEsforco/2.0'}),timeout=60) as response,clip.open('wb') as target:
            size=0
            while chunk:=response.read(1024*1024):
                size+=len(chunk)
                if size>40_000_000: raise ValueError('Source exceeds budget')
                target.write(chunk)
    if sha(clip)!=source['sha256']: raise ValueError('Source changed')
    voice=KokoroFemaleEngine(OUT/'voice-assets')
    start=time.monotonic()
    duration,timings=synthesize(voice,[item['hook'],item['steps'],item['cta']],OUT)
    synthesis_seconds=time.monotonic()-start
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(clip)],text=True))
    shape=next(s for s in meta['streams'] if s['codec_type']=='video')
    if float(meta['format']['duration'])<duration: raise ValueError('Cannot loop proof source')
    base=OUT/'unlettered.mp4'
    start=time.monotonic()
    run(['ffmpeg','-v','error','-y','-i',str(clip),'-t',str(duration),'-an','-filter_complex',product_frame_filter(shape['width'],shape['height']),'-c:v','libx264','-threads','2','-preset','veryfast','-crf','23',str(base)])
    framing_seconds=time.monotonic()-start
    records=[]
    for name in ('A','B'):
        folder=OUT/name;folder.mkdir(exist_ok=True)
        if name=='B': fs=measured(folder,timings)
        else:
            fs=[]
            for i,(a,b,text) in enumerate(timings):
                p=folder/f'caption-{i}.txt';p.write_text(text)
                fs.append(f"drawtext=fontfile={FONT}:textfile={p}:fontsize=58:fontcolor=white:box=1:boxcolor=black@0.70:boxborderw=18:x=(w-text_w)/2:y=1320:enable='between(t,{a:.3f},{b:.3f})'")
        fs+=overlay(folder,item['hook'],duration)
        fs.append(f'drawtext=fontfile={FONT}:text=CENAS ILUSTRATIVAS:fontsize=24:fontcolor=white:x=70:y=200')
        path=OUT/f'comparison-{name}.mp4'
        start=time.monotonic()
        run(['ffmpeg','-v','error','-y','-i',str(base),'-i',str(OUT/'voice.wav'),'-vf',','.join(fs),'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-t',str(duration),'-c:v','libx264','-threads','2','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(path)])
        elapsed=time.monotonic()-start
        quality=validate(path)
        run(['ffmpeg','-v','error','-y','-i',str(path),'-vf',f'fps=6/{duration},scale=270:480,tile=3x2','-frames:v','1',str(path.with_suffix('.jpg'))])
        if before!={str(p):sha(p) for p in tracked}: raise RuntimeError('State changed')
        records.append(dict(file=path.name,quality=quality,caption_style='legacy' if name=='A' else 'measured-v51',render_seconds=elapsed,synthesis_seconds_shared=synthesis_seconds,framing_seconds_shared=framing_seconds,peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,voice=voice.name,voice_sha256=sha(OUT/'voice.wav'),source=source,timings=timings,proof_only=True,approved=False,publication_allowed=False,avatar_present=False,state_unchanged=True,cost_added=0,limitations=['Same stock and audio, caption comparison only; not new editorial inventory.','Sentence boundaries measured; intra-sentence chunk timing remains approximate.','Voice not evaluated by listening; no lip-sync or avatar.','RSS is per-child maximum, not aggregate.']))
        (OUT/'report.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
        print('REAL_PROOF_READY='+str(path),flush=True)

if __name__=='__main__': main()
