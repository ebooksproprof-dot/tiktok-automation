# Auditoria independente 4.3 — 23/10/2026

Revisão por agente separado dos implementadores. Base recuperada `64e3133`; checkpoint de trabalho `d918f9`. Nenhuma aprovação ou publicação executada pelo auditor. Resultado provisório **PARCIAL**, sujeito aos resultados dos experimentos em andamento.

## Operação recuperada

Consulta independente aos jobs/logs GitHub confirmou:

- Run `39972690905`, job `120479215305`: envio e persistência concluídos; zero chamadas Buffer, zero envios novos e 12 publicações históricas verificadas. Falha exclusivamente no gate de cobertura: 23/10 às 10h `NOT_SUBMITTED_REVIEW_ROUTE_OR_CONSENT_REQUIRED`; 18h `NO_VIDEO`.
- Run `39949935232`, job `120401654076`: primeiro vídeo salvo no commit `64e3133`, mas segundo render bloqueado por `SOURCE_TOO_SHORT_WITHOUT_REPEATING`. Sem indício de autenticação ou quota como causa dessa falha.
- Runs anteriores `39866437930` e `39954967820`: passos de envio/persistência com sucesso e falha de cobertura. Aquisição `39943053578` cancelada durante instalação, antes de adquirir cenas; motivo do cancelamento não comprovado.

O estado local contém 12 publicações reais verificadas pelo provedor, última `casasem-2026-10-22-1`, 22/10 às 10h BRT, além de um registro sandbox sem essa verificação. Nenhum `SCHEDULED`/`UNKNOWN`. Cinco itens não submetidos, todos sem aprovação e rota, incluindo os slots expirados de 22/10 às 18h e 23/10 às 10h. Não houve inspeção independente da página pública TikTok nesta auditoria.

O novo vídeo `casasem-2026-10-23-1` tem metadados Kokoro, 1080×1920, 21,27 s, oito cortes e zero intervalos pretos/silêncios longos; continua pendente de revisão. Não confundir renderização com publicação.

Crons preservados: aquisição 07h30, criação 08h30, preparação de envio 09h07/17h07 e reconciliação 10h17/11h17/18h17/19h17, BRT. A pontualidade exata do GitHub cron não é garantida.

## Causa concreta da insuficiência de cenas

O único candidato restante após rotação, novidade de roteiro e histórico visual é `piso-pouca-agua`, fonte `piso2`/Pexels `7551204`.

Download independente limitado a 250 MB e inspeção ffprobe: **11.300.651 bytes, 2160×3840, duração 4,360000 s**. A reserva de 0,05 s do planejador deixa 4,31 s úteis, abaixo do mínimo de 15 s. A correção exige novas cenas pertinentes suficientes ou outro conteúdo, não remoção do gate, loops ou aceleração artificial da fala. URL medida: https://videos.pexels.com/video-files/7551204/7551204-uhd_2160_3840_25fps.mp4

## Alterações revisadas e testes

Regressão independente após as alterações: `python -m unittest discover -s automation/tests` — **227 testes aprovados**, 0,107 s. Baseline histórico não foi repetido antes de haver alterações.

- ONNX: `disable_telemetry_events()` chamado antes da criação de sessões Piper/Kokoro. Não altera consentimento ou envio.
- Gate audiovisual: início de streams deve diferir no máximo 80 ms e fim no máximo 150 ms; tempos ausentes/não finitos e durações não positivas são rejeitados. `lip_sync_verified=false` é explícito: alinhamento de streams não mede sincronização de boca. Testes incluem padding AAC, offset e áudio truncado.
- Framing: foreground integral centralizado em caixa y=500–1220, sem crop e fora das áreas atuais de headline/legendas; fundo desfocado. Preservar o quadro reduz o tamanho do produto, não comprova superioridade perceptiva.
- EchoMimic: workflow isolado, CPU, permissões `contents: read`, checkout sem credenciais persistentes, dez minutos máximos; instalação quatro, experimento cinco, subprocesso de inferência três. Sem Buffer/TikTok ou escrita em fila. Código e pesos em revisões fixadas; inventário de arquivos, teto de 13 GB, RAM mínima e reserva de disco antes do download. Voz existente com SHA conferido e download limitado. Configuração 256×256, 12 fps/quatro passos é diagnóstico, não qualidade comercial.

As licenças/fontes foram documentadas pelo implementador em `AVATAR-4.3.md` (Apache 2.0/MIT, sem modelo gated ou aceite adicional); esta revisão de integração não constitui análise jurídica independente de todos os pesos. Dependências auxiliares não estão todas fixadas, portanto reprodutibilidade futura integral não é certificada.

