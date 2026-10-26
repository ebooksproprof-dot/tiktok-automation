"""Persist bounded avatar proof/evidence; no production queue or TikTok access."""
import hashlib
import json
import os
from pathlib import Path
from release_media import API, REPO, request, verified_asset

def main():
    if os.getenv('GITHUB_ACTIONS')!='true' or not os.getenv('GH_TOKEN'):
        raise RuntimeError('Authorized cloud runner required')
    folder=Path(__file__).resolve().parents[1]/'avatar52-output'
    report=json.loads((folder/'report.json').read_text())
    files=[folder/'report.json']
    if report.get('avatar_video_produced') is True:
        path=folder/'avatar52-accelerated.mp4'
        if hashlib.sha256(path.read_bytes()).hexdigest()!=report['video_sha256']:
            raise ValueError('Avatar digest changed')
        files.append(path)
    log=folder/'execution.log'
    if log.exists():files.append(log)
    if sum(x.stat().st_size for x in files)>30_000_000:raise ValueError('Proof budget exceeded')
    token=os.environ['GH_TOKEN'];tag='avatar-v52-2026-10-25'
    release=request(API+'/releases/tags/'+tag,token)
    if release is None:
        release=request(API+'/releases',token,'POST',dict(tag_name=tag,target_commitish=os.environ['GITHUB_SHA'],name='Avatar 5.2 — experiment evidence',draft=False,prerelease=True,make_latest='false',body='Experimental CPU avatar evidence. No realism or lip-sync claim without review. Not authorized for TikTok.'))
    assets=request(API+'/releases/'+str(release['id'])+'/assets?per_page=100',token)
    if not isinstance(assets,list) or len(assets)>15:raise RuntimeError('Release asset budget')
    links=[]
    for path in files:
        body=path.read_bytes();digest=hashlib.sha256(body).hexdigest();name=path.stem+'-'+digest[:16]+path.suffix
        found=next((a for a in assets if a['name']==name),None)
        if found is None:
            mime={'.mp4':'video/mp4','.json':'application/json','.log':'text/plain'}[path.suffix]
            uploaded=request('https://uploads.github.com/repos/'+REPO+'/releases/'+str(release['id'])+'/assets?name='+name,token,'POST',body,mime)
            found=request(API+'/releases/assets/'+str(uploaded['id']),token)
        links.append(dict(file=path.name,sha256=digest,url=verified_asset(found,name,digest,len(body))))
    result=dict(release=release['html_url'],assets=links,avatar_video_produced=report.get('avatar_video_produced',False),published_to_tiktok=False)
    (folder/'release-links.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
