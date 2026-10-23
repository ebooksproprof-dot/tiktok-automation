"""Bounded official-API discovery. Inbox is NOT an editorial approval or publish queue."""
import json
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

from visual_library import fingerprint, check_sources, history

ROOT = Path(__file__).resolve().parent
MAX_BYTES = 250 * 1024 * 1024
# Source clips may be combined; the completed MP4 still requires 15–28 seconds.
MIN_SCENE_SECONDS = 5.0
MAX_SCENE_SECONDS = 300.0
TOPICS = [
    ('gavetas', 'organizing drawers', ['drawer']),
    ('cozinha', 'washing dishes sponge', ['sponge']),
    ('livros', 'arranging books shelves', ['books']),
    ('banheiro', 'organizing bathroom storage', ['bathroom']),
]


class AcquisitionError(Exception):
    """Only fixed, credential-free error codes cross the network boundary."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AcquisitionError('REDIRECT_REJECTED')


def safe_url(url, host):
    p = urllib.parse.urlsplit(url)
    return (p.scheme == 'https' and p.netloc == host and not p.query
            and not p.fragment and not p.username)


def request(url, key=None):
    headers = {'User-Agent': 'CasaSemEsforco/3.1 (https://github.com/ebooksproprof-dot/tiktok-automation)'}
    if key:
        headers['Authorization'] = key
    try:
        return urllib.request.build_opener(NoRedirect()).open(
            urllib.request.Request(url, headers=headers), timeout=45)
    except urllib.error.HTTPError as error:
        code = ('PROVIDER_AUTH_REJECTED' if error.code in (401, 403) else
                'PROVIDER_RATE_LIMITED' if error.code == 429 else
                'PROVIDER_SERVER_ERROR' if error.code >= 500 else 'PROVIDER_REQUEST_FAILED')
        raise AcquisitionError(code) from None
    except Exception:
        raise AcquisitionError('PROVIDER_REQUEST_FAILED') from None


class PexelsProvider:
    name = 'pexels'

    def __init__(self, key, cache, now=None):
        if not key:
            raise AcquisitionError('PEXELS_API_KEY_MISSING')
        self.key, self.cache = key, cache
        self.now = time.time() if now is None else now

    def search(self, query):
        cached = self.cache.get(query)
        if cached and 0 <= self.now - cached['at'] < 86400:
            return cached['videos']
        url = 'https://api.pexels.com/v1/videos/search?' + urllib.parse.urlencode(
            dict(query=query, orientation='portrait', per_page=15, page=1))
        with request(url, self.key) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise AcquisitionError('API_RESPONSE_TOO_LARGE')
        try:
            videos = json.loads(raw)['videos']
            # Persist only fields used by the selector; never request headers/key.
            videos = [{k: v.get(k) for k in ('id', 'url', 'user', 'duration', 'video_files')}
                      for v in videos[:15]]
        except (ValueError, KeyError, TypeError):
            raise AcquisitionError('API_RESPONSE_INVALID') from None
        self.cache[query] = dict(at=self.now, videos=videos)
        return videos


def candidates(videos, category, query, required_words):
    result = []
    for video in videos:
        try:
            page = video['url']
            words = set(re.findall(r'[a-z]+', urllib.parse.urlsplit(page).path.lower()))
            if not safe_url(page, 'www.pexels.com') or not page.startswith('https://www.pexels.com/video/'):
                continue
            if (not set(required_words).issubset(words) or
                not MIN_SCENE_SECONDS <= float(video['duration']) <= MAX_SCENE_SECONDS):
                continue
            author = video['user']['name']
            if not isinstance(author, str) or not author.strip():
                continue
            files = [f for f in video['video_files']
                     if f['file_type'] == 'video/mp4' and f['width'] >= 1080
                     and f['height'] >= 1920 and .5 <= f['width']/f['height'] <= .6
                     and safe_url(f['link'], 'videos.pexels.com')
                     and f['link'].endswith('.mp4')]
            if not files:
                continue
            selected = min(files, key=lambda f: f['width'] * f['height'])
            result.append(dict(provider='pexels', provider_id=str(int(video['id'])),
                url=selected['link'], source_page=page, author=author,
                license_url='https://www.pexels.com/license/',
                attribution=f'Video: {author} / Pexels — {page}',
                category=category, query=query,
                selection_reason='Source-page keywords: ' + ', '.join(required_words),
                semantic_verified=False, editorial_approved=False,
                status='pending_visual_review'))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    return result


MEDIA_HOSTS = {'pexels': 'videos.pexels.com', 'pixabay': 'cdn.pixabay.com',
               'wikimedia': 'upload.wikimedia.org'}


def media_allowed(record):
    host = MEDIA_HOSTS.get(record.get('provider'))
    return bool(host and safe_url(record['url'], host))


def media_name(record):
    suffix = Path(urllib.parse.urlsplit(record['url']).path).suffix.lower()
    if suffix not in ('.mp4', '.webm', '.ogv', '.ogg'):
        raise AcquisitionError('MEDIA_EXTENSION_REJECTED')
    return record['provider'] + '-' + str(int(record['provider_id'])) + suffix


def prepare_review_artifact(record, source, destination):
    """Bound artifact storage; original bytes remain recoverable by URL + SHA."""
    destination.mkdir(parents=True, exist_ok=True)
    if source.stat().st_size <= 8 * 1024 * 1024:
        shutil.copyfile(source, destination/source.name)
    else:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-t', '10',
                        '-vf', 'fps=0.6,scale=270:480:force_original_aspect_ratio=decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2:color=0x202020,tile=3x2', '-frames:v', '1',
                        str(destination/(source.stem + '-first-10s.jpg'))], check=True, timeout=90)
    save_json(destination/(source.stem + '.json'), record)


def download_and_measure(record, folder, previous):
    if not media_allowed(record):
        raise AcquisitionError('MEDIA_ORIGIN_REJECTED')
    destination = folder / media_name(record)
    temporary = destination.with_suffix('.part')
    try:
        with request(record['url']) as response, temporary.open('wb') as output:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_BYTES:
                    raise AcquisitionError('MEDIA_TOO_LARGE')
                output.write(chunk)
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
            '-show_streams', '-show_format', '-of', 'json', str(temporary)], timeout=30))
        stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        w, h = int(stream['width']), int(stream['height'])
        duration = float(probe['format']['duration'])
        max_ratio = 2.0 if record.get('provider') == 'pixabay' else .6
        if w < 1080 or h < 1920 or not .5 <= w/h <= max_ratio or not MIN_SCENE_SECONDS <= duration <= MAX_SCENE_SECONDS:
            raise AcquisitionError('MEDIA_TECHNICAL_REJECTED')
        evidence = fingerprint(temporary, record['url'])
        check_sources([evidence], previous)
        temporary.replace(destination)
        return dict(record, **evidence, width=w, height=h, duration=duration,
                    bytes=total, acquired_at=int(time.time()))
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save_json(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def recover(provider_id):
    """Re-download an inbox asset for review, requiring its original byte digest."""
    inbox = read_json(ROOT/'media_inbox.json', {'items': []})
    provider, provider_id = provider_id.split(':', 1) if ':' in provider_id else ('pexels', provider_id)
    matches = [r for r in inbox['items'] if r['provider'] == provider
               and r['provider_id'] == provider_id]
    if len(matches) != 1:
        raise AcquisitionError('INBOX_ID_NOT_UNIQUE')
    record = matches[0]
    if not media_allowed(record):
        raise AcquisitionError('MEDIA_ORIGIN_REJECTED')
    folder = ROOT.parent/'tmp'/'media-inbox'
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder/media_name(record)
    temporary = destination.with_suffix('.part')
    digest, total = hashlib.sha256(), 0
    try:
        with request(record['url']) as response, temporary.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_BYTES:
                    raise AcquisitionError('MEDIA_TOO_LARGE')
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != record['sha256']:
            raise AcquisitionError('RECOVERY_SHA_MISMATCH')
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    from media_providers import credits
    # Recover attribution together with the exact media bytes after artifact expiry.
    if record.get('attribution') and record.get('license_url'):
        destination.with_suffix('.credits.txt').write_text(credits([record]))
    print('RECOVERED_FOR_REVIEW; EDITORIAL_APPROVED=0')


def run():
    from media_providers import PixabayProvider, WikimediaProvider, credits
    cache_path, inbox_path = ROOT/'media_search_cache.json', ROOT/'media_inbox.json'
    cache = read_json(cache_path, {})
    inbox = read_json(inbox_path, {'items': []})
    now = int(time.time())
    rejected = {key: until for key, until in inbox.get('rejected_until', {}).items()
                if until > now}
    inbox['rejected_until'] = rejected
    # Hard storage/review backlog limit; never evict deduplication history.
    if len(inbox['items']) >= 120:
        raise AcquisitionError('INBOX_REVIEW_CAPACITY_REACHED')
    providers = {}
    for name in os.environ.get('MEDIA_PROVIDER_ORDER', 'pixabay,wikimedia,pexels').split(','):
        name = name.strip()
        if name in providers:
            continue
        if name == 'wikimedia':
            providers[name] = WikimediaProvider(cache)
        elif name in ('pexels', 'pixabay'):
            key = os.environ.get(name.upper() + '_API_KEY')
            print(name.upper() + '_API_KEY_PRESENT=' + str(bool(key)))
            if key:
                providers[name] = (PexelsProvider if name == 'pexels' else PixabayProvider)(key, cache)
        else:
            raise AcquisitionError('UNKNOWN_PROVIDER')
    if not providers:
        raise AcquisitionError('NO_AUTHORIZED_PROVIDER')
    previous = history(read_json(ROOT/'queue.json', {}), read_json(ROOT/'state.json', {}))
    previous += [read_json(ROOT/'visual_history.json', {}), {'visual_sources': inbox['items']}]
    folder = ROOT.parent/'tmp'/'media-inbox'
    folder.mkdir(parents=True, exist_ok=True)
    acquired, attempts = 0, 0
    known = {x['provider'] + ':' + x['provider_id'] for x in inbox['items']}
    # At most four queries/provider and four downloads total per run.
    offset = int(time.time() // 86400) % len(TOPICS)
    errors = []
    diagnostics = []
    try:
        disabled = set()
        for category, query, words in TOPICS[offset:] + TOPICS[:offset]:
            for name, provider in providers.items():
                if name in disabled:
                    continue
                try:
                    records = (candidates(provider.search(query), category, query, words)
                               if name == 'pexels' else provider.search(category, query, words))
                except (AcquisitionError, KeyError, TypeError, ValueError, AttributeError) as error:
                    print('PROVIDER_UNAVAILABLE=' + name)
                    diagnostics.append(dict(provider=name, status=str(error) if isinstance(error, AcquisitionError)
                                            else 'PROVIDER_RESPONSE_INVALID'))
                    disabled.add(name)  # no retry storm, especially after 429/maxlag
                    continue
                print('PROVIDER_SEARCH_OK=' + name + '; CANDIDATES=' + str(len(records)))
                diagnostics.append(dict(provider=name, category=category, status='search_ok',
                                        eligible_candidates=len(records),
                                        response_source=getattr(provider, 'last_response_source', 'not_recorded')))
                provider_attempts = 0
                for record in records:
                    identity = name + ':' + record['provider_id']
                    if identity in known or identity in rejected:
                        continue
                    if provider_attempts >= 1 or attempts >= 4 or acquired >= 2 or len(inbox['items']) >= 120:
                        break
                    attempts += 1
                    provider_attempts += 1
                    try:
                        measured = download_and_measure(record, folder, previous)
                    except (AcquisitionError, ValueError, subprocess.SubprocessError, StopIteration, KeyError) as error:
                        code = str(error) if isinstance(error, AcquisitionError) else 'CANDIDATE_VALIDATION_REJECTED'
                        errors.append(code)
                        diagnostics.append(dict(provider=name, provider_id=record['provider_id'], status=code))
                        transient = code in ('PROVIDER_RATE_LIMITED', 'PROVIDER_SERVER_ERROR', 'PROVIDER_REQUEST_FAILED')
                        rejected[identity] = now + (3600 if transient else 7 * 86400)
                        continue
                    inbox['items'].append(measured)
                    previous.append({'visual_sources': [measured]})
                    known.add(identity)
                    acquired += 1
                    prepare_review_artifact(measured, folder/media_name(measured),
                                            folder.parent/'media-review')
                if attempts >= 4 or acquired >= 2:
                    break
            if attempts >= 4 or acquired >= 2:
                break
    finally:
        inbox['last_run'] = dict(at=now, acquired=acquired, rejected=len(errors),
                                diagnostics=diagnostics, editorial_approved=0)
        save_json(cache_path, cache)
        save_json(inbox_path, inbox)
        (folder/'CREDITS.txt').write_text(credits(inbox['items']))
        review_folder = folder.parent/'media-review'
        review_folder.mkdir(parents=True, exist_ok=True)
        (review_folder/'CREDITS.txt').write_text(credits(inbox['items']))
    print(f'ACQUIRED={acquired}; REJECTED={len(errors)}; EDITORIAL_APPROVED=0')
    from editorial_drafts import main as draft_from_media
    draft_from_media(ROOT)
    if not acquired:
        raise AcquisitionError('NO_NEW_REVIEWABLE_MEDIA')


if __name__ == '__main__':
    try:
        if len(sys.argv) == 3 and sys.argv[1] == '--recover':
            recover(sys.argv[2])
        elif len(sys.argv) == 1:
            run()
        else:
            raise AcquisitionError('INVALID_ARGUMENTS')
    except Exception as error:
        # Do not serialize exception text from HTTP/ffprobe/provider payloads.
        print('ACQUISITION_BLOCKED=' + (str(error) if isinstance(error, AcquisitionError)
                                      else 'LOCAL_VALIDATION_FAILED'))
        raise SystemExit(1)
