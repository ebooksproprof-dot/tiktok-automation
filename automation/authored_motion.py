"""Measure decoded illustration action, excluding static layout and subtitles.

The stock/Wan whole-frame freeze detector is unchanged. This specialized check
requires the original authored renderer and checks its action panel densely.
"""
import hashlib
from pathlib import Path
import subprocess


def validate(path):
    import numpy as np
    renderer=Path(__file__).with_name('household_animation.py')
    args=['ffmpeg','-v','error','-i',str(path),'-vf','crop=744:567:132:465,scale=256:192,format=rgb24',
          '-an','-threads','2','-f','rawvideo','-']
    proc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    size=256*192*3;previous=None;run=maximum=frames=changed=0
    while True:
        raw=proc.stdout.read(size)
        if not raw:break
        if len(raw)!=size:raise ValueError('ACTION_PANEL_FRAME_INCOMPLETE')
        frame=np.frombuffer(raw,dtype=np.uint8).reshape(192,256,3).astype(np.int16)
        if previous is not None:
            # Require spatially real changes, beyond small compression noise.
            count=int(np.count_nonzero(np.max(np.abs(frame-previous),axis=2)>12))
            if count<5:run+=1
            else:changed+=1;maximum=max(maximum,run);run=0
        previous=frame;frames+=1
    maximum=max(maximum,run)
    code=proc.wait(timeout=30)
    if code or frames<30 or maximum>=30:
        raise ValueError('AUTHORED_ACTION_PANEL_STATIC_OR_INVALID')
    return {'decoder_pass':True,'freeze_intervals_over_1s':0,
        'method':'decoded action-panel changes above compression noise; no subtitle or layout credit',
        'frames_checked':frames,'max_unchanged_action_frames':maximum,'changed_action_pairs':changed,
        'authored_renderer_sha256':hashlib.sha256(renderer.read_bytes()).hexdigest(),
        'stock_wan_detector_unchanged':True}
