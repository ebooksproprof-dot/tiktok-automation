"""Bind a stock file digest to current official page and license evidence."""
import datetime as dt
import hashlib
import json
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from media_rights import valid_source


def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'CasaSemEsforco/10.2'}), timeout=45) as response:
        body = response.read(2_000_001)
    if len(body) > 2_000_000:
        raise ValueError('LICENSE_EVIDENCE_TOO_LARGE')
    return body


def verify(record, fetcher=fetch):
    if (record.get('provider') != 'pixabay' or not valid_source(record)
            or not re.fullmatch(r'[a-f0-9]{64}', record.get('sha256', ''))):
        raise ValueError('UNVERIFIED_SOURCE_RIGHTS')
    page = fetcher(record['source_page'])
    text = page.decode('utf-8', errors='replace')
    objects = []
    for raw in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.S | re.I):
        try:
            obj = json.loads(raw)
            objects.extend(obj if isinstance(obj, list) else [obj])
        except ValueError:
            continue
    matched = next((obj for obj in objects if obj.get('@type') == 'VideoObject'
                    and obj.get('contentUrl') == record['url']
                    and obj.get('license') == record['license_url']
                    and (obj.get('author') or {}).get('name') == record['author']), None)
    if matched is None:
        raise ValueError('SOURCE_PAGE_DOES_NOT_CONFIRM_EXACT_FILE_AND_AUTHOR')
    terms = fetcher('https://pixabay.com/service/terms/')
    plain = re.sub('<[^>]+>', ' ', terms.decode('utf-8', errors='replace'))
    plain = ' '.join(plain.split())
    if 'commercial or non-commercial purposes' not in plain or 'royalty-free' not in plain:
        raise ValueError('CURRENT_COMMERCIAL_LICENSE_NOT_CONFIRMED')
    return {'source_sha256': record['sha256'], 'source_page': record['source_page'],
            'license_url': record['license_url'], 'binding_terms': 'https://pixabay.com/service/terms/',
            'page_sha256': hashlib.sha256(page).hexdigest(),
            'terms_sha256': hashlib.sha256(terms).hexdigest(),
            'author': record['author'], 'commercial_use': True,
            'reviewed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
            'use_scope': 'adapted illustrative educational video; no endorsement or standalone redistribution'}