## Pendências encontradas durante revisão

1. Versão inicial de `validation_v43.py` usava fonte `51807` no item C, já publicada em 21/10. Reproduzido sem render/modelo: **`VISUAL_SOURCE_REUSED`**. Preservar histórico/gate e trocar por fonte inédita pertinente; não declarar C concluído até saída real do helper corrigido.
2. Versão inicial do smoke marcava `avatar_video_produced` após ffprobe retornar sucesso, sem validar explicitamente streams/duração no JSON. Solicitação ao implementador: exigir áudio+vídeo e parâmetros esperados antes dessa alegação. Mesmo um MP4 válido precisa revisão visual de identidade, naturalidade e boca.
3. Provas finais, escuta da voz e resultado cloud do avatar ainda pendentes nesta revisão inicial. Não afirmar avatar produzido ou qualidade melhorada sem evidências.

Fontes de operação: https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/39972690905 e https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/39949935232; `automation/state.json`, `queue.json`, `scene_plan.py`, `media_quality.py`, `framing.py`, `validation_v43.py`, `avatar43_smoke.py` e workflow correspondente.

## Adendo após correções e provas locais

Regressão independente final desta etapa: **230 testes aprovados**, 0,181 s. Nenhum novo bloqueador encontrado na revisão abaixo; conclusão cloud do avatar ainda pendente.

Os dois achados acima foram corrigidos: C passou a usar `38115`, ainda não publicado, mantendo histórico integral; smoke agora exige exatamente um stream de vídeo e um de áudio, 256×256, durações 3 s ±0,3 s e decodificação integral antes de registrar vídeo produzido. Isso não certifica qualidade facial ou labial.

`offline_exec.py` aplica seccomp antes de executar a inferência cacheada: nega criação de sockets, conexão e chamadas de envio; falha se não conseguir carregar o filtro. Teste em subprocesso confirmou `PermissionError` na criação de socket e herança no filho. O wrapper destina-se ao ambiente Linux local com assets previamente baixados; não deve ser tratado como compatibilidade multiplataforma. Duas tentativas anteriores de telemetria foram rejeitadas pelo ambiente; nenhuma autorização de telemetria foi concedida. A execução offline resolve a necessidade de inferência sem saída de rede.

Renderer passou a selecionar diretamente `PROVENANCE.frame_mode=preserve_full`, usando o mesmo helper de composição; política desconhecida falha. Verifica capacidade mínima de 15 s antes da síntese e mantém verificação da duração real após síntese, evitando gastar TTS no candidato comprovadamente curto. Nenhum loop, reset de histórico ou alteração de consentimento foi introduzido. Dois itens de catálogo foram acrescentados após revisão de contexto; `reviewed=true` no catálogo não é aprovação de publicação, e novos posts continuam `approved=false`.

Relatório `framing-4.3-local-evidence.json` registra dois MP4s reais com fila/estado/histórico inalterados: B 17,155 s, delta final áudio/vídeo 0,021667 s, SHA `311a1d024cb91e6df854d571ab1c6e72794ac8ce6fdc5bc91694ca6e020ca403`; C 19,466667 s, delta 0,007667 s, SHA `8fad17956f30cfefff3db434ac09772998cab26c9ce8581cb9baa2e1f1347753`. Ambos 1080×1920 e sem preto/silêncio longo segundo o relatório. O auditor conferiu metadados e código, não realizou escuta ou nova renderização. Contact sheets foram inspecionadas pelo implementador: produto visível, legendas fora do quadro útil; C tem iluminação escura. Persistência externa dessas provas e resultados cloud devem receber adendo após verificação.

## Adendo final — execução e persistência cloud verificadas

Consulta independente ao GitHub confirmou:

