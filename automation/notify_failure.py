"""Maintain one actionable GitHub issue for workflow failures; no secret/log payloads."""
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
    body=('Uma execucao da automacao terminou com falha.\n\n'
          'Execucao: https://github.com/'+REPO+'/actions/runs/'+run_id+'\n\n'
          'Leia o resumo e a etapa com falha. Publicacao publica nao deve ser inferida de testes aprovados.\n\n'
          'Verificar: conexao/secret Buffer, revisao editorial, catalogo, upload de midia e persistencia. '
          'Nao reenviar posts com resultado incerto antes de reconciliar a plataforma.\n\n'
          'Este alerta nao inclui tokens, logs ou dados privados. A entrega de email depende das notificacoes do GitHub.')
    # Bound scans. If a repository is too busy, keep the Actions error rather than create duplicates.
    issues=call('/issues?state=open&per_page=100')
    matches=[i for i in issues if i.get('title')==TITLE and not i.get('pull_request')]
    if matches:
        issue=call('/issues/'+str(matches[0]['number']),'PATCH',{'body':body})
    elif len(issues)>=100:
        raise RuntimeError('Open issue listing truncated; refusing duplicate alert')
    else:
        issue=call('/issues','POST',{'title':TITLE,'body':body})
    print('FAILURE_ISSUE='+issue['html_url'])


if __name__=='__main__':main()
