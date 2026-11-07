"""Replenish up to four reviewed videos through the existing renderer/queue.

Owner authorization: mission 10.2. Acceptance is automatic and recorded as such;
unknown rights, failed visual review, repetition and uncertain publishing fail closed.
The existing AI collector remains the generative route. This is its free-stock
fallback, never a second publishing system. No calls to Buffer or paid inference.
"""
import argparse
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import time
from zoneinfo import ZoneInfo

import render_daily as render
from content_catalog import fingerprint as script_sha, novel_scripts
from daily_coverage import stamp, confirmed_live_tests
from media_acquisition import download_and_measure, read_json, save_json
from media_providers import crop_capable, native_full_frame, plain
from media_rights import caption_with_credits
from semantic_review import Reviewer, nominate, assess, motion, REVISION
from source_license import verify as license_verify, CACHE as RIGHTS_CACHE, SourceLicenseBudgetExceeded
import visual_library as visuals

ROOT = Path(__file__).resolve().parent
BRT = ZoneInfo('America/Sao_Paulo')
TARGET = 4
MAX_CANDIDATES = 6
STATE_PATH = ROOT/'production_state.json'


class PrimaryVoiceFailure(RuntimeError):
    pass


class CheckedVoice:
    def __init__(self, engine):
        self.engine, self.name = engine, engine.name

    def speak(self, text, path):
        try:
            return self.engine.speak(text, path)
        except (OSError, ImportError, RuntimeError) as exc:
            raise PrimaryVoiceFailure(type(exc).__name__) from None


def render_with_voice_fallback(idea, post_id):
    from narration import load_engine
    reason = None
    try:
        voice = CheckedVoice(load_engine(render.ASSETS, 'kokoro-female'))
    except (OSError, ImportError, RuntimeError) as exc:
        reason = 'PRIMARY_LOAD_'+type(exc).__name__
        voice = load_engine(render.ASSETS, 'piper')
    try:
        output, quality = render.render(idea, voice, post_id)
    except PrimaryVoiceFailure as exc:
        # Restart the entire narration, never mix sample rates/voices midway.
        reason = 'PRIMARY_SYNTHESIS_'+str(exc)
        output, quality = render.render(idea, load_engine(render.ASSETS, 'piper'), post_id)
    quality.update(requested_voice='pf_dora', voice_fallback_reason=reason)
    return output, quality

