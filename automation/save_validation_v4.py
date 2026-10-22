"""Persist the explicit validation batch to Releases; never submit to TikTok."""
import hashlib
import json
import os
from pathlib import Path
from release_media import API, REPO, request, verified_asset


def main():
    if os.getenv('GITHUB_ACTIONS') != 'true' or not os.getenv('GH_TOKEN'):
        raise RuntimeError('Authorized cloud runner required')
    root = Path(__file__).resolve().parents[1]
    folder = root/'tmp/validation-v4'
    report = json.loads((folder/'report.json').read_text())
    if not isinstance(report, list) or not 1 <= len(report) <= 3:
        raise ValueError('Expected one to three completed validation pairs')
    names = {'report.json'}
    for item in report:
        if any(not isinstance(item.get(k), str) or not item[k].endswith('.mp4') for k in ('file', 'baseline_file')):
            raise ValueError('Expected MP4 comparison names')
        names.update((item['file'], item['baseline_file']))
        names.add(str(Path(item['file']).with_suffix('.jpg')))
    if any(Path(n).name != n for n in names) or len(names) > 10:
        raise ValueError('Unexpected validation asset list')
    files = [folder/n for n in sorted(names)]
    if sum(p.stat().st_size for p in files) > 120_000_000:
        raise ValueError('Validation batch exceeds 120 MB budget')
    token = os.environ['GH_TOKEN']
    tag = 'validation-v4-2026-10-22'
    release = request(API+'/releases/tags/'+tag, token)
    if release is None:
        release = request(API+'/releases', token, 'POST', dict(
            tag_name=tag, target_commitish=os.environ['GITHUB_SHA'],
            name='CasaSemEsforco 4.0 — validation only', make_latest='false',
            draft=False, prerelease=True,
            body=str(len(report))+' completed validation compositions with baseline comparisons. '
                 'Not approved for TikTok publication. See report for measured limits.'))
    endpoint = API+'/releases/'+str(release['id'])+'/assets?per_page=100'
    assets = request(endpoint, token)
    if not isinstance(assets, list) or len(assets) >= 100:
        raise RuntimeError('Validation release listing truncated or unavailable')
    pending = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        name = path.stem+'-'+digest[:16]+path.suffix
        if not any(a['name'] == name for a in assets):
            pending.append(path)
    if len(assets)+len(pending)>30 or sum(a['size'] for a in assets)+sum(p.stat().st_size for p in pending)>240_000_000:
        raise RuntimeError('Validation release cumulative budget reached')
    links = []
    for path in files:
        body = path.read_bytes(); digest = hashlib.sha256(body).hexdigest()
        name = path.stem+'-'+digest[:16]+path.suffix
        found = next((a for a in assets if a['name'] == name), None)
        if found is None:
            mime = {'.mp4':'video/mp4', '.jpg':'image/jpeg', '.json':'application/json'}[path.suffix]
            uploaded = request('https://uploads.github.com/repos/'+REPO+'/releases/'+
                               str(release['id'])+'/assets?name='+name, token, 'POST', body, mime)
            found = request(API+'/releases/assets/'+str(uploaded['id']), token)
        url = verified_asset(found, name, digest, len(body))
        links.append(dict(file=path.name, sha256=digest, url=url))
    result = dict(release_url=release['html_url'], assets=links, published_to_tiktok=False,
                  completed_pairs=len(report), batch_complete=len(report)==3)
    (folder/'release-links.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
