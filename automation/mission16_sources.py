"""Bounded official footage intake using the existing acquisition and rights code.

Only metadata and annotated review sheets leave the runner. API credentials are
never persisted. A 401/403/429 stops that source; no alternate identity or proxy.
"""
import json
import os
from pathlib import Path
import subprocess
import time
from media_acquisition import download_and_measure,AcquisitionError,save_json
from media_providers import PixabayProvider,WikimediaProvider
from visual_library import history,source_identity

QUERIES=[('copos','washing glass',['glass']),('copos','dish drying rack',['rack']),
         ('copos','kitchen glasses cabinet',['glasses']),('copos','washing dishes',['dishes'])]


def run(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    cache={};manifest={'status':'SOURCE_INTAKE_PENDING','providers':{},'candidates':[],
        'downloaded':[],'failures':[],'publication_approved':False}
    previous=history(json.loads(Path('automation/queue.json').read_text()),json.loads(Path('automation/state.json').read_text()))
    previous.append(json.loads(Path('automation/visual_history.json').read_text()))
    providers=[]
    if os.getenv('PIXABAY_API_KEY'):providers.append(PixabayProvider(os.environ['PIXABAY_API_KEY'],cache))
    else:manifest['providers']['pixabay']={'status':'API_KEY_UNAVAILABLE'}
    providers.append(WikimediaProvider(cache))
    for provider in providers:
        provider.allow_full_frame=True
        provider.known_urls={r['source_id'] for p in previous for r in p.get('visual_sources',[])}
        count=0
        for category,query,words in QUERIES[:4 if provider.name=='pixabay' else 2]:
            try:
                records=provider.search(category,query,words);count+=1
                manifest['candidates'].extend(records)
            except AcquisitionError as exc:
                manifest['failures'].append({'provider':provider.name,'stage':'official_api','code':str(exc),'http_status':exc.http_status})
                if exc.http_status in (401,403,429):break
        manifest['providers'][provider.name]={'official_queries_completed':count,'http_requests':provider.requests}
    # Save before downloads; partial progress remains reviewable after any failure.
    save_json(folder/'manifest.json',manifest)
    seen=set()
    for record in manifest['candidates']:
        if len(seen)>=8:break
        key=source_identity(record['url'])
        if key in seen:continue
        seen.add(key)
        try:
            measured=download_and_measure(record,folder,previous)
            from media_acquisition import media_name
            path=folder/media_name(measured)
            measured['rights_status']='PENDING_VERIFICATION'
            manifest['downloaded'].append(measured)
            # Preserve exact source rights using the existing license validator.
            from source_license import verify
            try:
                measured['rights_evidence']=verify(measured)
                measured['rights_status']='COMMERCIAL_RIGHTS_VERIFIED'
            except Exception as exc:
                manifest['failures'].append({'provider':record['provider'],'provider_id':record['provider_id'],
                    'stage':'rights_verification','error_type':type(exc).__name__,'code':'COMMERCIAL_RIGHTS_NOT_VERIFIED'})
            from PIL import Image,ImageDraw,ImageFont
            sheet=Image.new('RGB',(1200,760),'#162527');draw=ImageDraw.Draw(sheet)
            font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
            draw.text((12,8),record['provider']+':'+record['provider_id']+' | '+record['selection_reason'][:105],font=font,fill='white')
            draw.text((12,34),str(measured['width'])+'x'+str(measured['height'])+' native | crop REVIEW ONLY | '+record['author'][:65],font=font,fill='white')
            for i,fraction in enumerate((.12,.37,.62,.87)):
                image=folder/(media_name(record)+f'-{i}.jpg')
                subprocess.run(['ffmpeg','-v','error','-y','-ss',str(measured['duration']*fraction),'-i',str(path),'-frames:v','1',
                    '-vf','scale=300:534:force_original_aspect_ratio=increase,crop=300:534',str(image)],check=True,timeout=45)
                sheet.paste(Image.open(image),(300*i,78))
            draw.text((12,640),record['license_url'],font=font,fill='white')
            draw.text((12,668),record['source_page'],font=font,fill='white')
            draw.text((12,696),'PENDING NARRATIVE / PHYSICAL / CROP REVIEW. NO PUBLICATION APPROVAL.',font=font,fill='white')
            sheet.save(folder/(record['provider']+'-'+record['provider_id']+'-review.jpg'),quality=92)
        except Exception as exc:
            manifest['failures'].append({'provider':record['provider'],'provider_id':record['provider_id'],'stage':'download_or_rights_review',
                'error_type':type(exc).__name__,'code':str(exc) if isinstance(exc,AcquisitionError) else 'REVIEW_NOT_COMPLETED',
                'http_status':getattr(exc,'http_status',None)})
        save_json(folder/'manifest.json',manifest)
    manifest['status']='GENERATION_COMPLETED_AWAITING_REVIEW' if manifest['downloaded'] else 'NO_REVIEWABLE_FOOTAGE_OBTAINED'
    save_json(folder/'manifest.json',manifest)
    print(json.dumps({'status':manifest['status'],'candidates':len(manifest['candidates']),'downloaded':len(manifest['downloaded']),'failures':len(manifest['failures'])}))


if __name__=='__main__':run('tmp/mission16/sources')
