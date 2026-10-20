"""Stage one immutable cloud proof. Never approve or publish automatically."""
import datetime as dt
import json
from pathlib import Path
import sys
import re
from zoneinfo import ZoneInfo
import render_daily as r
import visual_library as v
from media_quality import validate
from release_media import publish
from content_catalog import category, fingerprint

EXPECTED_SHA = '8764601bee4d91010539ae91d1f21d2bd2e17bb915f485f62e45488d3d45751a'
POST_ID = 'casasem-2026-10-20-1'

def main(folder, post_id=POST_ID, expected_sha=EXPECTED_SHA, proof_run_id=39353432805):
    if not re.fullmatch(r'casasem-\d{4}-\d{2}-\d{2}-[12]', post_id):
        raise ValueError('Invalid destination slot')
    if not re.fullmatch(r'[a-f0-9]{64}', expected_sha):
        raise ValueError('Invalid reviewed fingerprint')
    day = dt.date.fromisoformat(post_id[8:18])
    hour = 10 if post_id.endswith('-1') else 18
    queue = json.loads(r.QUEUE.read_text())
    state = json.loads((r.ROOT/'automation/state.json').read_text())
    if post_id in state.get('posts', {}):
        raise ValueError('Already submitted; no restaging')
    if any(p['id'] == post_id for p in queue['posts']):
        raise ValueError('Slot already occupied; no overwrite')
    report = json.loads((folder/'report.json').read_text())[0]
    path = folder/'preview-v3-1-v2.mp4'
    quality = report['quality']
    if validate(path)['sha256'] != expected_sha or quality['sha256'] != expected_sha:
        raise ValueError('Cloud proof fingerprint mismatch')
    previous = v.history(queue, state)
    previous.append(json.loads((r.ROOT/'automation/visual_history.json').read_text()))
    v.require_evidence({'quality': quality}, previous)
    quality['editorial_approved'] = False
    video_url = publish(path, post_id, quality)
    concept = report['concept']
    entry = dict(id=post_id, concept=concept, category=category(concept),
        script_lines=report['script'], script_sha256=fingerprint(report['script']),
        title=' '.join(report['script'])+' #CasaSemEsforco #OrganizacaoDaCasa',
        video_url=video_url, media_storage='release', quality=quality,
        render_version=2, composition_revision=r.COMPOSITION_REVISION,
        scheduled_at=dt.datetime.combine(day,dt.time(hour),ZoneInfo('America/Fortaleza')).isoformat(),
        approved=False, consented_at=None,
        publishing_status='AWAITING_EDITORIAL_REVIEW_AND_VALID_PUBLISHING_ROUTE',
        proof_run_id=proof_run_id)
    queue['posts'].append(entry)
    r.atomic_json(r.QUEUE, queue)
    print('STAGED_RELEASE_VERIFIED='+post_id+'; PUBLICATION_CONFIRMED=false')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    parser.add_argument('--post-id', default=POST_ID)
    parser.add_argument('--sha256', default=EXPECTED_SHA)
    parser.add_argument('--proof-run-id', type=int, default=39353432805)
    args = parser.parse_args()
    main(args.folder, args.post_id, args.sha256, args.proof_run_id)
