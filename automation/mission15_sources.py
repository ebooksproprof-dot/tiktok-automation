"""One bounded official Pixabay API intake for the first review episode.

No raw source upload. Annotated contact sheets and metadata only leave runner;
final derivative assembly runs with the licensed sources in the same cloud job.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request

QUERIES=('cleaning kitchen','washing dishes','watering plants','folding towels')


def run(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    token=os.environ['PIXABAY_API_KEY'];items={};calls=0
    for query in QUERIES:
        params={'key':token,'q':query,'per_page':20,'safesearch':'true','min_width':1080,'min_height':1920}
        req=urllib.request.Request('https://pixabay.com/api/videos/?'+urllib.parse.urlencode(params),headers={'User-Agent':'CasaSemEsforco official API review'})
        try:
            with urllib.request.urlopen(req,timeout=45) as response:result=json.load(response)
        except Exception:
            raise RuntimeError('OFFICIAL_PIXABAY_API_UNAVAILABLE_NO_ERROR_BODY') from None
        calls+=1
        for hit in result.get('hits',[]):
            if re.search(r'\b(ai generated|animation|mosque|quran|bird|wildlife|car|tractor|construction)\b',hit.get('tags',''),re.I):continue
            choices=[f for f in hit.get('videos',{}).values() if f.get('width',0)>=1080 and f.get('height',0)>=1920 and f.get('size',0)<=150_000_000]
            if not choices or hit['duration']<8:continue
            selected=min(choices,key=lambda f:f['size'])
            items.setdefault(hit['id'],dict(provider='pixabay',provider_id=str(hit['id']),source_page=hit['pageURL'],author=hit['user'],
                tags=hit['tags'],duration=hit['duration'],file=selected,query=query,license_url='https://pixabay.com/service/license-summary/',
                rights_status='OFFICIAL_API_CANDIDATE_PENDING_EDITORIAL_AND_SOURCE_CHECK'))
    (folder/'candidates.json').write_text(json.dumps({'calls':calls,'items':list(items.values())},ensure_ascii=False,indent=2)+'\n')
    # Avoid the already published list; a good new source must remain new.
    used={u for p in json.load(open('automation/queue.json'))['posts'] for u in p.get('quality',{}).get('source_urls',[])}
    selected=[x for x in items.values() if x['file']['url'] not in used][:8]
    from PIL import Image,ImageDraw,ImageFont
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
    manifest=[]
    for item in selected:
        path=folder/(item['provider_id']+'.mp4')
        try:
            with urllib.request.urlopen(item['file']['url'],timeout=60) as r:
                data=r.read(150_000_001)
            if len(data)>150_000_000:continue
            path.write_bytes(data)
            item['sha256']=hashlib.sha256(data).hexdigest()
            row=Image.new('RGB',(960,650),'#202020');draw=ImageDraw.Draw(row)
            for i,fraction in enumerate((.15,.5,.85)):
                frame=folder/(item['provider_id']+f'-{i}.jpg')
                subprocess.run(['ffmpeg','-v','error','-y','-ss',str(item['duration']*fraction),'-i',str(path),'-frames:v','1','-vf','scale=320:570:force_original_aspect_ratio=increase,crop=320:570',str(frame)],check=True,timeout=40)
                row.paste(Image.open(frame),(i*320,80))
            draw.text((10,5),item['provider_id']+' | '+item['tags'][:100],font=font,fill='white')
            draw.text((10,30),'REVIEW ONLY | '+item['author']+' / Pixabay',font=font,fill='white')
            row.save(folder/(item['provider_id']+'-review.jpg'))
            manifest.append(item)
        except Exception as exc:
            item['held_error_type']=type(exc).__name__
        finally:
            # Raw footage stays only on this private runner disk. No artifact upload.
            pass
    print('SOURCE_REVIEW_COUNTS='+json.dumps({'api_calls':calls,'candidates':len(items),'selected':len(selected),'downloaded':len(manifest)}),flush=True)
    (folder/'review-manifest.json').write_text(json.dumps({'requests':calls,'sources':manifest},ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':run('tmp/mission15/sources')
