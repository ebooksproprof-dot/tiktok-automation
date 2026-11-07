"""Additional public TikTok playback check; never authenticates or publishes."""
import datetime as dt
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit


def verify(entry):
    from playwright.sync_api import sync_playwright
    urls = entry.get('public_urls') or []
    if len(urls) != 1 or not re.fullmatch(
            r'https://www\.tiktok\.com/@\.casasemesforo/video/\d+', urls[0]):
        raise ValueError('EXACT_PUBLIC_VIDEO_URL_REQUIRED')
    url = urls[0]
    video_id = url.rsplit('/', 1)[-1]
    executable = next((shutil.which(x) for x in ('google-chrome', 'chromium', 'chromium-browser')
                       if shutil.which(x)), None)
    with sync_playwright() as p:
        options = {'headless': True, 'args': ['--no-sandbox']}
        if executable:
            options['executable_path'] = executable
        browser = p.chromium.launch(**options)
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            response = page.goto(url, wait_until='domcontentloaded', timeout=45000)
            page.wait_for_selector('video', timeout=25000)
            skip = page.get_by_text('Skip', exact=True)
            if skip.count() and skip.first.is_visible():
                skip.first.click()
            page.locator('video').first.evaluate('(v) => {v.muted=true; v.play().catch(()=>{});} ')
            page.wait_for_function('() => {const v=document.querySelector("video"); return v && v.readyState>=2 && v.duration>0;}', timeout=25000)
            page.wait_for_timeout(3000)
            before = page.locator('video').first.evaluate('(v)=>({t:v.currentTime,d:v.duration,w:v.videoWidth,h:v.videoHeight,r:v.readyState})')
            page.wait_for_timeout(3000)
            after = page.locator('video').first.evaluate('(v)=>({t:v.currentTime,d:v.duration,w:v.videoWidth,h:v.videoHeight,r:v.readyState})')
            body = page.inner_text('body')
            hook = ' '.join((entry.get('script_lines') or [''])[0].split())
            text = ' '.join(body.split())
            progressed = after['t'] > before['t']+.5 or (before['t'] > after['t'] and after['d'] > 3)
            accepted = (response is not None and response.status == 200
                        and urlsplit(page.url).path.endswith('/video/'+video_id)
                        and bool(hook) and hook in text
                        and after['r'] >= 2 and after['w'] > 0 and after['h'] > 0
                        and after['d'] >= 3 and progressed)
            result = {'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                      'url': url, 'video_id': video_id, 'public_playback_verified': accepted,
                      'caption_hook_matches': bool(hook) and hook in text,
                      'playback_progressed': progressed, 'media_duration': after['d'],
                      'width': after['w'], 'height': after['h'],
                      'authenticated': False, 'method': 'public browser video + matching caption + playback progression'}
            folder = Path('tmp/public-proof')
            folder.mkdir(parents=True, exist_ok=True)
            (folder/(video_id+'.json')).write_text(json.dumps(result, indent=2)+'\n')
            page.screenshot(path=str(folder/(video_id+'.png')))
            return result
        finally:
            browser.close()


def require(entry, verifier=verify):
    if entry.get('status') != 'PUBLISH_COMPLETE':
        return
    try:
        evidence = verifier(entry)
        entry['public_visibility_evidence'] = evidence
        if evidence.get('public_playback_verified') is True:
            entry['verification_source'] += ' + unauthenticated public TikTok playback'
            return
    except Exception as exc:
        entry['public_visibility_evidence'] = {'error_type': type(exc).__name__,
            'public_playback_verified': False, 'checked_at': dt.datetime.now(dt.timezone.utc).isoformat()}
    # Provider acceptance remains durable and still blocks resubmission.
    entry.update(provider_sent_verified=True, publicly_verified=False,
                 status='AWAITING_PUBLIC_VERIFICATION')
    entry['candidate_public_urls'] = entry.pop('public_urls', [])
    entry.pop('publicly_available_post_id', None)
