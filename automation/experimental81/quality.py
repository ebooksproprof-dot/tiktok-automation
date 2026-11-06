"""Opt-in 30-second validation; legacy validation is deliberately unchanged."""
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

import media_quality


@dataclass(frozen=True)
class Policy:
    target_seconds: float = 30.0
    tolerance_seconds: float = 0.15
    width: int = 1080
    height: int = 1920
    min_bytes: int = 100_000
    max_bytes: int = 20_000_000

    def check(self):
        if (not math.isfinite(self.target_seconds) or not math.isfinite(self.tolerance_seconds)
                or not 1 <= self.target_seconds <= 120 or not 0 < self.tolerance_seconds <= .5
                or self.width < 2 or self.height < 2 or self.width % 2 or self.height % 2
                or not 0 < self.min_bytes < self.max_bytes <= 100_000_000):
            raise ValueError('INVALID_EXPERIMENTAL_POLICY')


def validate(path, profile='hybrid30', policy=None):
    if profile == 'legacy':
        if policy is not None:
            raise ValueError('LEGACY_POLICY_OVERRIDE_FORBIDDEN')
        return media_quality.validate(path)
    if profile != 'hybrid30':
        raise ValueError('UNKNOWN_VALIDATION_PROFILE')
    policy = policy or Policy()
    policy.check()
    path = Path(path)
    if path.suffix.lower() != '.mp4' or not policy.min_bytes <= path.stat().st_size <= policy.max_bytes:
        raise ValueError('MP4_SIZE_OR_EXTENSION_INVALID')
    try:
        meta = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                         '-show_format', '-of', 'json', str(path)], text=True,
                         stderr=subprocess.PIPE, timeout=30))
        video = next(s for s in meta['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in meta['streams'] if s['codec_type'] == 'audio')
        duration = float(meta['format']['duration'])
    except (subprocess.SubprocessError, ValueError, KeyError, StopIteration):
        raise ValueError('INVALID_OR_MISSING_AV_STREAMS') from None
    if not math.isfinite(duration) or abs(duration-policy.target_seconds) > policy.tolerance_seconds:
        raise ValueError('DURATION_OUTSIDE_EXPERIMENTAL_TOLERANCE')
    if video.get('codec_name') != 'h264' or video.get('pix_fmt') != 'yuv420p':
        raise ValueError('H264_YUV420P_REQUIRED')
    if (video.get('width'), video.get('height')) != (policy.width, policy.height):
        raise ValueError('RESOLUTION_MISMATCH')
    if audio.get('codec_name') != 'aac':
        raise ValueError('AAC_AUDIO_REQUIRED')
    timing = media_quality.av_timing(video, audio)
    decoded = subprocess.run(['ffmpeg', '-hide_banner', '-xerror', '-i', str(path),
        '-vf', 'blackdetect=d=0.3:pix_th=0.10:pic_th=0.98',
        '-af', 'volumedetect,silencedetect=noise=-45dB:d=0.8', '-f', 'null', '-'],
        capture_output=True, text=True, timeout=180)
    if decoded.returncode:
        raise ValueError('FULL_DECODE_FAILED')
    match = re.search(r'mean_volume: ([-\w.]+) dB', decoded.stderr)
    volume = float(match.group(1)) if match else float('-inf')
    if not math.isfinite(volume) or volume < -40:
        raise ValueError('ABSENT_OR_SILENT_AUDIO')
    findings = media_quality.temporal_findings(decoded.stderr)
    if findings['black_intervals_over_300ms']:
        raise ValueError('BLACK_FRAME_INTERVAL')
    if findings['silence_intervals_over_800ms']:
        raise ValueError('UNREVIEWED_SILENCE_INTERVAL')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return dict(profile=profile, technical_pass=True, editorial_approved=False,
        publication_enabled=False, sha256=digest, duration=duration,
        duration_tolerance_seconds=policy.tolerance_seconds, size=path.stat().st_size,
        width=policy.width, height=policy.height, video_codec='h264', audio_codec='aac',
        audio_mean_db=volume, **timing, **findings)
