"""Isolated CPU inference worker, avoids the semantic reviewer's Transformers ABI."""
import argparse
import json
from pathlib import Path
from chatterbox_v3 import ChatterboxBrazilEngine
from narration import synthesize

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--lines',type=Path,required=True)
    args=p.parse_args()
    engine=ChatterboxBrazilEngine(args.cache)
    duration,timings=synthesize(engine,json.loads(args.lines.read_text()),args.folder,target_seconds=30)
    (args.folder/'isolated-result.json').write_text(json.dumps({'duration':duration,'timings':timings}))
