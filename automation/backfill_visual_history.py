"""Measure authorized legacy source files once; never modifies publication history."""
import json
import render_daily as r
from visual_library import fingerprint


def main():
    r.ASSETS.mkdir(parents=True, exist_ok=True)
    queue = json.loads(r.QUEUE.read_text())
    urls = {url for p in queue['posts'] for url in p.get('quality', {}).get('source_urls', [])}
    records = []
    for key, url in r.SOURCE.items():
        if url in urls:
            records.append(fingerprint(r.get_clip(key), url))
    r.atomic_json(r.ROOT/'automation/visual_history.json', {'visual_sources': records})
    print('LEGACY_SOURCES_MEASURED=' + str(len(records)))


if __name__ == '__main__':
    main()
