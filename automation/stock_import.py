"""Import reviewed Symphony exports from the public stock-inbox GitHub Release.

Upload NAME.mp4 and NAME.json. Files stay in Releases; no MP4 enters Git history.
Attestations describe the uploader's review, never automated identity verification.
Invalid/incomplete uploads remain retryable, with no publishing side effects.
"""
import hashlib
from datetime import datetime, timezone
import json
import re
import tempfile
import urllib.request
from pathlib import Path

from media_quality import validate
from release_media import API, REPO, request

TAG = 'stock-inbox'
MAX_VIDEO_BYTES = 20_000_000
MAX_MANIFEST_BYTES = 128_000
IDENTITY = {'avatar_id': '7616458821397659655', 'voice_name': 'Keren', 'locale': 'pt-BR'}
ATTESTATIONS = ('identity_reviewed', 'lip_sync_reviewed', 'subtitles_reviewed',
                'editorial_approved', 'rights_confirmed', 'publication_approved')


def script_hash(script):
    return hashlib.sha256(' '.join(script.split()).casefold().encode()).hexdigest()


def manifest_check(manifest):
    if not isinstance(manifest, dict):
        raise ValueError('MANIFEST_OBJECT_REQUIRED')
    for key, expected in IDENTITY.items():
        if manifest.get(key) != expected:
            raise ValueError('OFFICIAL_IDENTITY_REQUIRED')
    if type(manifest.get('commercial_content')) is not bool:
        raise ValueError('COMMERCIAL_CONTENT_DECLARATION_REQUIRED')
    try:
        reviewed = datetime.fromisoformat(manifest.get('reviewed_at', '').replace('Z', '+00:00'))
        if reviewed.tzinfo is None or reviewed > datetime.now(timezone.utc):
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError('VALID_REVIEW_TIMESTAMP_REQUIRED') from None
    for key in ATTESTATIONS:
        if manifest.get(key) is not True:
            raise ValueError('UPLOADER_REVIEW_REQUIRED')
    for key in ('script', 'topic', 'caption', 'source_evidence'):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            raise ValueError('MANIFEST_TEXT_REQUIRED')
    if not 40 <= len(manifest['script']) <= 2000 or len(manifest['caption']) > 2200:
        raise ValueError('TEXT_LIMIT_EXCEEDED')
    if len(re.findall(r'(?<!\w)#\w+', manifest['caption'])) > 5:
        raise ValueError('TOO_MANY_HASHTAGS')
    if not re.fullmatch('[a-f0-9]{64}', manifest.get('sha256', '')):
        raise ValueError('SHA256_REQUIRED')
    # Evidence is public metadata. Never accept credential-bearing signed URLs.
    if '?' in manifest['source_evidence'] or len(manifest['source_evidence']) > 1000:
        raise ValueError('USE_PUBLIC_NON_SECRET_EVIDENCE_REFERENCE')
    return manifest


def safe_asset_url(asset):
    name = asset.get('name', '')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\.(?:mp4|json)', name):
        raise ValueError('UNSAFE_ASSET_NAME')
    expected = f'https://github.com/{REPO}/releases/download/{TAG}/{name}'
    if asset.get('browser_download_url') != expected or asset.get('state') != 'uploaded':
        raise ValueError('UNEXPECTED_OR_INCOMPLETE_ASSET')
    return expected


def download(asset, path, limit):
    url = safe_asset_url(asset)
    size = asset.get('size')
    if type(size) is not int or not 0 < size <= limit:
        raise ValueError('ASSET_SIZE_LIMIT')
    # Public asset URL only; no token is sent through GitHub's binary redirect.
    with urllib.request.urlopen(url, timeout=60) as response, Path(path).open('wb') as target:
        total = 0
        while chunk := response.read(min(1024 * 1024, limit + 1)):
            total += len(chunk)
            if total > limit:
                raise ValueError('DOWNLOAD_SIZE_LIMIT')
            target.write(chunk)
    if total != size:
        raise ValueError('INCOMPLETE_DOWNLOAD')


def list_assets(token):
    release = request(API + '/releases/tags/' + TAG, token)
    if release is None:
        return []
    if release.get('draft') or release.get('tag_name') != TAG:
        raise ValueError('PUBLIC_STOCK_INBOX_RELEASE_REQUIRED')
    assets = []
    for page in range(1, 11):
        batch = request(API + '/releases/' + str(release['id']) + f'/assets?per_page=100&page={page}', token)
        if not isinstance(batch, list):
            raise ValueError('INVALID_RELEASE_LIST')
        assets.extend(batch)
        if len(batch) < 100:
            return assets
    raise ValueError('INBOX_TOO_LARGE_REVIEW_REQUIRED')


def legacy_fingerprints(legacy_queue=None, legacy_state=None):
    hashes, scripts = set(), set()
    posts = list((legacy_queue or {}).get('posts', []))
    posts += list((legacy_state or {}).get('posts', {}).values())
    for post in posts:
        for value in (post.get('sha256'), (post.get('quality') or {}).get('sha256')):
            if value:
                hashes.add(value)
        if post.get('script_sha256'):
            scripts.add(post['script_sha256'])
        if post.get('script'):
            scripts.add(script_hash(post['script']))
        if post.get('script_lines'):
            scripts.add(script_hash(' '.join(post['script_lines'])))
    return hashes, scripts