# Reviewed factual sentences. New combinations are checked against the complete
# script history; a new hook alone never makes a repeated script acceptable.
BANK = {
 'iron': ('Vai passar roupa?', [
    'Confira a etiqueta antes de escolher a temperatura.',
    'Use um apoio firme e mantenha o fio fora da passagem.',
    'Trabalhe uma parte por vez, sem deixar o ferro parado.',
    'Guarde apenas peças secas, depois de esfriarem completamente.',
    'Separe os tecidos que pedem temperaturas diferentes.',
    'Desligue o aparelho ao terminar e siga o manual.',
    'Deixe as peças prontas separadas das que ainda precisam de cuidado.',
    'Reserve espaço para movimentar o tecido sem puxar o fio.']),
 'hangers': ('Seu armário está apertado?', [
    'Separe as peças por tipo antes de organizar os cabides.',
    'Deixe espaço para retirar uma roupa sem derrubar as outras.',
    'Escolha cabides adequados ao peso e ao formato das peças.',
    'Guarde somente roupas limpas e completamente secas.',
    'Deixe as peças de uso frequente fáceis de alcançar.',
    'Evite esconder muitas roupas no mesmo cabide.',
    'Confira se as portas fecham sem prender os tecidos.',
    'Revise um pequeno trecho do armário por vez.']),
 'folding': ('Roupas esperando para guardar?', [
    'Separe uma pequena categoria para começar.',
    'Confira se cada peça está completamente seca.',
    'Ajuste a dobra ao espaço disponível na gaveta.',
    'Deixe as peças de uso frequente visíveis.',
    'Não comprima a pilha além da altura do móvel.',
    'Guarde a primeira pilha antes de começar outra.',
    'Separe as roupas que precisam de reparo.',
    'Use as orientações da etiqueta para conservar cada tecido.']),
 'dishes': ('A louça acumulou?', [
    'Retire os restos dos pratos antes de começar a lavagem.',
    'Separe um pequeno grupo de utensílios por vez.',
    'Use o produto e a esponja adequados ao material.',
    'Deixe espaço no escorredor sem formar uma pilha instável.',
    'Guarde as peças que já estão completamente secas.',
    'Confira as orientações de limpeza dos utensílios.',
    'Mantenha os objetos cortantes separados e seguros.',
    'Ao terminar, retire os resíduos do coletor do ralo.']),
 'sweeping': ('O piso precisa de atenção?', [
    'Retire os objetos soltos antes de começar.',
    'Escolha uma vassoura adequada ao acabamento.',
    'Reúna os resíduos em uma área pequena.',
    'Mantenha uma passagem livre durante a tarefa.',
    'Aproxime a pá e recolha a sujeira aos poucos.',
    'Confira as orientações de cuidado do seu piso.',
    'Guarde o material sem bloquear a circulação.',
    'Termine uma parte do ambiente antes de avançar.']),
 'wiping': ('Seu pano está pronto?', [
    'Confira se o pano está limpo e sem partículas.',
    'Use apenas produtos compatíveis com a superfície.',
    'Siga a diluição e o modo de uso do rótulo.',
    'Troque a parte do pano quando ela ficar suja.',
    'Separe os materiais usados em cada ambiente.',
    'Não improvise misturas de produtos de limpeza.',
    'Seque a superfície quando a orientação indicar.',
    'Deixe o pano secar antes de guardar.']),
 'books': ('Sua estante está confusa?', [
    'Escolha uma pequena prateleira para começar.',
    'Agrupe os livros por uma regra simples.',
    'Mantenha as lombadas visíveis para encontrar os títulos.',
    'Confira a estabilidade das peças na prateleira.',
    'Deixe as leituras atuais fáceis de alcançar.',
    'Evite comprimir os livros contra o móvel.',
    'Devolva cada título ao grupo correspondente depois do uso.',
    'Separe os volumes de uma coleção antes de organizar.']),
 'handwashing': ('Vai lavar as mãos?', [
    'Use um produto indicado para a higiene das mãos.',
    'Siga o modo de uso e a quantidade indicados no rótulo.',
    'Espalhe o sabonete pelas mãos sem deixar áreas esquecidas.',
    'Enxágue e use material limpo para a secagem.',
    'Confira se há sabonete disponível antes de começar.',
    'Ao terminar, feche a torneira sem deixar água correndo.',
    'Mantenha a área da pia livre para utilizar com segurança.',
    'Siga as orientações dos órgãos de saúde para a higiene.']),
 'laundry': ('Vai colocar roupa para lavar?', [
    'Confira a etiqueta das peças antes de escolher o ciclo.',
    'Siga o manual da sua máquina e a capacidade indicada.',
    'Use o produto e a quantidade recomendados no rótulo.',
    'Revise os bolsos antes de colocar as peças no tambor.',
    'Separe os tecidos conforme as orientações de lavagem.',
    'Mantenha os produtos na embalagem original e longe de crianças.',
    'Retire as roupas ao terminar e organize a secagem.',
    'Confira as instruções de limpeza do filtro no manual.']),
 'surfaces': ('Vai limpar esta superfície?', [
    'Confira qual material é compatível com o acabamento.',
    'Siga a diluição e o modo de uso indicados no rótulo.',
    'Retire os objetos soltos para deixar a área livre.',
    'Cuide de uma pequena parte antes de avançar.',
    'Não improvise misturas de produtos de limpeza.',
    'Evite espalhar os resíduos para áreas já limpas.',
    'Mantenha os produtos longe de crianças e animais.',
    'Ao terminar, guarde os materiais em local adequado.']),
 'drying': ('Roupa pronta para secar?', [
    'Confira a etiqueta antes de escolher a secagem.',
    'Deixe espaço entre as peças para o ar circular.',
    'Use um apoio adequado ao peso das roupas.',
    'Prenda as peças sem deformar o tecido.',
    'Consulte a etiqueta sobre exposição ao sol.',
    'Guarde as peças somente quando estiverem totalmente secas.',
    'Evite empilhar roupas ainda úmidas.',
    'Separe as peças que exigem cuidados especiais.']),
 'drain': ('O que vai parar no ralo?', [
    'Retire os restos de comida antes de lavar a louça.',
    'Use um coletor adequado ao ralo da sua pia.',
    'Não despeje óleo de cozinha no escoamento.',
    'Mantenha objetos pequenos longe da abertura.',
    'Descarte os resíduos recolhidos no local adequado.',
    'Siga as orientações do fabricante para limpar as peças.',
    'Não improvise misturas de produtos para desentupir.',
    'Confira se o coletor está bem encaixado depois da limpeza.']),
 'products': ('Vai usar um produto de limpeza?', [
    'Leia o rótulo antes de abrir a embalagem.',
    'Confira se o produto é indicado para a superfície.',
    'Siga a diluição e o modo de uso recomendados.',
    'Não improvise misturas de produtos de limpeza.',
    'Mantenha o produto na embalagem original.',
    'Guarde os produtos longe de crianças e animais.',
    'Siga as orientações de ventilação indicadas no rótulo.',
    'Feche a embalagem corretamente depois de usar.']),
}


