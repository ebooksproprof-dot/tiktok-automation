"""Reviewed, bounded content packs. No scraping, paid API or invented licenses."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from media_rights import valid_source

PATH = Path(__file__).with_name('catalog_extension.json')
CATEGORIES = {'limpeza', 'organizacao', 'preparacao', 'conservacao', 'rotina'}

def slug(value):
    return isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9-]{2,63}', value)

def load(path=PATH):
    if not path.exists():
        return {}, [], {}
    data = json.loads(path.read_text(encoding='utf8'))
    if data.get('version') != 1 or len(data.get('items', [])) > 120:
        raise ValueError('Invalid content pack version or size')
    sources, topics, provenance = {}, [], {}
    for item in data['items']:
        key = item.get('id')
        if not slug(key) or any(t[0] == key for t in topics):
            raise ValueError('Invalid or duplicate content ID')
        if item.get('reviewed') is not True or not item.get('reviewed_at'):
            raise ValueError('Content pack requires explicit editorial provenance')
        if item.get('category') not in CATEGORIES:
            raise ValueError('Invalid category')
        for field, minimum, maximum in [('hook', 8, 100), ('steps', 160, 600), ('cta', 8, 100)]:
            value = item.get(field)
            if not isinstance(value, str) or not minimum <= len(value) <= maximum:
                raise ValueError('Invalid script field: '+field)
        media = item.get('media', [])
        if not 1 <= len(media) <= 3:
            raise ValueError('One to three contextual clips required')
        keys = []
        for asset in media:
            asset_id = asset.get('id')
            url = urlparse(asset.get('url', ''))
            page = urlparse(asset.get('source_page', ''))
            if (not slug(asset_id) or not valid_source(asset)
                or not asset.get('author') or len(asset.get('context', '')) < 20
                or not re.fullmatch(r'[a-f0-9]{64}', asset.get('sha256', ''))):
                raise ValueError('Invalid source, license, context or fingerprint')
            if asset_id in sources and provenance[asset_id] != asset:
                raise ValueError('Conflicting asset identity')
            sources[asset_id] = asset['url']; provenance[asset_id] = asset
            keys.append(asset_id)
        topics.append((key, item['category'], keys, item['hook'], item['steps'], item['cta']))
    return sources, topics, provenance

SOURCES, TOPICS, PROVENANCE = load()
