"""Isolated CPU microbenchmark; never changes production or publication state.

Usage: python automation/benchmark_tools43.py /path/to/verified/effectcraft-cli
Three sequential renders each: one second, 30 frames, 1080x1920, no audio.
The shared scene is a static mint rectangle on a dark green background.
Different encoders/settings mean timing is not a codec-quality comparison.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PIN = 'fe78d8df0221d06d5519e02f3c382c1dfcd3241217a0e46644b4598a215b8d61'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd):
    start = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    elapsed = time.perf_counter() - start
    if result.returncode:
        raise RuntimeError(result.stderr[-1500:] or result.stdout[-1500:])
    return elapsed, result


def main(binary):
    binary = Path(binary).resolve()
    if sha(binary) != PIN:
        raise ValueError('UNVERIFIED_EFFECTCRAFT_BINARY')
    folder = ROOT/'tmp/tools-4.3'
    folder.mkdir(parents=True, exist_ok=True)
    fixture = json.loads((ROOT/'automation/fixtures/effectcraft-original.ecproj').read_text())
    fixture['settings']['gpu_acceleration'] = False
    comp = fixture['items']['1']['kind']
    comp['layers'] = comp['layers'][:1]
    comp['enable_motion_blur'] = False
    # Retain exact original box geometry/color; remove animation and text so
    # the two compositors receive the same low-complexity visual workload.
    for group in comp['layers'][0]['props']['children']:
        if group['match'] == 'transform':
            for node in group['children']:
                if node['match'] == 'scale':
                    node.pop('keys', None)
                    node.pop('keyframes', None)
                    node['value']['v'] = [100., 100., 100.]
    def sharp_corners(value):
        if isinstance(value, dict):
            if value.get('match') == 'roundness':
                value['value']['v'] = 0.
            for child in value.values():
                sharp_corners(child)
        elif isinstance(value, list):
            for child in value:
                sharp_corners(child)
    sharp_corners(fixture)
    project = folder/'equivalent.ecproj'
    project.write_text(json.dumps(fixture, indent=2)+'\n')
    evidence = dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        platform=platform.platform(), cpu_count=os.cpu_count(),
        effectcraft_version='0.11.1', effectcraft_binary_sha256=PIN,
        fixture_sha256=sha(project), ffmpeg_version=subprocess.check_output(
            ['ffmpeg', '-version'], text=True).splitlines()[0],
        workload=dict(width=1080, height=1920, fps=30, duration_seconds=1,
            frames=30, audio=False, scene='Static 760x16 mint rectangle, centered at (540,1080), dark green background'),
        limitations=['Local microbenchmark, not GitHub Actions or full video throughput.',
            'Different H264 encoders and default quality/bitrate; no codec-quality equivalence claimed.',
            'Sequential process wall time includes startup; no warm-up exclusion.',
            'No footage, narration, text layout or complex effects tested.',
            'Outputs are temporary QA assets; script and measurements are durable.'], results={})
    for engine in ('effectcraft', 'ffmpeg'):
        times=[]
        output=folder/(engine+'.mp4')
        for repeat in range(3):
            output.unlink(missing_ok=True)
            if engine == 'effectcraft':
                cmd=[str(binary),'render','--project',str(project),'--comp','CasaSemEsforco Original','--audio','off','--out',str(output)]
            else:
                cmd=['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=0x0c2926:s=1080x1920:r=30:d=1',
                    '-vf','drawbox=x=160:y=1072:w=760:h=16:color=0x8ce6b0:t=fill',
                    '-frames:v','30','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','23',
                    '-pix_fmt','yuv420p',str(output)]
            seconds, result = run(cmd)
            times.append(seconds)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames',
            '-show_entries','stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration',
            '-of','json',str(output)],text=True))
        _, decode=run(['ffmpeg','-v','error','-i',str(output),'-f','null','-'])
        video=probe['streams'][0]
        passed=(video['width']==1080 and video['height']==1920 and
            video['nb_read_frames']=='30' and video['r_frame_rate']=='30/1' and
            abs(float(probe['format']['duration'])-1)<0.04 and len(probe['streams'])==1)
        evidence['results'][engine]=dict(seconds=times,median_seconds=statistics.median(times),
            bytes=output.stat().st_size,sha256=sha(output),probe=probe,decode_errors=decode.stderr,
            technical_pass=passed,command=cmd)
        run(['ffmpeg','-v','error','-y','-i',str(output),'-frames:v','1',str(folder/(engine+'.png'))])
    _, comparison=run(['ffmpeg','-hide_banner','-i',str(folder/'effectcraft.mp4'),
        '-i',str(folder/'ffmpeg.mp4'),'-lavfi','ssim','-f','null','-'])
    evidence['ssim_log']=[line for line in comparison.stderr.splitlines() if 'SSIM' in line]
    evidence['decision']='Keep FFmpeg/Piper production; primitive benchmark does not establish production benefit from replacing the renderer.'
    target=ROOT/'automation/tools-4.3-evidence.json'
    target.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k: {n:v[n] for n in ('median_seconds','bytes','technical_pass')} for k,v in evidence['results'].items()},indent=2))
    print(evidence['ssim_log'])


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary')
    main(parser.parse_args().binary)