def ready(queue, state, now):
    return [p for p in queue['posts'] if p.get('approved') is True
            and (p['id'] not in state['posts'] or state['posts'][p['id']].get('status') in ('SCHEDULED', 'SENDING'))
            and p.get('consented_at')
            and p.get('quality', {}).get('technical_pass') is True
            and p.get('scheduled_at') and (stamp(p['scheduled_at']) > now
                 or state['posts'].get(p['id'], {}).get('status') in ('SCHEDULED', 'SENDING'))]


def reconcile_outputs(ledger, state):
    for post_id, output in ledger.get('outputs', {}).items():
        remote = state.get('posts', {}).get(post_id, {})
        if remote and remote.get('sha256') == output.get('sha256'):
            output.update(status=remote.get('status', 'UNKNOWN'),
                          provider_id=remote.get('buffer_post_id'),
                          publicly_verified=remote.get('publicly_verified', False),
                          public_urls=remote.get('public_urls', []))
    return ledger


def held_reservations(queue, state):
    ids = {p['id'] for p in queue.get('posts', [])}
    return [key for key, entry in state.get('posts', {}).items()
            if key in ids and entry.get('provider') == 'buffer'
            and entry.get('status') not in ('PUBLISH_COMPLETE', 'FAILED', 'CANCELLED_EDITORIAL', 'SCHEDULED', 'SENDING')]


def stock_status(queue, state, now):
    available = len(ready(queue, state, now))
    held = held_reservations(queue, state)
    return {'ready': available, 'held_uncertain': len(held), 'target_max': TARGET,
            'low_stock': available < 2, 'refill_needed': max(0, TARGET-available-len(held)),
            'held_ids': held, 'publication_confirmation_is_separate': True}


def choose_slot(queue, state, now, soon=False):
    entries = {p['id']: p for p in queue['posts']}
    entries.update({key: dict(value, id=key) for key, value in state['posts'].items()})
    reservations = {key: stamp(p['scheduled_at']).astimezone(BRT)
                    for key, p in entries.items() if p.get('scheduled_at')}
    local = now.astimezone(BRT)
    for day in range(8):
        for hour in (10, 18):
            when = (local+dt.timedelta(days=day)).replace(hour=hour, minute=0, second=0, microsecond=0)
            if soon and day == 0:
                when = (local+dt.timedelta(minutes=20)).replace(microsecond=0)
            completed_tests = confirmed_live_tests(queue, state, when.date())
            if (when < local+dt.timedelta(minutes=15) or when in reservations.values()
                    or sum(x.date() == when.date() for key, x in reservations.items() if key not in completed_tests) >= 2):
                continue
            occupied = {p.get('id') for p in queue['posts']} | set(state['posts'])
            numbers = (1, 2, 3) if completed_tests else (1, 2)
            post_id = next((f'casasem-{when.date()}-{n}' for n in numbers
                            if f'casasem-{when.date()}-{n}' not in occupied), None)
            if post_id:
                return post_id, when
    raise ValueError('NO_UNRESERVED_SLOT')


