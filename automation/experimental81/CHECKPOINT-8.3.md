# CasaSemEsforço 8.3 — ligação da geração IA ao GitHub Actions e à fila Buffer

Data: 03/11/2026. Estado: **AGENDADO PARA TENTAR**, mas **NÃO VALIDADO EM PRODUÇÃO**.

## Agendamento real instalado na MAIN

- Workflow `.github/workflows/ai30-free-collector.yml`.
- URL: https://github.com/ebooksproprof-dot/tiktok-automation/actions/workflows/ai30-free-collector.yml
- Rodará às 06:10 e 12:10 UTC (03:10 e 09:10 São Paulo; horários de cron do GitHub são aproximados, podem atrasar).
- Ele existe no **default branch main**, requisito para cron automático no GitHub.
- Usa Ubuntu standard gratuito de repo público, CPU FFmpeg/Kokoro e API pública ZeroGPU anônima via Gradio (token=False). Não usa conta PRO, cartão, GPU paga, créditos pagos nem usuário com computador ligado.
- Faz checkout da branch `feature/ai-video-hybrid-30s`, e mantém o código em revisão isolada.
- `AI30_MAIN_SCHEDULER_ALLOW=true` identifica o único workflow agendado autorizado a reservar no ledger experimental.
- A geração está configurada para *tentar*, não há vídeo novo gerado ou postado nessa implantação.

### Prova rápida do GitHub, sem cota de GPU

Run: https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/41581476296

Resultado: 68 testes unitários executados, 4 ignorados, zero falhas; `--dry-run` reportou `DRY_RUN_NO_REMOTE_CALLS`. O job de geração foi pulado **intencionalmente** nesse push; não comprova geração nem postagem.

## Fluxo de dados preparado

1. `auto_collect.py`: usa referência estática obtida de vídeo Pexels previamente licenciado, mas envia o **quadro** ao Wan; cada movimento final nasce da geração IA. Usa prompt autoral e idêntico conjunto de 6 cenas para o primeiro episódio.
2. `github_ledger.py` + `daily_budget.py`: check e reserva CAS persistentes em `automation/experimental81/ledger.json` antes de uma submissão real ao Hugging Face. Para a conta anônima, limite conservador equivalente a até 2 chamadas de ~55s estimados por janela de 24h. O real débito do serviço ainda não é exposto/verificado.
3. Cada arquivo real de saída é validado, recebe SHA256, verificação de não duplicata e é armazenado em uma Release mensal `ai30-drafts-YYYY-MM`, com readback de hash. Registro durável em `auto_inventory.json`. Falhas ambíguas não são reenviadas às cegas; erros claros de cota aguardam nova janela e novo fingerprint.
4. `auto_finish.py`: somente depois de **seis clipes reais diferentes** calcula o plano `AI_ONLY=(30,0)`, sintetiza voz Kokoro pf_dora, compõe MP4 vertical H264/AAC 30s e testa decodificação, silêncio, quadros pretos e duração. O compositor não preenche duração com filmagens reais nem congela frames para ampliar tempo.
5. Carrega o MP4 final com SHA em Release normal `media-YYYY-MM` usando o publicador de mídia já existente.
6. Faz staging com GitHub CAS na **única** `automation/queue.json` de main, apenas se slot de 10h estiver disponível nas próximas 26h e metadados/consentimento do proprietário e fingerprints não indicarem duplicação.
7. `.github/workflows/tiktok-online-runner.yml` e `buffer_runner.py` existentes continuam o único publicador real para TikTok. Em main, o `media_quality.validate(..., ai_only30=True)` e o desvio em `buffer_runner.verify_hosted` validam explicitamente 30s **apenas** para posts originados como AI30; demais posts seguem 15–28s.
8. Postagem com flag AI é solicitada ao Buffer. Um post aceito por Buffer NÃO comprova postagem pública; verifique `state.json` / permalink.

## Estado de produção e limites

