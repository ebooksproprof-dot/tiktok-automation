# CasaSemEsforço 4.0 — auditoria de 22/10/2026

## Resultado: PARCIAL

Publicação automática via Buffer é comprovada para uma fila previamente aprovada.
Renovação editorial contínua de dois vídeos/dia não está comprovada. Os previews 4.0
não possuem aprovação para TikTok e não são adicionados à fila.

## Base e correções salvas

- Base: 8a3720c5c6e87e99a8cce3d4b3a69cd8316b23ac.
- 9bd56894b750e4ea83a92c056af85cf78df1821e: consentimento explícito no gate Buffer,
  histórico visual legado no gate e cobertura diária após reconciliação/persistência.
- 7a6d8fbadcab043fef2c013930096ab2d83dca72: decode estrito, detecção contínua de preto
  >=300ms e silêncio abaixo de -45dB por >=800ms.
- 8bca2cee603f861f89eb16ed3d3f934a4c6db8b9: lote isolado de três comparações e
  persistência em Release, sem API Buffer/TikTok nem modificação da fila.

O erro real histórico 39473684713 foi lido: teto conservador local do Buffer, não
HTTP429. A correção anterior já estava funcional. Não foram resetados contadores,
substituídas credenciais nem reenviadas publicações.

## Auditoria independente

Um agente separado, sem edição de arquivos, executou a suíte original (175 testes)
e revisou as correções. Suíte final: 192 testes aprovados, repetidos pelo auditor independente. Além da suíte:

- Probes de consentimento ausente, futuro e sem fuso: bloqueados.
- Fonte realmente presente no histórico legado: bloqueada pelo gate Buffer.
- Fila real: lacuna das18h detectada, bloqueio a partir de17h de Brasília.
- FFmpeg real: preto completo, preto ao final e silêncio completo detectados.
- Três MP4s legados passaram novo gate (16-2,17-1,17-2), volumes -16,6/-16/-17dB.
- Filtros dos previews extraídos do código e executados no FFmpeg: exit0.
- Salvamento corrigido após revisão:1–3 pares,120MB/lote,30assets/240MB acumulados,
  identidade por SHA, readback de digest, sem sobrescrita e descrição de lote parcial.
- Busca conservadora em textos versionados não encontrou padrões de tokens privados;
  isso não equivale a auditoria exaustiva de todos os segredos possíveis.

Testes aprovados não comprovam operação sustentada, retenção ou ausência absoluta de falhas.

## Publicações confirmadas pelo estado do provedor

| Slot Brasília | Evidência Buffer |
|---|---|
|20/10 10h|https://www.tiktok.com/@.casasemesforo/video/7698734823640239378|
|20/10 18h|https://www.tiktok.com/@.casasemesforo/video/7698857915008077063|
|21/10 10h|https://www.tiktok.com/@.casasemesforo/video/7699106108543241479|
|21/10 18h|https://www.tiktok.com/@.casasemesforo/video/7699229087600086293|
|22/10 10h|https://www.tiktok.com/@.casasemesforo/video/7699477167792753927|

Também há dois slots confirmados em18/10 e19/10. Trata-se de Buffer sent+automatic+
link da conta correta persistidos; páginas públicas não inspecionadas independentemente.
Na base recuperada não há posts apenas agendados restantes. O MP4 pontos-de-toque
para22/10 às18h está sem aprovação/consentimento/rota, portanto NÃO agendado.

## Ferramentas: o que realmente existe

|Ferramenta|Estado observado|Decisão|
|---|---|---|
|FFmpeg/Piper|Integrados ao diário e previews, CPU, pt_BR-faber-medium|Preservados; QA técnico ampliado|
|Pixabay|Aquisição real anterior e diária, autoria/licença/SHA/dHash persistidos|Preservado|
|Buffer/GitHub Actions|Envio e reconciliação real na nuvem|Preservados com gates adicionais|
|EffectCraft|PoC histórica v0.11.1,1080x1920/1s CPU0,86s; adaptador isolado|Não integrado ao diário; nenhum benchmark novo de superioridade|
|OpenCut|Pesquisado; README atual ainda anuncia API/headless futuros|Não adotado como backend obrigatório|
|FilmCraft|Pesquisado; CLI/headless disponível, alpha; sem PoC local comprovada|Não adotado sem benefício medido|
|PhotoCraft/VectorCraft|Pesquisados; ferramentas de assets/headless|Sem necessidade demonstrada para este lote|
|VoiceStudio|Não integrado; CPU suportada, direitos de modelos separados|Piper preservado; comparação não executada|
|Remotion|Nenhuma dependência ou teste de integração encontrado|Não adotado sem comparação|