def candidate_records(inbox, cache):
    records = {r['url']: r.copy() for r in inbox['items'] if r.get('provider') == 'pixabay'}
    # Reuse official API discoveries rather than spending new calls for the same
    # files. Current item-page license is still checked before each acceptance.
    for key, entry in cache.items():
        if not key.startswith('pixabay:'):
            continue
        for hit in entry.get('data', {}).get('hits', []):
            files = [f for f in hit.get('videos', {}).values()
                     if (crop_capable(f.get('width', 0), f.get('height', 0))
                         or native_full_frame(f.get('width', 0), f.get('height', 0)))
                     and 0 < f.get('size', 0) <= 250*1024*1024
                     and str(f.get('url', '')).startswith('https://cdn.pixabay.com/')]
            if not files:
                continue
            f = min(files, key=lambda x: (not crop_capable(x['width'], x['height']), x['width']*x['height']))
            r = dict(provider='pixabay', provider_id=str(hit['id']), url=f['url'],
                     source_page=hit['pageURL'], author=plain(hit['user']),
                     license_url='https://pixabay.com/service/license-summary/',
                     selection_reason='Provider tags: '+plain(hit['tags']),
                     category='autonomous', query=key[8:], status='pending_visual_review',
                     frame_mode='reviewed_portrait' if crop_capable(f['width'], f['height']) else 'preserve_full')
            records.setdefault(r['url'], r)
    def priority(r):
        tags = r.get('selection_reason', '').lower()
        return (0 if any(w in tags for w in ('ironing', 'closet', 'sweeping', 'dish,')) else 1,
                r['provider_id'])
    selected = {}
    for record in records.values():
        identity = record['provider_id']
        old = selected.get(identity)
        if old is None or (old.get('frame_mode') == 'preserve_full' and record.get('frame_mode') != 'preserve_full'):
            selected[identity] = record
    return sorted((r for r in selected.values() if nominate(r)), key=priority)


def scripts(pool, queue, state):
    family = pool[0]['visual_review']['family']
    tags = ' '.join(x['record']['selection_reason'] for x in pool).lower()
    descriptions = ' '.join(' '.join(x['visual_review']['captions']) for x in pool).lower()
    iron_seen = bool(re.search(r'\biron(?:ing)?\b', descriptions))
    key = ('iron' if 'ironing' in tags and iron_seen else 'hangers' if any(w in descriptions for w in ('hanger', 'closet', 'clothing rack'))
           else 'folding') if family == 'clothes' else family
    if family == 'laundry' and not re.search(r'\b(machine|washer|drum)\b', descriptions):
        key = 'drying'
    hook, sentences = BANK[key]
    seed = int(hashlib.sha256(''.join(x['record']['sha256'] for x in pool).encode()).hexdigest(), 16)
    rng = random.Random(seed)
    choices = []
    for _ in range(24):
        tips = rng.sample(sentences, 4)
        if key == 'iron' and any('closet' in x['record']['selection_reason'].lower() for x in pool):
            storage = next(s for s in sentences if s.startswith('Guarde'))
            tips = rng.sample([s for s in sentences if s != storage], 3)+[storage]
        if key == 'laundry' and 'clothesline' in tags:
            drying_tip = next(s for s in sentences if s.startswith('Retire as roupas'))
            tips = rng.sample([s for s in sentences if s != drying_tip], 3)+[drying_tip]
        # Ironing demonstrator first, storage footage last: keep storage advice
        # at the end instead of claiming that a hanger is an iron demonstration.
        tips.sort(key=lambda s: 'Guarde' in s or 'Retire as roupas' in s)
        lines = [hook, *tips, 'Salve este cuidado para a sua rotina.']
        concept = 'auto-'+key+'-'+script_sha(lines)[:12]
        choices.append((concept, [x['record']['id'] for x in pool], lines))
    return novel_scripts(choices, queue, state)


