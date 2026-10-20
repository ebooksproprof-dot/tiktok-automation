"""Finite factual draft renewal from measured footage; NEVER approves or publishes.

Hooks are presentation variants, not new topics. Exhaustion is explicit: adding
new factual topics and reviewing visual context remains editorial work.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from media_rights import valid_source
from visual_library import check_sources, history as visual_history

ROOT = Path(__file__).resolve().parent
MAX_HISTORY = 120
# topic, semantic family, required tag groups, hook, steps, CTA
TEMPLATES = [
    ('louca-espaco-escorredor', 'louca', ({'dish', 'dishes', 'plate'}, {'wash', 'washing', 'cleaning'}),
     'Faltou espaço no escorredor?',
     'Antes de começar, guarde a louça que já está seca. Deixe uma área livre para as peças que serão lavadas. Organize os utensílios sem empilhar de forma instável. Termine um pequeno grupo antes de aumentar a pilha.',
     'Salve para organizar a próxima lavagem.'),
    ('louca-restos-antes', 'louca', ({'dish', 'dishes', 'plate'}, {'wash', 'washing', 'cleaning'}),
     'A pia enche de restos de comida?',
     'Antes de lavar, retire os restos dos pratos para o lixo adequado. Separe as peças e preserve uma área de trabalho. Lave conforme o material dos utensílios. Ao terminar, confira o coletor do ralo e retire os resíduos.',
     'Inclua esta etapa na rotina da cozinha.'),
    ('estante-uma-prateleira', 'estante', ({'book', 'books'}, {'shelves', 'shelf', 'bookcase', 'library'}),
     'Organizar a estante parece uma tarefa enorme?',
     'Comece por uma única prateleira. Separe os livros que pertencem a outro lugar. Devolva os títulos em uma ordem que você reconheça. Deixe as lombadas visíveis e confira se as peças estão estáveis antes de passar à próxima prateleira.',
     'Salve para começar por uma parte pequena.'),
    ('estante-local-de-devolucao', 'estante', ({'book', 'books'}, {'shelves', 'shelf', 'bookcase', 'library'}),
     'Você nunca lembra onde devolver o livro?',
     'Escolha uma regra simples para a estante: assunto ou autor, por exemplo. Mantenha a mesma regra em cada grupo. Reserve um lugar acessível para as leituras atuais. Depois de usar, devolva o título ao grupo correspondente.',
     'Escolha uma regra que faça sentido para você.'),
    ('pia-embalagens-vazias', 'pia', ({'sink', 'faucet', 'bathroom'}, {'soap', 'washing', 'wash', 'cleaning'}),
     'As embalagens vazias continuam na pia?',
     'Confira os itens ao redor da pia. Separe as embalagens que realmente acabaram. Guarde fora da bancada os produtos que não usa na rotina diária. Deixe o sabonete acessível e preserve espaço para utilizar a pia.',
     'Salve para fazer uma revisão rápida.'),
    ('pia-local-do-sabonete', 'pia', ({'sink', 'faucet', 'bathroom'}, {'soap', 'washing', 'wash', 'cleaning'}),
     'O sabonete está sempre fora do lugar?',
     'Escolha um apoio estável e fácil de alcançar. Confira se ele atrapalha a torneira ou o uso da cuba. Deixe os itens da rotina próximos e retire os objetos sem função naquele espaço. Ao terminar, devolva cada item ao seu lugar.',
     'Organize a pia pensando no uso de todos os dias.'),
]


def digest(text):
    normalized = unicodedata.normalize('NFKD', text.casefold())
    return hashlib.sha256(' '.join(re.findall(r'\w+', normalized)).encode()).hexdigest()


def measured(record):
    return (valid_source(record) and bool(record.get('author'))
            and record.get('source_id') == record.get('url')
            and re.fullmatch(r'[a-f0-9]{64}', record.get('sha256', ''))
            and isinstance(record.get('dhash'), list) and len(record['dhash']) == 5
            and all(isinstance(x, str) and re.fullmatch(r'[a-f0-9]{16}', x) for x in record['dhash'])
            and isinstance(record.get('duration'), (int, float)) and record['duration'] >= 15
            and record.get('status') == 'pending_visual_review')


def generate(inbox, ledger, previous=(), limit=2):
    if not isinstance(limit, int) or not 1 <= limit <= 2:
        raise ValueError('DRAFT_LIMIT_MUST_BE_ONE_OR_TWO')
    if ledger.get('version') != 1 or not isinstance(ledger.get('drafts'), list):
        raise ValueError('INVALID_DRAFT_LEDGER')
    if len(ledger['drafts']) > MAX_HISTORY:
        raise ValueError('DRAFT_HISTORY_CAPACITY_REACHED')
    drafts = list(ledger['drafts'])
    used_topics = {d['topic'] for d in drafts}
    used_bodies = {d['body_sha256'] for d in drafts}
    prior = list(previous) + [{'visual_sources': [d['media']]} for d in drafts]
    added = []
    for record in inbox.get('items', []):
        if len(added) >= limit or len(drafts) + len(added) >= MAX_HISTORY:
            break
        if not measured(record):
            continue
        try:
            check_sources([record], prior)
        except ValueError:
            continue
        # Lexical relevance is only draft eligibility, never a semantic approval.
        tags = set(re.findall(r'[a-z]+', record.get('selection_reason', '').lower()))
        for topic, family, groups, hook, steps, cta in TEMPLATES:
            body_hash = digest(steps)
            if topic in used_topics or body_hash in used_bodies or not all(tags & g for g in groups):
                continue
            draft = dict(id='draft-' + topic, topic=topic, family=family,
                         hook=hook, steps=steps, cta=cta, body_sha256=body_hash,
                         script_sha256=digest(hook + ' ' + steps + ' ' + cta),
                         media=dict(record), status='pending_editorial_review',
                         editorial_approved=False, approved=False, published=False,
                         limitations=['Lexical context only; inspect footage and final crop.',
                                      'Finite factual template; not evidence of monthly capacity.'])
            added.append(draft)
            used_topics.add(topic); used_bodies.add(body_hash)
            prior.append({'visual_sources': [record]})
            break
    return dict(version=1, drafts=drafts + added,
                last_run=dict(created=len(added), status='drafted' if added else 'exhausted_or_no_eligible_media',
                              automatic_approval=False, template_capacity=len(TEMPLATES)))


def read(path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def main(root=ROOT):
    root = Path(root)
    target = root/'editorial_drafts.json'
    ledger = read(target, dict(version=1, drafts=[]))
    previous = visual_history(read(root/'queue.json', {}), read(root/'state.json', {}))
    previous.append(read(root/'visual_history.json', {}))
    result = generate(read(root/'media_inbox.json', {'items': []}), ledger, previous)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(target)
    print('EDITORIAL_DRAFTS_CREATED=' + str(result['last_run']['created']) + '; APPROVED=0; PUBLISHED=0')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    result = main(args.root)
    raise SystemExit(0 if result['last_run']['created'] else 1)