- [Provas 40013113619](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40013113619): job `120618242187` concluído com sucesso, incluindo download verificado, render sem rede, persistência e artifact. [Release 422244378](https://github.com/ebooksproprof-dot/tiktok-automation/releases/tag/validation-v43-2026-10-23) contém cinco assets `uploaded`: dois MP4s, dois JPGs e relatório. MP4 B: 6.661.731 bytes, SHA `0164541ca8dca409eada309fbc7a85d82b7e84458a313889527b23696f666501`; C: 6.247.060 bytes, SHA `597a3a1cf01cb87f1b2d43f165c9701f2cbc5adb78f08c8549e376e5d10801f8`. A API declara hashes completos compatíveis com os nomes. São outputs cloud diferentes dos arquivos locais acima, não hashes intercambiáveis. Corpo da Release declara formato C, sem avatar e sem aprovação TikTok.
- [Integração diária 40013644972](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40013644972): job `120620140613` concluído com sucesso. Log registra `NEW_VIDEO_COUNT=1; PUBLICATION_CONFIRMED=false` e commit bot `1b3bafb`. Há comprovação de criação diária real após integração, não apenas suíte verde.
- [Runner 40013923518](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40013923518): envio/persistência com sucesso, zero chamadas Buffer e zero envios; 12 publicações históricas verificadas. Gate de cobertura falhou com `NOT_SUBMITTED_REVIEW_ROUTE_OR_CONSENT_REQUIRED` nos dois slots. Essa falha preserva a exigência de aprovação, não demonstra defeito de autenticação.
- [Avatar 40013645148](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40013645148): job `120620055390` instalou dependências com sucesso e falhou no passo do experimento; artifact `12527382129` preservado (4.218 bytes). O log de job não contém a exceção detalhada, que o script grava no relatório. A causa deve ser extraída desse artifact antes de uma conclusão específica. Falha do passo não comprova inferência realizada nem impossibilidade universal de CPU; nenhum avatar aprovado foi evidenciado nesta verificação.

Última revisão da aquisição: query de cozinha direcionada a `washing dishes sponge`, correspondência exigindo `sponge`; contact sheet usa escala para caber e padding, preservando o quadro completo em vez de ocultar laterais. Essa melhoria facilita revisão visual, mas não certifica pertinência por tags nem capacidade ilimitada. Regressão completa independente após essa alteração: **230 testes aprovados**, 0,212 s.

Conclusão mantida: **PARCIAL**. Renderização com voz feminina, novo enquadramento, controles técnicos e persistência cloud comprovados; nenhuma nova publicação autorizada pelo auditor, nenhum avatar fotorrealista com lip-sync comprovado, nenhuma escuta comparativa e nenhuma evidência de dois conteúdos inéditos publicados diariamente sem intervenção.

### Causa do segundo experimento avatar

Após obtenção do artifact, leitura independente de `tmp/avatar43-evidence/report.json` e `execution.log` confirmou: pesos baixados, PyTorch `2.2.2+cpu`, CUDA ausente, subprocesso iniciado e falha ao carregar `face_locator` em `torch.load(config.face_locator_path)` sem `map_location`. Erro exato: tentativa de desserializar tensor CUDA em ambiente CPU. Tempo registrado 71,271 s; pico RSS de filho 14.108.044 KiB, não memória agregada; nenhum MP4. O relatório mantém `inference_executed=null` e `avatar_video_produced=false`. Uma correção limitada de mapeamento CPU pode resolver esse erro específico, mas ainda não comprova viabilidade da inferência completa ou qualidade comercial. Resultado de eventual nova tentativa deve ser registrado separadamente.

### Tentativa final limitada e aquisição

Patch AST revisado: exige exatamente as três chamadas `torch.load` conhecidas do entrypoint fixado e adiciona `map_location='cpu'`; rejeita inventário ou mapeamento inesperado. Spot checks independentes de três inserções, idempotência e rejeições passaram; não são testes adicionais contados na suíte de 230.

Run [40014366737](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40014366737), job `120622513799`, terminou com falha após instalação bem-sucedida. Auditor baixou artifact `12528276303` e confirmou SHA-256 ZIP `fa6fb862ffec7c3b00d1b11615dadff6cb4734eba39804075df21ed7f40ceaae` antes de ler relatório/log. Tempo 73,726 s, pico RSS filho 14.104.688 KiB, aproximadamente 12,333 GB de pesos baixados, nenhum MP4. A falha anterior de checkpoint foi superada; esta tentativa chegou à chamada do pipeline, mas `ReferenceAttentionControl` em `src/models/mutual_self_attention.py`, linha 83, ainda executou `.to(device)` para CUDA e lançou `AssertionError: Torch not compiled with CUDA enabled`. Não foi OOM nem timeout. Resta adaptar e testar o tratamento interno de dispositivo; isso não prova que tal adaptação seria suficiente para qualidade ou execução diária gratuita. O experimento limitado encerra sem alegar avatar produzido.

Aquisição [40014366564](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40014366564) também conferida por logs: consultas dos fornecedores responderam, mas `ACQUIRED=0`, `EDITORIAL_DRAFTS_CREATED=0`, `APPROVED=0` e `ACQUISITION_BLOCKED=NO_NEW_REVIEWABLE_MEDIA`. Histórico/proveniência foram preservados. A nova query e apresentação integral de previews foram executadas, porém não entregaram novas cenas elegíveis nesta rodada; continuidade editorial permanece limitada.
