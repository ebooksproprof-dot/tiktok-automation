"""Maintain one actionable GitHub issue for workflow failures; no secret/log payloads."""
import hashlib
from pathlib import Path
import json
import os
import urllib.request

REPO='ebooksproprof-dot/tiktok-automation'
TITLE='[Automation] CasaSemEsforco: operacao bloqueada'
BASE='https://api.github.com/repos/'+REPO


def call(path, method='GET', payload=None):
    req=urllib.request.Request(BASE+path,method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],
                 'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
    except Exception:
        raise RuntimeError('Could not update failure issue; inspect Actions. No credential/log payload was sent.') from None


def main():
    if os.getenv('GITHUB_ACTIONS')!='true':raise RuntimeError('Cloud runner only')
    run_id=os.environ['GITHUB_RUN_ID']
    if not run_id.isdigit():raise ValueError('Invalid run ID')
    health_path=Path(__file__).with_name('operational_health.json')
    health=json.loads(health_path.read_text()) if health_path.exists() else {}
    active=health.get('active_incidents', {})
    # Exclude timestamps/counters from the incident identity. Same causes do not
    # create comments or update notifications repeatedly on every cron.
    causes={code: item.get('details') for code,item in active.items()}
    fingerprint=hashlib.sha256(json.dumps(causes,sort_keys=True).encode()).hexdigest()[:20]
    marker='<!-- casasem-incident:'+fingerprint+' -->'
    body=('CasaSemEsforco: incidentes operacionais ativos.\n\n'+marker+'\n\n'
          'Execucao: https://github.com/'+REPO+'/actions/runs/'+run_id+'\n\n'
          'Causas registradas: '+', '.join(sorted(active) or ['ETAPA_FALHOU_CONSULTAR_ACTIONS'])+'\n\n'
          'Consulte automation/operational_health.json e os codigos nas etapas. '
          'Nao reenviar pedidos de resultado desconhecido. Agendamento nao confirma publicacao.')
    # Bound scans. If a repository is too busy, keep the Actions error rather than create duplicates.
    issues=call('/issues?state=open&per_page=100')
    matches=[i for i in issues if i.get('title')==TITLE and not i.get('pull_request')]
    if matches and marker in matches[0].get('body', ''):
        print('INCIDENT_ALREADY_REPORTED')
        return
    if matches:
        issue=call('/issues/'+str(matches[0]['number']),'PATCH',{'body':body})
    elif len(issues)>=100:
        raise RuntimeError('Open issue listing truncated; refusing duplicate alert')
    else:
        issue=call('/issues','POST',{'title':TITLE,'body':body})
    print('FAILURE_ISSUE='+issue['html_url'])


if __name__=='__main__':main()
