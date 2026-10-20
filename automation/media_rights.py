"""Approved source boundaries and public attribution for reviewed content packs."""
from urllib.parse import urlsplit

COMMONS_LICENSES = {
    'https://creativecommons.org/publicdomain/zero/1.0/': 'CC0 1.0',
    'https://creativecommons.org/licenses/by/4.0/': 'CC BY 4.0',
    'https://creativecommons.org/licenses/by/3.0/': 'CC BY 3.0',
}


def valid_source(asset):
    provider = asset.get('provider', 'pexels')
    url, page = urlsplit(asset.get('url', '')), urlsplit(asset.get('source_page', ''))
    if any(p.scheme != 'https' or p.query or p.fragment or p.username for p in (url, page)):
        return False
    license_url = asset.get('license_url')
    if provider == 'pexels':
        return (url.netloc == 'videos.pexels.com' and url.path.endswith('.mp4')
                and page.netloc == 'www.pexels.com' and page.path.startswith('/video/')
                and license_url == 'https://www.pexels.com/license/')
    if provider == 'pixabay':
        return (url.netloc == 'cdn.pixabay.com' and url.path.endswith('.mp4')
                and page.netloc == 'pixabay.com' and page.path.startswith('/videos/')
                and license_url == 'https://pixabay.com/service/license-summary/')
    if provider == 'wikimedia':
        return (url.netloc == 'upload.wikimedia.org' and url.path.lower().endswith(('.webm', '.ogv', '.ogg', '.mp4'))
                and page.netloc == 'commons.wikimedia.org' and page.path.startswith('/wiki/File:')
                and license_url in COMMONS_LICENSES and not asset.get('restrictions'))
    return False


def public_credit(asset):
    if not valid_source(asset) or not asset.get('author'):
        raise ValueError('Source rights or author missing')
    return (f"{asset.get('title', 'Video')} — {asset['author']}; "
            f"{asset['source_page']}; {asset['license_url']}. "
            'Adaptacoes: enquadramento, cortes, narracao e legendas.')


def caption_with_credits(caption, assets):
    credits = [public_credit(asset) for asset in assets]
    result = caption + ('\n\n' + '\n'.join(credits) if credits else '')
    if len(result) > 2200:
        raise ValueError('Caption and required credits exceed safe publishing limit')
    return result, credits
