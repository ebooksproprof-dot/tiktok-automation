"""Free, deterministic Portuguese semantic/structural novelty gate.

Queue + publication receipts are the durable ledger. Legacy metadata is derived,
never erased. The window is the UNION of 14 days and the last 30 submissions;
exact/reordered instructions remain blocked outside the rolling window.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import unicodedata

POLICY = Path(__file__).with_name('editorial_policy.json')
STOP = set('a o os as de da do das dos um uma e em no na nos nas para por com que se ao antes depois sua seu suas seus este esta salve dica rotina confira use siga indicado indicada orientacoes fabricante fabricantes'.split())
ALIASES = {'lavagem':'lavar', 'lavando':'lavar', 'lave':'lavar', 'enxague':'lavar',
           'organize':'organizar', 'organizacao':'organizar', 'arrume':'organizar',
           'guarde':'guardar', 'armazenar':'guardar', 'armazenamento':'guardar',
           'dobrar':'dobra', 'dobre':'dobra', 'cabides':'cabide', 'toalhas':'toalha',
           'roupas':'roupa', 'pecas':'roupa', 'tecidos':'tecido', 'maos':'mao',
           'potes':'pote', 'utensilios':'utensilio', 'prateleiras':'prateleira'}


def norm(value):
    value = unicodedata.normalize('NFKD', str(value).lower())
    return ' '.join(re.findall('[a-z0-9]+', ''.join(c for c in value if not unicodedata.combining(c))))


def tokens(lines):
    return {ALIASES.get(w, w) for w in norm(' '.join(lines)).split() if w not in STOP}


def settings():
    return json.loads(POLICY.read_text())


def describe(post):
    lines = post.get('script_lines') or []
    text = norm(' '.join(lines))
    concept = post.get('concept', '')
    key = re.sub(r'^auto-|-[a-f0-9]{12}$', '', concept)
    # IDs are derived from editorial meaning, never the media/text hash.
    if concept.startswith('licensed-wan104-episode-'):
        key = 'legacy-mixed-cupboard'
    elif concept.startswith('tip12-'):
        key = concept[6:]
    elif 'lavar as maos' in text or ('mao' in tokens(lines) and 'sabonete' in text):
        key = 'handwashing'
    elif 'armario' in text and ('cabide' in text or 'apertado' in text):
        key = 'hangers'
    elif 'dobra' in text and ('roupa' in text or 'gaveta' in text):
        key = 'folding'
    stable = {'topic_id': key, 'problem_id': key, 'solution_id': key,
              'narrative_id': 'hook-problem-demonstration-solution-cta',
              'hook_id': norm(lines[0]) if lines else '', 'environment': 'unknown', 'objects': []}
    # Only authored catalog IDs may supply finer metadata. Callers cannot label
    # arbitrary repeated text as a new topic to bypass semantic comparison.
    if concept.startswith('tip12-'):
        from editorial_topics import BY_ID
        tip = BY_ID.get(key)
        if tip:
            stable.update({k: tip[k] for k in ('topic_id','problem_id','solution_id','environment','objects')})
    patterns = {
        'series-order': ('colecao', 'volumes'),
        'air-gap-drying': ('espaco', 'ar circular'),
        'fabric-temperature-sort': ('etiqueta', 'temperatura'),
        'original-product-container': ('embalagem original',),
        'surface-compatibility': ('produto', 'superficie', 'rotulo'),
        'particle-free-cloth': ('pano', 'particulas'),
        'solid-waste-strainer': ('coletor', 'ralo'),
        'exit-route': ('fundo', 'saida'),
        'drawer-clearance': ('pilha', 'altura'),
        'visible-sharp-tools': ('cortantes', 'separad'),
        'empty-pocket-check': ('bolso', 'tambor'),
        'rated-hook-load': ('suporte', 'capacidade'),
        'door-clearance': ('prender', 'porta'),
    }
    stable['instruction_ids'] = [key for key, terms in patterns.items() if all(t in text for t in terms)]
    if concept.startswith('tip12-'): stable['instruction_ids'].append(stable['solution_id'])
    return stable


def date(post):
    raw = post.get('scheduled_at') or post.get('submitted_at')
    if isinstance(raw, dict): raw = raw.get('dateTime')
    try:
        parsed = dt.datetime.fromisoformat(raw.replace('Z', '+00:00'))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except (AttributeError, ValueError, TypeError):
        return None


def history(queue, state, exclude_id=None):
    merged = {p.get('id', 'queue-'+str(n)): dict(p) for n,p in enumerate(queue.get('posts', []))}
    for key, receipt in state.get('posts', {}).items():
        merged[key] = {**merged.get(key, {}), **receipt, 'id':key}
    return [p for key,p in merged.items() if key != exclude_id and p.get('script_lines')]


def reason(candidate, queue, state, exclude_id=None, now=None):
    cfg = settings()
    old = history(queue, state, exclude_id)
    lines = candidate.get('script_lines') or []
    if not lines: return None  # Other approval gates require script/consent as applicable.
    meta, bag = describe(candidate), tokens(lines)
    body = tokens(lines[1:-1] if len(lines) > 3 else lines)
    reference = now or date(candidate) or dt.datetime.now(dt.timezone.utc)
    ordered = sorted(old, key=lambda p: date(p) or dt.datetime.max.replace(tzinfo=dt.timezone.utc))
    recent_ids = {id(p) for p in ordered[-cfg['last_publications']:]}
    for p in old:
        previous = p['script_lines']
        other = tokens(previous)
        other_body = tokens(previous[1:-1] if len(previous) > 3 else previous)
        # Order-free overlap catches sentence reordering, new CTA and synonyms.
        overlap = len(body & other_body)/max(1, min(len(body),len(other_body)))
        union = len(bag & other)/max(1,len(bag | other))
        if norm(' '.join(lines)) == norm(' '.join(previous)) or (len(body) >= 8 and len(other_body) >= 8 and overlap >= cfg['instruction_overlap']):
            return 'EDITORIAL_REPEATED_INSTRUCTIONS'
        recent = id(p) in recent_ids or date(p) is None or date(p) >= reference-dt.timedelta(days=cfg['days'])
        if not recent: continue
        prior = describe(p)
        if set(meta['instruction_ids']) & set(prior['instruction_ids']):
            return 'EDITORIAL_SOLUTION_ALREADY_COVERED'
        if meta['problem_id'] == prior['problem_id'] and meta['solution_id'] == prior['solution_id']:
            return 'EDITORIAL_TOPIC_COOLDOWN'
        if meta['topic_id'] and meta['topic_id'] == prior['topic_id']:
            return 'EDITORIAL_TOPIC_COOLDOWN'
        if meta['hook_id'] and meta['hook_id'] == prior['hook_id']:
            return 'EDITORIAL_HOOK_REPEATED'
        if len(bag) >= 8 and union >= cfg['semantic_jaccard']:
            return 'EDITORIAL_SEMANTIC_OVERLAP'
    return None


def require(candidate, queue, state, exclude_id=None):
    blocked = reason(candidate, queue, state, exclude_id)
    if blocked: raise ValueError(blocked)
    return describe(candidate)


def audit(queue, state):
    records = history(queue, state)
    return {'policy': settings(), 'entries': [dict(id=p.get('id'), scheduled_at=p.get('scheduled_at'),
        editorial=describe(p), script_sha256=hashlib.sha256(norm(' '.join(p['script_lines'])).encode()).hexdigest()) for p in records]}
