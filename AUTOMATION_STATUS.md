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
Checkpoint adicional: auditor independente repetiu 58 testes após as correções sem novo bloqueador técnico. Workflow 39353810347 concluído com sucesso. Estoque atual: oito roteiros elegíveis usando apenas seis fontes inéditas; não equivale a oito vídeos visualmente exclusivos. Stage-v3-proof transfere somente o primeiro preview da execução 39353432805, exige SHA exato e read-back de Release, cria slot de 20/10 às 10h Fortaleza sem aprovação. Não reexecutar após ocupar slot.

1. Ler este arquivo, queue.json, state.json e visual_history.json diretamente do main atual.
2. Executar python -m unittest discover -s automation/tests -q.
3. Não reintroduzir fontes já usadas, não reenviar IDs existentes e não sobrepor fila/estado com cópias locais antigas.
4. Previews: python automation/preview_batch.py; não publica. EffectCraft opcional usa binário oficial fixado e adaptador separado. Piper/FFmpeg continuam padrão.