def repaired_context(prior, record):
    """Re-review only a demonstrated category error; never override other gates."""
    review = prior.get('visual_review', {})
    family = nominate(record)
    return (prior.get('error') == 'PORTRAIT_VISUAL_CONTEXT_REJECTED'
            and review.get('accepted') is False and family and family != review.get('family')
            and review.get('revision') == REVISION and review.get('decoder_pass') is True
            and review.get('freeze_intervals_over_1s') == 0
            and review.get('source_sha256') == prior.get('license', {}).get('source_sha256')
            and assess(family, review.get('captions', [])))


def run(stage=False, soon=False, limit=2):
    if stage and (os.getenv('GITHUB_ACTIONS') != 'true'
                  or os.getenv('GITHUB_REF_NAME') != 'main'
                  or os.getenv('GITHUB_WORKFLOW') != 'CasaSemEsforco Daily Video Creation'):
        raise ValueError('TRUSTED_MAIN_CLOUD_CONTEXT_REQUIRED')
    if not 1 <= limit <= 2:
        raise ValueError('PRODUCTION_LIMIT_ONE_OR_TWO')
    queue = read_json(ROOT/'queue.json', {})
    state = read_json(ROOT/'state.json', {})
    if not isinstance(queue.get('posts'), list) or not isinstance(state.get('posts'), dict):
        raise ValueError('EXISTING_QUEUE_AND_STATE_REQUIRED')
    ledger = read_json(STATE_PATH, {'version': 1, 'candidates': {}, 'outputs': {}})
    reconcile_outputs(ledger, state)
    now = dt.datetime.now(dt.timezone.utc)
    before = len(ready(queue, state, now))
    occupied = before+len(held_reservations(queue, state))
    if occupied >= TARGET:
        result = {'status': 'STOCK_TARGET_MET' if before >= TARGET else 'STOCK_RESERVED_UNCERTAIN',
                  'ready': before, 'held_uncertain': occupied-before, 'created': 0}
        if stage:
            ledger['last_run'] = result
            save_json(STATE_PATH, ledger)
        return result
    previous = visuals.history(queue, state)+[read_json(ROOT/'visual_history.json', {})]
    inbox = read_json(ROOT/'media_inbox.json', {'items': []})
    cache = read_json(ROOT/'media_search_cache.json', {})
    render.ASSETS.mkdir(parents=True, exist_ok=True)
    render.OUT.mkdir(parents=True, exist_ok=True)
    reviewer = None
    pools, outputs, examined = {}, [], 0
    for candidate in candidate_records(inbox, cache):
        if len(outputs) >= min(limit, TARGET-occupied) or examined >= MAX_CANDIDATES:
            break
        key = candidate['url']
        prior = ledger['candidates'].get(key, {})
        repair = repaired_context(prior, candidate)
        if prior.get('status') == 'QUEUED' or prior.get('status') == 'REJECTED' and not repair:
            continue
        known_rights = read_json(RIGHTS_CACHE, {'sources': {}})['sources']
        new_evidence = prior.get('error_type') == 'HTTPError' and (key in known_rights or bool(os.getenv('PIXABAY_API_KEY')))
        if prior.get('retry_after', 0) > time.time() and not new_evidence:
            continue
        try:
            phase = 'download'
            if not visuals.preflight([key], previous):
                continue
            examined += 1
            # Acquire and hash original bytes even when a former preview expired.
            measured = download_and_measure(candidate, render.ASSETS, previous)
            if candidate.get('sha256') and candidate['sha256'] != measured['sha256']:
                raise ValueError('PREVIOUS_SOURCE_BYTES_CHANGED')
            measured.update(id='auto-pixabay-'+measured['provider_id']+'-'+measured['sha256'][:12],
                            frame_mode='reviewed_portrait' if crop_capable(measured['width'], measured['height']) else 'preserve_full',
                            context='Illustrative real household footage, accepted by local CPU frame review.')
            phase = 'license'
            license_proof = license_verify(measured)
            entry = ledger['candidates'].setdefault(key, {})
            if repair:
                entry.setdefault('classification_history', []).append(dict(entry['visual_review']))
            errors = ('error', 'error_type', 'error_stage', 'http_status', 'retry_after')
            if entry.get('error'):
                entry.setdefault('hold_history', []).append({k: entry[k] for k in errors if k in entry})
            for field in errors:
                entry.pop(field, None)
            entry.update(status='LICENSE_VERIFIED_PENDING_VISUAL', source_sha256=measured['sha256'], license=license_proof)
            cached_review = prior.get('visual_review') or {}
            if not stage and not cached_review:
                # Only preview mode may reuse local proof files. Operational
                # acceptance caches come exclusively from durable main state.
                cached_review = read_json(render.ASSETS/('review-'+measured['provider_id'])/'review.json', {})
            if (cached_review.get('source_sha256') == measured['sha256']
                    and cached_review.get('frame_mode', 'reviewed_portrait') == measured['frame_mode']
                    and cached_review.get('family') == nominate(measured)
                    and cached_review.get('revision') == REVISION and cached_review.get('accepted') is True):
                review = cached_review
            else:
                if reviewer is None:
                    phase = 'semantic_model_load'
                    reviewer = Reviewer(os.getenv('SEMANTIC_MODEL_CACHE'))
                phase = 'semantic_review'
                review = reviewer.review(render.ASSETS/('pixabay-'+measured['provider_id']+'.mp4'),
                    measured, render.ASSETS/('review-'+measured['provider_id']))
            entry.update(status='ACCEPTED', source_sha256=measured['sha256'],
                         license=license_proof, visual_review=review)
            pool = pools.setdefault(review['family'], [])
            pool.append({'record': measured, 'visual_review': review, 'license': license_proof})
            capacity = sum(x['record']['duration']-.05 for x in pool)
            if capacity < 15:
                continue
            if review['family'] == 'clothes':
                pool.sort(key=lambda x: 'ironing' not in x['record']['selection_reason'].lower())
            elif review['family'] == 'laundry':
                pool.sort(key=lambda x: not re.search(r'\b(machine|washer|drum)\b', ' '.join(x['visual_review']['captions']).lower()))
            for x in pool:
                record = x['record']
                render.SOURCE[record['id']] = record['url']
                render.PROVENANCE[record['id']] = record
                src = render.ASSETS/('pixabay-'+record['provider_id']+'.mp4')
                dest = render.ASSETS/(record['id']+'.mp4')
                if not dest.exists():
                    shutil.copyfile(src, dest)
                if hashlib.sha256(dest.read_bytes()).hexdigest() != record['sha256']:
                    raise ValueError('RENDER_SOURCE_COPY_HASH_MISMATCH')
            if not scripts(pool, queue, state):
                raise ValueError('NO_NEW_SCRIPT_COMBINATION')
            failure = None
            phase = 'render'
            for idea in scripts(pool, queue, state)[:3]:
                post_id, when = choose_slot(queue, state, dt.datetime.now(dt.timezone.utc), soon and not outputs)
                try:
                    video, quality = render_with_voice_fallback(idea, post_id)
                    break
                except ValueError as exc:
                    if not any(t in str(exc) for t in ('Narration length', 'SOURCE_TOO_SHORT')):
                        raise
                    failure = exc
            else:
                raise failure or ValueError('NO_VALID_NARRATION_PLAN')
            motion(video)
            records = [x['record'] for x in pool]
            title, credits = caption_with_credits(' '.join(idea[2])+' #CasaSemEsforco #OrganizacaoDaCasa', records)
            quality.update(editorial_approved=True, required_public_credits=credits,
                automated_review=True, review_policy='mission102_cpu_semantics_motion_licensed_source',
                source_rights=[x['license'] for x in pool], semantic_reviews=[x['visual_review'] for x in pool],
                human_perceptual_review=False)
            post = dict(id=post_id, concept=idea[0], title=title, approved=True,
                consented_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                approval_scope='mission102_owner_authorized_automated_quality_and_license_checks',
                publication_provider='buffer', scheduled_at=when.isoformat(), quality=quality,
                video_url='', script_lines=idea[2], script_sha256=script_sha(idea[2]),
                media_storage='release', render_version=2, video_origin='licensed_stock_cpu_review',
                first_test_outside_recurring_slots=bool(soon and not outputs),
                publishing_status='READY_FOR_EXISTING_BUFFER_RUNNER')
            visuals.require_evidence(post, previous)
            if stage:
                phase = 'release_and_queue'
                from release_media import publish
                post['video_url'] = publish(video, post_id, quality)
                queue['posts'].append(post)
                save_json(ROOT/'queue.json', queue)
                for x in pool:
                    ledger['candidates'][x['record']['url']]['status'] = 'QUEUED'
                ledger['outputs'][post_id] = {'sha256': quality['sha256'], 'status': 'QUEUED',
                    'scheduled_at': when.isoformat(), 'source_urls': quality['source_urls']}
            outputs.append({'post_id': post_id, 'video': str(video), 'quality': quality,
                            'scheduled_at': when.isoformat(), 'video_url': post['video_url']})
            previous.append(quality)
            pools[review['family']] = []
        except Exception as exc:
            controlled = isinstance(exc, ValueError) and bool(re.fullmatch(r'[A-Z][A-Z0-9_]{2,100}', str(exc)))
            local_cap = isinstance(exc, SourceLicenseBudgetExceeded)
            code = str(exc) if controlled or local_cap else 'SOURCE_OR_RENDER_UNAVAILABLE'
            entry = ledger['candidates'].setdefault(key, {})
            review_path = render.ASSETS/('review-'+candidate['provider_id'])/'review.json'
            sampled = read_json(review_path, {}) if review_path.exists() else {}
            if sampled.get('source_sha256') and sampled['source_sha256'] == entry.get('source_sha256'):
                entry['visual_review'] = sampled
            entry.update({'status': 'REJECTED' if controlled else 'RETRYABLE',
                'error': code, 'error_type': type(exc).__name__,
                'error_stage': phase,
                'http_status': getattr(exc, 'code', None),
                'retry_after': time.time()+6*3600 if not controlled and not local_cap else 0})
            print('AUTONOMOUS_CANDIDATE_HELD='+candidate['provider_id']+'; REASON='+code)
        finally:
            if stage:
                save_json(STATE_PATH, ledger)
    result = {'status': 'QUEUED' if stage and outputs else 'RENDERED_PREVIEW' if outputs else 'NO_VALID_OUTPUT',
              'created': len(outputs), 'ready_before': before,
              'ready_after': len(ready(queue, state, dt.datetime.now(dt.timezone.utc))),
              'target': TARGET, 'outputs': outputs, 'source': 'licensed_stock_fallback',
              'new_generative_ai_calls': 0, 'paid_services_enabled': False,
              'generative_ai_status': 'Existing independent Wan collector retains commercial clearance gates'}
    if stage:
        ledger['last_run'] = {k: v for k, v in result.items() if k != 'outputs'}
        save_json(STATE_PATH, ledger)
    folder = Path('tmp/autonomous-proof')
    folder.mkdir(parents=True, exist_ok=True)
    save_json(folder/'result.json', result)
    return result


def exit_status(result):
    # Existing stock is not evidence that a required refill succeeded.
    return 0 if result.get('created', 0) or result['status'] == 'STOCK_TARGET_MET' else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', action='store_true')
    parser.add_argument('--soon', action='store_true')
    parser.add_argument('--limit', type=int, default=2)
    args = parser.parse_args()
    result = run(args.stage, args.soon, args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(exit_status(result))
