# CasaSemEsforço 4.0 — checkpoint 22/10/2026

Estado: PARCIAL. Não confundir publicação de fila previamente aprovada com renovação editorial autônoma.

- Base recuperada: 8a3720c5c6e87e99a8cce3d4b3a69cd8316b23ac.
- Correção operacional salva: 9bd56894b750e4ea83a92c056af85cf78df1821e; Runner 39828669675 concluído com sucesso.
- Buffer agora exige approved=true e consented_at válido antes de novos envios; revalida também visual_history.json.
- daily_coverage.py, após reconciliação/persistência, identifica lacunas nos slots 10h/18h e falha a partir de uma hora antes do slot; não altera consentimentos nem reenvia posts.
- QA contínuo salvo: 7a6d8fbadcab043fef2c013930096ab2d83dca72. Decode com -xerror, preto >=300ms e silêncio <=-45dB por >=800ms bloqueiam MP4.
- Auditor independente repetiu 187 testes; três MP4s legados passaram no novo gate e streams sintéticos reais confirmaram detecção.
- Estado recuperado: Buffer confirma dois posts/dia em 18–21/10 e um em 22/10 às10h. Último link: https://www.tiktok.com/@.casasemesforo/video/7699477167792753927 . Evidência do provedor, não inspeção independente da página pública.
- 22/10 às18h: pontos-de-toque está renderizado, sem aprovação editorial/consentimento/rota; NÃO agendado. Nenhuma aprovação fabricada.
- Quatro drafts finitos; última rodada sem novo draft. Renovação contínua e 60 vídeos/mês não comprovados.
- Referência externa exclusiva @vault_shopp: vídeos reais não acessíveis na pesquisa; não há análise empírica de cortes, audiência ou retenção.
- FFmpeg/Piper permanecem integrados. EffectCraft é PoC histórica isolada; demais ferramentas não comprovadas no pipeline diário. VoiceStudio suporta CPU: limitação atual é avaliação/licença dos pesos, não exigência de GPU.
- Três previews4.0+três baselines concluídos na nuvem39829264202, salvos na Release validation-v4-2026-10-22. Todos1080x1920, sem preto/silêncio longos, nenhum publicado no TikTok. Evidência completa em automation/validation-4.0-evidence.json.
- Estilo casasem-v4 integrado às novas renderizações diárias (gancho visual, recorte alternado com margem segura, marcador final); três renders do helper real validados sem alterar fila/estado. Preservados MP4s existentes.192 testes locais finais repetidos pelo auditor.
- Relatório completo em automation/AUDIT-4.0.md; próximo passo: revisão editorial dos conteúdos pendentes e ampliação de filmagens pertinentes. Não repetir setup nem declarar2/dia sustentados.
- Nenhum serviço pago contratado. Preservar cotas e histórico existentes.

## Checkpoint final 3.5 — recuperação e idempotência comprovadas

- Commit de correção58c2a09 e checkpointdabc37ce já enviados ao GitHub.
- Envio real39475156076:1 novo vídeo aceito/agendado,4 chamadas, nenhum erro429/401/403.
- Reexecução39475534489 concluída:175 testes cloud,0 chamadas Buffer,0 envios,
  nenhuma alteração em state.json. Uso permaneceu112 registros30d; último18:29:44Z.
- Economia concreta dessa reexecução:2 consultas evitadas versus fluxo antigo
  (canal+pendentes futuros); não confundir com medição mensal de economia.
- Segunda auditoria independente repetiu175 testes sem bloqueador novo.
- Nenhuma publicação nova confirmada:21/10 às10h continua futura;20/10 às18h também
  ainda futura na verificação18:32UTC. Não reenviar nenhum desses IDs.
- Próximo passo automático: cron17:07 Fortaleza tenta segundo MP4 para21/10 às18h;
  cron18:17/19:17 verifica o post antigo de20/10. Estado continua PARCIAL.
- Custos adicionais contratados:R$0; sem promessa de produção editorial ilimitada
  nem de dois vídeos todos os dias sem aprovação. Relatórios/evidência preservados no Git.

## 3.5 — envio real confirmado, publicação ainda futura

- Correção58c2a09 enviada; workflow39475156076/job118809092308 concluído com sucesso.
-174 testes cloud;175 na regressão local após corrigir alerta de fila inválida/expirada.
-4 chamadas reais: canal, capacidade, create, readback. Novo post casasem-2026-10-21-1
  SCHEDULED para21/10 às10h Fortaleza; Buffer ID6ad7b316adf3e386a760ccfb. NÃO publicado ainda.
