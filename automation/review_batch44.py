"""Read-only, hash-bound preview for explicit consent in chat; never submits posts."""
import argparse
import datetime as dt
import html
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from batch_approval import digest, identity, stamp
from visual_library import history, require_evidence

TZ = ZoneInfo('America/Sao_Paulo')
REMOTE_KEYS = ('public_url', 'metricool_post_id', 'buffer_post_id', 'publish_id')


def safe_url(value):
    if not isinstance(value, str) or any(ord(c) < 33 for c in value):
        return False
    p = urlsplit(value)
    if p.scheme != 'https' or p.username or p.password or p.port or p.query or p.fragment:
        return False
    prefixes = {
        'github.com': '/ebooksproprof-dot/tiktok-automation/releases/download/media-',
        'ebooksproprof-dot.github.io': '/tiktok-automation/public/rendered/daily/',
        'raw.githubusercontent.com': '/ebooksproprof-dot/tiktok-automation/',
    }
    return (p.netloc in prefixes and p.path.startswith(prefixes[p.netloc])
            and p.path.endswith('.mp4') and '..' not in p.path and '%' not in p.path)


def due_of(post):
    value = post.get('scheduled_at')
    if not value:
        return None
    if isinstance(value, dict):
        result = dt.datetime.fromisoformat(value['dateTime'].replace('Z', '+00:00'))
        return result if result.tzinfo else result.replace(tzinfo=ZoneInfo(value['timezone']))
    return stamp(value)


def slot_valid(due, now):
    if due is None:
        return False
    local = due.astimezone(TZ)
    return (now + dt.timedelta(minutes=30) <= due <= now + dt.timedelta(days=7)
            and local.hour in (10, 18) and not any((local.minute, local.second, local.microsecond)))


