"""Official Pixabay and Commons adapters. All outputs require visual review."""
import html
import json
import re
import time
from urllib.parse import urlencode, urlsplit

from media_acquisition import AcquisitionError, request, safe_url, MIN_SCENE_SECONDS, MAX_SCENE_SECONDS
from media_rights import COMMONS_LICENSES


def plain(value):
    return ' '.join(html.unescape(re.sub('<[^>]*>', ' ', str(value))).split())[:2000]


def contextual(text, words):
    tokens = set(re.findall(r'[a-z]+', plain(text).lower()))
    return set(words).issubset(tokens)


def vertical(width, height):
    return width >= 1080 and height >= 1920 and .5 <= width / height <= .6


def crop_capable(width, height):
    # Final 9:16 crop must contain at least 1080x1920 native pixels.
    # Landscape sources require explicit visual framing review, never approval here.
    return width >= 1080 and height >= 1920 and .5 <= width / height <= 2.0


class CachedProvider:
    def __init__(self, cache, now=None):
        self.cache = cache
        self.now = time.time() if now is None else now
        self.requests = 0
        self.last_response_source = None

    def json(self, cache_key, url):
        key = self.name + ':' + cache_key
        cached = self.cache.get(key)
        if cached and 0 <= self.now - cached['at'] < 86400:
            self.last_response_source = 'cache'
            return cached['data']
        if self.requests >= 4:
            raise AcquisitionError('PROVIDER_REQUEST_BUDGET_REACHED')
        self.requests += 1
        with request(url) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise AcquisitionError('API_RESPONSE_TOO_LARGE')
        try:
            data = json.loads(raw)
            if not isinstance(data, dict) or 'error' in data:
                raise ValueError()
        except (ValueError, TypeError):
            raise AcquisitionError('API_RESPONSE_INVALID') from None
        # No request URL or key is persisted; only successful response data.
        self.last_response_source = 'live_api'
        self.cache[key] = dict(at=self.now, data=data)
        return data


class PixabayProvider(CachedProvider):
    name = 'pixabay'

    def __init__(self, key, cache, now=None):
        super().__init__(cache, now)
        if not key:
            raise AcquisitionError('PIXABAY_API_KEY_MISSING')
        self.key = key

    def search(self, category, query, words):
        # Modest user-triggered acquisition, not systematic library harvesting.
        params = dict(key=self.key, q=query[:100], video_type='film', safesearch='true',
                      min_width=1080, min_height=1920, per_page=15, page=1)
        data = self.json(query, 'https://pixabay.com/api/videos/?' + urlencode(params))
        result = []
        for hit in data.get('hits', [])[:15]:
            try:
                if not contextual(hit['tags'], words) or not MIN_SCENE_SECONDS <= float(hit['duration']) <= MAX_SCENE_SECONDS:
                    continue
                page = hit['pageURL']
                if not safe_url(page, 'pixabay.com') or not hit['user'].strip():
                    continue
                files = [f for f in hit['videos'].values()
                         if crop_capable(f['width'], f['height'])
                         and safe_url(f['url'], 'cdn.pixabay.com')
                         and f['url'].endswith('.mp4') and 0 < f.get('size', 0) <= 250*1024*1024]
                if not files:
                    continue
                file = min(files, key=lambda f: f['width'] * f['height'])
                result.append(dict(provider=self.name, provider_id=str(int(hit['id'])),
                    url=file['url'], source_page=page, author=plain(hit['user']),
                    license='Pixabay Content License', license_url='https://pixabay.com/service/license-summary/',
                    attribution=f"Video: {plain(hit['user'])} / Pixabay — {page}",
                    category=category, query=query, selection_reason='Provider tags: ' + plain(hit['tags']),
                    requires_crop_review=not vertical(file['width'], file['height']),
                    semantic_verified=False, editorial_approved=False, status='pending_visual_review'))
            except (KeyError, TypeError, ValueError, AttributeError, ZeroDivisionError):
                continue
        return result


# Explicit allowlist; ShareAlike/NC/ND/custom/unknown terms need a separate workflow.
def commons_record(page, category, query, words):
    try:
        info = page['imageinfo'][0]
        meta = info['extmetadata']
        value = lambda key: plain(meta.get(key, {}).get('value', ''))
        license_url = value('LicenseUrl')
        if license_url.startswith('http://creativecommons.org/'):
            license_url = 'https://' + license_url[len('http://'):]
        license_url = license_url.rstrip('/') + '/'
        author = value('Artist')
        if license_url not in COMMONS_LICENSES or not author or value('Restrictions'):
            return None
        context = page['title'] + ' ' + value('ImageDescription')
        if not contextual(context, words) or not vertical(info['width'], info['height']):
            return None
        if info['mime'] not in ('video/webm', 'video/ogg', 'video/mp4'):
            return None
        if not 0 < info['size'] <= 250*1024*1024:
            return None
        if not safe_url(info['url'], 'upload.wikimedia.org'):
            return None
        source = info['descriptionurl']
        if not safe_url(source, 'commons.wikimedia.org'):
            return None
        license_name = COMMONS_LICENSES[license_url]
        return dict(provider='wikimedia', provider_id=str(int(page['pageid'])),
            url=info['url'], source_page=source, author=author,
            title=plain(page['title']), license=license_name, license_url=license_url,
            attribution=f"{plain(page['title'])} — {author}; {license_name} ({license_url}); {source}",
            attribution_required=license_name != 'CC0 1.0',
            changes_notice='Adapted: vertical framing, cuts, narration and captions.',
            category=category, query=query, selection_reason='Title/description: ' + plain(context),
            semantic_verified=False, editorial_approved=False, status='pending_visual_review')
    except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError):
        return None


class WikimediaProvider(CachedProvider):
    name = 'wikimedia'

    def search(self, category, query, words):
        params = dict(action='query', format='json', generator='search',
            gsrsearch=' '.join(words) + ' filetype:video', gsrnamespace=6, gsrlimit=5,
            prop='imageinfo', iiprop='url|size|mime|extmetadata',
            iiextmetadatalanguage='en', maxlag=5)
        data = self.json('keywords:' + ','.join(words), 'https://commons.wikimedia.org/w/api.php?' + urlencode(params))
        records = [commons_record(p, category, query, words)
                   for p in data.get('query', {}).get('pages', {}).values()]
        return [record for record in records if record]


def credits(records):
    """Required credit text travels with every review artifact and future promotion."""
    return '\n\n'.join(r['attribution'] + '\n' + r['license_url'] + '\n' +
                       r.get('changes_notice', 'Adapted: framing, cuts, narration and captions.')
                       for r in records) + '\n'
