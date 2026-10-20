## Bloqueio final confirmado e recuperação
- Runner39473319061 encontrou o teto conservador de60 chamadas Buffer/24h.
  Nenhum vídeo novo enviado; fila de21/10 preservada. Não aumentar/resetar orçamento.
- Pré-checagem agora reserva chamadas suficientes para todo o ciclo antes de consultar
  o canal. Evita gastar saldo que não permite concluir envio/read-back.
-142 testes locais passam após essa correção. Retentativa pelos workflows agendados;
  aceite Buffer de21/10 ainda NÃO confirmado. O post20/10 às18h já estava agendado.
- Três MP4s cloud decodificados integralmente: zero intervalos pretos>=0,3s e zero
  silêncios>=0,8s abaixo de-45dB. Não equivale a avaliação humana da naturalidade.

# Auditoria CasaSemEsforço 3.4 — 20/10/2026

## Evidência real e limites
- Base recuperada: 79b957d, posterior ao checkpoint fe684f2.
- Autenticação Pixabay real: run 39467916880 attempt 2; secret presente,
  quatro respostas API novas persistidas. Zero fontes verticais elegíveis naquela tentativa.
- Correção permite fonte Pixabay >=1080x1920, razão até2, recorte vertical nativo
  sem ampliação. Fontes horizontais HD continuam recusadas. Crop exige revisão.
- Runs39471657588,39471667432,39472349382,39472519142: oito fontes medidas na nuvem.
  Não equivale a oito fontes aprovadas nem oito vídeos.
- Prova cloud39472349389: três MP4s; artifact12288495146 baixado e hashes conferidos.
  Pia17,233s/8.306.414bytes/-17,1dB; louça17,836s/3.578.274bytes/-16,3dB;
  leitura16,6s/6.383.411bytes/-16,4dB. Todos1080x1920/H264/AAC.
- Contact sheets finais inspecionadas: crop, texto legível, fontes diferentes.
  Uma composição local anterior foi substituída por inadequação contextual.
  São cenas ilustrativas, não demonstrações exatas de todas as etapas narradas.
  Legendas por frases/estimativa proporcional, não alinhamento fonema/palavra.
  Áudio verificado por decodificação/nível; não houve avaliação humana independente
  da naturalidade da voz. Retenção e conversão não medidas.
- 141 testes finais locais; auditor independente repetiu141. Mocks não contam
  como aquisição, geração real ou publicação. Duas auditorias encontraram/corrigiram
  contact sheet deformada e condição success() implícita no staging do workflow.

## Componentes
|Componente|Estado/evidência|
|---|---|
|Pixabay|FUNCIONAL para autenticação, busca e aquisição real; seleção semântica PARCIAL|
|Pexels|BLOQUEADO para nova API por chave ausente; fontes históricas preservadas|
|Wikimedia|PARCIAL: consultas reais, sem fonte elegível adquirida|
|Renovação editorial|PARCIAL:2 rascunhos reais persistidos,6 modelos factuais finitos; não60/mês|
|Seleção visual|PARCIAL:tags e revisão humana/agente de composição; sem aprovação automática|
|Duplicidade|FUNCIONAL:URL/SHA/5dHashes/histórico; sem garantia semântica universal|
|Piper|FUNCIONAL CPU/pt-BR:3 provas cloud; modelo fixado por SHA|
|FFmpeg|FUNCIONAL:3 provas cloud, sem loops; montagem usa fonte ilustrativa por vídeo|
|OpenCut|NÃO TESTADO nesta etapa; avaliação anterior preservada, não integrado|
|Craft|EffectCraft PoC anterior preservada; demais NÃO TESTADOS nesta etapa|
|VoiceStudio|NÃO TESTADO/integração não adotada; não substituiu Piper|
|Actions|FUNCIONAL:coleta07h30/criação08h30 Fortaleza, runner e persistência; cron sujeito a atraso|
|Releases|FUNCIONAL histórico; staging novo exige read-back/digest,64assets/mês e6coleções|
|Buffer|FUNCIONAL histórico e envio via rota validada; agendado não é publicado|
|Metricool|PARCIAL:conta .casasemesforo confirmada via API; fila20–23/10 vazia, sem conflito; operação diária via Actions não demonstrada|
|TikTok|Confirmação anterior das10h via Buffer;18h20/10 ainda futura. API direta não comprovada|
|Segurança|Chave não lida/configurada; logs sanitizados,origens permitidas,aprovação por SHA|
|Custos|Sem serviço pago contratado; runner público padrão e CPU. Sem garantia ilimitada de cotas|
|Persistência|Git:estado/fila/inbox/cache/drafts/provas; MP4s de prova artifacts7dias e ZIP entregue|
|Recuperação|Falhas transitórias1h versus rejeições7dias; uploads ambíguos bloqueados; relatório parcial preservado|

## Limitações que impedem declarar operação definitiva
1. Drafts não são aprovados/renderizados/publicados automaticamente. Exigem seleção contextual.
2. Catálogo factual6 modelos, consultas4 temas/página1 e histórico120 itens são finitos.
3. Originais >8MiB só têm miniaturas/metadados nos artifacts; recuperação depende da origem.
4. Armazenamento Releases possui teto; não é política permanente de arquivo.
5. Ainda falta demonstrar30 dias/60 vídeos distintos e publicados sem intervenção.
6. Intenção de upload é arquivo local até commit final. Cancelamento abrupto pode
   deixar Release órfã; sem publicação automática ou reenvio de estado ambíguo.
7. Fontes ilustrativas e montagem simples são avanço funcional, não evidência de alta retenção.

## Próxima ação indispensável
Confirmar os novos estados Buffer e, depois, ampliar o estoque factual/visual e
implementar revisão editorial contínua validada. Não remover gates para aparentar2/dia.

Staging real39473106379 concluído: Releases com digest/read-back para21/10 às10h e18h; fila aprovada persistida. Não equivale a aceite Buffer ou publicação.
