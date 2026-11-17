"""Bind a stock file digest to current official page and license evidence."""
import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path
import os
from urllib.parse import urlencode
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from media_rights import valid_source

CACHE = Path(__file__).with_name('stock_license_evidence.json')
POLICY = Path(__file__).with_name('pixabay_license_policy.json')
API_CHECKS = 0
MAX_API_CHECKS = 6  # Two outputs can require three short source clips each.


class SourceLicenseBudgetExceeded(RuntimeError):
    """Local per-process cap, not a provider 429 or an uncertain mutation."""


def known_evidence(record):
    evidence = json.loads(CACHE.read_text()).get('sources', {}).get(record['url'], {}) if CACHE.exists() else {}
    ledger = CACHE.with_name('production_state.json')
    if not evidence and ledger.exists():
        evidence = json.loads(ledger.read_text()).get('candidates', {}).get(record['url'], {}).get('license', {})
    if (evidence.get('source_sha256') == record.get('sha256')
            and evidence.get('author') == record.get('author')
            and evidence.get('source_page') == record.get('source_page')
            and evidence.get('license_url') == record.get('license_url')
            and evidence.get('commercial_use') is True
            and re.fullmatch(r'[a-f0-9]{64}', evidence.get('page_sha256', ''))
            and re.fullmatch(r'[a-f0-9]{64}', evidence.get('terms_sha256', ''))):
        # The recorded grant is perpetual for these exact bytes; a later WAF
        # denial doesn't revoke it. Never extend this evidence to another file.
        return dict(evidence, verification_method='previously_retrieved_official_evidence_exact_bytes')
    return None



def refreshed_policy(policy, terms, docs, now=None):
    """Accept only positive evidence from both official terms and API docs."""
    def text(body):
        return ' '.join(html.unescape(re.sub('<[^>]+>', ' ', body.decode('utf-8', errors='replace'))).split())
    terms_text, docs_text = text(terms), text(docs)
    phrase = 'commercial or non-commercial purposes'
    api_phrase = 'images and videos released by Pixabay under the Content License'
    if phrase not in terms_text or 'royalty-free' not in terms_text or api_phrase not in docs_text:
        raise ValueError('CURRENT_OFFICIAL_API_LICENSE_POLICY_REQUIRED')
    at, api_at = terms_text.index(phrase), docs_text.index(api_phrase)
    return dict(policy, retrieved_at=(now or dt.datetime.now(dt.timezone.utc)).isoformat(),
        terms_sha256=hashlib.sha256(terms_text.encode()).hexdigest(),
        terms_response_sha256=hashlib.sha256(terms).hexdigest(),
        commercial_grant_excerpt=terms_text[max(0, at-450):at+220],
        api_docs_url='https://pixabay.com/api/docs/',
        api_license_excerpt=docs_text[max(0, api_at-130):api_at+180],
        api_docs_text_sha256=hashlib.sha256(docs_text.encode()).hexdigest(),
        verification_method='current_official_public_HTTPS_terms_and_API_documentation')

def policy_evidence():
    policy = json.loads(POLICY.read_text()) if POLICY.exists() else {}
    try:
        checked = dt.datetime.fromisoformat(policy['retrieved_at'])
        age = dt.datetime.now(dt.timezone.utc)-checked
        current = checked.tzinfo and dt.timedelta(0) <= age <= dt.timedelta(days=7)
    except (KeyError, ValueError, TypeError):
        current = False
    if not current:
        # Prefer simple official HTTPS documents; browser challenges must not be
        # the only path to retrieving a publicly accessible license. No bypass.
        try:
            policy = refreshed_policy(policy, fetch('https://pixabay.com/service/terms/'),
                                      fetch('https://pixabay.com/api/docs/'))
        except (OSError, ValueError):
            pass  # The ordinary public browser remains a separate fallback.
        else:
            POLICY.write_text(json.dumps(policy, ensure_ascii=False, indent=2)+'\n')
            current = True
    if not current:
        # Normal public browsing, never CAPTCHA solving or login. A failure
        # holds new assets; previously documented perpetual grants remain valid.
        from playwright.sync_api import sync_playwright
        import shutil
        with sync_playwright() as p:
            executable = next((shutil.which(x) for x in ('google-chrome', 'chromium') if shutil.which(x)), None)
            browser = p.chromium.launch(headless=True, executable_path=executable, args=['--no-sandbox'])
            try:
                page = browser.new_page()
                page.goto('https://pixabay.com/service/terms/', wait_until='domcontentloaded', timeout=45000)
                page.wait_for_function('() => document.body.innerText.includes("commercial or non-commercial purposes")', timeout=25000)
                text = ' '.join(page.inner_text('body').split())
                at = text.index('commercial or non-commercial purposes')
                policy.update(retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                    terms_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    commercial_grant_excerpt=text[max(0, at-450):at+220],
                    verification_method='public_browser_current_binding_terms')
                POLICY.write_text(json.dumps(policy, ensure_ascii=False, indent=2)+'\n')
            finally:
                browser.close()
    if ('commercial or non-commercial purposes' not in policy.get('commercial_grant_excerpt', '')
            or 'Content License' not in policy.get('api_license_excerpt', '')
            or not policy.get('api_docs_url')):
        raise ValueError('CURRENT_OFFICIAL_API_LICENSE_POLICY_REQUIRED')
    return policy


