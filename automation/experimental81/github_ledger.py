"""GitHub-CAS quota reservations for experimental Wan calls; no publication.

Reserves a single request on the experimental branch BEFORE contacting HF.
Conflicts and uncertain readbacks fail closed, with no retry of generation.
"""
import base64
from datetime import datetime, timezone
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from experimental81 import daily_budget

REPO = 'ebooksproprof-dot/tiktok-automation'
BRANCH = 'feature/ai-video-hybrid-30s'
PATH = 'automation/experimental81/ledger.json'
API = f'https://api.github.com/repos/{REPO}/contents/{PATH}'
SPACE = 'https://zerogpu-aoti-wan2-2-fp8da-aoti-faster.hf.space'


class LedgerError(RuntimeError):
    pass


def request_json(method, url, token, payload=None):
    if not isinstance(token, str) or not token:
        raise LedgerError('GITHUB_TOKEN_REQUIRED')
    headers = {'Accept': 'application/vnd.github+json',
               'Authorization': 'Bearer ' + token,
               'X-GitHub-Api-Version': '2022-11-28'}
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.loads(response.read(1_000_000))
    except urllib.error.HTTPError as exc:
        # Do not log a response body, which could contain credentials.
        raise LedgerError(f'GITHUB_LEDGER_HTTP_{exc.code}') from None
    except (urllib.error.URLError, TimeoutError):
        raise LedgerError('GITHUB_LEDGER_NETWORK_UNKNOWN_NO_RETRY') from None


def parse_file(response):
    if not isinstance(response, dict) or not isinstance(response.get('sha'), str):
        raise LedgerError('GITHUB_LEDGER_CONTENTS_SHA_MISSING')
    if response.get('encoding') != 'base64' or not isinstance(response.get('content'), str):
        raise LedgerError('GITHUB_LEDGER_ENCODING_INVALID')
    try:
        data = json.loads(base64.b64decode(response['content']).decode('utf-8'))
    except (ValueError, UnicodeError):
        raise LedgerError('GITHUB_LEDGER_CORRUPT') from None
    return response['sha'], data


def reserve_remote(record, *, tier='anonymous', now=None, transport=request_json):
    """Callback for wan_probe.run(before_submit=...); no credentials leave Actions.

    This is not a scheduler or a proof of actual quota balance. 'free' assumes
    prior independent verification of a no-billing free HF account, not supplied
    by this module. Normal production should keep anonymous/token=False.
    """
    main_scheduler = (os.getenv('GITHUB_REF_NAME') == 'main'
                      and os.getenv('GITHUB_WORKFLOW') == 'CasaSemEsforco AI30 Free Collector'
                      and os.getenv('AI30_MAIN_SCHEDULER_ALLOW') == 'true'
                      and os.getenv('GITHUB_EVENT_NAME') in ('schedule', 'workflow_dispatch'))
    if os.getenv('GITHUB_ACTIONS') != 'true' or not (os.getenv('GITHUB_REF_NAME') == BRANCH or main_scheduler):
        raise LedgerError('EXPERIMENTAL_ACTIONS_BRANCH_REQUIRED')
    token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
    if not token:
        raise LedgerError('GITHUB_TOKEN_REQUIRED')
    spec = record.get('request', {})
    steps = spec.get('steps')
    if (spec.get('space') != SPACE or spec.get('duration_seconds') != 5
            or (tier == 'free' and steps not in (3, 4))
            or (tier == 'anonymous' and steps != 4)
            or tier not in ('anonymous', 'free')):
        raise LedgerError('UNVERIFIED_WAN_CONFIGURATION')
    request_id = record.get('request_sha256')
    now = datetime.now(timezone.utc) if now is None else now
    url = API + '?ref=' + urllib.parse.quote(BRANCH, safe='')
    old_sha, old_data = parse_file(transport('GET', url, token))
    updated = daily_budget.reserve(old_data, request_id, now, tier=tier,
                                   estimated_seconds=daily_budget.estimated_request_seconds(steps))
    body = {'message': 'Reserve experimental Wan request; no automatic retry',
            'content': base64.b64encode((json.dumps(updated, sort_keys=True, indent=2)+'\n').encode()).decode(),
            'sha': old_sha, 'branch': BRANCH}
    response = transport('PUT', API, token, body)
    if not isinstance(response, dict) or not response.get('commit', {}).get('sha'):
        raise LedgerError('GITHUB_LEDGER_WRITE_UNCONFIRMED')
    _, actual = parse_file(transport('GET', url, token))
    if (actual != updated or not any(c['request_sha256'] == request_id for c in actual['claims'])):
        raise LedgerError('GITHUB_LEDGER_READBACK_MISMATCH_NO_RETRY')
    return {'reserved': True, 'request_sha256': request_id,
            'commit': response['commit']['sha'], 'generation_attempted': False,
            'publication_allowed': False}


if __name__ == '__main__':
    print('No direct execution. Supply reserve_remote as a Wan callback inside authorized Actions.')