def prepare_candidate(asset, manifest, local_path, *, legacy_queue=None, legacy_state=None):
    manifest_check(manifest)
    url = safe_asset_url(asset)
    digest = hashlib.sha256(Path(local_path).read_bytes()).hexdigest()
    if digest != manifest['sha256']:
        raise ValueError('MEDIA_HASH_MISMATCH')
    hashes, scripts = legacy_fingerprints(legacy_queue, legacy_state)
    script_digest = script_hash(manifest['script'])
    if digest in hashes or script_digest in scripts:
        raise ValueError('LEGACY_DUPLICATE')
    quality = validate(local_path)
    if quality.get('technical_pass') is not True or quality.get('sha256') != digest:
        raise ValueError('VALIDATION_FAILED')
    return dict(id='stock-' + digest, filename=asset['name'], storage_url=url,
                sha256=digest, created_at=asset['created_at'], script=manifest['script'],
                script_sha256=script_digest, subject=manifest['topic'], caption=manifest['caption'],
                commercial_content=manifest['commercial_content'], reviewed_at=manifest['reviewed_at'],
                consented_at=manifest['reviewed_at'],
                identity_reviewed=True, rights_reviewed=True, editorial_reviewed=True,
                lip_sync_reviewed=True, subtitles_reviewed=True,
                **IDENTITY, duration=quality['duration'], validation_status='PASSED',
                quality=quality, validation=quality,
                review={key: manifest[key] for key in ATTESTATIONS},
                source_evidence=manifest['source_evidence'],
                review_source='Uploader attestation bound to media SHA256; not machine verification',
                source_asset_id=asset['id'], source_asset_updated_at=asset.get('updated_at') or asset['created_at'],
                source_created_at=asset['created_at'],
                media_persisted=True, status='READY')


def scan(token, accept, *, known_asset_ids=(), legacy_queue=None, legacy_state=None):
    """Download new pairs, validate, call accept(candidate) to durably insert.

    accept must perform atomic hash/script uniqueness checks. It may return false
    for an already-known candidate. Exceptions fail that pair only; uploads are
    reconsidered next run. Report contains IDs/error codes, never private content.
    """
    assets = list_assets(token)
    by_name = {a.get('name'): a for a in assets}
    report = {'imported': [], 'skipped': [], 'errors': [], 'waiting_for_manifest': []}
    for asset in assets:
        name = asset.get('name', '')
        if not name.endswith('.mp4'):
            continue
        if asset.get('id') in known_asset_ids:
            report['skipped'].append(asset['id'])
            continue
        metadata = by_name.get(name[:-4] + '.json')
        if not metadata:
            report['waiting_for_manifest'].append(asset.get('id'))
            continue
        try:
            with tempfile.TemporaryDirectory() as folder:
                manifest_path, media_path = Path(folder)/'manifest.json', Path(folder)/'video.mp4'
                download(metadata, manifest_path, MAX_MANIFEST_BYTES)
                manifest = json.loads(manifest_path.read_text())
                manifest_check(manifest)
                download(asset, media_path, MAX_VIDEO_BYTES)
                candidate = prepare_candidate(asset, manifest, media_path,
                    legacy_queue=legacy_queue, legacy_state=legacy_state)
                accepted = accept(candidate)
                report['imported' if accepted is not False else 'skipped'].append(asset['id'])
        except Exception as exc:
            # Validator/HTTP failures may contain filenames, captions or bodies.
            # Only a stable class marker leaves this component.
            code = str(exc) if re.fullmatch(r'[A-Z][A-Z0-9_]{2,79}', str(exc)) else 'IMPORT_FAILED'
            report['errors'].append({'asset_id': asset.get('id'), 'error': type(exc).__name__,
                                     'code': code, 'retryable_import': True})
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create a reviewed MP4 companion manifest for stock-inbox.')
    parser.add_argument('command', choices=['manifest'])
    parser.add_argument('--video', type=Path, required=True)
    parser.add_argument('--script-file', type=Path, required=True)
    parser.add_argument('--topic', required=True)
    parser.add_argument('--caption', required=True)
    parser.add_argument('--source-evidence', required=True)
    parser.add_argument('--commercial-content', choices=['true', 'false'], required=True)
    parser.add_argument('--reviewed-all', action='store_true', required=True,
                        help='Confirm official avatar/Keren/pt-BR, lip sync, subtitles, rights, editorial quality and permission to publish this exact MP4.')
    args = parser.parse_args()
    if args.video.suffix != '.mp4' or not args.video.is_file():
        parser.error('Select an existing .mp4 file')
    # Filename must be acceptable to the public GitHub Release import.
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\.mp4', args.video.name):
        parser.error('Use a simple ASCII filename, for example bancada-01.mp4')
    output = args.video.with_suffix('.json')
    data = dict(IDENTITY, **{key: True for key in ATTESTATIONS},
                sha256=hashlib.sha256(args.video.read_bytes()).hexdigest(),
                script=args.script_file.read_text(), topic=args.topic, caption=args.caption,
                source_evidence=args.source_evidence,
                commercial_content=args.commercial_content == 'true',
                reviewed_at=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
    manifest_check(data)
    with output.open('x') as target:
        json.dump(data, target, ensure_ascii=False, indent=2)
        target.write('\n')
    print('Manifest created: ' + output.name + '; upload this file and the matching MP4 to stock-inbox.')


if __name__ == '__main__':
    main()
