"""Persist experimental evidence as Release assets, never a publishing queue."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys

AUTOMATION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUTOMATION))
from release_media import API, REPO, request


def persist(folder):
    if os.getenv('GITHUB_ACTIONS') != 'true' or os.getenv('GITHUB_REF_NAME') != 'feature/ai-video-hybrid-30s':
        raise ValueError('EXPERIMENTAL_CLOUD_BRANCH_REQUIRED')
    token = os.environ['GH_TOKEN']
    commit = os.environ['GITHUB_SHA']
    if not re.fullmatch('[a-f0-9]{40}', commit):
        raise ValueError('FULL_COMMIT_REQUIRED')
    folder = Path(folder)
    files = [p for p in folder.rglob('*') if p.is_file() and
             ((p.name.startswith('experimental81-') and p.suffix in ('.mp4', '.json'))
              or p.name in ('cloud-result.json', 'generation-status.json'))]
    if len(files) > 12 or any(p.stat().st_size > 20_000_000 for p in files):
        raise ValueError('EXPERIMENTAL_STORAGE_BUDGET_EXCEEDED')
    if not files:
        return {'status': 'NO_OUTPUT_TO_PERSIST', 'publication_enabled': False}
    tag = 'experiment81-' + commit[:12]
    release = request(API + '/releases/tags/' + tag, token)
    if release is None:
        release = request(API + '/releases', token, 'POST', {
            'tag_name': tag, 'target_commitish': commit, 'name': 'Mission 8.1 experimental evidence ' + commit[:12],
            'draft': False, 'prerelease': True, 'make_latest': 'false',
            'body': 'Experimental evidence only. Not approved for social publication. '
                    'REFERENCE_ONLY outputs contain zero newly generated AI footage. '
                    'See paired JSON provenance and the experimental branch checkpoint.'})
    assets = request(API + '/releases/' + str(release['id']) + '/assets?per_page=100', token)
    if not isinstance(assets, list) or len(assets) >= 100:
        raise ValueError('ASSET_LIST_UNCONFIRMED')
    urls = []
    for path in sorted(files):
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        name = path.stem + '-' + digest[:16] + path.suffix
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', name):
            raise ValueError('UNSAFE_ASSET_NAME')
        found = next((x for x in assets if x['name'] == name), None)
        if found is None:
            found = request('https://uploads.github.com/repos/' + REPO + '/releases/' + str(release['id']) + '/assets?name=' + name,
                token, 'POST', body, 'video/mp4' if path.suffix == '.mp4' else 'application/json')
        actual = request(API + '/releases/assets/' + str(found['id']), token)
        if (actual.get('digest') != 'sha256:' + digest or actual.get('size') != len(body)
                or actual.get('state') != 'uploaded'):
            raise ValueError('RELEASE_READBACK_HASH_MISMATCH')
        expected = f'https://github.com/{REPO}/releases/download/{tag}/{name}'
        if actual.get('browser_download_url') != expected:
            raise ValueError('UNEXPECTED_ASSET_URL')
        urls.append({'file': path.name, 'sha256': digest, 'url': expected})
    result = {'release': release['html_url'], 'assets': urls, 'publication_enabled': False}
    print(json.dumps(result, indent=2))
    summary = os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as stream:
            stream.write('## Evidências persistentes 8.1\n\n' +
                '\n'.join('- [' + x['file'] + '](' + x['url'] + ')' for x in urls) + '\n')
    return result


if __name__ == '__main__':
    persist(sys.argv[1])
