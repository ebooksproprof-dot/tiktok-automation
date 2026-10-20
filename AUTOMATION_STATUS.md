# CasaSemEsforço 3.0 — checkpoint 2026-10-20 UTC

Estado: PARCIAL. Publicação Buffer funcional; produção editorial contínua não comprovada.

## Base confirmada antes das alterações
- HEAD dcdf1161c12e867b5ef5dbabd6893bf36afe7fcd.
- Runner 39336473612: autenticação Buffer correta, 47 testes, sete publicações verificadas pelo provedor (cinco Buffer, duas Metricool). Não inspecionadas independentemente na página pública nesta retomada.
- Renderizador FFmpeg/Piper, Releases mensais, fila e estado persistentes. Código atual já tinha 11 fontes visuais e revisão de composição 4.
- Problema real: fontes reutilizadas entre temas; SHA do MP4 final não detecta cenas repetidas.

## Marco 1
Biblioteca visual integrada ao renderizador e aos dois publicadores: SHA por arquivo, cinco fingerprints perceptuais por fonte, histórico em fila/estado e bloqueio conservador de reutilização. 53 testes locais passaram, preservando os 47 anteriores. Fingerprint é heurístico; não comprova originalidade semântica. Fontes antigas sem fingerprints são comparadas por URL; backfill ainda necessário para detectar reencodes históricos. Nenhuma mídia inadequada deve ser aprovada só para manter frequência.

## Continuidade
Preservar posts já enviados; não repetir o teste público anterior. Ler o Marco 3 antes de continuar. Não há credenciais neste documento.

## Marco 2
- Commit visual: 0bcc392517fd78abd338cfe38032c74f3a30ebb4.
- Narração isolada em interface speak(text, wav), Piper CPU, frases completas e legendas por trecho temporal medido. Voz/modelo com hash fixado; runtime ONNX fixado.
- Três provas locais concluídas: bancada 19,913s/3,38MB; piso 20,04s/8,36MB; gaveta 18,7s/4,69MB. Fontes independentes, SHA e fingerprints distintos, áudio -16,1 a -16,3dB. Não publicadas e não enfileiradas pelo script preview_batch. Renderizações locais levaram 24,15/46,97/28,59s após carregar voz; não equivale a benchmark GitHub.
- Releases agora limitados a seis coleções mensais de até 64 arquivos/20MB. Não há exclusão automática de histórico; ao atingir teto, exige política de arquivo/revisão.
- OpenCut atual anuncia headless como futuro; não substitui FFmpeg. Craft oficial storytold; EffectCraft em PoC isolada. VoiceStudio é candidato experimental, não instalado como dependência obrigatória.
- Novo workflow review-v3 gera três MP4s na nuvem sem secrets de publicação, com artefatos temporários de sete dias. Relatório de medições deve ser preservado no Git; previews não são o histórico de publicação.

## Marco 3 — auditoria independente e provas reais
- Commits anteriores desta sessão: 0bcc3925, 2db436fb, 9fd4383c. Este checkpoint pertence ao commit de correções da auditoria.
- GitHub Actions 39353432805: três vídeos completos gerados, comparação visual e upload de artifacts aprovados. Link: https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/39353432805 . Retenção dos MP4s: sete dias. Medições locais duráveis em automation/review-v3-evidence.json.
- 58 testes locais aprovados após revisão independente. Corrigidos: histórico visual preservado no TikTok direto, fingerprints obrigatórios e rechecados contra envios anteriores, refiltro de fontes entre os dois slots. Manifesto visual legado preenchido com SHA e cinco dHashes por fonte.
- Buffer autenticado no perfil .casasemesforo no runner 39336473612; não houve alteração ou leitura da chave. Sete publicações históricas confirmadas pelo provedor. Nenhuma nova publicação pública nesta sessão 3.0: os três previews permanecem sem aprovação editorial, deliberadamente fora da fila.
- EffectCraft oficial storytold/effectcraft v0.11.1: executável Linux com SHA fixado, composição original vertical 1080x1920/30fps/1s renderizada em CPU em 0,86s pelo adaptador isolado. Projeto reproduzível em automation/fixtures/effectcraft-original.ecproj. Sem áudio; não integrado à montagem diária. Não substitui FFmpeg.

