"""Reproducible same-script CPU comparison; run each engine in a separate process."""
import argparse
import json
from pathlib import Path
import resource
import time
from narration import PiperEngine, synthesize

SCRIPT = [
    'A bancada está cheia de objetos?',
    'Antes de limpar, retire o que não precisa ficar ali.',
    'Use um pano limpo e um produto adequado à superfície.',
    'Respeite as instruções do fabricante.',
    'Deixe os itens da rotina juntos, em um lugar fácil de alcançar.',
    'Salve esta dica para a próxima limpeza.',
]


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--engine', choices=['piper', 'kokoro'], required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    if args.engine == 'kokoro':
        from female_narration import KokoroFemaleEngine
        engine = KokoroFemaleEngine(args.cache)
    else:
        engine = PiperEngine(args.cache)
    initialized = time.perf_counter()
    duration, timings = synthesize(engine, SCRIPT, args.output)
    report = dict(engine=engine.name, init_seconds=initialized-start,
                  synthesis_seconds=time.perf_counter()-initialized,
                  duration=duration, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  script=SCRIPT, timings=timings, cost_added=0,
                  resource_platform='Linux ru_maxrss KiB',
                  perceptual_quality='not_listened_no_naturalness_claim')
    (args.output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
