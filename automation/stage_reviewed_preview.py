"""Stage one immutable cloud proof. Never approve or publish automatically."""
import datetime as dt
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
import render_daily as r
import visual_library as v
from media_quality import validate
from release_media import publish
from content_catalog import category, fingerprint

EXPECTED_SHA = '8764601bee4d91010539ae91d1f21d2bd2e17bb915f485f62e45488d3d45751a'
POST_ID = 'casasem-2026-10-20-1'

def main(folder):
    queue = json.loads(r.QUEUE.read_text())
    state = json.loads((r.ROOT/'automation/state.json').read_text())
    if POST_ID in state.get('posts', {}):
        raise ValueError('Already submitted; no restaging')
    if any(p['id'] == POST_ID for p in queue['posts']):
        raise ValueError('Slot already occupied; no overwrite')
    report = json.loads((folder/'report.json').read_text())[0]
    path = folder/'preview-v3-1-v2.mp4'
    quality = report['quality']
    if validate(path)['sha256'] != EXPECTED_SHA or quality['sha256'] != EXPECTED_SHA:
        raise ValueError('Cloud proof fingerprint mismatch')
    previous = v.history(queue, state)
    previous.append(json.loads((r.ROOT/'automation/visual_history.json').read_text()))
    v.require_evidence({'quality': quality}, previous)
    quality['editorial_approved'] = False
    video_url = publish(path, POST_ID, quality)
    concept = report['concept']
    entry = dict(id=POST_ID, concept=concept, category=category(concept),
        script_lines=report['script'], script_sha256=fingerprint(report['script']),
        title=' '.join(report['script'])+' #CasaSemEsforco #OrganizacaoDaCasa',
        video_url=video_url, media_storage='release', quality=quality,
        render_version=2, composition_revision=r.COMPOSITION_REVISION,
        scheduled_at=dt.datetime(2026,10,20,10,tzinfo=ZoneInfo('America/Fortaleza')).isoformat(),
        approved=False, consented_at=None,
        publishing_status='AWAITING_EDITORIAL_REVIEW_AND_VALID_PUBLISHING_ROUTE',
        proof_run_id=39353432805)
    queue['posts'].append(entry)
    r.atomic_json(r.QUEUE, queue)
    print('STAGED_RELEASE_VERIFIED='+POST_ID+'; PUBLICATION_CONFIRMED=false')

if __name__ == '__main__':
    main(Path(sys.argv[1]))