VoiceStudio não foi descartado por falta de GPU. Supertonic-3 documenta CPU/ONNX,
português e aceite explícito OpenRAIL-M. Não foi aceito um novo contrato de pesos.
Nenhum componente experimental substituiu motores funcionais.

Fontes oficiais consultadas:
- https://github.com/OpenCut-app/OpenCut
- https://github.com/storytold/effectcraft
- https://github.com/storytold/filmcraft
- https://github.com/storytold/photocraft
- https://github.com/storytold/vectorcraft
- https://github.com/debpalash/VoiceStudio
- https://github.com/debpalash/VoiceStudio/blob/main/docs/engines/supertonic3.md
- https://www.remotion.dev/docs/license/pricing
- https://www.remotion.dev/docs/renderer/render-media

## Comparação audiovisual e limites

Referência externa exclusiva: @vault_shopp. Tentativa de acesso e buscas não recuperaram
vídeos reais verificáveis. Nenhuma frequência de cortes, métrica de retenção ou
semelhança medida ao perfil é alegada.

Previews4.0 usam três fontes inéditas no histórico:34818,140587,37325, com SHA/licença
e contexto revisados. Cenas ilustrativas de mãos/livros/secador, não demonstrações de
produtos específicos. Comparação usa o renderer anterior como baseline e acrescenta
faixa inicial de3s, recorte alternado±60px dentro de fonte4K e marcador no último quarto.
Legendas permanecem temporizadas por frases/chunks proporcionais, não alinhadas palavra
por palavra. Piper é estocástico: mesma voz/roteiro não significa áudio idêntico.

Não afirmar melhoria de naturalidade, retenção ou conversão. Não contar segmentos
contíguos com o mesmo enquadramento como cortes perceptíveis. Após as comparações, o helper composition_style.py foi integrado às novas renderizações
diárias: crop alternado apenas com margem suficiente, gancho limitado a duas linhas
e marcador final. DYNAMIC_STYLE=False congela o baseline dos previews. Os MP4s já
existentes são preservados; graphics_style identifica o estilo novo sem forçar rerender.
Três renders adicionais usaram o helper real, passaram QA e tiveram18quadros inspecionados.
Hooks atuais cabem na faixa; textos futuros excepcionalmente largos requerem revisão visual.

## Custos, capacidade e continuação

Nenhum serviço pago contratado. Runners públicos padrão, sem GPU paga nem fallback
comercial. Orçamento adicional observado:R$0, sem garantia de políticas futuras dos serviços.

Inbox possui10 fontes e ledger4drafts; última rodada gerou0. Fontes e templates são
finitos. A nova aquisição não promove automaticamente uma filmagem só por palavras-chave.

Próximos passos exatos:
1. Ler o relatório e assets da Release validation-v4-2026-10-22; não rerenderizar por padrão.
2. Decidir quais previews merecem aprovação editorial; os três continuam não aprovados.
3. Revisar separadamente pontos-de-toque e escolher um slot futuro antes de qualquer envio.
4. Ampliar cenas realmente pertinentes e roteiros revistos; não reciclar fontes já publicadas.
5. Preservar composition_style.py já integrado; não repetir instalação/benchmark de motores sem necessidade.
6. Observar dias consecutivos de criação+aprovação+agendamento+sent antes de declarar2/dia autônomos.

## Evidência final dos três vídeos na nuvem

Workflow39829264202 terminou com sucesso (render+salvamento).
Release: https://github.com/ebooksproprof-dot/tiktok-automation/releases/tag/validation-v4-2026-10-22
Hashes, links e relatório completo em automation/validation-4.0-evidence.json.

|Prova|Duração cloud|Shots/enquadramentos|Tempo base→variante|
|---|---:|---:|---:|
|Sabonete|16,167s|6|19,29→19,07s|
|Livros|15,794s|8|21,25→21,15s|
|Secador|16,479s|7|27,39→28,60s|

Todos1080x1920, decodificação completa, zero intervalos pretos≥0,3s e silêncios≥0,8s.
Relatório/contact sheets cloud foram baixados, SHA comparado ao digest da Release e
18quadros inspecionados. Três variantes e três baselines persistidos. Nenhum enviado
para TikTok. Provas com cenas ilustrativas, sem alegação de equivalência visual ao Vault.

## Verificação cloud da integração final

Commit a3a236e80475d1713521822b35c8d0332ca3ea87: workflow diário39830366236
concluído com sucesso,192 testes na nuvem. NEW_VIDEO_COUNT=0, pois os MP4s já existentes
foram preservados; essa execução não é alegada como geração de novos vídeos nem publicação.
A reprodução adicional dos previews39830366403 foi iniciada pelo push; os três MP4s
e links já entregáveis pertencem ao lote concluído39829264202 e não dependem dessa repetição.
