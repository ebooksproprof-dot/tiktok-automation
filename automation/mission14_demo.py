"""30s technical calibration clip, not household stock or an approved female voice."""
import argparse
import json
from pathlib import Path
import subprocess
import wave
from chatterbox_v3 import NAME, digest
from narration import finish_30
from caption_layout import filters
from experimental81.render import caption_timings
from media_quality import validate


def make(folder, cpu):
    folder=Path(folder).resolve();folder.mkdir(parents=True,exist_ok=True);cpu=Path(cpu)
    report=json.loads((cpu/'report.json').read_text());parts=[];timings=[];position=0
    for index,item in enumerate(report['utterances']):
        with wave.open(str(cpu/f'cpu-{index}.wav'),'rb') as inp:
            rate=inp.getframerate();parts.append(inp.readframes(inp.getnframes()));duration=inp.getnframes()/rate
        timings.append((position,position+duration,item['text']));position+=duration
    engine=type('TechnicalProbe',(),{'name':NAME})()
    duration,timings=finish_30(folder,parts,rate,position,timings,engine)
    timings=caption_timings(timings)
    graph=filters(folder,timings)
    label=folder/'disclosure.txt';label.write_text('TESTE TÉCNICO • VOZ NÃO APROVADA',encoding='utf8')
    graph.append(f'drawtext=textfile={label}:expansion=none:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.8:x=132:y=300')
    graph.append('setsar=1')
    video=folder/'mission14-vertical-30s.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=s=1080x1920:r=30',
        '-i',str(folder/'voice.wav'),'-vf',','.join(graph),'-t',str(duration),'-c:v','libx264',
        '-threads','2','-preset','veryfast','-crf','23','-maxrate','3M','-bufsize','6M',
        '-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-map_metadata','-1','-metadata:s:v:0','rotate=0',
        '-movflags','+faststart',str(video)],check=True,timeout=180)
    quality=validate(video,ai_only30=True)
    quality.update(technical_demo_only=True,publication_approved=False,female_voice_approved=False,
        source='FFmpeg native moving calibration pattern; no household footage or new Wan inference',
        voice=NAME,script=[x['text'] for x in report['utterances']],timings=timings,
        wav_sha256=digest(folder/'voice.wav'))
    (folder/'demo-report.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2)+'\n')
    subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)],
        stdout=(folder/'ffprobe.json').open('w'),check=True,timeout=30)
    from PIL import Image, ImageDraw, ImageFont
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',28)
    for i,stamp in enumerate((1,7,15,23,28)):
        frame=folder/f'frame-{i}.jpg'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(stamp),'-i',str(video),'-frames:v','1',str(frame)],check=True,timeout=30)
        img=Image.open(frame).convert('RGBA');ui=Image.new('RGBA',img.size,(0,0,0,0));draw=ImageDraw.Draw(ui)
        # Conservative derived masks, NOT a screenshot of a real TikTok session.
        for box in [(0,0,1080,240),(0,1260,1080,1920),(900,820,1080,1920)]:draw.rectangle(box,fill=(220,30,50,130))
        draw.rectangle((120,240,900,1260),outline=(20,255,140,255),width=4)
        draw.text((140,1510),'SIMULAÇÃO DE UI • NÃO PUBLICADO',font=font,fill='white')
        Image.alpha_composite(img,ui).convert('RGB').save(folder/f'ui-safe-{i}.jpg')
    return quality

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=Path('tmp/mission14/demo'))
    p.add_argument('--cpu',type=Path,default=Path('tmp/mission14/cpu'));args=p.parse_args()
    print(json.dumps(make(args.folder,args.cpu),ensure_ascii=False,indent=2))
