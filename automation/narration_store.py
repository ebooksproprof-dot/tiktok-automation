"""Durable generated utterances in the existing free GitHub Releases storage.

Never stores reference recordings. No overwrite; uncertain writes reconcile by
unique asset name on the next run. Local previews do not write to GitHub.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

TAG = 'narration-v14-cache'
REPO = 'ebooksproprof-dot/tiktok-automation'


def enabled():
    return os.getenv('GITHUB_ACTIONS') == 'true' and os.getenv('GITHUB_REF_NAME') == 'main' and bool(os.getenv('GH_TOKEN'))


def gh(args, **kwargs):
    return subprocess.run(['gh',*args,'--repo',REPO],capture_output=True,check=True,timeout=120,**kwargs)


def restore(key, target):
    if not enabled(): return False
    with tempfile.TemporaryDirectory() as folder:
        try: gh(['release','download',TAG,'--pattern',key+'.zip','--dir',folder])
        except subprocess.CalledProcessError as exc:
            # Only a confirmed missing tag/asset permits synthesis; network/auth
            # failures must not masquerade as cache misses.
            message=exc.stderr.decode(errors='replace').lower()
            if 'no assets match' in message or 'release not found' in message: return False
            raise RuntimeError('NARRATION_DURABLE_CACHE_READ_UNAVAILABLE') from None
        with zipfile.ZipFile(Path(folder)/(key+'.zip')) as archive:
            data=archive.read('speech.wav'); meta=json.loads(archive.read('manifest.json'))
        if meta['key']!=key or hashlib.sha256(data).hexdigest()!=meta['sha256']:
            raise ValueError('NARRATION_DURABLE_CACHE_CORRUPT')
        Path(target).write_bytes(data)
        return True


def persist(key, source):
    if not enabled(): return
    try: gh(['release','view',TAG])
    except subprocess.CalledProcessError:
        # Creation is idempotent by tag; on lost acknowledgement stop here.
        gh(['release','create',TAG,'--target','main','--title','Generated narration cache v14',
            '--notes','Generated speech only. No voice reference recordings. Not publication evidence.','--prerelease'])
    with tempfile.TemporaryDirectory() as folder:
        archive=Path(folder)/(key+'.zip'); data=Path(source).read_bytes()
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as out:
            out.writestr('speech.wav',data)
            out.writestr('manifest.json',json.dumps({'key':key,'sha256':hashlib.sha256(data).hexdigest()}))
        try: gh(['release','upload',TAG,str(archive)])
        except subprocess.CalledProcessError:
            restored=Path(folder)/'readback.wav'
            if not restore(key,restored) or restored.read_bytes()!=data:
                raise RuntimeError('NARRATION_DURABLE_WRITE_UNCONFIRMED') from None
