"""Monitor the existing queue and request refill once per confirmed publication.

No media creation or publishing API here. The durable receipt precedes a GitHub
workflow dispatch; a lost dispatch reply is never blindly repeated. Regular
production crons recover independently. Legacy Symphony inventory is preserved.
"""
import datetime as dt
import json
import os
import urllib.request

from autonomous_production import stock_status
import video_stock as stock
import buffer_runner as buffer
from stock_publish import DurableClient


def newly_published(ledger, state):
    receipts = ledger.get('refill_events', {})
    return [key for key, output in ledger.get('outputs', {}).items()
            if key not in receipts
            and (entry := state.get('posts', {}).get(key, {})).get('status') == 'PUBLISH_COMPLETE'
            and entry.get('publicly_verified') is True
            and entry.get('public_visibility_evidence', {}).get('public_playback_verified') is True
            and entry.get('sha256') == output.get('sha256')]


def recovery_workflow(ledger):
    return ('acquire-media.yml' if ledger.get('last_run', {}).get('status') == 'NO_VALID_OUTPUT'
            else 'casasemesforco-daily.yml')


def dispatch(token, workflow='casasemesforco-daily.yml'):
    if workflow not in ('acquire-media.yml', 'casasemesforco-daily.yml'):
        raise ValueError('EXISTING_RECOVERY_WORKFLOW_REQUIRED')
    payload = {'ref': 'main'}
    if workflow == 'casasemesforco-daily.yml':
        payload['inputs'] = {'production_limit': '2'}
    request = urllib.request.Request(
        'https://api.github.com/repos/'+stock.REPO+'/actions/workflows/'+workflow+'/dispatches',
        method='POST', data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer '+token, 'Accept': 'application/vnd.github+json',
                 'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28'})
    # Dispatch is not a video submission. Even so, stop on an uncertain reply;
    # the production cron, stock cap and source history are recovery controls.
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            if response.status != 204:
                raise RuntimeError('REFILL_DISPATCH_ACK_UNCONFIRMED')
    except Exception:
        raise RuntimeError('REFILL_DISPATCH_UNCERTAIN; no blind repeat; scheduled production remains active') from None


def request_refill(store, state, now, sender, maintenance=False, target_workflow='casasemesforco-daily.yml'):
    ledger, revision = store.load()
    ids = newly_published(ledger, state)
    trigger = 'CONFIRMED_CONSUMPTION'
    publication_ids = ids.copy()
    if not ids:
        if not maintenance:
            return {'status': 'NO_NEW_CONFIRMED_CONSUMPTION', 'publication_ids': []}
        # Cold/partial stock must recover even when a previous consumption
        # already has a dispatch receipt. Bound maintenance to once per six
        # hours and retain uncertain replies instead of blindly repeating them.
        receipts = list(ledger.get('refill_events', {}).values())+list(ledger.get('maintenance_refills', {}).values())
        for receipt in receipts:
            if receipt.get('status') in ('INTENT_RECORDED_NO_BLIND_RETRY', 'UNKNOWN_WORKFLOW_DISPATCH'):
                try:
                    if now-stock.instant(receipt['at']) < dt.timedelta(hours=6):
                        return {'status': 'HOLD_UNCERTAIN_WORKFLOW_DISPATCH', 'publication_ids': []}
                except (ValueError, KeyError, TypeError):
                    return {'status': 'HOLD_UNCERTAIN_WORKFLOW_DISPATCH', 'publication_ids': []}
        bucket = dt.datetime.fromtimestamp(int(now.timestamp())//21600*21600, dt.timezone.utc).isoformat()
        receipts = ledger.setdefault('maintenance_refills', {})
        key = bucket+'|'+target_workflow
        if key in receipts or (target_workflow == 'casasemesforco-daily.yml' and bucket in receipts):
            return {'status': 'MAINTENANCE_ALREADY_RESERVED_THIS_WINDOW', 'publication_ids': []}
        ids, trigger = [key], 'LOW_STOCK_MAINTENANCE'
    else:
        receipts = ledger.setdefault('refill_events', {})
    for key in ids:
        receipts[key] = {'status': 'INTENT_RECORDED_NO_BLIND_RETRY', 'at': stock.stamp(now),
                         'trigger': trigger, 'target_workflow': target_workflow}
    revision = store.save(ledger, revision)  # A failed CAS prevents dispatch.
    try:
        sender()
        result = 'DISPATCHED'
    except Exception:
        for key in ids:
            receipts[key]['status'] = 'UNKNOWN_WORKFLOW_DISPATCH'
        store.save(ledger, revision)
        raise
    for key in ids:
        receipts[key]['status'] = result
    store.save(ledger, revision)
    return {'status': result, 'publication_ids': publication_ids, 'trigger': trigger,
            'target_workflow': target_workflow}


def run(token, check_channel=False, probe=None):
    now = dt.datetime.now(dt.timezone.utc)
    queue_store = stock.GitHubStore(token, path='automation/queue.json', validate=False)
    legacy_store = stock.GitHubStore(token, path='automation/state.json', validate=False)
    producer_store = stock.GitHubStore(token, path='automation/production_state.json', validate=False)
    inventory_store = stock.GitHubStore(token)
    queue, _ = queue_store.load()
    state, _ = legacy_store.load()
    if 'posts' not in queue or 'posts' not in state:
        raise ValueError('EXISTING_QUEUE_AND_STATE_REQUIRED')
    status = stock_status(queue, state, now)
    channel_ok = None
    if check_channel:
        client = DurableClient(legacy_store)
        channel_id = os.getenv('BUFFER_CHANNEL_ID', '6ad14dc2778b240e2f1f7c2f')
        channel = client.call(buffer.CHANNEL_QUERY, {'input': {'id': channel_id}})['channel']
        buffer.check_channel(channel, channel_id)
        channel_ok = True
    refill = {'status': 'CHECK_ONLY' if check_channel else 'STOCK_TARGET_MET', 'publication_ids': []}
    if not check_channel and status['refill_needed']:
        ledger, _ = producer_store.load()
        target = recovery_workflow(ledger)
        refill = request_refill(producer_store, state, now, lambda: dispatch(token, target),
                                maintenance=True, target_workflow=target)
    inventory, revision = inventory_store.load()
    old = inventory.get('production', {})
    if old.get('provider') == 'tiktok_symphony':
        inventory.setdefault('legacy_production_settings', old)
    inventory['production'] = {'enabled': True, 'provider': 'licensed_stock_cpu_and_existing_cleared_Wan',
        'voice': 'pf_dora', 'tts': 'kokoro_cpu', 'fallback': 'piper_on_proven_TTS_failure',
        'runner': 'CasaSemEsforco Daily Video Creation', 'target_max': 4,
        'legacy_symphony_import_enabled': False, 'paid_services_enabled': False}
    result = {'at': stock.stamp(now), 'mode': 'AUTOMATIC_LICENSED_STOCK', 'stock': status,
              'refill': refill, 'channel_verified': channel_ok, 'cloud_probe': probe,
              'generation_enabled': True, 'this_monitor_generates_or_publishes': False,
              'legacy_inventory_preserved': len(inventory['items']),
              'additional_paid_services_enabled': False}
    inventory['last_run'] = result
    inventory_store.save(inventory, revision)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as out:
            out.write('\n## Automatic stock\n\n```json\n'+json.dumps(result, indent=2)+'\n```\n')
    if not check_channel and not status['ready']:
        print('::error::Automatic ready stock is empty; inspect refill outcome. No publication is implied.')
        return 2
    return 0
