"""Refresh derived review pages without approving or changing operational files."""
import argparse
import json
import os
from pathlib import Path
import tempfile

from review_batch44 import build_preview, render_html

INPUTS = ('queue.json', 'state.json', 'visual_history.json', 'QUEUE-AUDIT-4.4.json')


def read_snapshot(root):
    result = {}
    for name in INPUTS:
        path = root/'automation'/name
        result[name] = path.read_bytes() if path.exists() else None
    if result['queue.json'] is None or result['state.json'] is None:
        raise ValueError('QUEUE_AND_STATE_REQUIRED')
    return result


def refresh(root, now=None):
    """Atomic replacement per derived file; serialize with queue/state workflow lock.

HTML embeds its own manifest, so a reader never mixes authorization data from two
files during the two atomic replacements. A changed snapshot aborts before replace.
"""
    root = Path(root)
    snapshot = read_snapshot(root)
    loaded = {key: json.loads(value) if value is not None else None for key, value in snapshot.items()}
    manifest = build_preview(loaded['queue.json'], loaded['state.json'], now,
                             archived=loaded['visual_history.json'], audit=loaded['QUEUE-AUDIT-4.4.json'])
    content = {'review44.json': json.dumps(manifest, indent=2, ensure_ascii=False)+'\n',
               'review44.html': render_html(manifest)}
    public = root/'public'
    if public.is_symlink():
        raise ValueError('PUBLIC_DIRECTORY_SYMLINK_REJECTED')
    public.mkdir(parents=True, exist_ok=True)
    staged = []
    try:
        for name, text in content.items():
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=public,
                                             prefix='.review44-', delete=False) as handle:
                staged.append((Path(handle.name), public/name))
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
        if snapshot != read_snapshot(root):
            raise ValueError('STATE_CHANGED_DURING_REFRESH')
        for temporary, destination in staged:
            os.replace(temporary, destination)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    return dict(refreshed=True, pending=manifest['pending_count'], selectable=manifest['selectable_count'],
                manifest_sha256=manifest['manifest_sha256'], approved=False, submitted=False)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    print(json.dumps(refresh(args.root)))
