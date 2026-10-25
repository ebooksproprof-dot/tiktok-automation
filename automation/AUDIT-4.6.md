# Auditoria independente 4.6 — 25/10/2026

Revisão por agente separado dos implementadores. Sem aprovação, envio ou alteração de fila/estado pelo auditor. Único documento produzido nesta etapa pelo auditor: este relatório.

## Métricas de aquisição

Revisados os campos novos `download_attempts`, `skipped_known` e `skipped_cooldown` em `media_acquisition.py`. A separação dos dois motivos de skip conserva a decisão anterior: candidatos conhecidos ou sob cooldown não são baixados. Esses contadores descrevem ocorrências durante a passagem pelas consultas, não necessariamente IDs únicos. Nenhum reset de histórico, quota ou cooldown foi introduzido.

Mantêm-se os limites auditados na 4.5: duas tentativas de candidatos por consulta/provedor, quatro downloads totais, duas aquisições e interrupção do provedor diante de erro de autenticação, limite, servidor ou requisição. Os contadores adicionais não autorizam conteúdo nem alteram gates editoriais.

Regressão independente: `python -m unittest discover -s automation/tests` — **268 testes aprovados**, 0,296 s. As asserções novas conferem tentativas e skips por cooldown sem adicionar casos à contagem total.

## Execução real recuperada

API/logs GitHub consultados independentemente: [run 40222077074](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40222077074), job `121255614575`. Instalação/regressão passaram; aquisição terminou com `NO_NEW_REVIEWABLE_MEDIA`, preservação de proveniência/cache e artifact passaram.

A fase real às 18:37:21 UTC registra `ACQUIRED=0`, `REJECTED=0`, `EDITORIAL_APPROVED=0`, `EDITORIAL_DRAFTS_CREATED=0`. Os oito diagnósticos persistidos em `media_inbox.json` indicam resposta por cache; nenhum erro de autenticação é evidenciado nessa execução. Zero aquisições/rejeições não deve ser apresentado como falha da API ou como validação de novas credenciais. As linhas anteriores de log com aquisições/rejeições positivas pertencem aos fixtures da regressão, não à aquisição real.

Esse run antecede a disponibilidade dos novos contadores no relatório persistido consultado; não atribuir seus valores à nuvem sem novo run correspondente. Inbox registra 15 itens não revisados, o que não equivale a 15 vídeos aprovados ou a dias de reserva.

## Limites e pendências desta revisão

Nenhum novo bloqueador de segurança identificado no patch de métricas. Promoções de fontes ao catálogo, auditoria dos MP4s pendentes e proposta de reserva ainda requerem revisão final conforme os respectivos arquivos sejam concluídos. Fonte já existente revisada não deve ser contada como nova aquisição. Reserva técnica ou revisão de catálogo não substituem consentimento de publicação.

Classificação provisória: **PARCIAL**. Nenhuma comprovação adicional de dois vídeos publicados diariamente ou avatar animado decorre dessas métricas/testes.

## Verificação dos arquivos de reserva e nova fonte

Relatório `RESERVE-4.6.json` registra download e validação técnica de sete MP4s reais, todos aprovados tecnicamente, sem publicação/aprovação editorial. O auditor recalculou independentemente SHA-256 dos sete arquivos locais baixados: todos coincidem com o relatório e a fila. Também repetiu `require_evidence` para cada item contra fila, estado e histórico arquivado completos, excluindo somente o próprio item: sete passaram. Metadados confirmam seis Kokoro femininos e um Piper legado. Não houve escuta ou segunda renderização pelo auditor; aprovação técnica não certifica naturalidade ou alegações comerciais.

Novo catálogo `mesa-caneca-afastada` usa fonte existente `133319`, com hash fixado `29851ab6e02b49e82e04f2500c495f4eb8c34299d672a70f0c5ff5495b8357f3` e enquadramento integral. `SOURCE-EVIDENCE-4.6.md` registra inspeção de seis quadros pelo implementador, 21,588333 s e 30.490.886 bytes. Roteiro descreve a bebida servida perto de celular/teclado e oferece recomendações; não afirma que a filmagem demonstra arrumação já realizada ou eficácia. Fonte botânica `118275` foi descartada corretamente e `165820` não foi reutilizada por já constar na fila. Isso é revisão de material existente, não nova aquisição da API; `reviewed=true` não aprova publicação.

Uma futura proposta de seis vídeos distribuídos por três dias deve manter seleção vazia, consentimento ausente e horários propostos explícitos, com revalidação integral ao consumir a autorização. A existência dos sete MP4s não comprova três dias de publicações aprovadas.

## Revisão final do preview e regressão

Patch de `review_batch44.py` revisado: prioriza voz Kokoro, preserva prioridade dos horários futuros válidos e propõe apenas datas posteriores ao dia atual em Brasília. Mantém janela de sete dias, horários 10h/18h e reservas existentes. Campo de voz passa a integrar o manifesto e a página, sem inferir naturalidade. Nenhum item é pré-selecionado ou aprovado.

Consumidor `approve_preview44.py` continua reconstruindo a proposta no instante original e comparando identidade, slots e snapshots, incluindo o campo de voz agora presente. Atualização do teste de expiração usa o prazo real do manifesto, sem relaxar o gate. Novos testes cobrem seis Kokoro nos próximos três dias completos sem reservas prévias e fronteira entre data UTC e Brasília. Conflitos/reservas existentes continuam prioritários; não garantir três dias consecutivos em qualquer estado de fila.

Regressão independente final após esses patches: **270 testes aprovados**, 0,337 s. Sem bloqueador novo identificado. Não houve aplicação de autorização, agendamento ou publicação pelo auditor. Resultado do render cloud `40222665672` permanece a ser confirmado separadamente; nenhum novo vídeo é declarado concluído nesta revisão apenas pelo código salvo.

## Adendo cloud confirmado

Consulta independente posterior ao GitHub: run `40222665672`, job `121257409053`, concluído com falha no passo de renderização, mas refresh e persistência concluídos com sucesso. O log da fase real registra às 18:46:13 UTC `RENDERED casasem-2026-10-26-1: 19.40s; technical pass; NOT PUBLISHED`. A tentativa seguinte falhou por fonte restante com 4,31 s úteis, abaixo do mínimo de 15 s, antes da narração. Isso comprova um novo render, não dois. Linhas anteriores de 20 s e `NEW_VIDEO_COUNT=2` pertencem aos testes e não devem ser contadas como produção real.

Refresh desse run registrou 11 pendentes e oito selecionáveis, `approved=false`, `submitted=false`; persistência após falha funcionou como previsto. A coordenação deve recuperar o novo commit/MP4 e regenerar o preview com o estado atualizado e a política final de voz/datas antes de apresentar o lote. O sistema permanece PARCIAL, com um vídeo novo salvo pelo fluxo e insuficiência de cenas para o próximo slot, sem publicação autorizada nesta missão.