### Auditoria individual
| Componente | Classificação e evidência/limitação |
| --- | --- |
| Roteiros | Funcional com limitações: catálogo curado e rotação, não geração ilimitada |
| Biblioteca visual | Funcional com limitações: SHA, URL e cinco dHashes; heurística não detecta toda similaridade semântica |
| OpenCut | Não recomendado como backend atual: API/headless anunciados como futuros; não instalado |
| FilmCraft (storytold) | Experimental: CLI/headless documentado, alpha; sem PoC local |
| EffectCraft (storytold) | Experimental: PoC CPU e adaptador testados, separado do pipeline diário |
| PhotoCraft / VectorCraft (storytold) | Não recomendados como substitutos do renderer: ferramentas de assets; não instaladas |
| VoiceStudio | Bloqueado para adoção: Supertonic3 exige aceite específico de licença de pesos; Docker padrão pesado com CUDA. Não contornado |
| Piper / FFmpeg | Funcional e testado: três narrações e três MP4s locais e na nuvem; legendas por trecho, não alinhamento palavra a palavra |
| Releases | Funcional com limitações: upload/recuperação existentes; teto de seis meses, 64 assets/mês, 20MB/asset; requer arquivo ao atingir teto |
| GitHub Actions | Funcional com limitações: agendamento UTC sujeito a atraso; prova render real aprovada |
| Buffer | Funcional com limitações: autenticação e publicações históricas; novo vídeo 3.0 ainda não publicado |
| Metricool | Funcional com limitações: duas publicações históricas; não demonstrada interface gratuita autônoma via Actions nesta sessão |
| TikTok direto | Bloqueado para comprovação: aprovação/permissões não demonstradas; não presumir operativo por testes unitários |
| Monitoramento e duplicidade | Funcional com limitações: checkpoints, alertas e regressões; falha ambígua não é reenviada automaticamente |
| Custos e cotas | R$0 gasto; CPU open source. 60 vídeos originais/mês NÃO comprovados por falta de renovação visual/editorial |

### Próxima ação prioritária
Adicionar e validar um fornecimento autorizado de filmagens inéditas contextuais, com capacidade demonstrada para 60 vídeos/mês; depois aprovar e publicar UM novo vídeo pelo Buffer e confirmar o permalink. Não desabilitar gates para atingir frequência. Produção e aprovação editorial contínuas ainda impedem classificar como OPERACIONAL.

### Retomada
Confiabilidade: runner39355508502 foi cancelado enquanto aguardava o grupo compartilhado, sem executar jobs. Adicionado workflow_run após conclusão da criação em main para reconciliar novamente sem retirar a serialização do estado. Checkout continua main, não código/artifact de PR. Agendamentos permanecem como recuperação. Verificar próximo runner antes de afirmar aceitação do segundo vídeo.

Segundo slot: Release do vídeo de livros confirmado, commit891f2c5b. Aprovação editorial específica registrada no SHA f385676... e rota Buffer, para20/10/2026 às18h Fortaleza. Primeiro slot permanece10h. A aprovação não significa que Buffer já aceitou; confirmar estado subsequente. Nenhum dos dois é nova publicação pública confirmada nesta sessão.

Regressão final desta etapa:77testes passam também na revisão independente. Gate visual agora rejeita duplicação de uma fonte dentro do próprio vídeo, mesmo com IDs diferentes. MP4 de livros baixado do artifact da nuvem e comparado ao SHA f385676..., contact sheet conferida. Staging do segundo slot:39355345920. Aguardar resultado e aprovação específica; nenhuma prova pública adicional até o horário agendado.

Nova prova na nuvem aprovada: 39355200660, vídeo livros 20,933s, SHA f38567677f9914670a55450601c4c1cec6a6981bd429787e18e595152cf8b273, render22,21s após carregar voz. Auditor independente repetiu74testes sem novo bloqueador no planejador. Staging agora aceita slot ehash explícitos, mantendo proibição de sobrescrita e aprovação desativada; workflow transfere somente esta prova para casasem-2026-10-20-2 (18h Fortaleza). 76testes locais incluem validação dos novos parâmetros. Conferir estado real antes de afirmar envio/publicação.

