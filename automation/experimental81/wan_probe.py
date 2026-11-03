"""Opt-in Wan2.2 I2V public Gradio adapter, isolated from publishing.

No tokens, purchases or automatic retries. On GitHub Actions a caller must
supply before_submit(record), which atomically creates a remote request ledger
entry and rejects every previously reserved fingerprint, including failures.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

try:
    from experimental81 import hf_probe as common
except ModuleNotFoundError:
    import hf_probe as common

SPACE='https://zerogpu-aoti-wan2-2-fp8da-aoti-faster.hf.space'
MODEL='Wan-AI/Wan2.2-I2V-A14B-Diffusers + Lightx2v I2V14B LoRA'
ORDER=['input_image','prompt','steps','negative_prompt','duration_seconds',
       'guidance_scale','guidance_scale_2','seed','randomize_seed']


def inspect_clip(path):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams',
        '-show_format','-of','json',str(path)],text=True,timeout=30))
    video=next(s for s in data['streams'] if s['codec_type']=='video')
    duration=float(data['format']['duration'])
    width,height=video['width'],video['height']
    if not 4.8<=duration<=5.3 or not 480<=width<=832 or not 480<=height<=832:
        raise ValueError('Unexpected Wan clip shape/duration')
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'],
                   capture_output=True,check=True,timeout=60)
    return {'duration_seconds':duration,'width':width,'height':height,
            'video_codec':video.get('codec_name'),'fps':video.get('r_frame_rate'),
            'has_audio':any(s['codec_type']=='audio' for s in data['streams']),
            'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'bytes':Path(path).stat().st_size}


def run(reference, case, directory, enabled=False, before_submit=None,
        client_factory=None, file_handler=None, prompt=None, hf_token=None, steps=4,
        seed_offset=0):
    if not enabled:
        return {'status':'DISABLED','generation_attempted':False,'publication_allowed':False}
    if os.getenv('GITHUB_ACTIONS')=='true' and before_submit is None:
        return {'status':'BLOCKED','error':'REMOTE_LEDGER_REQUIRED',
                'generation_attempted':False,'publication_allowed':False}
    reference=Path(reference)
    if reference.suffix.lower() not in ('.png','.jpg','.jpeg') or not reference.is_file() or not 1000<=reference.stat().st_size<=20_000_000:
        raise ValueError('A bounded licensed reference image is required')
    if case not in common.PROMPTS:raise ValueError('Unknown test case')
    prompt = common.PROMPTS[case] if prompt is None else prompt
    if not isinstance(prompt,str) or not 40<=len(prompt)<=2000:
        raise ValueError('Bounded descriptive prompt required')
    if type(steps) is not int or steps not in (3,4):
        raise ValueError('Unreviewed inference step count')
    if steps == 3 and not hf_token:
        raise ValueError('Three-step mode requires verified authenticated Free account')
    if type(seed_offset) is not int or not 0 <= seed_offset <= 3:
        raise ValueError('Unreviewed seed variation')
    spec={'case':case,'space':SPACE,'model':MODEL,'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
          'prompt':prompt,'steps':steps,'negative_prompt':'warped objects, deformed hands, duplicate objects, text, logos',
          'duration_seconds':5,'guidance_scale':1,'guidance_scale_2':1,'seed':8100+ord(case)-ord('A')+1+seed_offset*101,'randomize_seed':False}
    digest=common.fingerprint(spec);directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    path=directory/(digest+'.json')
    with (directory/(digest+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if path.exists():return common.cached_record(path)
        record={'request':spec,'request_sha256':digest,'status':'DISCOVERING',
                'created_at':datetime.now(timezone.utc).isoformat(),'generation_attempted':False,
                'publication_allowed':False,'authenticated':False,'billable_account_used':False,
                'gpu_seconds_requested':None,'gpu_seconds_consumed':None,'quota_consumed':None,
                'queue_seconds':None,'usable_video_seconds':0,'license_review_pending':True}
        common.save(path,record);started=time.monotonic()
        try:
            if client_factory is None or file_handler is None:
                from gradio_client import Client,handle_file
                client_factory=client_factory or Client;file_handler=file_handler or handle_file
            client=client_factory(SPACE,token=hf_token if hf_token else False,verbose=False,
                download_files=str(directory/'downloads'),httpx_kwargs={'timeout':30})
            api=client.view_api(return_format='dict',print_info=False)
            endpoint=api.get('named_endpoints',{}).get('/generate_video',{})
            if [p.get('parameter_name') for p in endpoint.get('parameters',[])]!=ORDER:
                raise ValueError('Wan published schema changed')
            values=[file_handler(str(reference))]+[spec[k] for k in ORDER[1:]]
            record.update(status='SUBMITTING',discovered_endpoint='/generate_video')
            common.save(path,record)
            if before_submit is not None:before_submit(dict(record))
            record['generation_attempted']=True;common.save(path,record)
            result=client.submit(*values,api_name='/generate_video').result(timeout=180)
            source=common.video_path(result);media=inspect_clip(source)
            target=directory/('wan-'+case+'-'+media['sha256'][:16]+'.mp4')
            if not target.exists():shutil.copyfile(source,target)
            if hashlib.sha256(target.read_bytes()).hexdigest()!=media['sha256']:
                raise ValueError('Persisted media mismatch')
            record.update(status='GENERATED_PENDING_VISUAL_REVIEW',file=target.name,media=media,
                          model_output_generated=True,visual_quality_approved=False,usable_video_seconds=None)
        except Exception as exc:
            record.update(status='UNKNOWN' if record['generation_attempted'] else 'BLOCKED',
                          error=common.classify_error(exc),error_type=type(exc).__name__)
        record['wall_seconds']=round(time.monotonic()-started,3);common.save(path,record)
        return record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--case',choices=list(common.PROMPTS),default='C')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--prompt-file',type=Path)
    p.add_argument('--reference-rights-confirmed',action='store_true',required=True)
    a=p.parse_args()
    print(json.dumps(run(a.reference,a.case,a.output,
        os.getenv('AI_VIDEO_EXPERIMENTAL_ENABLED','false').lower()=='true',
        prompt=a.prompt_file.read_text() if a.prompt_file else None),indent=2))


if __name__=='__main__':main()
