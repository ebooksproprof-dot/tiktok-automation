# Auditoria independente 4.4 — recuperação

Base recuperada: `603332f`. Revisor separado dos implementadores. Revisão inicial somente leitura, sem aprovações, chamadas Buffer, agendamentos ou publicação. Baseline de 230 testes conhecido e não repetido antes de alterações.

## Seis vídeos pendentes

Verificação executada com `visual_library.require_evidence` contra fila, estado e `visual_history.json`, excluindo somente o próprio item. Conferência adicional de URLs com `preflight`.

| Item | Resultado de histórico e direitos registrados | Bloqueios restantes |
|---|---|---|
| `casasem-2026-10-17-1` / sem-misturas | `VISUAL_REVIEW_REQUIRED`; URLs já presentes no histórico | Evidência visual legada insuficiente e cenas reutilizadas; horário expirado |
| `casasem-2026-10-18-1` / piso-rota-saida | `VISUAL_REVIEW_REQUIRED`; URL já presente no histórico | Evidência visual legada insuficiente e cena reutilizada; sem horário |
| `casasem-2026-10-18-2` / torneira-final-seco | `VISUAL_REVIEW_REQUIRED`; URL já presente no histórico | Evidência visual legada insuficiente e cena reutilizada; sem horário |
| `casasem-2026-10-22-2` / pontos-de-toque | Gate visual aprovado; três fontes Pexels registradas | Revisão humana de arquivo/roteiro, consentimento, rota e novo horário |
| `casasem-2026-10-23-1` / gaveta-uma-categoria | Gate visual aprovado; fonte Pexels registrada | Revisão humana de arquivo/roteiro, consentimento, rota e horário apropriado |
| `casasem-2026-10-23-2` / secador-visivel | Gate visual aprovado; fonte Pixabay e crédito obrigatório presente na legenda | Revisão humana de arquivo/roteiro, consentimento, rota e horário apropriado |

Todos os seis têm `approved=false`, `quality.editorial_approved=false`, ausência de `consented_at` e ausência de rota. O resultado positivo do gate não supre esses requisitos. Os três itens legados não podem ser liberados apenas atualizando hashes, aprovando visualmente ou removendo verificações. Os itens Pexels incorporados ao catálogo antigo têm lista vazia de créditos obrigatórios; isso descreve a política registrada, não uma nova verificação jurídica externa.

O estado contém 12 publicações com `publicly_verified=true`, última em 22/10 às 10h; o registro sandbox adicional não conta como publicação real. Nenhum `SCHEDULED` ou `UNKNOWN` no estado recuperado. Não houve nova inspeção das páginas públicas TikTok nesta etapa. Datas/horários expirados ou ausentes devem ser propostos novamente de maneira explícita antes de eventual aprovação; não reutilizar consentimentos antigos ou inventar consentimento.

A avaliação perceptiva dos MP4s está sendo feita separadamente pela coordenação. Este relatório inicial não certifica naturalidade, correspondência exata das cenas ou aprovação editorial dos três itens tecnicamente elegíveis. Revisões dos novos componentes e resultados de regressão serão acrescentados após as alterações.

## Revisão das alterações 4.4

Regressão independente após alterações: `python -m unittest discover -s automation/tests` — **263 testes aprovados**, 0,327 s. Nenhum novo bloqueador de segurança identificado na revisão. Não foram aplicadas aprovações ou enviadas publicações.

`review_batch44.py` cria propostas, sem escrever fila/estado ou chamar publicação. Vincula arquivos e roteiros por hashes, snapshots da fila/estado/histórico arquivado e prazo de validade; exclui enviados e bloqueia fontes repetidas, rejeitados, metadados insuficientes e URLs externas. Propõe apenas 10h/18h, com antecedência mínima de 30 minutos, sem colisão e em sete dias. A página não possui submissão de publicação: seleção apenas prepara mensagem explícita de consentimento para o chat. Conteúdo textual e atributos são escapados. Horários exibidos não são agendamentos reais.

`approve_preview44.py` retorna somente cópia em memória. Exige autorização explícita (`approved is True`), hash do manifesto autorizado, IDs escolhidos, revisão textual e instante de consentimento com timezone dentro da janela. Rejeita snapshot alterado, prazo vencido, conteúdo/horário adulterado, item inelegível ou já submetido. Recalcula a proposta original e delega a aprovação à função legada, preservando créditos, duplicações, no máximo dois slots/dia e demais gates. A função não pode provar por si mesma que um humano enviou a autorização: quem a chamar deve fornecer o consentimento real, nunca preencher esses argumentos por inferência. Não há aplicação CLI ou persistência nova neste módulo.

`planned_reserve_slots` limita o horizonte a 1–7 dias; workflow usa três. O renderer conserva máximo de duas renderizações por execução, IDs/datas explícitos, proteção dos itens existentes e fila sem aprovação automática. Uma reserva planejada não é reserva aprovada. Fonte insuficiente ainda falha visivelmente e resultados anteriores são persistidos pelo workflow; não foram adicionados loops ou resets.

Aquisição amplia o banco para 24 consultas, escolhendo quatro estáveis por dia UTC; repetições no mesmo dia não percorrem consultas adicionais. Mantém limites de downloads, caches, proveniência e histórico; Pexels passa a ter também teto explícito de quatro requisições na instância. Novos templates são finitos e rascunhos continuam sem aprovação. Tags servem para triagem, não comprovam correspondência visual. `approved_reserve_days=null` evita apresentar rascunhos como capacidade aprovada; a renovação ilimitada não está demonstrada.

Patch de avatar revisado: inventário AST exige métodos/defaults conhecidos; somente os defaults internos de dispositivo/tipo passam a ser derivados dos parâmetros UNet quando ausentes, preservando valores explicitamente fornecidos. Continua experimento isolado, não integração de produção. Resultado cloud e qualidade ainda dependem de evidência de saída; correção de erro anterior não equivale a avatar produzido.

Coordenação relatou inspeção e hashes dos seis MP4s (`QUEUE-AUDIT-4.4.json`); os três itens legados seguem bloqueados pelos gates apesar da validade técnica. Também relatou nova criação diária com um MP4 futuro seguida de esgotamento da única fonte curta restante. Esses relatos devem ser associados aos resultados cloud finais na entrega, sem converter renderização ou teste aprovado em publicação comprovada.

## Resultado do experimento avatar

API GitHub consultada independentemente: run `40015884986`, job `120627699722`, instalação concluída, experimento falhou e artifact preservado. Leitura independente de `tmp/avatar44/report.json` e `execution.log`: erro `TimeoutExpired` do subprocesso após 180 segundos; tempo total registrado 214,131 s, pico RSS de filho 14.108.036 KiB. Os erros CUDA anteriores foram superados neste caminho. O log chegou a características de áudio, latentes da imagem e máscara facial e à barra de difusão `0/4`, sem MP4. `avatar_video_produced=false`, aprovação e integração de produção falsas.

Conclusão restrita: configuração CPU não completou a prova de três segundos dentro do orçamento desta tentativa. Isso não estabelece impossibilidade fundamental de CPU, nem permite certificar naturalidade ou lip-sync. Encerrar novas tentativas neste orçamento e preservar a alternativa funcional sem avatar; qualquer aumento de recursos/tempo requer avaliação própria, sem serviço pago introduzido implicitamente.
