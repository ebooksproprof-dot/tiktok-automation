"""Optional one-second CPU/headless EffectCraft proof, never a render dependency."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

AUTOMATION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUTOMATION))
from effectcraft_adapter import render, BINARY_SHA256


def main(binary, output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    fixture = json.loads((AUTOMATION/'fixtures/effectcraft-original.ecproj').read_text())
    fixture['settings']['gpu_acceleration'] = False
    fixture['items']['1']['kind']['enable_motion_blur'] = False
    project = output/'cpu-original.ecproj'
    project.write_text(json.dumps(fixture, indent=2)+'\n')
    video = output/'effectcraft81-headless.mp4'
    start = time.monotonic()
    render(binary, project, video)
    elapsed = time.monotonic()-start
    meta = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams',
        '-show_format','-of','json',str(video)],text=True,timeout=30))
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],
                   check=True,capture_output=True,timeout=30)
    stream = next(s for s in meta['streams'] if s['codec_type']=='video')
    report = {'test':'Optional EffectCraft CPU/headless original fixture, not integration',
        'binary_sha256':BINARY_SHA256,'effectcraft_version':'0.11.1',
        'wall_seconds':round(elapsed,3),'width':stream['width'],'height':stream['height'],
        'duration':float(meta['format']['duration']),'codec':stream['codec_name'],
        'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'bytes':video.stat().st_size,
        'full_decode_pass':True,'gpu_acceleration':False,'publication_enabled':False,
        'audio':False,'video':video.name,
        'limitations':['One-second graphics fixture; no footage or narration.',
                      'Technical execution alone is not visual quality approval.',
                      'No measured benefit for the 30-second composition; FFmpeg remains primary.']}
    (output/'effectcraft81-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    main(args.binary,args.output)
