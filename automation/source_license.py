"""Bind a stock file digest to current official page and license evidence."""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from media_rights import valid_source

CACHE = Path(__file__).with_name('stock_license_evidence.json')


def known_evidence(record):
    evidence = json.loads(CACHE.read_text()).get('sources', {}).get(record['url'], {}) if CACHE.exists() else {}
    if (evidence.get('source_sha256') == record.get('sha256')
            and evidence.get('author') == record.get('author')
            and evidence.get('source_page') == record.get('source_page')
            and evidence.get('license_url') == record.get('license_url')
            and evidence.get('commercial_use') is True
            and evidence.get('page_sha256') and evidence.get('terms_sha256')):
        # The recorded grant is perpetual for these exact bytes; a later WAF
        # denial doesn't revoke it. Never extend this evidence to another file.
        return dict(evidence, verification_method='previously_retrieved_official_evidence_exact_bytes')
    return None


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
    cached = known_evidence(record)
    if cached:
        return cached
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
