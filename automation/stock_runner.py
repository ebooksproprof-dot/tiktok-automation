"""Cloud stock orchestrator. Production is independent of import and publication."""
import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path

import daily_coverage
from release_media import API, request
import stock_import
import stock_publish
import video_stock as stock


def ensure_inbox(token):
    release = request(API + '/releases/tags/stock-inbox', token)
    if release is None:
        # On lost response, stop. Next execution reconciles the unique tag.
        release = request(API + '/releases', token, 'POST', {
            'tag_name': 'stock-inbox', 'target_commitish': 'main',
            'name': 'CasaSemEsforço — entrada de vídeos revisados',
            'draft': False, 'prerelease': True, 'make_latest': 'false',
            'body': 'Envie pares NOME.mp4 + NOME.json conforme automation/STOCK-7.0.md. '
                    'Arquivos públicos. Não inclua credenciais. Não apague vídeos em fila. '
                    'Estar nesta Release não comprova publicação no TikTok.'})
    if release.get('draft') or release.get('tag_name') != 'stock-inbox':
        raise ValueError('Public stock-inbox release required')
    return release['id']


def occupied_slots(queue, legacy):
    result = []
    for item in list(queue.get('posts', [])) + list(legacy.get('posts', {}).values()):
        value = item.get('scheduled_at')
        if value:
            result.append(daily_coverage.stamp(value))
    return result


def import_and_schedule(store, token, queue, legacy, now):
    state, revision = store.load()
    previous = copy.deepcopy(state)
    stock.recover_interrupted(state, now)
    if state != previous or revision is None:
        store.save(state, revision)

    def accept(candidate):
        current, rev = store.load()
        if any(i['sha256'] == candidate['sha256'] or
               i['script_sha256'] == candidate['script_sha256'] for i in current['items']):
            return False
        stock.add_video(current, candidate, now)
        store.save(current, rev)
        return True

    current, _ = store.load()
    report = stock_import.scan(token, accept,
        known_asset_ids=[i.get('source_asset_id') for i in current['items']],
        legacy_queue=queue, legacy_state=legacy)
    state, revision = store.load()
    previous = copy.deepcopy(state)
    stock.schedule(state, now, occupied_slots(queue, legacy))
    state['last_import'] = {'at': stock.stamp(now), **report}
    # No generation quota invented from Studio's displayed credits.
    state['production'] = {'enabled': False, 'provider': 'tiktok_symphony',
        'reason': 'API entitlement, free terms and Keren mapping unverified',
        'api_balance': None, 'api_renews_at': None}
    if state != previous:
        store.save(state, revision)
    return report


def cloud_probe(token):
    """Actual cloud read/write/restart/CAS proof, separate from production items."""
    store = stock.GitHubStore(token, path='automation/stock_cloud_probe.json')
    state, revision = store.load()
    state['probe'] = {'at': stock.stamp(datetime.now(timezone.utc)),
                      'run_id': os.environ.get('GITHUB_RUN_ID'),
                      'publication_attempted': False}
    updated = store.save(state, revision)
    loaded, read_revision = stock.GitHubStore(token,
        path='automation/stock_cloud_probe.json').load()
    if loaded != state or read_revision != updated:
        raise RuntimeError('Cloud persistence readback failed')
    try:
        store.save(state, revision)
    except stock.Conflict:
        return {'cloud_readback': True, 'stale_writer_rejected': True,
                'publication_attempted': False}
    raise RuntimeError('Stale cloud writer unexpectedly accepted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--check-channel', action='store_true')
    args = parser.parse_args()
    if os.getenv('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Operational stock runner requires GitHub Actions')
    token = os.environ['GH_TOKEN']
    now = datetime.now(timezone.utc)
    store = stock.GitHubStore(token)
    legacy_store = stock.GitHubStore(token, path='automation/state.json', validate=False)
    queue_store = stock.GitHubStore(token, path='automation/queue.json', validate=False)
    queue, _ = queue_store.load()
    legacy, _ = legacy_store.load()
    if 'posts' not in queue or 'posts' not in legacy:
        raise RuntimeError('Existing queue/state missing; refusing replacement')
    ensure_inbox(token)
    probe = cloud_probe(token) if args.probe else None
    imported = import_and_schedule(store, token, queue, legacy, now)
    publication = stock_publish.run(store, legacy_store, queue,
        os.getenv('BUFFER_CHANNEL_ID', '6ad14dc2778b240e2f1f7c2f'),
        now=now, check_only=args.check_channel)
    state, revision = store.load()
    report = {'at': stock.stamp(now), 'import': imported, 'stock': stock.stock_report(state, now),
              'publication': publication, 'cloud_probe': probe,
              'generation_enabled': False, 'additional_paid_services_enabled': False}
    # Operational evidence persists outside a temporary runner and test logs.
    state['last_run'] = report
    store.save(state, revision)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    summary = os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as out:
            out.write('## Estoque CasaSemEsforço\n\n```json\n' +
                      json.dumps(report, ensure_ascii=False, indent=2) + '\n```\n')
    if report['stock']['low_stock']:
        print('::warning::Estoque abaixo de 7; gere um lote no Symphony e envie os pares MP4/JSON.')
    if imported['errors']:
        raise RuntimeError('Some imports failed; inspect persisted sanitized report')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Avoid remote bodies, credentials and untrusted filenames in logs.
        print('::error::Stock runner stopped safely: ' + type(exc).__name__)
        raise SystemExit(1)