- Headers reais confirmaram100/15min,250/24h,3000/30dias; saldo final96/190/2888.
  Política90/90/1800 preservada abaixo disso; histórico não resetado.
- Segundo MP4 casasem-2026-10-21-2 está aprovado/Release/fila, aguardando janela26h;
  cron20/10 às17:07 Fortaleza deve tentar agendar21/10 às18h, sujeito a sucesso do provedor.
- Terceiro MP4 cantinho-de-leitura aprovado por SHA em review_requests, aguardando staging
  para próximo dia livre. Nenhum terceiro slot diário criado.
- Post20/10 às18h permanece SCHEDULED ID6ad6c8e0e9c669def5e52725; ainda futuro na verificação.
- Evidência em automation/buffer-3.5-evidence.json; auditoria em automation/AUDIT-3.5.md.
- Estado PARCIAL: envio recuperado; uma nova aceitação/agendamento, zero novas publicações
  confirmadas nesta missão. Produção sustentada/aprovação editorial diária ainda não comprovadas.

# CasaSemEsforço 3.5 — correção Buffer em validação

- Base real c342bbd; runner39473684713 confirmou142 testes e bloqueio LOCAL antes da rede.
- Limite60/24h vinha de Client.check_budget, não de HTTP429 do Buffer. Histórico preservado.
- Política agora90/15min,90/24h e1800/30dias,8/run: abaixo do menor limite oficial
  divulgado (buffer.com/api:100/d; developers.buffer.com/guides/api-limits.html:250/d,
  ambos100/15min e3000/30dias). Headers reais podem somente restringir novas chamadas.
- Sem trabalho elegível: zero chamadas. SCHEDULED reutilizado até dueAt; reconciliação
  em lote no máximo a cada30min; não consulta canal em reconciliação sem novos envios.
- Diagnóstico reserva4 chamadas para publicação. Tests-only push não dispara mais API.
- Retry-After/429,401/403 e backoff exponencial persistentes; sem retry cego de mutation.
- Gate adicional máximo2 reservas por data Fortaleza/slot; UNKNOWN continua bloqueando reenvio.
- Teste de envio real e auditoria final ainda pendentes neste checkpoint. Nenhum novo aceite alegado.

## Bloqueio final confirmado e recuperação
- Runner39473319061 encontrou o teto conservador de60 chamadas Buffer/24h.
  Nenhum vídeo novo enviado; fila de21/10 preservada. Não aumentar/resetar orçamento.
- Pré-checagem agora reserva chamadas suficientes para todo o ciclo antes de consultar
  o canal. Evita gastar saldo que não permite concluir envio/read-back.
-142 testes locais passam após essa correção. Retentativa pelos workflows agendados;
  aceite Buffer de21/10 ainda NÃO confirmado. O post20/10 às18h já estava agendado.
- Três MP4s cloud decodificados integralmente: zero intervalos pretos>=0,3s e zero
  silêncios>=0,8s abaixo de-45dB. Não equivale a avaliação humana da naturalidade.

## Resultado 3.4 — checkpoint de provas e staging
- Pixabay autenticado;8 filmagens adquiridas na nuvem.2 rascunhos automáticos persistidos.
-3 vídeos distintos renderizados na nuvem39472349389; artifact12288495146 baixado,
  hashes e contact sheets conferidos. Cenas ilustrativas; não afirmar alta retenção.
-141 testes finais locais e auditoria independente. Correção adicional do workflow
  mantém staging elegível mesmo se criação diária falhar, sem mascarar a falha original.
- Staging39473106379 concluído: dois MP4s salvos em Releases e fila aprovada para
 21/10 às10h/18h Fortaleza. Aceite Buffer/publicação devem ser lidos em state.json.
- Terceira prova aprovada permanece no review_requests para próximo staging limitado;
  nenhum terceiro slot diário criado. Hoje20/10 às18h ainda futuro nesta verificação.
- Aquisição agendada07h30 e criação08h30; drafts persistentes sem aprovação automática.
- Metricool API confirma .casasemesforo, sem agendamentos20–23/10; não criar rota paralela.
- Auditoria20 componentes em automation/AUDIT-3.4.md; sistema PARCIAL,60/mês não comprovado.
- Zero serviços pagos contratados; nenhum login nem reconfiguração do secret.

