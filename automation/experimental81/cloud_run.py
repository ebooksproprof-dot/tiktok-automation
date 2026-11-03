"""Cloud experiment: no production state, no generation unless separately authorized."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import hf_probe, render


def main(folder):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    result = {'at': datetime.now(timezone.utc).isoformat(), 'publication_enabled': False,
              'paid_resources_enabled': False, 'generation': hf_probe.run('A', folder/'ledger', enabled=False)}
    (folder/'generation-status.json').write_text(json.dumps(result['generation'], indent=2))
    try:
        # Reproduce the already generated, hash-pinned 5s AI fixture with licensed
        # project references. Never spend another remote GPU request to run CI.
        record = render.reference_demo(folder/'demo')
        result.update(status='RENDERED_REFERENCE_ONLY' if record['ai_seconds'] == 0 else 'RENDERED_HYBRID',
                      profile=record['profile'], ai_seconds=record['ai_seconds'],
                      quality=record['quality'], render_seconds=record['render_seconds'])
    except Exception as exc:
        result.update(status='BLOCKED_RENDER', error_type=type(exc).__name__,
                      detail='Source download, narration or render failed; no paid fallback and no publishing')
    finally:
        (folder/'cloud-result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if result['status'].startswith('RENDERED') else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    raise SystemExit(main(parser.parse_args().output))
