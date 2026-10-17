"""Bounded, reviewed factual topic bank; programmatic scripts, never fake novelty.

A topic is used once, irrespective of changes to its opening/CTA. Adding new
facts and appropriate visual sources remains editorial work. No paid text API.
"""
import hashlib
import textwrap

# id, category, coherent illustrative footage, hook, factual steps, contextual CTA
TOPICS = [
 ('piso-rota-saida','rotina',['piso'], 'Você pisa onde acabou de limpar?',
  'Antes de começar, planeje o caminho. Limpe a partir do fundo do ambiente. Avance na direção da saída. Deixe uma passagem livre. Evite atravessar a parte que ainda está molhada. Espere o piso secar antes de circular.', 'Salve para sua próxima faxina.'),
 ('torneira-final-seco','conservacao',['pia'], 'Terminou de limpar a torneira?',
  'Depois da limpeza indicada pelo fabricante, confira se ficou água na superfície. Use um pano limpo e macio para secar. Passe também ao redor da base. Não use o mesmo pano sujo da etapa anterior. Termine uma peça antes de começar outra.', 'Inclua este passo na rotina.'),
 ('espelho-pano-sem-fiapos','limpeza',['espelho'], 'Seu pano deixa fiapos no espelho?',
  'Confira o pano antes de começar. Prefira um pano limpo, macio e que não solte fiapos. Use o produto indicado para o espelho. Não improvise com materiais ásperos. Observe o resultado com outra iluminação. Se houver resíduos, use uma parte limpa do pano.', 'Salve para lembrar do pano.'),
 ('retirar-tapetes','preparacao',['piso'], 'Tem tapete no caminho da faxina?',
  'Retire os tapetes antes de limpar o piso. Coloque cada um em um local seco, fora da passagem. Limpe a área que estava coberta. Espere o piso secar completamente. Só então devolva os tapetes ao lugar. Assim você consegue cuidar de toda a área.', 'Lembre desse passo na próxima limpeza.'),
 ('bancada-tirar-objetos','preparacao',['pia'], 'Você limpa só ao redor dos objetos?',
  'Antes de limpar a bancada, retire os itens soltos. Coloque tudo em um apoio seguro. Limpe a área que estava escondida. Seque conforme a orientação da superfície. Confira a base dos objetos antes de devolvê-los. Retorne apenas o que pertence àquele espaço.', 'Salve para organizar a bancada.'),
 ('piso-pouca-agua','conservacao',['piso'], 'Seu piso pode receber tanta água?',
  'Confira a orientação do fabricante antes de molhar. Cada material pede um cuidado diferente. Se a orientação for usar pano úmido, torça bem antes de passar. Não deixe poças. Observe cantos e juntas. Não use a aparência do piso como única referência.', 'Guarde esta pergunta para a faxina.'),
 ('pano-inspecao','limpeza',['pia','espelho'], 'O pano está pronto para outra limpeza?',
  'Antes de começar, confira se o pano está limpo. Observe restos de produto, sujeira e partículas que possam riscar. Se estiver sujo, troque por outro. Separe os panos usados dos limpos. Lave conforme a etiqueta e deixe secar antes de guardar.', 'Salve para cuidar dos seus panos.'),
 ('faxina-checagem-final','rotina',['pia','piso'], 'A faxina terminou de verdade?',
  'Faça uma checagem rápida antes de sair. Confira se o piso está seco. Retire os materiais da passagem. Feche as embalagens de limpeza. Guarde os produtos no local adequado. Separe os panos usados para lavar. Deixe o ambiente pronto para ser utilizado.', 'Salve esta checagem final.'),
]


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


def rotate(ideas, queue, state):
    used = {p.get('concept') for p in queue.get('posts', [])}
    used.update(p.get('concept') for p in state.get('posts', {}).values())
    seen_scripts = {p.get('script_sha256') for p in queue.get('posts', [])}
    seen_scripts.update(p.get('script_sha256') for p in state.get('posts', {}).values())
    remaining = [i for i in ideas if i[0] not in used and fingerprint(i[2]) not in seen_scripts]
    last = category(next((p.get('concept') for p in reversed(queue.get('posts', [])) if p.get('concept')), ''))
    ordered = []
    while remaining:
        item = next((i for i in remaining if category(i[0]) != last), remaining[0])
        remaining.remove(item); ordered.append(item); last = category(item[0])
    return ordered
