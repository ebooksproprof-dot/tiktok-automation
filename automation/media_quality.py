"""Technical validation. Passing does not imply editorial approval."""
import hashlib
import json
import pathlib
import re
import subprocess


def validate(path):
    path = pathlib.Path(path)
    meta = json.loads(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], text=True, timeout=30))
    video = next((s for s in meta['streams'] if s['codec_type'] == 'video'), {})
    audio = next((s for s in meta['streams'] if s['codec_type'] == 'audio'), {})
    duration = float(meta['format']['duration'])
    errors = []
    if video.get('codec_name') != 'h264' or video.get('pix_fmt') != 'yuv420p':
        errors.append('Expected H.264 yuv420p')
    if (video.get('width'), video.get('height')) != (1080, 1920):
        errors.append('Expected 1080x1920')
    if audio.get('codec_name') != 'aac':
        errors.append('Expected AAC audio')
    if not 15 <= duration <= 28:
        errors.append('Duration outside 15–28 seconds')
    if not 100_000 <= path.stat().st_size <= 20_000_000:
        errors.append('File outside 100 KB–20 MB')
    check = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', 'volumedetect',
                            '-f', 'null', '-'], capture_output=True, text=True, timeout=90)
    if check.returncode:
        errors.append('Decode failed')
    match = re.search(r'mean_volume: ([-\w.]+) dB', check.stderr)
    mean = float(match.group(1)) if match else float('-inf')
    if mean < -40:
        errors.append('Audio is absent or effectively silent')
    if errors:
        raise ValueError('; '.join(errors))
    return dict(technical_pass=True, editorial_approved=False,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                duration=duration, size=path.stat().st_size,
                width=1080, height=1920, audio_mean_db=mean)


if __name__ == '__main__':
    import sys
    print(json.dumps(validate(sys.argv[1]), ensure_ascii=False, indent=2))
