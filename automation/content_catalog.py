"""Bounded, reviewed factual topic bank; programmatic scripts, never fake novelty.

A topic is used once, irrespective of changes to its opening/CTA. Adding new
facts and appropriate visual sources remains editorial work. No paid text API.
"""
import hashlib
import textwrap
import re
import unicodedata
from catalog_extension import TOPICS as EXTRA_TOPICS

# id, category, coherent illustrative footage, hook, factual steps, contextual CTA
TOPICS = [
 ('piso-rota-saida','rotina',['piso'], 'Você pisa onde acabou de limpar?',
  'Antes de começar, planeje o caminho. Limpe a partir do fundo do ambiente. Avance na direção da saída. Deixe uma passagem livre. Evite atravessar a parte que ainda está molhada. Espere o piso secar antes de circular.', 'Salve para sua próxima faxina.'),
 ('torneira-final-seco','conservacao',['pia'], 'Terminou de limpar a torneira?',
  'Depois da limpeza indicada pelo fabricante, confira se ficou água na superfície. Use um pano limpo e macio para secar. Passe também ao redor da base. Não use o mesmo pano sujo da etapa anterior. Termine uma peça antes de começar outra.', 'Inclua este passo na rotina.'),
 ('espelho-pano-sem-fiapos','limpeza',['espelho2'], 'Seu pano deixa fiapos no espelho?',
  'Confira o pano antes de começar. Prefira um pano limpo, macio e que não solte fiapos. Use o produto indicado para o espelho. Não improvise com materiais ásperos. Observe o resultado com outra iluminação. Se houver resíduos, use uma parte limpa do pano.', 'Salve para lembrar do pano.'),
 ('retirar-tapetes','conservacao',['tapete'], 'Vai aspirar o tapete?',
  'Primeiro confira a etiqueta e a orientação do fabricante. Confirme se o material permite aspirador. Retire objetos pequenos do caminho. Use o acessório indicado. Passe sem puxar franjas ou partes soltas. Interrompa se notar qualquer dano.', 'Guarde este cuidado para o tapete.'),
 ('bancada-tirar-objetos','preparacao',['bancada'], 'Você limpa só ao redor dos objetos?',
  'Antes de limpar a bancada, retire os itens soltos. Coloque tudo em um apoio seguro. Limpe a área que estava escondida. Seque conforme a orientação da superfície. Confira a base dos objetos antes de devolvê-los. Retorne apenas o que pertence àquele espaço.', 'Salve para organizar a bancada.'),
 ('piso-pouca-agua','conservacao',['piso2'], 'Seu piso pode receber tanta água?',
  'Confira a orientação do fabricante antes de molhar. Cada material pede um cuidado diferente. Se a orientação for usar pano úmido, torça bem antes de passar. Não deixe poças. Observe cantos e juntas. Não use a aparência do piso como única referência.', 'Guarde esta pergunta para a faxina.'),
 ('pano-inspecao','limpeza',['pia2','espelho2'], 'O pano está pronto para outra limpeza?',
  'Antes de começar, confira se o pano está limpo. Observe restos de produto, sujeira e partículas que possam riscar. Se estiver sujo, troque por outro. Separe os panos usados dos limpos. Lave conforme a etiqueta e deixe secar antes de guardar.', 'Salve para cuidar dos seus panos.'),
 ('faxina-checagem-final','rotina',['bancada-limpa','geladeira'], 'A faxina terminou de verdade?',
  'Faça uma checagem rápida antes de sair. Confira se o piso está seco. Retire os materiais da passagem. Feche as embalagens de limpeza. Guarde os produtos no local adequado. Separe os panos usados para lavar. Deixe o ambiente pronto para ser utilizado.', 'Salve esta checagem final.'),
 ('geladeira-puxador','limpeza',['geladeira'], 'Você limpou o puxador da geladeira?',
  'Confira a orientação do fabricante. Use um pano limpo e adequado à superfície. Passe também nas laterais do puxador. Não deixe excesso de produto. Seque quando a orientação indicar. Guarde o pano usado para lavar.', 'Inclua o puxador na próxima limpeza.'),
 ('gaveta-uma-categoria','organizacao',['roupas'], 'Sua gaveta mistura tudo?',
  'Retire apenas uma categoria por vez. Separe o que realmente pertence à gaveta. Dobre de um jeito que permita ver as peças. Devolva primeiro o que usa com frequência. Não aperte além do espaço disponível. Termine uma gaveta antes de abrir outra.', 'Salve para organizar sem bagunçar tudo.'),
 ('bancada-livre','preparacao',['bancada','bancada-limpa'], 'A bancada está cheia antes da limpeza?',
  'Retire os itens soltos e coloque em um apoio seguro. Descarte apenas o que você já identificou. Limpe a superfície conforme o material. Confira a base dos objetos. Devolva somente o que pertence à bancada. Deixe livre a área de uso diário.', 'Salve para a próxima organização.'),
 ('tapete-orientacao','conservacao',['tapete'], 'Vai limpar o tapete de qualquer jeito?',
  'Primeiro confira a etiqueta e a orientação do fabricante. Observe se o material permite aspirador. Use o acessório indicado. Passe sem puxar franjas ou partes soltas. Interrompa se notar dano. Para manchas, siga a orientação específica do material.', 'Guarde este cuidado para o tapete.'),
 ('pia-por-partes','limpeza',['pia2'], 'Você limpa a pia toda de uma vez?',
  'Separe a limpeza por partes. Comece pela área mais distante do ralo. Use o produto indicado para o material. Passe pela cuba e depois pela borda. Enxágue somente quando o rótulo orientar. Termine secando as áreas que não devem ficar molhadas.', 'Salve esta ordem para testar depois.'),
 ('objetos-da-bancada','organizacao',['bancada'], 'Cada objeto tem lugar na bancada?',
  'Agrupe os itens pelo uso. Deixe juntos os que fazem parte da mesma tarefa. Retire embalagens vazias. Evite empilhar objetos instáveis. Reserve uma área livre para preparar alimentos ou apoiar materiais. Revise a bancada antes de encerrar.', 'Salve para organizar por função.'),
]


