# Auditoria CasaSemEsforço 3.5 — 20/10/2026

Base: c342bbd. Correção inicial enviada: 58c2a09edda4f36c6f82781ab32f1e5af18bb713.
Revisão independente em agente separado, sem tráfego Buffer: 11 regressões novas,
173 testes aprovados na primeira revisão; 175 após headers sem Policy e alerta de fila inválida.
Teste unitário não comprova envio real. Execução cloud39475156076 concluiu com174 testes
e envio real:4 chamadas,1 aceito e SCHEDULED,ID6ad7b316adf3e386a760ccfb,21/10 às10h.
Zero novas publicações concluídas nesta missão. Headers reais100/250/3000 confirmados;
política90/90/1800 mantida. Evidência JSON acompanha este relatório.

## Diagnóstico e política

Bloqueio confirmado no job118804009495/run39473684713: RuntimeError local antes da
rede. A condição diária era daily+required>60, limite próprio; não era HTTP429.
Até esse checkpoint havia108 registros30d,60 nas24h do último bloqueio. Nenhum apagado.
Cada execução antiga consultava canal(1); reconciliava todos os pendentes mesmo futuros(1);
com candidato consultava capacidade(1), criava(1 por vídeo) e lia novamente(1 por vídeo).
Push de testes disparava o runner com secrets reais, somando consultas desnecessárias.

Documentação oficial consultada20/10:
- https://buffer.com/api : Free100/15min,100/24h,3000/30d.
- https://developers.buffer.com/guides/api-limits.html : Free100/15min,250/24h,3000/30d.
Divergência preservada, não resolvida por suposição. Política interna90/15min,90/24h,
1800/30d,8/run fica abaixo do menor valor. Headers podem restringir mais; não aumentam
limites locais. Limite de10 posts pendentes é separado das chamadas API.

## Resultados da revisão

| Item | Resultado |
|---|---|
| Consumo API | No-op0; futuro SCHEDULED sem consulta; reconciliação em lote1 sem canal; envio isolado4, com readback |
| Credenciais | Somente secret existente; nenhum login/configuração; corpos de erros/headers brutos não registrados |
| Integração | Perfil exato .casasemesforo, canal6ad14dc2778b240e2f1f7c2f; canal validado a cada novo envio |
| Erros |429/Retry-After segundos/data;401/403 cooldown6h; falhas transitórias backoff60s exponencial até1h |
| Persistência | Uso gravado antes HTTP; cooldown/headers após resposta; workflow salva estado mesmo em falha |
| Idempotência | Intent durável antes create; ID durável antes readback; SHA/ID/slot bloqueiam reenvio |
| Agendamento |10h/18h Fortaleza; cron09:07/17:07 prepara,10:17/11:17/18:17/19:17 verifica; atrasos GitHub possíveis |
| Publicação | Somente sent+automatic+sentAt+permalink de conta exata confirma; SCHEDULED não confirma |
| Logs | Mensagens fixas, sem corpo/token; quota preserva apenas números/política/reset, exclui pk |
| Recuperação | Próximo cron respeita next_allowed_at; consulta sem mutation quando ID conhecido; UNKNOWN sem ID exige reconciliação |
| Concorrência | Grupo casasemesforco-state e cancel-in-progress:false preservados; checkpoint remoto antes mutação |
| Custos | Nenhum serviço pago contratado; limites de assets, chamadas e render existentes preservados |
| Plano gratuito | API separada de capacidade10 posts; queries só quando necessárias; não garante cota livre se outros clientes consumirem |
| Outros workflows | Pixabay/Piper/FFmpeg/render/staging não alterados; gatilho tests-only removido, cron/workflow_run mantidos |

## Economia verificável por cenário

Comparação do código com regressões; não é uma medição de um mês em produção:
- Execução apenas com post futuro:2→0 chamadas (economia2).
- Reconciliação de post vencido sem novo envio:2→1 (economia1).
- Novo vídeo com outro post futuro:5→4 (economia1).
- Commit apenas de testes: runner deixa de disparar (antes1–2 leituras típicas).
- --check reserva4 chamadas adicionais para envio e consome somente1; pode adiar diagnóstico.

## Limitações mantidas

Uma aceitação não demonstra operação permanente. Terceiro MP4 ainda depende de staging;
conteúdo novo continua sujeito a aprovação editorial específica, sem aprovação automática.
60 vídeos/mês não comprovados. UNKNOWN sem ID nunca é reenviado automaticamente, mesmo
quando cota volta; exige reconciliação humana/provedor. GitHub concurrency pode substituir
jobs pendentes, cron recupera. Falta comprovar comportamento multi-dia após esta correção.

## Segunda regressão e execução idempotente

175 testes repetidos localmente e pelo auditor independente. Workflow39475534489
confirmou175 testes cloud e no-op real:0 chamadas,0 envios, estado sem mudanças.
Histórico permaneceu112 registros30d, último18:29:44UTC. Economia demonstrada
nesse cenário:2 chamadas redundantes evitadas contra o fluxo antigo. Sem novos
permalinks, sem extrapolar prova de agendamento para publicação concluída.
