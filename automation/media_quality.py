"""Technical validation. Passing does not imply editorial approval."""
import hashlib
import json
import math
import pathlib
import re
import subprocess


def temporal_findings(log):
    """FFmpeg reports completed black intervals and silence starts, including EOF."""
    black = [float(x) for x in re.findall(r'black_duration:([\d.]+)', log)]
    silence = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
    return dict(black_intervals_over_300ms=sum(x >= .3 for x in black),
                silence_intervals_over_800ms=len(silence))


def av_timing(video, audio):
    """Stream alignment only; this is not a perceptual lip-sync score."""
    try:
        vs, aus = float(video['start_time']), float(audio['start_time'])
        vd, ad = float(video['duration']), float(audio['duration'])
    except (KeyError, TypeError, ValueError):
        raise ValueError('Audio/video timestamps missing or invalid') from None
    if not all(math.isfinite(x) for x in (vs, aus, vd, ad)) or min(vd, ad) <= 0:
        raise ValueError('Audio/video timestamps must be finite with positive duration')
    start_delta, end_delta = abs(vs-aus), abs(vs+vd-aus-ad)
    if start_delta > .08 or end_delta > .15:
        raise ValueError('Audio/video stream timing mismatch')
    return dict(av_start_delta_seconds=round(start_delta,6),
                av_end_delta_seconds=round(end_delta,6), lip_sync_verified=False)


def validate(path, *, ai_only30=False):
    path = pathlib.Path(path)
    meta = json.loads(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], text=True, timeout=30))
    video = next((s for s in meta['streams'] if s['codec_type'] == 'video'), {})
    audio = next((s for s in meta['streams'] if s['codec_type'] == 'audio'), {})
    duration = float(meta['format']['duration'])
    timing = av_timing(video, audio)
    errors = []
    if video.get('codec_name') != 'h264' or video.get('pix_fmt') != 'yuv420p':
        errors.append('Expected H.264 yuv420p')
    if (video.get('width'), video.get('height')) != (1080, 1920):
        errors.append('Expected 1080x1920')
    if audio.get('codec_name') != 'aac':
        errors.append('Expected AAC audio')
    contract = vertical_contract(path, video) if ai_only30 else {}
    borders = embedded_borders(path) if ai_only30 else {}
    if ai_only30:
        if abs(duration-30.0)>0.15:
            errors.append('AI-only duration outside 30.0 ± 0.15 seconds')
    elif not 15 <= duration <= 28:
        errors.append('Duration outside 15–28 seconds')
    if not 100_000 <= path.stat().st_size <= 20_000_000:
        errors.append('File outside 100 KB–20 MB')
    check = subprocess.run(['ffmpeg', '-hide_banner', '-xerror', '-i', str(path),
                            '-vf', 'blackdetect=d=0.3:pix_th=0.10:pic_th=0.98',
                            '-af', 'volumedetect,silencedetect=noise=-45dB:d=0.8',
                            '-f', 'null', '-'], capture_output=True, text=True, timeout=90)
    if check.returncode:
        errors.append('Decode failed')
    match = re.search(r'mean_volume: ([-\w.]+) dB', check.stderr)
    mean = float(match.group(1)) if match else float('-inf')
    if mean < -40:
        errors.append('Audio is absent or effectively silent')
    temporal = temporal_findings(check.stderr)
    if temporal['black_intervals_over_300ms']:
        errors.append('Black interval of at least 300 ms')
    if temporal['silence_intervals_over_800ms']:
        errors.append('Silence interval of at least 800 ms')
    if errors:
        raise ValueError('; '.join(errors))
    return dict(technical_pass=True, editorial_approved=False,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                duration=duration, size=path.stat().st_size,
                width=1080, height=1920, audio_mean_db=mean, **temporal, **timing, **contract, **borders)


if __name__ == '__main__':
    import sys
    print(json.dumps(validate(sys.argv[1]), ensure_ascii=False, indent=2))


def vertical_contract(path, video=None):
    """Verify display geometry and MP4 atom order, not only encoded dimensions."""
    import struct
    from fractions import Fraction
    path = pathlib.Path(path)
    if video is None:
        meta = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(path)],text=True,timeout=30))
        video = next(s for s in meta['streams'] if s['codec_type']=='video')
    if video.get('sample_aspect_ratio') != '1:1' or video.get('display_aspect_ratio') != '9:16':
        raise ValueError('SQUARE_PIXELS_AND_9_16_DISPLAY_REQUIRED')
    if Fraction(video.get('avg_frame_rate','0/1')) != 30 or Fraction(video.get('r_frame_rate','0/1')) != 30:
        raise ValueError('CONSTANT_30_FPS_REQUIRED')
    rotations = [float(video.get('tags',{}).get('rotate',0))]+[float(s.get('rotation',0)) for s in video.get('side_data_list',[])]
    if any(r % 360 for r in rotations): raise ValueError('ROTATION_METADATA_FORBIDDEN')
    atoms = []
    with path.open('rb') as inp:
        while True:
            header = inp.read(8)
            if len(header)<8: break
            size, kind = struct.unpack('>I4s',header); consumed=8
            if size==1: size=struct.unpack('>Q',inp.read(8))[0]; consumed=16
            if size==0: break
            if size < consumed: raise ValueError('INVALID_MP4_ATOM')
            atoms.append(kind); inp.seek(size-consumed,1)
    if b'moov' not in atoms or b'mdat' not in atoms or atoms.index(b'moov')>atoms.index(b'mdat'):
        raise ValueError('MP4_FASTSTART_REQUIRED')
    return dict(sample_aspect_ratio='1:1',display_aspect_ratio='9:16',fps=30,rotation=0,faststart=True)


def embedded_borders(path):
    """Sample edges at five times. Detect persistent baked-in black framing."""
    meta = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(path)],text=True,timeout=30))
    duration=float(meta['format']['duration']); findings=[]
    for fraction in (.1,.3,.5,.7,.9):
        raw = subprocess.check_output(['ffmpeg','-v','error','-ss',str(duration*fraction),'-i',str(path),
            '-frames:v','1','-vf','scale=108:192','-pix_fmt','rgb24','-f','rawvideo','-'],timeout=30)
        if len(raw)!=108*192*3: raise ValueError('BORDER_SAMPLE_DECODE_FAILED')
        def dark(points):
            pixels=[max(raw[(y*108+x)*3:(y*108+x)*3+3])<=16 for x,y in points]
            return sum(pixels)/len(pixels)>.98
        findings.append([dark([(x,y) for x in range(108) for y in range(3)]),
            dark([(x,y) for x in range(108) for y in range(189,192)]),
            dark([(x,y) for x in range(3) for y in range(192)]),
            dark([(x,y) for x in range(105,108) for y in range(192)])])
    if any(sum(row[edge] for row in findings)>=4 for edge in range(4)):
        raise ValueError('PERSISTENT_EMBEDDED_BLACK_BORDERS')
    return {'black_border_samples':findings,'embedded_border_check_pass':True}
