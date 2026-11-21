"""Persist actionable, deduplicated incidents and separate production states."""
import datetime as dt
import json
from pathlib import Path
from collections import Counter
from autonomous_production import stock_status
from editorial_policy import reason, date

ROOT = Path(__file__).resolve().parent


def inspect(queue, state, producer, wan, now):
    stock = stock_status(queue, state, now)
    issues = {}
    def add(code, details): issues[code] = {'code': code, 'details': details}
    if stock['refill_needed']: add('STOCK_BELOW_TARGET', {k:stock[k] for k in ('ready','refill_needed','held_uncertain')})
    repeated = []
    previous = {'posts': []}
    for p in sorted(queue.get('posts', []), key=lambda p: date(p) or now):
        why = reason(p, previous, {'posts': {}}, now=date(p) or now)
        if why: repeated.append({'id': p['id'], 'reason': why})
        previous['posts'].append(p)
    future_repeated = [p for p in repeated if any(q['id']==p['id'] and date(q) and date(q)>now and (q.get('approved') is True or state.get('posts', {}).get(q['id'], {}).get('status') in ('SCHEDULED','SENDING')) for q in queue['posts'])]
    if future_repeated: add('SIMILAR_FUTURE_CONTENT', future_repeated)
    from editorial_topics import ideas
    available_ideas = len(ideas(queue, state))
    if available_ideas < 4: add('EDITORIAL_CATALOG_LOW', {'eligible_tips':available_ideas, 'not_approved_videos':True})
    failures = Counter(c.get('error') for c in producer.get('candidates', {}).values() if c.get('error'))
    if failures: add('PRODUCTION_SOURCE_HOLDS', dict(failures))
    if producer.get('last_run', {}).get('status') == 'NO_VALID_OUTPUT':
        add('NO_APPROVED_PRODUCTION_OUTPUT', producer['last_run'])
    if wan.get('last_wait', {}).get('not_before'):
        until = dt.datetime.fromisoformat(wan['last_wait']['not_before'])
        if until > now: add('WAN_FREE_QUOTA_WAIT', {'not_before':until.isoformat()})
    unknown = [k for k,v in wan.get('requests', {}).items() if v.get('status') in ('UNKNOWN_NO_RETRY','INTENT_RECORDED_NO_RETRY')]
    if unknown: add('WAN_REQUEST_RESULT_UNKNOWN', {'count':len(unknown)})
    if any('LICENSE' in str(k) or 'RIGHTS' in str(k) for k in failures): add('SOURCE_LICENSE_HOLD', {'review_required':True})
    bad = [k for k,e in state.get('posts', {}).items() if e.get('status') in
           ('FAILED','PUBLICATION_OVERDUE','SUBMISSION_UNKNOWN','AWAITING_PUBLIC_EVIDENCE','BLOCKED_SCHEDULE_MISMATCH')]
    if bad: add('PUBLICATION_RECONCILIATION_REQUIRED', {'ids':bad})
    from zoneinfo import ZoneInfo
    local = now.astimezone(ZoneInfo('America/Sao_Paulo'))
    missing = []
    for day in range(2):
        for hour in (10,18):
            slot=(local-dt.timedelta(days=day)).replace(hour=hour,minute=0,second=0,microsecond=0)
            if slot > local-dt.timedelta(hours=2): continue
            entries=[e for e in state.get('posts', {}).values() if date(e) and date(e)==slot]
            if not any(e.get('status')=='PUBLISH_COMPLETE' and e.get('publicly_verified') is True for e in entries): missing.append(slot.isoformat())
    if missing: add('EXPECTED_PUBLICATION_NOT_VERIFIED', {'slots':missing})
    lifecycle = Counter()
    for c in wan.get('clips', []):
        review=wan.get('source_reviews', {}).get(c['sha256'], {})
        lifecycle['scenes_approved' if review.get('accepted') else 'scenes_generated']+=1
    lifecycle['scenes_preserved_unused']=len([c for c in wan.get('scene_bank', []) if not c.get('consumed_by')])
    lifecycle['scenes_rejected']=len(wan.get('rejected_clips', []))
    for p in queue.get('posts', []):
        entry=state.get('posts', {}).get(p['id'], {})
        if entry.get('status')=='PUBLISH_COMPLETE':
            lifecycle['published_verified' if entry.get('publicly_verified') else 'sent_unverified']+=1
        elif entry.get('status') in ('SCHEDULED','SENDING'): lifecycle['scheduled' if entry['status']=='SCHEDULED' else 'sending']+=1
        elif p.get('approved') is False: lifecycle['videos_rejected']+=1
        elif p.get('quality', {}).get('technical_pass'): lifecycle['videos_approved' if p.get('approved') else 'videos_assembled']+=1
    return {'stock':stock, 'lifecycle':dict(lifecycle), 'active_incidents':issues,
            'historical_similar_scripts':len(repeated), 'public_confirmation_is_separate':True}


def reconcile(old, snapshot, now):
    incidents=old.get('incidents', {})
    for code,entry in snapshot['active_incidents'].items():
        incident=incidents.setdefault(code, {'first_seen':now.isoformat(), 'occurrences':0})
        incident.update(entry, active=True, last_seen=now.isoformat(), occurrences=incident['occurrences']+1)
    for code,entry in incidents.items():
        if code not in snapshot['active_incidents'] and entry.get('active'):
            entry.update(active=False,resolved_at=now.isoformat())
    return {'version':12,'at':now.isoformat(),**snapshot,'incidents':incidents}


def main():
    read=lambda name: json.loads((ROOT/name).read_text())
    path=ROOT/'operational_health.json'
    old=json.loads(path.read_text()) if path.exists() else {}
    result=reconcile(old,inspect(read('queue.json'),read('state.json'),read('production_state.json'),
                      read('experimental81/wan104_inventory.json'),dt.datetime.now(dt.timezone.utc)),dt.datetime.now(dt.timezone.utc))
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'stock':result['stock'],'active_incidents':list(result['active_incidents']),'lifecycle':result['lifecycle']}))

if __name__=='__main__': main()