# CasaSemEsforço 3.4 — checkpoint de aquisição real, 20/10/2026

- Base recuperada: 79b957d, posterior a fe684f2. Secret não foi lido/configurado.
- Reexecução 39467916880 attempt 2: PIXABAY_API_KEY_PRESENT=True;
  quatro consultas reais respondidas e cache novo, zero fontes verticais elegíveis.
- Correção: fontes Pixabay 4K podem fornecer crop 1080x1920 sem ampliação;
  revisão de enquadramento continua obrigatória. Não baixa horizontal HD para ampliar.
- Execuções 39471657588 e 39471667432: quatro filmagens reais baixadas na nuvem,
  com SHA/dHash/duração/autoria/licença em media_inbox.json. Não são quatro vídeos finais.
- 119 testes locais e auditoria independente aprovados. Corrigida distinção cache/API,
  diagnóstico de falhas de download e espera de uma hora para falhas transitórias.
  Corrigida contact sheet horizontal para mostrar crop central sem deformação.
- Três novas composições Pixabay solicitadas na produção para prova, sem publicação.
  Somente relatórios rendered_for_review comprovam término; pending não comprova render.
- Confirmação anterior de 10h pelo Buffer preservada. 18h de 20/10 ainda futura
  nesta retomada (15h Fortaleza); não reenviada nem declarada publicada.
- Estado geral PARCIAL: 60 vídeos/mês e renovação/autorização editorial contínua não comprovados.
- R$0 em serviços contratados. Nenhum login/reconfiguração de credencial realizado.

# CasaSemEsforço 3.0 — checkpoint 2026-10-20 UTC

Estado: PARCIAL. Publicação Buffer funcional; produção editorial contínua não comprovada.

## CasaSemEsforço 3.2 — preparação para ativação Pixabay
- Base recuperada:7cf019c3b3fcb3fcd4a839154e802351fa5527a5; criação39465899920
  concluída com sucesso. Aquisição39465899928 continuava bloqueada, sem cenas elegíveis.
- PIXABAY_API_KEY NÃO foi configurada nesta etapa. O conector não oferece escrita de
  secrets; página GitHub exigiu login e autenticação segura foi recusada. Credencial
  fornecida pelo usuário não foi repetida, salva em arquivos, commits ou logs.
  Ação necessária: usuário adicionar PIXABAY_API_KEY diretamente nos secrets GitHub.
  Recomendada rotação posterior por ter sido compartilhada em conversa.
- Melhoria independente: fontes contextuais de5–300s agora podem ser combinadas.
  Antigo mínimo28s por fonte descartava filmagens aproveitáveis. MP4 final continua
  exigindo15–28s e tempo de cenas suficiente, sem loops nem aprovação automática.
- Falhas HTTP distinguem autenticação recusada, limite e erro de servidor por códigos
  fixos; last_run persiste diagnóstico por fornecedor sem URL autenticada/corpo de erro.
-116 testes locais aprovados, repetidos pelo auditor independente sem bloqueador novo.
  Zero novas filmagens adquiridas e zero novos vídeos produzidos nesta etapa3.2.
  Prova3.1 e seus artifacts permanecem registrados abaixo; não contar como nova aquisição.
- R$0 em compras. Dois vídeos diários/60 mensais ainda não comprovados; depende de
  secret, aquisição real, cenas suficientes e revisão editorial. Não ativado cron
  de coleta em massa nem substituídos os motores audiovisuais já testados.
- Próximo passo: após salvar o secret, executar CasaSemEsforco official media acquisition;
  conferir autenticação, arquivos medidos/inbox e créditos antes de promover ao catálogo.

## CasaSemEsforço 3.1 — fornecedores adicionais
- Auditoria independente final:113 testes repetidos, sem novo bloqueador. Artifact
  da nuvem baixado; SHA7a0898ca... conferido e contact sheet inspecionada. Contact sheets
  parciais de aquisição servem só para triagem; revisar os trechos antes de promover.
- Prova NA NUVEM concluída: https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/39465289889
  111 testes; novo vídeo pontos-de-toque17,048s,1080x1920,4.039.980 bytes,-16,1dB;
  SHA7a0898ca9ffdc4d7bb0fc81ef961607f4fe077561c5fe5f3715d35e197fc57dc.
  Artifact12285340507 requested-quality-proof, expira27/10. Relatório persistido em
  review_requests.json, status rendered_for_review, published=false. Não sobrescrever
  esse arquivo com cópia antiga pending. Um vídeo novo, não três e não publicado.
