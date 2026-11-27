"""Original household explainer animation, native 1080x1920, no stock loops.

This is an authored illustration, not Wan footage or proof of a physical test.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
from PIL import Image,ImageDraw,ImageFont
from caption_layout import layout,FONT
from experimental81.render import caption_timings
from media_quality import validate

BG='#F7F2E7'; INK='#173B36'; TEAL='#1F8378'; BLUE='#75B9D1'; CORAL='#D9664E'
FONT_REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def font(size,bold=False):return ImageFont.truetype(FONT if bold else FONT_REG,size)
def ease(p):return p*p*(3-2*p)


def text(draw,xy,value,size=34,fill=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=fill)


def glass(draw,x,y,size=1,water=0,inverted=False):
    w,h=120*size,205*size
    points=[(x-w/2,y),(x+w/2,y),(x+w*.37,y+h),(x-w*.37,y+h)]
    if inverted:points=[(px,y+h-(py-y)) for px,py in points]
    draw.polygon(points,fill='#DEF0EF',outline=TEAL,width=max(2,int(4*size)))
    rim_y=y+h if inverted else y
    draw.ellipse((x-w/2,rim_y-12*size,x+w/2,rim_y+12*size),fill='#EAF8F5',outline=TEAL,width=max(2,int(4*size)))
    draw.line([(x-w*.25,y+32*size),(x-w*.22,y+h-28*size)],fill='white',width=max(2,int(6*size)))
    if water>0:
        bottom=y+h-15*size
        draw.rounded_rectangle((x-w*.30,bottom-water*size,x+w*.30,bottom),radius=10*size,fill=BLUE)


def drop(draw,x,y,r=8,fill=BLUE):
    draw.polygon([(x,y-r*2),(x-r,y),(x+r,y)],fill=fill);draw.ellipse((x-r,y-r,x+r,y+r),fill=fill)


def rack(draw):
    draw.rounded_rectangle((175,930,865,988),radius=20,fill='#BFD3CD')
    for y in (930,945,960):draw.line((185,y,855,y),fill='#61877F',width=5)
    for x in range(200,851,60):draw.line((x,926,x+30,982),fill='#90ADA5',width=4)


def base(stage,p):
    img=Image.new('RGB',(1080,1920),BG);d=ImageDraw.Draw(img)
    # All editorial text sits within the conservative TikTok central area.
    text(d,(132,260),'CasaSemEsforço',31,TEAL,True)
    text(d,(132,306),'UM CUIDADO POR VEZ',20,INK)
    titles=['Água no fundo?','Depois da lavagem','Espaço para secar','Confira os detalhes','Pronto para guardar']
    text(d,(132,360),titles[stage],48,INK,True)
    d.rounded_rectangle((132,465,876,1032),radius=38,fill='#FFFFFF',outline='#D7DFD8',width=3)
    d.rounded_rectangle((155,485,340,530),radius=20,fill=TEAL)
    text(d,(178,493),f'PASSO {stage+1} / 5',22,'white',True)
    q=ease(p)
    if stage==0:
        glass(d,504,550+55*q,size=1.75,water=30-10*q)
        d.line((620,965,738,965),fill=CORAL,width=4)
        d.ellipse((607,950,637,980),outline=CORAL,width=4)
        text(d,(665,985),'Observe',25,CORAL,True)
    elif stage==1:
        rack(d)
        glass(d,500,565+55*q,size=1.45,inverted=True)
        # A single draining action, never a repeated loop.
        for n in range(4):
            y=895+(q*.9+n*.2)*45
            if y<950:drop(d,470+n*20,y,5)
        text(d,(228,560),'Use o suporte indicado para o copo.',24)
    elif stage==2:
        rack(d)
        for n in range(3):glass(d,500+(n-1)*(145+65*q),700,size=1.05,inverted=True)
        d.line((345,680,655,680),fill=CORAL,width=4)
        for x in (345,655):d.line((x,668,x,692),fill=CORAL,width=4)
        text(d,(288,570),'Sem empilhar ou equilibrar.',28)
    elif stage==3:
        glass(d,470,630,size=1.5,water=max(0,16-16*q))
        # Inspection moves from rim to base, illustrating the narrated check.
        lens_y=630+305*q;lens_x=584
        d.ellipse((lens_x-47,lens_y-47,lens_x+47,lens_y+47),outline=CORAL,width=7)
        d.line((lens_x+34,lens_y+34,lens_x+75,lens_y+75),fill=CORAL,width=10)
        text(d,(230,560),'Borda + fundo',32,TEAL,True)
        text(d,(230,970),'Com gotas? Espere secar.',27)
    else:
        d.rounded_rectangle((208,565,820,965),radius=18,fill='#DFCCAB',outline='#977C54',width=4)
        d.rectangle((230,590,798,914),fill='#F5E9D5')
        d.line((230,910,798,910),fill='#A48559',width=12)
        for n in range(3):glass(d,335+n*165,640+(1-q)*(90-15*n),size=1.1)
        text(d,(235,975),'Estáveis e fáceis de retirar.',27,TEAL,True)
    text(d,(132,431),'ILUSTRAÇÃO AUTORAL',19,TEAL)
    text(d,(132,1234),'Siga as instruções do fabricante.',22,INK)
    return img


def render(audio_folder,output):
    folder=Path(audio_folder);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((folder/'audio-manifest.json').read_text());duration=manifest['duration']
    timings=manifest['timings']
    from caption_alignment import align
    recognition=json.loads((folder/'asr.json').read_text())
    captions=align(manifest['lines'],recognition)
    target=output/'casasem-copos-secos-review.mp4'
    temporary=target.with_name(target.stem+'.partial.mp4')
    args=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-',
          '-i',str(folder/'voice.wav'),'-map','0:v','-map','1:a','-t',str(duration),'-c:v','libx264','-threads','2',
          '-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-vf','setsar=1','-c:a','aac','-b:a','128k',
          '-map_metadata','-1','-metadata:s:v:0','rotate=0','-movflags','+faststart',str(temporary)]
    proc=subprocess.Popen(args,stdin=subprocess.PIPE)
    sample_frames={30,210,450,690,840}
    try:
        for frame in range(math.ceil(duration*30)):
            t=frame/30
            stage=next((i for i,(a,b,_) in enumerate(timings) if a<=t<b),len(timings)-1)
            start,end,_=timings[stage];p=max(0,min(1,(t-start)/(end-start)))
            img=base(stage,p);draw=ImageDraw.Draw(img)
            current=next((txt for a,b,txt in captions if a<=t<b),None)
            if current:
                wrapped,size=layout(current)
                for n,line in enumerate(wrapped.splitlines()):
                    face=font(size,True);width=face.getlength(line);x=132+(744-width)/2;y=1080+n*(size+12)
                    draw.rounded_rectangle((x-17,y-9,x+width+17,y+size+16),radius=12,fill=INK)
                    draw.text((x,y),line,font=face,fill='white')
            if frame in sample_frames:img.save(output/f'frame-{frame}.jpg')
            proc.stdin.write(img.tobytes())
        proc.stdin.close()
        if proc.wait(timeout=120):raise RuntimeError('EDITORIAL_ANIMATION_RENDER_FAILED')
    finally:
        if proc.poll() is None:proc.kill()
    quality=validate(temporary,ai_only30=True)
    temporary.replace(target)
    quality.update(mission='15.0',publication_approved=False,editorial_review_status='PENDING_AUDIO_AND_IDENTITY_REVIEW',
        video_origin='authored_household_illustration',generated_wan_seconds=0,
        source_rights={'basis':'original procedural graphics authored for the owner in this mission','external_visual_assets':[]},
        script=manifest['lines'],timings=captions,caption_timing_method='observed ASR word timestamps after complete sequence agreement',voice_reference_sha256=manifest['reference_sha256'])
    (output/'video-review.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2)+'\n')
    return quality

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--audio-folder',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(render(a.audio_folder,a.output),ensure_ascii=False,indent=2))