if {t[0] for t in TOPICS}.intersection(t[0] for t in EXTRA_TOPICS):
    raise ValueError('Extension duplicates built-in topic')
TOPICS.extend(EXTRA_TOPICS)


def script(topic):
    key, category, sources, hook, steps, cta = topic
    lines = [hook]
    # Bound line width so captions remain within the existing portrait safe area.
    for sentence in steps.split('. '):
        sentence = sentence.rstrip('.') + '.'
        lines.extend(textwrap.wrap(sentence, width=29, break_long_words=False))
    lines.extend(textwrap.wrap(cta, width=29, break_long_words=False))
    return key, sources, lines


def category(key):
    return next((t[1] for t in TOPICS if t[0] == key), 'limpeza')


def fingerprint(lines):
    normalized = ' '.join(' '.join(lines).lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()


def near_duplicate(left, right):
    def shingles(lines):
        text = unicodedata.normalize('NFKD', ' '.join(lines).lower())
        words = re.findall(r'[a-z0-9]+', ''.join(c for c in text if not unicodedata.combining(c)))
        return {tuple(words[i:i+3]) for i in range(len(words)-2)}
    a, b = shingles(left), shingles(right)
    return bool(a and b) and len(a & b)/len(a | b) >= .65


def novel_scripts(ideas, queue, state, exclude_id=None):
    historical = [p for p in queue.get('posts', []) if exclude_id is None or p.get('id') != exclude_id]
    historical += [p for key, p in state.get('posts', {}).items() if key != exclude_id]
    return [i for i in ideas if not any(near_duplicate(i[2], p['script_lines'])
            for p in historical if p.get('script_lines'))]


def validate_ids(ideas):
    if len(ideas) != len({i[0] for i in ideas}):
        raise ValueError('Duplicate concept ID in complete catalog')


def rotate(ideas, queue, state):
    used = {p.get('concept') for p in queue.get('posts', [])}
    used.update(p.get('concept') for p in state.get('posts', {}).values())
    seen_scripts = {p.get('script_sha256') for p in queue.get('posts', [])}
    seen_scripts.update(p.get('script_sha256') for p in state.get('posts', {}).values())
    remaining = [i for i in ideas if i[0] not in used and fingerprint(i[2]) not in seen_scripts]
    remaining = novel_scripts(remaining, queue, state)
    last = category(next((p.get('concept') for p in reversed(queue.get('posts', [])) if p.get('concept')), ''))
    ordered = []
    while remaining:
        item = next((i for i in remaining if category(i[0]) != last), remaining[0])
        remaining.remove(item); ordered.append(item); last = category(item[0])
    return ordered