- Regressão final local:113 testes. Corrigida condição da prova para executar também
  após falha de criação, desde que instalação/testes tenham passado; falha original
  continua visível. Originais de mídia acima de8MiB não vão para artifacts: recebem
  contact sheet dos primeiros10s + metadados/créditos e recuperação por URL/SHA.
  Máximo dois originais pequenos (~16MiB) por execução, retenção3dias; prova final7dias.
- Auditoria por componente em automation/AUDIT-3.1.md. Nenhuma ferramenta experimental
  substituiu FFmpeg/Piper. Publicação confirmada permanece a das10h;18h ainda futura.
- Nova prova LOCAL: pontos-de-toque, 17,267s,1080x1920,4.084.208 bytes, áudio -16,3dB,
  SHA bf9fa47e90a0d57bf2fc9faf6804568cc82b4308c169356ff4a0d2d13aec2bf8.
  Três fontes restantes do catálogo existente medidas: bancada6,68s,pia10,01s,
  geladeira10,01s. Cenas/contexto e contact sheet inspecionados; hashes perceptuais
  distintos do histórico e dos três previews anteriores. Não adquiridas por nova API.
- Corrigido planejador: preserva montagem anterior quando cabe; com durações desiguais
  distribui pelo tempo disponível, sem loop/sobreposição. Novo roteiro contextual.
  111 testes locais passam. Uma prova explícita solicitada no workflow de produção,
  registrada em review_requests.json e artifacts7dias, sem aprovação/publicação.
- Reavaliação breve: OpenCut README continua anunciando API/headless como futuros;
  EffectCraft última release v0.11.1, mesma PoC CPU já testada; VoiceStudio README
  documenta CPU com instalação de cerca de5GB, mas direitos dos pesos separados.
  Não demonstrado benefício para substituir Piper nem integrado novo motor.
- Commit de créditos/fallback: 23278094a3e308922a6fe41c3e37bbb4b09749d0.
  Actions 39464338721: 109 testes aprovados na nuvem; APIs sem credenciais opcionais;
  Wikimedia respondeu, zero cenas elegíveis. Alerta real atualizado em issues/2.
- Segunda auditoria independente: 109 testes, sem novo bloqueador nos créditos/gates.
- Correção adicional de concorrência motivada por evidência: criação 39464338701
  cancelada antes de começar, enquanto aquisição ocupava grupo comum. Coletor agora
  usa casasemesforco-media-acquisition: somente inbox/cache próprios, com rebase antes
  de push. Renderer/Runner mantêm serialização do estado de publicação.
- Primeiro commit 3.1 salvo: 874b68b9d7cd53ec56863878e8e05430a693afb7.
- Evidência real Actions https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/39463815894 :
  102 testes aprovados, PIXABAY_API_KEY_PRESENT=False, PEXELS_API_KEY_PRESENT=False.
  Wikimedia respondeu quatro buscas; zero candidatos elegíveis. Falha explícita
  NO_NEW_REVIEWABLE_MEDIA; histórico/cache persistidos mesmo após falha.
- Segunda busca local por palavras essenciais também respondeu, sem cenas elegíveis:
  resultados horizontais/baixa resolução, contexto inadequado ou licenças fora da
  lista aceita. Não baixar/produzir vídeos com esses resultados apenas para cumprir meta.
- Auditoria corrigida: orçamento distribuído entre provedores, créditos recuperados
  junto da mídia após expiração. Catálogo revisado aceita Pixabay/Commons, renderer
  preserva licença correta por fonte e inclui créditos na descrição. Gate de envio
  bloqueia remoção desses créditos. 109 testes locais passam.
- Novo coletor usa alerta de falhas existente, sem mensagens com tokens. Sem cron
  ativado para aquisição; dependeria de validar acesso/licença/qualidade e uso continuado.
- Situação: Pixabay implementado/testado com mocks, bloqueado por chave; Wikimedia
  comunicação real funcional, fornecimento de cenas adequadas não comprovado; Pexels
  preservado/opcional, chave ausente. Zero novos vídeos/publicações nesta etapa.
- Próximo bloqueio: adicionar PIXABAY_API_KEY nos secrets e testar aquisição real;
  depois revisar/promover cenas inéditas com roteiro contextual. Produção de 60/mês
  continua não comprovada. Nenhum gasto, compra ou serviço pago ativado.
