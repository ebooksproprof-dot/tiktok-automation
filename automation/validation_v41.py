"""Three bounded Format C female-voice proofs; no approval or publication writes."""
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import time
import render_daily as r
import visual_library as visual
from female_narration import KokoroFemaleEngine
from validation_v4 import BATCH, CONTEXT, checks


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = r.ROOT/'tmp/validation-v41'
    assets = out/'assets'
    assets.mkdir(parents=True, exist_ok=True)
    cache = r.ROOT/'tmp/voice41'
    source_assets = r.ROOT.parent/'tiktok-automation/tmp/validation-v4/assets'
    tracked = [r.QUEUE, r.ROOT/'automation/state.json', r.ROOT/'automation/visual_history.json']
    before = {str(p): digest(p) for p in tracked if p.exists()}
    items = {x['provider_id']:x for x in json.loads((r.ROOT/'automation/media_inbox.json').read_text())['items']}
    r.ASSETS, r.OUT, r.DYNAMIC_STYLE = assets, out, True
    voice = KokoroFemaleEngine(cache)
    previous, reports = [], []
    for index, (source_id, concept, headline, lines) in enumerate(BATCH, 1):
        item = dict(items[source_id], id='pixabay-'+source_id, context=CONTEXT[source_id])
        r.SOURCE[source_id], r.PROVENANCE[source_id] = item['url'], item
        source = assets/(source_id+'.mp4')
        local_cached = source_assets/source.name
        if not source.exists() and local_cached.exists():
            source.symlink_to(local_cached)
        # Actions has no sibling workspace: existing bounded downloader verifies
        # the pinned inbox SHA before accepting the licensed source.
        source = r.get_clip(source_id)
        r.verify_source(source_id, source)
        start = time.monotonic()
        path, quality = r.render((concept, [source_id], lines), voice, f'validation-v41-C{index}-{concept}')
        elapsed = time.monotonic()-start
        quality.update(voice=voice.name, approved=False, editorial_approved=False, proof_only=True,
                       format='C', avatar_present=False, publication_allowed=False)
        visual.check_sources(quality['visual_sources'], previous)
        previous.append(quality)
        qa = checks(path)
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(path),'-vf',
             f"fps=6/{quality['duration']:.6f},scale=270:480,tile=3x2",'-frames:v','1',str(path.with_suffix('.jpg'))],check=True,timeout=90)
        record = dict(id=f'C{index}', file=path.name, source=item, source_context=CONTEXT[source_id],
            script=lines, quality=quality, technical_checks=qa, render_seconds=round(elapsed,3),
            peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
            resources_note='Linux max RSS; maxima per process, not aggregate or incremental per video',
            comparison={'same_script_and_source_as_v4':True,'voice_changed_to_female':True,
                'naturalness_improvement_measured':False,'audience_retention_measured':False},
            limitations=['Illustrative footage, not proof of specific product performance.',
                'No avatar. No listening-based pronunciation or lip-sync assessment.',
                'Local CPU proof, not sustained daily GitHub Actions evidence.'],
            cost_added=0, published=False, approved=False)
        r.atomic_json(path.with_suffix('.json'), record)
        reports.append(record)
        r.atomic_json(out/'report.json', reports)
        print('PROOF_READY='+path.name, flush=True)
    after = {str(p):digest(p) for p in tracked if p.exists()}
    if before != after:
        raise RuntimeError('PROOF_STATE_INTEGRITY_FAILED')
    print('PROOFS_COMPLETE=3;PUBLISHED=0;APPROVED=0;STATE_UNCHANGED=1',flush=True)


if __name__ == '__main__':
    main()
