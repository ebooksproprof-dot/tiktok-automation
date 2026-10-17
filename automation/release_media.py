"""Publish generated video binaries as immutable release assets, outside Git history.

No deletion, clobbering, LFS, paid storage, or credential output. One monthly release.
An interrupted upload is reconciled by deterministic SHA-256 asset name + digest.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

REPO = 'ebooksproprof-dot/tiktok-automation'
API = 'https://api.github.com/repos/' + REPO


def request(url, token, method='GET', data=None, content_type='application/json'):
    body = json.dumps(data).encode() if isinstance(data, dict) else data
    req = urllib.request.Request(url, data=body, method=method, headers={
        'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': content_type})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and method == 'GET':
            return None
        raise RuntimeError('Release media HTTP ' + str(exc.code) + '; response omitted') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Release media outcome uncertain; next run must reconcile asset by hash') from None


def verified_asset(asset, name, digest, size):
    if asset.get('name') != name or asset.get('state') != 'uploaded' or asset.get('size') != size:
        raise ValueError('Release media asset incomplete or mismatched')
    if asset.get('digest') != 'sha256:' + digest:
        raise ValueError('Release media digest absent or mismatched; do not overwrite')
    url = asset.get('browser_download_url', '')
    if not url.startswith('https://github.com/' + REPO + '/releases/download/') or not url.endswith('/' + name):
        raise ValueError('Unexpected release download URL')
    return url


def publish(path, post_id, quality):
    path = Path(path)
    if not re.fullmatch(r'casasem-\d{4}-\d{2}-\d{2}-[12]', post_id):
        raise ValueError('Invalid video ID')
    body = path.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    if not quality.get('technical_pass') or digest != quality.get('sha256') or len(body) > 20_000_000:
        raise ValueError('Release upload requires validated media within 20 MB')
    token = os.getenv('GH_TOKEN', '')
    if not token or os.getenv('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Release upload requires authorized cloud runner token')
    tag = 'media-' + post_id[8:15]
    name = post_id + '-' + digest[:16] + '.mp4'
    release = request(API + '/releases/tags/' + tag, token)
    if release is None:
        release = request(API + '/releases', token, 'POST', {
            'tag_name': tag, 'target_commitish': os.environ.get('GITHUB_SHA', 'main'),
            'name': 'Generated videos ' + tag[6:], 'draft': False, 'prerelease': False,
            'make_latest': 'false',
            'body': 'Generated audiovisual outputs of the CasaSemEsforco renderer. '
                    'Availability here is not evidence of editorial approval or TikTok publication.'})
    assets = request(API + '/releases/' + str(release['id']) + '/assets?per_page=100', token)
    if not isinstance(assets, list):
        raise RuntimeError('Unable to reconcile release assets')
    found = next((a for a in assets if a.get('name') == name), None)
    if found:
        return verified_asset(found, name, digest, len(body))
    if len(assets) >= 64:
        raise RuntimeError('Monthly release budget reached; inspect before adding more media')
    # No retry here: a lost reply is reconciled by name and digest next run.
    url = 'https://uploads.github.com/repos/' + REPO + '/releases/' + str(release['id']) + '/assets?name=' + name
    uploaded = request(url, token, 'POST', body, 'video/mp4')
    # Independent read-back before queue can use the asset.
    confirmed = request(API + '/releases/assets/' + str(uploaded['id']), token)
    return verified_asset(confirmed, name, digest, len(body))


def migrate_unpublished():
    from tiktok_runner import ROOT, load_json, save_json
    from media_quality import validate
    queue_path = ROOT / 'queue.json'
    queue = load_json(queue_path, {'posts': []})
    state = load_json(ROOT / 'state.json', {'posts': {}})
    for entry in queue['posts']:
        if entry.get('id') in state['posts'] or entry.get('media_storage') == 'release' or entry.get('render_version') != 2:
            continue
        path = ROOT.parent / 'public/rendered/daily' / (entry['id'] + '-v2.mp4')
        quality = validate(path)
        if quality['sha256'] != entry['quality']['sha256']:
            raise ValueError('Migration refused: bytes differ from queued hash')
        entry['video_url'] = publish(path, entry['id'], quality)
        entry['media_storage'] = 'release'
        save_json(queue_path, queue)
        print('RELEASE_MEDIA_VERIFIED=' + entry['id'])


if __name__ == '__main__':
    migrate_unpublished()