- Base remota: 709c5782bb65b93a65ec7c1ab2eef3c5d04bc68e. Estado de 20/10:
  10h PUBLISH_COMPLETE confirmado pelo Buffer; 18h ainda SCHEDULED às 14h locais.
- Pixabay e Wikimedia adicionados como adaptadores oficiais; Pexels preservado.
  Ordem configurável por MEDIA_PROVIDER_ORDER: pixabay,wikimedia,pexels.
  Ausência de chave opcional não bloqueia Wikimedia; erro de um provedor tenta o próximo.
- Wikimedia: apenas vídeos verticais, CC0 1.0/CC BY 3.0 ou 4.0, autor identificado,
  licença individual e ausência de restrições declaradas. Créditos por arquivo em
  CREDITS.txt; resultados permanecem pendentes, sem promoção automática/publicação.
- 102 testes locais aprovados (88 anteriores + 14 novos). APIs externas e presença
  de PIXABAY_API_KEY ainda aguardam evidência do novo workflow. Nenhum novo MP4 produzido.
- Limites: até quatro consultas por fornecedor, quatro downloads totais e dois
  candidatos aceitos por execução; cache 24h, sem cron de coleta em massa.
- Próxima ação: conferir workflow de aquisição, corrigir auditoria e registrar
  respostas reais das APIs antes de classificar os novos fornecedores como operacionais.

## Continuação — aquisição oficial de cenas (20/10/2026)
- Commit inicial salvo: 277d9f342948758230b9e374ac9890dc4178b248.
- Prova real: https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/39462236910
  87 testes aprovados no GitHub; aquisição BLOQUEADA: PEXELS_API_KEY_PRESENT=False.
  Nenhuma mídia nova adquirida. Inserir chave diretamente nos secrets do GitHub.
- Auditoria independente identificou repetição de candidatos rejeitados, falta de
  recuperação após expiração e resumo de testes não isolado. Corrigidos: quarentena
  de rejeições por sete dias, recuperação --recover ID com SHA obrigatório e isolamento
  de GITHUB_STEP_SUMMARY. Regressão final local: 88 testes aprovados.
  Busca limitada à primeira página/15 resultados por tema, sem promessa de renovação
  infinita. Paginação e novos temas devem seguir a validação real da API.
- Base recuperada: fffb773518ffc5683c31e0c98a13ee14be41b43b. 77 testes anteriores preservados.
- Estado persistido confirma casasem-2026-10-20-1 como PUBLISH_COMPLETE, verificado pelo
  Buffer, permalink https://tiktok.com/@.casasemesforo/video/7698734823640239378 .
  Página pública não inspecionada independentemente nesta retomada. Slot das 18h
  continua SCHEDULED, não reenviado nem declarado publicado.
- Novo coletor oficial Pexels, filtros contextuais/verticais, cache 24h, autoria/licença,
  SHA/dHash, backlog limitado e inbox separado da publicação. 87 testes locais passam.
  Nenhum vídeo novo gerado por esta alteração; aquisição real ainda depende de verificar
  PEXELS_API_KEY no workflow. Não há aprovação automática de cenas por palavras-chave.
- Workflow manual/push de aquisição não interfere com renderer/runner; serialização
  compartilhada, metadados persistidos mesmo após falha, artifacts de revisão por 3 dias.
  Não há novo cron até validar credencial e operação real. Custo adicional contratado: R$0.
- OpenCut/Craft/VoiceStudio não reintegrados: preservar avaliações e PoCs abaixo.
  FFmpeg/Piper e os workflows históricos intencionalmente inertes foram preservados.
- Próximo passo: confirmar execução do coletor; se faltar chave, inseri-la diretamente
  no GitHub e executar o workflow. Revisar cenas adquiridas antes de promover ao catálogo.
  A renovação editorial automática e capacidade de 60 vídeos/mês seguem não comprovadas.

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
Resultado do segundo envio: Buffer confirmou SCHEDULED para casasem-2026-10-20-2 às18h Fortaleza, buffer_post_id6ad6c8e0e9c669def5e52725. Primeiro vídeo às10h mantémse agendado. Ambos publicly_verified=false: não anunciar publicação antes dos horários/confirmarpermalink. Runner de envio39355592204; fonte/roteiro novos e Release comprovados. Auditor independente não encontrou risco novo no workflow_run, mas ressalta que concorrência GitHub não garante preservar cada evento pendente; cron permanece recuperação. Rerun de criação39355508592 testa o encadeamento sem publicar novamente.

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
