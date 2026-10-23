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
    ('roupas-uma-categoria', 'roupas', ({'clothes', 'clothing', 'laundry'},),
     'A pilha de roupas parece não acabar?',
     'Separe uma categoria para começar, como camisetas. Dobre as peças de um jeito que caibam no espaço disponível. Guarde essa pequena pilha antes de pegar a próxima. Deixe separadas as roupas que precisam de outro cuidado.',
     'Experimente começar por uma categoria.'),
    ('gaveta-medir-divisoria', 'gavetas', ({'drawer', 'drawers'},),
     'A divisória cabe mesmo na sua gaveta?',
     'Meça a largura, a profundidade e a altura útil antes de escolher uma divisória. Confira se a gaveta fecha sem encostar nos objetos. Separe os itens por uso e reserve o espaço mais acessível para o que você pega todos os dias.',
     'Anote as medidas antes de comprar.'),
    ('utensilios-por-funcao', 'utensilios', ({'utensil', 'utensils', 'cutlery'}, {'kitchen', 'drawer', 'cooking'}),
     'Você procura uma colher e encontra tudo misturado?',
     'Agrupe os utensílios pela função. Deixe juntos os que usa para servir e separe os de preparo. Confira se cada peça cabe sem prender a gaveta. Guarde objetos cortantes em um suporte apropriado, seguindo a orientação do fabricante.',
     'Salve para revisar uma gaveta da cozinha.'),
    ('sapatos-pares-completos', 'sapatos', ({'shoe', 'shoes'},),
     'Cadê o outro pé do sapato?',
     'Reúna os pares antes de organizar a sapateira. Confira quais estão secos e prontos para guardar. Separe os que precisam de limpeza ou reparo. Escolha uma posição em que cada par fique visível e não impeça a abertura da porta.',
     'Comece reunindo os pares.'),
    ('mesa-retirar-antes', 'mesa', ({'table', 'desk'}, {'cleaning', 'cloth', 'clean'}),
     'Limpar desviando de objetos dá trabalho?',
     'Escolha uma parte da mesa e retire os objetos soltos. Separe o que pertence a outro lugar. Limpe conforme o material da superfície e as instruções do produto. Depois, devolva apenas o que precisa ficar naquele espaço.',
     'Salve esta sequência para a próxima limpeza.'),
    ('toalhas-altura-prateleira', 'toalhas', ({'towel', 'towels'},),
     'A pilha de toalhas cai quando você pega uma?',
     'Confira a altura disponível na prateleira. Faça pilhas menores, sem comprimir as peças contra o móvel. Guarde apenas toalhas completamente secas e deixe as de uso frequente em uma posição fácil de alcançar. Ajuste a dobra ao espaço.',
     'Teste uma pilha menor no seu armário.'),
    ('potes-conferir-tampas', 'potes', ({'container', 'containers'}, {'kitchen', 'food', 'storage'}),
     'Tem pote demais e tampa de menos?',
     'Separe os potes e procure a tampa correspondente de cada um. Confira as condições das peças e as orientações de uso do fabricante. Agrupe por tamanho e deixe juntos os conjuntos que você utiliza com frequência.',
     'Salve para conferir seus potes.'),
    ('vassoura-liberar-percurso', 'piso', ({'broom', 'sweeping'},),
     'Você para de varrer para tirar objetos do caminho?',
     'Antes de começar, recolha os objetos soltos do piso. Escolha uma área pequena e mantenha uma passagem livre. Use o utensílio indicado para o acabamento e recolha os resíduos ao terminar. Guarde a vassoura em um lugar onde não atrapalhe a circulação.',
     'Prepare o espaço antes de varrer.'),
    ('mesa-papel-destino', 'escrivaninha', ({'desk', 'stationery'},),
     'Sua mesa virou uma pilha de papéis?',
     'Separe uma pequena pilha para revisar. Confira o que precisa guardar e o que tem uma tarefa pendente. Defina um lugar para cada grupo. Antes de descartar documentos, verifique se você ainda precisa deles e proteja informações pessoais.',
     'Escolha uma pilha pequena para começar.'),
    ('cabides-pecas-visiveis', 'cabides', ({'hanger', 'hangers'},),
     'Você esquece as roupas no fundo do armário?',
     'Separe as peças por tipo e confira se os cabides têm espaço para se mover. Evite esconder várias roupas no mesmo cabide. Use um modelo adequado ao peso e ao formato de cada peça. Deixe as opções de uso frequente visíveis.',
     'Revise um trecho do armário por vez.'),
    ('cama-guardar-roupa-extra', 'cama', ({'bed', 'bedroom'},),
     'A roupa de cama extra está sem lugar?',
     'Reúna as peças que pertencem ao mesmo conjunto. Confira se estão limpas e completamente secas antes de guardar. Escolha um espaço onde caibam sem bloquear portas ou gavetas. Identifique os conjuntos pelo tamanho da cama.',
     'Separe um lugar para cada conjunto.'),
    ('cesto-separar-destino', 'cestos', ({'basket', 'laundry'}, {'clothes', 'clothing', 'laundry'}),
     'O cesto mistura roupas com destinos diferentes?',
     'Antes de levar as peças para lavar, confira as etiquetas e separe os cuidados necessários. Reserve um lugar para as roupas que precisam de tratamento diferente. Evite devolver peças úmidas ao armário e mantenha o cesto em uma área acessível.',
     'Use as etiquetas para orientar a separação.'),
    ('panos-secar-antes-guardar', 'panos', ({'cloth', 'microfiber'}, {'cleaning', 'clean'}),
     'Você guarda o pano ainda úmido?',
     'Depois do uso, faça a limpeza indicada para o material do pano. Deixe secar completamente antes de guardar. Separe os panos por ambiente e mantenha os limpos em um lugar próprio. Confira as instruções antes de usar produtos na lavagem.',
     'Inclua a secagem no fim da rotina.'),
    ('plantas-conferir-apoio', 'plantas', ({'plant', 'plants'}, {'pot', 'indoor'}),
     'O vaso está apoiado direto no móvel?',
     'Confira se o apoio é estável e adequado ao peso do vaso. Observe se existe água acumulada ou umidade sobre a superfície. Siga os cuidados indicados para a planta e para o móvel. Deixe espaço para alcançar o vaso sem esbarrar em outros objetos.',
     'Revise os apoios das suas plantas.'),
    ('lixeira-saco-tamanho', 'lixeira', ({'trash', 'bin', 'garbage'},),
     'O saco fica caindo dentro da lixeira?',
     'Confira o tamanho e o formato da lixeira antes de escolher o saco. Ajuste a borda conforme o modelo e evite encher além da capacidade. Separe os resíduos seguindo as regras locais. Limpe o recipiente de acordo com o material e deixe secar.',
     'Anote o tamanho adequado para sua lixeira.'),
    ('livros-conferir-volumes', 'estante', ({'books', 'book'}, {'library', 'shelf', 'shelves', 'reading'}),
     'Os volumes da coleção ficaram espalhados?',
     'Escolha uma coleção e reúna os volumes que você já tem. Confira a ordem nas capas ou lombadas. Reserve um espaço em que todos caibam com estabilidade, sem forçar a prateleira. Anote os títulos ausentes antes de procurar novos exemplares.',
     'Comece por uma coleção da estante.'),
    ('torneira-area-livre', 'pia', ({'faucet', 'sink'}, {'kitchen'}),
     'Os objetos atrapalham o acesso à torneira?',
     'Observe o espaço que você usa para abrir a torneira e apoiar as mãos. Retire objetos sem função daquela área. Escolha um lugar estável para os itens da rotina e confira se nenhum deles impede o uso da cuba.',
     'Organize pensando no acesso à pia.'),
    ('janela-material-primeiro', 'janelas', ({'window', 'windows'}, {'cleaning', 'clean'}),
     'Antes de limpar a janela, confira o material.',
     'Leia as instruções do fabricante para o vidro, a película e a esquadria. Escolha os materiais compatíveis e retire os objetos próximos. Limpe apenas as partes acessíveis com segurança. Para áreas altas ou externas, procure ajuda adequada.',
     'Salve para conferir antes da limpeza.'),
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
                              automatic_approval=False, template_capacity=len(TEMPLATES),
                              unused_templates=len({t[0] for t in TEMPLATES} - used_topics),
                              pending_review=len([d for d in drafts + added
                                                  if d.get('status') == 'pending_editorial_review']),
                              approved_reserve_days=None,
                              reserve_note='Drafts are not approved videos; no daily publishing capacity inferred.'))


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