def build_preview(queue, state, now=None, archived=None, audit=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('TIMEZONE_REQUIRED')
    posts = queue['posts']
    ids = [p['id'] for p in posts]
    if len(set(ids)) != len(ids):
        raise ValueError('DUPLICATE_QUEUE_IDS')
    submitted = state.get('posts', {})
    pending = [p for p in posts if p['id'] not in submitted and not any(p.get(k) for k in REMOTE_KEYS)]
    occupied = set()
    for post in posts + list(submitted.values()):
        due = due_of(post)
        if due and due > now:
            occupied.add(due)
    items = []
    for post in pending:
        blocks = []
        if post.get('approved') is True:
            blocks.append('Já aprovado; requer tratamento separado, não reautorizar.')
        if 'REJECTED' in post.get('publishing_status', '') or post.get('editorial_rejection'):
            blocks.append('Rejeitado editorialmente: ' + post.get('editorial_rejection', 'revisão necessária'))
        if post.get('quality', {}).get('technical_pass') is not True:
            blocks.append('Validação técnica ausente.')
        try:
            exact = identity(post)
        except (KeyError, ValueError) as exc:
            exact = dict(id=post['id'], sha256=post.get('quality', {}).get('sha256'),
                         script_hash=None, post_snapshot_sha256=digest(post))
            blocks.append('Identidade incompleta: ' + str(exc))
        previous = history(queue, state, exclude_id=post['id'])
        if archived is not None:
            previous.append(archived)
        try:
            require_evidence(post, previous)
        except (ValueError, KeyError, TypeError) as exc:
            blocks.append('Controle visual: ' + str(exc))
        notes = None
        for record in audit or []:
            if (record.get('id') == post['id'] and record.get('sha256') == exact['sha256']
                    and record.get('video_url') == post.get('video_url')
                    and record.get('hash_matches_queue') is True):
                notes = {key: record.get(key) for key in ('editorial_review', 'visual_review_scope',
                                                         'perceptual_audio_review')}
        url = post.get('video_url')
        if not safe_url(url):
            blocks.append('URL de vídeo fora das origens permitidas.')
            url = None
        original = post.get('scheduled_at')
        due = due_of(post)
        proposed = None
        if not blocks:
            # Retain a future slot only if no *other* item also reserves it.
            others = [p for p in posts if p['id'] != post['id']] + list(submitted.values())
            if slot_valid(due, now) and not any(due_of(p) == due for p in others):
                proposed = due
            else:
                for day in range(8):
                    date = now.astimezone(TZ).date() + dt.timedelta(days=day)
                    for hour in (10, 18):
                        candidate = dt.datetime.combine(date, dt.time(hour), TZ)
                        if slot_valid(candidate, now) and candidate not in occupied:
                            proposed = candidate
                            break
                    if proposed:
                        break
            if proposed is None:
                blocks.append('Sem horário livre nos próximos sete dias.')
            else:
                occupied.add(proposed)
        items.append(dict(id=post['id'], video_url=url, sha256=exact['sha256'],
                          script_hash=exact['script_hash'], post_snapshot_sha256=exact['post_snapshot_sha256'],
                          title=post.get('title', ''), script_lines=post.get('script_lines', []),
                          original_scheduled_at=original,
                          proposed_scheduled_at=proposed.astimezone(TZ).isoformat() if proposed else None,
                          schedule_changed=bool(proposed and due != proposed),
                          selectable=not blocks, blockers=blocks, editorial_review='PENDING', audit_notes=notes,
                          approved=False, consented_at=None))
    valid_slots = [stamp(p['proposed_scheduled_at']) for p in items if p['selectable']]
    result = dict(schema='casasem-review-preview-4.4', generated_at=now.isoformat(),
                  expires_at=(min(valid_slots)-dt.timedelta(minutes=5)).isoformat() if valid_slots else now.isoformat(),
                  queue_snapshot_sha256=digest(queue), state_snapshot_sha256=digest(state),
                  archived_history_sha256=digest(archived) if archived is not None else None,
                  route='buffer', approved=False, consented_at=None, submitted=False,
                  pending_count=len(items), selectable_count=sum(p['selectable'] for p in items), items=items,
                  notice='Proposta somente. Selecionar/copiar não aprova nem agenda. Envie consentimento explícito no chat após assistir; hashes, revisão editorial e horários serão revalidados.')
    result['manifest_sha256'] = digest(result)
    return result


def render_html(manifest):
    esc = lambda x: html.escape(str(x), quote=True)
    cards = []
    for index, item in enumerate(manifest['items']):
        video = (f'<video controls preload="none" src="{esc(item["video_url"])}"></video>'
                 f'<p><a href="{esc(item["video_url"])}" target="_blank" rel="noopener noreferrer">Abrir MP4</a></p>') if item['video_url'] else '<p>URL bloqueada.</p>'
        lines = ''.join(f'<li>{esc(line)}</li>' for line in item['script_lines'])
        blockers = ''.join(f'<p class="blocked">{esc(b)}</p>' for b in item['blockers'])
        notes = item.get('audit_notes') or {}
        audit_text = ''.join(f'<p>{esc(value)}</p>' for value in notes.values() if value)
        audit_html = '<details><summary>Auditoria técnica/editorial — não é aprovação</summary>' + audit_text + '</details>' if notes else ''
        disabled = '' if item['selectable'] else ' disabled'
        cards.append(f'''<article><h2>{esc(item['id'])}</h2>{video}<p>{esc(item['title'])}</p>
<details><summary>Roteiro e identidade exata</summary><ol>{lines}</ol><p>MP4 SHA-256: <code>{esc(item['sha256'])}</code></p><p>Roteiro SHA-256: <code>{esc(item['script_hash'])}</code></p></details>
<p>Horário anterior: {esc(item['original_scheduled_at'] or 'nenhum')}</p>
<p><strong>Proposta, Brasília: {esc(item['proposed_scheduled_at'] or 'bloqueado')}</strong></p>
{audit_html}{blockers}<label><input type="checkbox" class="pick" value="{index}"{disabled}> Selecionar para solicitar autorização no chat</label></article>''')
    payload = json.dumps(manifest, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return '''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CasaSemEsforço — revisão do lote</title><style>body{font:17px system-ui;max-width:1050px;margin:auto;padding:24px;background:#f5f6fa;color:#18212b}article{background:white;padding:20px;border-radius:16px;margin:20px 0}video{max-height:480px;max-width:100%;background:#111}code{overflow-wrap:anywhere}textarea{width:100%;min-height:230px}button{padding:12px;margin:10px 0}.blocked{color:#9b2525}label{display:block;padding:12px 0}</style>
<h1>Revise os vídeos e escolha o lote</h1><p>Assista aos MP4s e confira roteiro, cenas, voz, créditos e horários. Nenhum item está pré-selecionado. Esta página não envia dados, aprova, agenda ou publica.</p>
<p>Horários abaixo são propostas em Brasília, não agendamentos. A seleção só prepara uma mensagem para você enviar no chat. Se a fila, os arquivos ou os horários mudarem, será necessária uma revisão atualizada.</p>
<p><a href="review44.json">Manifesto verificável do lote (JSON)</a></p><p id="expiry"></p>
''' + ''.join(cards) + '''<label><input id="reviewed" type="checkbox"> Assisti aos vídeos selecionados e revisei a correspondência das cenas com o roteiro, áudio, créditos e alegações.</label>
<button id="compose">Preparar mensagem para o chat</button><p id="status" role="status"></p><textarea id="message" readonly aria-label="Mensagem de autorização para enviar no chat"></textarea><button id="copy">Copiar mensagem</button>
<script type="application/json" id="manifest">''' + payload + r'''</script><script>
const m=JSON.parse(document.getElementById('manifest').textContent);
const box=document.getElementById('message'),status=document.getElementById('status');
document.getElementById('expiry').textContent='Proposta válida até '+new Date(m.expires_at).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo'})+' (Brasília). Após isso, solicite nova revisão no chat.';
const expired=()=>Date.now()>=Date.parse(m.expires_at);
document.querySelectorAll('input').forEach(el=>el.addEventListener('change',()=>{box.value='';status.textContent='Seleção alterada. Prepare novamente a mensagem.';}));
document.getElementById('compose').onclick=()=>{
 box.value='';const picked=[...document.querySelectorAll('.pick:checked')].map(x=>m.items[Number(x.value)]);
 if(expired()){status.textContent='Proposta vencida. Solicite um lote atualizado no chat.';return;}
 if(!picked.length||!document.getElementById('reviewed').checked){status.textContent='Selecione vídeos e confirme que fez a revisão.';return;}
 box.value='Revisei os MP4s e roteiros selecionados, incluindo cenas, áudio, créditos e alegações. Autorizo o envio pelo Buffer somente dos itens abaixo, nos horários propostos em Brasília, após revalidar os hashes, a fila e todos os controles existentes. Não autorizo outros vídeos.\nManifesto: '+m.manifest_sha256+'\n'+picked.map(p=>p.id+' | MP4 SHA-256: '+p.sha256+' | roteiro SHA-256: '+p.script_hash+' | horário: '+p.proposed_scheduled_at).join('\n');
 status.textContent='Mensagem preparada, não enviada. Copie e envie no chat para registrar sua autorização explícita.';
};
document.getElementById('copy').onclick=async()=>{if(expired()){box.value='';status.textContent='Proposta vencida. Solicite atualização no chat.';return;}if(!box.value)return;try{await navigator.clipboard.writeText(box.value);status.textContent='Copiado. Envie no chat; nada foi aprovado ou publicado por esta página.';}catch(e){box.select();status.textContent='Selecione e copie o texto manualmente, depois envie no chat.';}};
</script></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    paths = [args.root/'automation'/name for name in ('queue.json', 'state.json')]
    before = [p.read_bytes() for p in paths]
    archive_path = args.root/'automation/visual_history.json'
    audit_path = args.root/'automation/QUEUE-AUDIT-4.4.json'
    archived = json.loads(archive_path.read_text()) if archive_path.exists() else None
    audit = json.loads(audit_path.read_text()) if audit_path.exists() else None
    result = build_preview(*[json.loads(raw) for raw in before], archived=archived, audit=audit)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # Exclusive writes: never replace operational files or earlier review evidence.
    for name, content in [('review44.json', json.dumps(result, indent=2, ensure_ascii=False)+'\n'),
                          ('review44.html', render_html(result))]:
        with (args.output_dir/name).open('x', encoding='utf-8') as out:
            out.write(content)
    if before != [p.read_bytes() for p in paths]:
        raise RuntimeError('STATE_CHANGED_DURING_EXPORT_REFRESH_REQUIRED')
    print(json.dumps(dict(items=result['pending_count'], selectable=result['selectable_count'],
                          manifest_sha256=result['manifest_sha256'], approved=False, submitted=False)))


if __name__ == '__main__':
    main()