- Main recebeu somente workflow agendado e validação opt-in Buffer 30s; nenhuma postagem foi submetida por esta implementação, e a antiga fila não foi reescrita antecipadamente.
- A branch experimental contém o gerador, estoque, ledger, composer e testes. Não houve merge da PR inteira.
- A tarefa ChatGPT `CasaSemEsforço Diário` existente foi mantida e atualizada para MONITORAR este pipeline, sem lançar geração duplicada.
- O modelo Wan usado antes gera 5s por clip em ~480×832 a 16fps. A saída final 1080×1920 não transforma resolução nativa nem garante qualidade profissional.
- **Máximo teórico com quota anônima: ~2 clipes de 5s por janela de 24h** (sem falhas). Se tudo funcionar, o primeiro 30s exige no mínimo três janelas de cota. **Não sustenta 1 vídeo de 30 segundos IA por dia.**
- A quota da conta gratuita autenticada de 300s não é usada neste fluxo, pois não foi fornecido token HF autenticado nem confirmada ausência de faturamento.
- A aplicação da licença comercial do LoRA derivado/mirror ainda não tem confirmação formal, apesar de os modelos base Wan e vários Lightx2v originais serem Apache-2.0; a tentativa de publicação não pode ser chamada de licença comercial verificada.
- A autorização do proprietário para a primeira publicação de teste dispensa a prévia humana; os checks automáticos de vídeo não garantem fidelidade visual/semântica das mãos e objetos. Metadados explicitam isso.
- A API pública do terceiro Space não promete disponibilidade/geração gratuita ilimitada. Mudanças de endpoint, fila ou cotas podem parar o workflow.

## Atualização após auditoria de autenticação opcional

O coletor também aceita opcionalmente um Secret de repositório chamado `HF_FREE_TOKEN`, mas **nenhum token foi configurado pelo assistente**. Quando ausente, mantém `token=False` (120 segundos de quota documentada anônima). Se existir, realiza `whoami-v2` e somente permite `type=user, isPro=false`; contas PRO/pagas/identidade desconhecida são bloqueadas, sem fallback cobrável, e a mudança anônimo→Free só vale após 24h do ciclo anterior. Esse Secret não dá garantia de seis clipes de 5 segundos diários: quatro steps ainda exigem cota estimada superior aos 300s da conta Free.

O `auto_finish.py` contém recuperação idempotente para uma fila que já foi gravada em main, mas cuja confirmação de inventário falhou. Não reenvia a mesma postagem.

**Último teste isolado:** run [41582223948](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/41582223948), **71 testes, 4 ignorados, 0 erros**. Unidade/mock não é prova de primeira geração em nuvem na versão 8.3.

## Checkpoints para retomar

1. Conferir a primeira execução **schedule** no link do workflow principal após o cron: preflight, instalação FFmpeg, geração real e inventário.
2. Verificar `auto_inventory.json` após cada ciclo: número de clips reais, hashes, evidence, `status=COLLECTING/READY/BLOCKED`.
3. Consultar `ledger.json` e `github_ledger.py` antes de qualquer tentativa manual para não queimar a cota nem enviar requisição duplicada.
4. Quando seis clipes, conferir a Release do MP4, nova entrada única em main/queue.json e execução do `tiktok-online-runner.yml`.
5. Comprovar permalink público em `automation/state.json`, não declarar postado apenas por staging/Buffer.
6. Se o workflow terminar verde apenas com test/preflight ou `WAIT_CREDITS`, registrar como PENDENTE, sem resultados falsos.

**Classificação: SISTEMA DE TENTATIVA AUTOMÁTICA INSTALADO, publicação e produção recorrente NÃO COMPROVADAS.**


## Incidente 03/11/2026 — execução automática #41650152857

