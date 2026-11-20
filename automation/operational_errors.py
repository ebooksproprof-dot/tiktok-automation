"""Diagnostics without exception payloads, URLs, tokens or request bodies."""
import datetime as dt
import json
from pathlib import Path
import re
import traceback


def evidence(exc, stage):
    message=str(exc)
    if isinstance(exc, ValueError) and re.fullmatch(r'[A-Z][A-Z0-9_]{2,100}', message): code=message
    elif re.fullmatch(r'Inventory GitHub HTTP \d{3}; body omitted', message): code='GITHUB_HTTP_'+re.search(r'\d{3}', message)[0]
    elif message=='Inventory response uncertain; reload and stop external mutations': code='GITHUB_RESPONSE_UNCERTAIN'
    elif 'Media process failed: ffmpeg'==message: code='FFMPEG_PROCESS_FAILED'
    elif 'Media process failed: ffprobe'==message: code='FFPROBE_PROCESS_FAILED'
    else: code=type(exc).__name__.upper()
    frames=[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__)[-6:]]
    result={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'stage':stage,'code':code,
            'error_type':type(exc).__name__,'frames':frames,'raw_payload_omitted':True}
    folder=Path('tmp/operational-errors');folder.mkdir(parents=True,exist_ok=True)
    (folder/(stage+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result