Marco conteúdo real: primeiro lote preenchido com livros-por-assunto e filmagem vertical nova de Liudmyla Honcharova/Pexels, origem/licença consultadas e SHA conferido. Preview local completo: 20,389s,1080x1920,5,71MB, áudio -16,5dB; evidência em automation/review-books-evidence.json. Não publicado nem enfileirado. Três outras fontes foram avaliadas e não promovidas por enquadramento/duração. Render revisão6 remove stream_loop e usa janelas sequenciais sem sobreposição; fonte curta falha em vez de repetir. Novo tema expôs falha de equilíbrio de categorias, corrigida priorizando a categoria elegível mais abundante. 74 testes locais aprovados. Workflow review-v3 agora testa o novo lote; execução histórica dos três vídeos continua preservada em 39353432805.

Auditoria do lote de renovação encontrou e corrigiu duas falhas: colisão com IDs dos seis temas legados e similaridade textual entre slots no mesmo lote. A seleção agora reavalia o texto depois de salvar o primeiro vídeo. 71 testes locais aprovados com regressões específicas. Commit inicial do módulo: 200248ea9bed110c3f59f70ded648a02d0699b8d; correções neste checkpoint. Nenhuma nova fonte fictícia foi adicionada, nenhum vídeo adicional foi enviado.

Marco renovação: entrada JSON de lotes editoriais implementada em catalog_extension.py/json, sem API paga e sem coleta não autorizada. Valida origem Pexels, licença declarada, contexto, autoria, SHA, IDs e categorias; bytes conferidos no download/cache. Trigramas bloqueiam roteiros quase iguais, mesmo com gancho diferente; texto do roteiro passa a ser preservado no estado dos publicadores. 69 testes locais passam. Guia: automation/CONTENT_RENEWAL.md. Lote vazio proposital: não representa novos conteúdos nem resolve sozinho a reposição automática. Runner 39354219342 terminou com sucesso sem reenviar o post agendado.

Resultado confirmado às 01:34 UTC: Buffer recebeu via GitHub Actions o novo vídeo casasem-2026-10-20-1 e retornou SCHEDULED, buffer_post_id 6ad6c51cb81183413da8c66a; agendamento 20/10 às 10h Fortaleza. Estado persistido em commit 870f52c107fb92b695669b59495556eb178a6082. publicly_verified=false e permalink ausente: ainda NÃO publicado. Runner cron às 10:17/11:17 consultará o mesmo ID sem reenvio. Segunda revisão independente: 61 testes passam, staging sem novo bloqueador. Estoque restante tem no máximo cinco fontes ainda inéditas após esta reserva, insuficiente para 60/mês.

Regressão adicional: 61 testes locais aprovados. Três novos testes garantem que o staging recusa ID já submetido, slot ocupado e bytes diferentes do preview autorizado, antes de qualquer upload. Runner de envio da prova: https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/39354107437 . Confirmar o resultado neste run/state; não inferir de seu disparo.

Prova nova armazenada: execução 39353972929 concluída com sucesso; Release casasem-2026-10-20-1-8764601bee4d9101.mp4 verificada. Cloud MP4 baixado e hash conferido, contact sheet inspecionada. Aprovado especificamente para Buffer em 20/10/2026 às 10h Fortaleza; não implica aprovação automática de próximos vídeos. Não afirmar publicação antes de state.publicly_verified e permalink. Readiness agora informa limite superior visual, não apenas número de roteiros.

Checkpoint adicional: auditor independente repetiu 58 testes após as correções sem novo bloqueador técnico. Workflow 39353810347 concluído com sucesso. Estoque atual: oito roteiros elegíveis usando apenas seis fontes inéditas; não equivale a oito vídeos visualmente exclusivos. Stage-v3-proof transfere somente o primeiro preview da execução 39353432805, exige SHA exato e read-back de Release, cria slot de 20/10 às 10h Fortaleza sem aprovação. Não reexecutar após ocupar slot.

1. Ler este arquivo, queue.json, state.json e visual_history.json diretamente do main atual.
2. Executar python -m unittest discover -s automation/tests -q.
3. Não reintroduzir fontes já usadas, não reenviar IDs existentes e não sobrepor fila/estado com cópias locais antigas.
4. Previews: python automation/preview_batch.py; não publica. EffectCraft opcional usa binário oficial fixado e adaptador separado. Piper/FFmpeg continuam padrão.