- O GitHub disparou o evento `schedule` realmente, **às 14:04 UTC / 11:04 Brasília**; o cron previsto era 09:10 Brasília e teve atraso. Cron do GitHub é best-effort, não garante execução no minuto.
- O job `collect-and-stage` **falhou no preflight**: `test_wrong_branch_does_not_access_remote` supunha que toda invocação em `main` fosse proibida, mas a exceção controlada `GITHUB_WORKFLOW=CasaSemEsforco AI30 Free Collector` agora permite justamente esse fluxo programado. O teste herdou essas variáveis do runner e falhou com `AssertionError: LedgerError not raised`.
- Não houve instalação de mídia, chamada ao Wan/ZeroGPU, reserva de cota, criação de MP4 ou postagem. `auto_inventory.json` ainda tinha 0/6 cenas; `ledger.json` tinha 0 claims.
- Correção **commit 49977300efc92ed6354e27d51e74877480f7ef0f**: o teste de branch proibida passa explicitamente um workflow não autorizado. A regra de produção de bloqueio para outros workflows em `main` foi preservada.
- CI corretiva: [run #41653526696](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/41653526696) — **71 testes executados; 4 skips, 0 falhas**; teste rápido sem chamadas ao modelo.
- O agendamento principal `.github/workflows/ai30-free-collector.yml` continua inalterado em main e usará a branch experimental atualizada. **O sucesso deste teste não confirma geração nem publicação real**; verificar o próximo `schedule`.



## TESTE REAL DE GERAÇÃO EM 03/11/2026 — SUCESSO PARCIAL VERIFICADO

- O usuário autorizou testar imediatamente e declarou que as fichas/créditos voltaram; o fluxo do GitHub **não possui HF_FREE_TOKEN configurado** e operou de maneira **anônima**, com estimativa de 120s/24h.
- Reexecutado de forma explícita o job originalmente falho [#41650152857](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/41650152857), attempt 2: **conclusão success**.
- O preflight aprovado, a instalação CPU concluída, a geração pelo Wan bem-sucedida, duas Releases com MP4 IA verificados, inventário atualizado e `auto_finish.py` terminou em NOT_READY (2/6 clipes, sem postagem). Nenhum vídeo novo foi publicado.
- 1º clipe SHA `9beffe8705114e562201221ccf43013db950c72ad299500250060e14eb1e3689`; 5.0625s, 480x832, 16fps, 355783 bytes. Arquivo: [ai30-9beffe...mp4](https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/ai30-drafts-2026-11/ai30-9beffe8705114e562201221c.mp4).
- 2º clipe SHA `53057032695adf534e1b6b37fa01d077e8b18d955fc49d9a8557e5d623be0555`; 5.0625s. Arquivo: [ai30-530570...mp4](https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/ai30-drafts-2026-11/ai30-53057032695adf534e1b6b37.mp4).
- `auto_inventory.json` marcou `status=COLLECTING`, `clips=2`; `ledger.json` marcou duas solicitações e `tier=anonymous`, primeira reserva `2026-11-03T14:29:45Z` (= 11:29:45 Brasília).
- DURAÇÃO TOTAL: 10.125s de clipes IA reais, faltam 4 clipes para 30s. A saída 1080x1920/Kokoro/Buffer ainda não foi executada com seis clipes, nem a publicação TikTok comprovada.
- Corrigido cron da branch main para 03:10, 09:10 e **13:10** BRT (06:10,12:10,16:10 UTC), para capturar a renovação após a primeira janela de 24h, sem ultrapassar a cota. Commit main `31f4a48b6278ed41a1d651d5876c5cd88985ab8c`; teste rápido [#41654751534](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/41654751534) aprovado.
- O fluxo automático agora é *comprovadamente capaz de produzir e armazenar até dois clipes em uma execução*, mas **não existe prova de que ele consiga produzir 30 segundos diários ou publicar automaticamente**.
- Direitos e qualidade audiovisual do material gerado ainda não receberam revisão perceptual comercial. O modelo base Wan/Lightx2v upstream está sob Apache 2.0 (cartão do upstream), mas a distribuição espelho `Kijai/WanVideo_comfy` não declara de forma clara a licença do pacote; não declarar licença derivativa completamente verificada.

