"""Measure the downloaded original, separately from the eventual 1080p export.

This provides evidence, never an automatic photorealism or physical-coherence
approval. A texture metric alone cannot distinguish a good film from a drawing.
"""
import hashlib
import json
from pathlib import Path
import subprocess


def probe(path):
    path=Path(path)
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],timeout=30))
    video=next(s for s in data['streams'] if s['codec_type']=='video')
    w,h=video['width'],video['height']
    if w/h>=9/16:ch=h//2*2;cw=int(ch*9/16)//2*2
    else:cw=w//2*2;ch=int(cw*16/9)//2*2
    crop=[(w-cw)//2,(h-ch)//2,cw,ch]
    return {'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'native_dimensions':[w,h],'portrait_crop':crop,'duration':float(data['format']['duration']),
        'sample_aspect_ratio':video.get('sample_aspect_ratio'),
        'rotation':[s.get('rotation') for s in video.get('side_data_list',[]) if 'rotation' in s],
        'method':'FFprobe on original downloaded bytes; geometry only, not visual approval',
        'photorealism_approved':False,'publication_approved':False}
