"""One reviewed free-stock recovery proof, using the existing renderer and queue.

No generation service or publisher here. --stage is cloud-only and single-use.
The first proof may be scheduled shortly ahead; recurring slots stay 10h/18h.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path

import render_daily as renderer
import visual_library
from content_catalog import fingerprint, novel_scripts
from media_rights import caption_with_credits

ROOT = Path(__file__).resolve().parent
CONCEPT = 'vassoura-pa-residuos-91'
SOURCE_SHA = 'e7da0c5ea4f76261bbb8871409695d16b9cb97c3c15c00282942785f454c0fae'
LINES = ['Sujeira espalhada no piso?',
         'Reúna os resíduos com movimentos curtos.',
         'Aproxime a pá e recolha aos poucos.',
         'Antes de começar, retire os objetos do caminho.',
         'Escolha uma vassoura adequada ao seu piso.',
         'Salve para a próxima limpeza.']


def source():
    inbox = json.loads((ROOT/'media_inbox.json').read_text())
    asset = next(x.copy() for x in inbox['items'] if str(x.get('provider_id')) == '34821')
    if (asset.get('sha256') != SOURCE_SHA or asset.get('reviewed') is not True
            or asset.get('semantic_verified') is not True
            or asset.get('editorial_approved') is not True):
        raise ValueError('REVIEWED_SOURCE_CHANGED')
    asset.update(id='mission91-vassoura', frame_mode='preserve_full',
                 context=asset['editorial_context'])
    return asset


def check_unused(queue, state):
    records = queue['posts'] + list(state['posts'].values())
    if any(p.get('concept') == CONCEPT for p in records):
        raise ValueError('PROOF_ALREADY_RESERVED_DO_NOT_RESUBMIT')
    if not novel_scripts([(CONCEPT, [], LINES)], queue, state):
        raise ValueError('PROOF_SCRIPT_ALREADY_USED')


def schedule(queue, state, now, soon=False):
    from zoneinfo import ZoneInfo
    from daily_coverage import stamp
    brt = ZoneInfo('America/Sao_Paulo')
    reservations = []
    for p in queue['posts'] + list(state['posts'].values()):
        if p.get('scheduled_at'):
            reservations.append(stamp(p['scheduled_at']).astimezone(brt))
    local = now.astimezone(brt)
    if soon:
        chosen = (local + dt.timedelta(minutes=15)).replace(microsecond=0)
        # The validation proof consumes one of the same two daily reservations.
        occupied = {x for x in reservations if x.date() == chosen.date()}
        if len(occupied) >= 2 or chosen in occupied:
            raise ValueError('DAILY_CAPACITY_RESERVED')
        return chosen
    for day in (0, 1):
        for hour in (10, 18):
            chosen = (local + dt.timedelta(days=day)).replace(hour=hour, minute=0, second=0, microsecond=0)
            if (dt.timedelta(minutes=20) < chosen-local < dt.timedelta(hours=26)
                    and chosen not in reservations
                    and len({x for x in reservations if x.date() == chosen.date()}) < 2):
                return chosen
    raise ValueError('NO_FREE_SLOT')


def run(stage=False, soon=False):
    queue = json.loads((ROOT/'queue.json').read_text())
    state = json.loads((ROOT/'state.json').read_text())
    check_unused(queue, state)
    if stage and (os.getenv('GITHUB_ACTIONS') != 'true'
                  or os.getenv('GITHUB_WORKFLOW') != 'CasaSemEsforco 9.1 reviewed recovery proof'
                  or os.getenv('GITHUB_REF_NAME') != 'main'):
        raise ValueError('STAGING_REQUIRES_TRUSTED_MAIN_CLOUD_WORKFLOW')
    now = dt.datetime.now(dt.timezone.utc)
    when = schedule(queue, state, now, soon)
    ids = {p.get('id') for p in queue['posts']} | set(state['posts'])
    post_id = next((f'casasem-{when.date()}-{n}' for n in (1, 2)
                    if f'casasem-{when.date()}-{n}' not in ids), None)
    if not post_id:
        raise ValueError('PROOF_IDS_RESERVED')
    asset = source()
    key = asset['id']
    renderer.SOURCE[key] = asset['url']
    renderer.PROVENANCE[key] = asset
    renderer.ASSETS.mkdir(parents=True, exist_ok=True)
    renderer.OUT.mkdir(parents=True, exist_ok=True)
    video, quality = renderer.render((CONCEPT, [key], LINES), renderer.load_voice(), post_id)
    title, credits = caption_with_credits(' '.join(LINES) + ' #CasaSemEsforco #LimpezaDaCasa', [asset])
    quality.update(editorial_approved=True, required_public_credits=credits,
                   rights_review_reference='automation/MISSION-9.1-LICENSES.md',
                   editorial_review={'basis': 'source contact sheet, matching script and framing reviewed; final decode and timings measured',
                                     'reviewed_at': now.isoformat(), 'human_listening_verified': False})
    post = dict(id=post_id, concept=CONCEPT, title=title, scheduled_at=when.isoformat(),
                approved=True, consented_at=now.isoformat(), publication_provider='buffer',
                quality=quality, script_lines=LINES, script_sha256=fingerprint(LINES),
                render_version=2, media_storage='release',
                approval_scope='mission91_explicit_owner_publication_request',
                publishing_status='RENDERED_VALIDATED_PENDING_BUFFER',
                video_url='', first_test_outside_recurring_slots=soon)
    previous = visual_library.history(queue, state)
    previous.append(json.loads((ROOT/'visual_history.json').read_text()))
    visual_library.require_evidence(post, previous)
    if stage:
        from release_media import publish
        # Existing immutable monthly storage; verified readback before queue write.
        post['video_url'] = publish(video, post_id, quality)
        from buffer_runner import prepare, verify_hosted
        prepare(post, state, os.environ['BUFFER_CHANNEL_ID'])
        verify_hosted(post)
        # Exclusive casasemesforco-state workflow lock prevents concurrent sends.
        # Preserve all queue entries; push is fast-forward, never overwrite remote.
        queue['posts'].append(post)
        renderer.atomic_json(ROOT/'queue.json', queue)
    evidence = dict(status='QUEUED' if stage else 'RENDERED_LOCAL_ONLY', video=str(video),
                    quality=quality, post_id=post_id, scheduled_at=when.isoformat(),
                    video_url=post['video_url'], publication_verified=False,
                    new_ai_requests=0, recurring_slots_unchanged=True)
    Path('tmp/mission91').mkdir(parents=True, exist_ok=True)
    renderer.atomic_json(Path('tmp/mission91/proof.json'), evidence)
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', action='store_true')
    parser.add_argument('--soon', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.stage, args.soon), ensure_ascii=False, indent=2))