def verify_api(record, key, transport=None, policy=None):
    global API_CHECKS
    if API_CHECKS >= MAX_API_CHECKS:
        raise SourceLicenseBudgetExceeded('SOURCE_LICENSE_API_BUDGET_EXHAUSTED')
    API_CHECKS += 1
    policy = policy or policy_evidence()
    if transport is None:
        from media_acquisition import request
        def transport(url):
            with request(url) as response:
                return response.read(2_000_001)
    body = transport('https://pixabay.com/api/videos/?'+urlencode({'key': key, 'id': int(record['provider_id'])}))
    if len(body) > 2_000_000:
        raise ValueError('SOURCE_API_RESPONSE_TOO_LARGE')
    data = json.loads(body)
    item = next((a for a in data.get('hits', []) if str(a.get('id')) == record['provider_id']), None)
    if (not item or item.get('pageURL') != record['source_page'] or item.get('user') != record['author']
            or record['url'] not in [a.get('url') for a in item.get('videos', {}).values()]):
        raise ValueError('SOURCE_API_IDENTITY_AND_FILE_MISMATCH')
    return {'source_sha256': record['sha256'], 'source_url': record['url'],
        'source_page': record['source_page'], 'license_url': record['license_url'],
        'binding_terms': policy['terms_url'], 'terms_sha256': policy['terms_sha256'],
        'page_sha256': hashlib.sha256(body).hexdigest(), 'author': record['author'],
        'commercial_use': True, 'reviewed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'verification_method': 'authenticated_official_API_exact_asset_and_current_global_Content_License',
        'api_endpoint': 'https://pixabay.com/api/videos/', 'api_response_sha256': hashlib.sha256(body).hexdigest(),
        'license_policy': policy, 'use_scope': 'adapted illustrative educational video; no endorsement or standalone redistribution'}


def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'CasaSemEsforco/10.2'}), timeout=45) as response:
        body = response.read(2_000_001)
    if len(body) > 2_000_000:
        raise ValueError('LICENSE_EVIDENCE_TOO_LARGE')
    return body



def verify_commons(record, fetcher=fetch):
    from media_providers import commons_record
    params = {'action': 'query', 'format': 'json', 'pageids': int(record['provider_id']),
              'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata', 'iiextmetadatalanguage': 'en', 'maxlag': 5}
    body = fetcher('https://commons.wikimedia.org/w/api.php?'+urlencode(params))
    data = json.loads(body)
    if 'error' in data:
        raise RuntimeError('COMMONS_LICENSE_API_TEMPORARILY_UNAVAILABLE')
    page = data.get('query', {}).get('pages', {}).get(str(record['provider_id']))
    checked = commons_record(page or {}, 'rights', 'exact ID', [], allow_full_frame=True)
    if not checked or any(checked.get(k) != record.get(k) for k in ('url', 'source_page', 'author', 'license_url')):
        raise ValueError('COMMONS_EXACT_ASSET_COMMERCIAL_LICENSE_REQUIRED')
    terms = fetcher(record['license_url'])
    return {'source_sha256': record['sha256'], 'source_url': record['url'],
            'source_page': record['source_page'], 'author': record['author'],
            'license_url': record['license_url'], 'commercial_use': True,
            'page_sha256': hashlib.sha256(body).hexdigest(), 'terms_sha256': hashlib.sha256(terms).hexdigest(),
            'reviewed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
            'verification_method': 'official_Commons_exact_file_metadata_and_allowlisted_commercial_license',
            'use_scope': 'adapted illustrative educational video with full attribution and changes notice'}

def verify(record, fetcher=fetch):
    if (record.get('provider') not in ('pixabay', 'wikimedia') or not valid_source(record)
            or not re.fullmatch(r'[a-f0-9]{64}', record.get('sha256', ''))):
        raise ValueError('UNVERIFIED_SOURCE_RIGHTS')
    cached = known_evidence(record)
    if cached:
        return cached
    if record.get('provider') == 'wikimedia':
        return verify_commons(record, fetcher)
    if os.getenv('PIXABAY_API_KEY'):
        return verify_api(record, os.environ['PIXABAY_API_KEY'])
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
