"""Three distinct real renders, no public posting and no queue mutation."""
import json
from pathlib import Path
import time
import render_daily as r
import visual_library as visual

CONCEPTS = ['bancada-tirar-objetos', 'piso-pouca-agua', 'gaveta-uma-categoria']


def main(concepts=None):
    r.ASSETS.mkdir(parents=True, exist_ok=True)
    r.OUT = r.ROOT/'tmp/review-v3'
    r.OUT.mkdir(parents=True, exist_ok=True)
    engine = r.load_voice()
    results, previous = [], []
    for index, concept in enumerate(concepts or CONCEPTS, 1):
        idea = next(i for i in r.IDEAS if i[0] == concept)
        started = time.monotonic()
        path, quality = r.render(idea, engine, 'preview-v3-' + str(index))
        visual.check_sources(quality['visual_sources'], previous)
        previous.append(quality)
        results.append(dict(concept=concept, file=path.name, quality=quality,
                            elapsed_seconds=round(time.monotonic()-started, 2),
                            script=idea[2], published=False))
        r.atomic_json(r.OUT/'report.json', results)
        r.run(['ffmpeg', '-v', 'error', '-y', '-i', str(path), '-vf',
               'fps=1/3,scale=270:480,tile=3x2', '-frames:v', '1', str(path.with_suffix('.jpg'))])
    r.atomic_json(r.OUT/'report.json', results)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--concept', action='append', choices=[i[0] for i in r.IDEAS])
    main(parser.parse_args().concept)
