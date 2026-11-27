"""Authored, bounded tips and evidence requirements shared by stock and Wan."""
import json
import re
from pathlib import Path
from editorial_policy import reason

TOPICS = json.loads(Path(__file__).with_suffix('.json').read_text())
BY_ID = {t['id']: t for t in TOPICS}


def ideas(queue, state, family=None, captions=None):
    from semantic_review import words
    seen = [words(c) for c in captions or []]
    result = []
    for tip in TOPICS:
        if family and family != tip['family']: continue
        if captions is not None and not matches_visual(tip, captions): continue
        concept = 'tip12-'+tip['id']
        if not reason({'concept': concept, 'script_lines': tip['script_lines']}, queue, state):
            result.append((concept, [], tip['script_lines']))
    # Favor rooms least represented recently, without treating room reuse as a rejection.
    from collections import Counter
    from editorial_policy import history, describe
    counts = Counter(describe(p)['environment'] for p in history(queue, state)[-30:])
    return sorted(result, key=lambda i: counts[BY_ID[i[0][6:]]['environment']])


def prompt(tip, slot):
    # Each episode addresses one specific problem, with three contextual views.
    stages = ['Establish the household setting and objects.',
              'Close view clearly revealing the relevant arrangement and physical details.',
              'Wider view of the safe practical arrangement, with clear access.',
              'Alternate side view of the same task, with a clearly different composition.',
              'Detail of the completed arrangement and its practical clearance.',
              'Final wide view showing the finished result in the household context.']
    return ('Photorealistic domestic '+tip['environment']+'. Main objects: '+', '.join(tip['visual_terms'])+'. '
            'Subject: '+tip.get('visual_subject', ', '.join(tip['visual_terms']))+'. Visual explanation of '+tip['solution_id'].replace('-', ' ')+'. '+stages[slot]+
            ' Realistic materials, stable geometry. Gentle continuous camera slide, visible parallax. '
            'No people, hands, text, logos, labels or watermarks. One uninterrupted shot.')


def matches_visual(tip, captions):
    from semantic_review import words
    if tip.get('required_visual_pattern'):
        return sum(bool(re.search(tip['required_visual_pattern'],c.lower())) for c in captions)>=2
    return sum(bool(set(tip['visual_terms']) & words(c)) for c in captions)>=2
