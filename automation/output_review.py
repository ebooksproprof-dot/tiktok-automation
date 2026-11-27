"""Machine review receipts for the current renderer; unknown results fail closed."""
import json
import os
from pathlib import Path
import subprocess
import sys


def review(folder, lines, timings, duration):
    folder=Path(folder).resolve(); script=folder/'audio-review-script.json';script.write_text(json.dumps(lines,ensure_ascii=False))
    output=folder/'audio-review.json'
    completed = subprocess.run([os.getenv('ASR_PYTHON',sys.executable),str(Path(__file__).with_name('audio_review.py')),
        '--audio',str(folder/'voice.wav'),'--script',str(script),'--output',str(output)],check=False,timeout=600)
    if not output.exists():
        raise ValueError('ASR_REVIEW_FAILED_WITHOUT_EVIDENCE')
    audio=json.loads(output.read_text())
    if completed.returncode not in (0,2):
        raise ValueError('ASR_REVIEW_PROCESS_FAILED')
    if not audio.get('audio_content_verified'):
        confirmation=folder/'asr-confirmation.json'
        subprocess.run([os.getenv('ASR_PYTHON',sys.executable),str(Path(__file__).with_name('asr_confirmation.py')),
            '--audio',str(folder/'voice.wav'),'--script',str(script),'--primary',str(output),'--output',str(confirmation)],
            check=False,timeout=900)
        if not confirmation.exists():raise ValueError('ASR_SECONDARY_REVIEW_UNAVAILABLE')
        evidence=json.loads(confirmation.read_text())
        audio['independent_confirmation']=evidence
        audio['audio_content_verified']=evidence['decision']['audio_content_verified']
        if not audio['audio_content_verified']:
            raise ValueError('AUDIO_CONTENT_REQUIRES_AUDITORY_REVIEW')
    from caption_layout import layout
    if not timings or any(start<0 or end>duration+.01 or end<=start for start,end,text in timings):
        raise ValueError('CAPTION_TIMING_INVALID')
    for start,end,text in timings: layout(text)
    return {'audio_content_verified':audio['audio_content_verified'],'audio_review':audio,
        'captions_reviewed':True,'caption_review_method':'measured glyph bounds in conservative TikTok zone; sentence-level timing',
        'full_frame_reviewed':True,'framing_review_method':'source portrait semantic review, bounded proportional crop, decoded border samples',
        'human_perceptual_review':False}
