# Auditoria 10.2 — publicação e reposição verificadas

Evidência final de 7 de novembro de 2026. Recuperação da main inicial `e75ada1a8d4271eb3f7c238aa25b06b7caae453c`, que contém o checkpoint `6806065`; trabalho preservado na branch `codex/casasem-10-2`, alterações integradas por fast-forward na main. O snapshot de estado abaixo foi lido de uma única revisão imutável: `f7865139a5f4c33a47b5842c28a53889905423c8`.

## Publicações públicas

- Post anterior: Buffer `6aed59747b7e47e8f40a39a7`; TikTok [7704915298847132980](https://www.tiktok.com/@.casasemesforo/video/7704915298847132980), conta `.casasemesforo`. Metadados públicos: 06/11/2026 01:46:30 BRT. Reconciliação real somente de leitura: [run 42337189009](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42337189009). Reprodução pública confirmada; nenhum reenvio.
- Novo post desta missão: Buffer `6aeead2a229bf05daf2ad3a0`; TikTok [7705290911931960596](https://www.tiktok.com/@.casasemesforo/video/7705290911931960596). Metadados públicos: 07/11/2026 02:04:01 BRT. `sentAt` Buffer: 05:05:43.639 UTC; horários são evidências diferentes e foram preservados. Última reconciliação: [run 42350134666](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42350134666), `PUBLISH_COMPLETE`, reprodução pública, legenda correspondente e avanço do vídeo sem login. O MP4 original possui 18,619 s, 1080×1920, SHA `3027bb2dc7640b3c8ba27722c47433c7ab73b4a6aed8ecb4a54adae284a09a14`.

O primeiro retorno `SENDING` resultou em falha visível na confirmação; a reconciliação posterior consultou o mesmo ID. Nunca se tratou envio ou agendamento como prova de publicação pública.

## Estoque auditado

| ID interno | Horário com fuso | Estado | Buffer ID | Duração | SHA-256 (prefixo) |
|---|---|---|---|---|---|
| casasem-2026-11-07-1 | 2026-11-07T02:03:51-03:00 | PUBLISH_COMPLETE | 6aeead2a229bf05daf2ad3a0 | 18.619 s | 3027bb2dc7640b3c |
| casasem-2026-11-07-2 | 2026-11-07T10:00:00-03:00 | SCHEDULED | 6aeeba3c229bf05daf2e0527 | 18.0 s | cdfa9ac88f8866fe |
| casasem-2026-11-08-1 | 2026-11-08T10:00:00-03:00 | SCHEDULED | 6aeec550d6bbae6fa16c63f7 | 19.2 s | 448ec4a6ae33f368 |
| casasem-2026-11-07-3 | 2026-11-07T18:00:00-03:00 | SCHEDULED | 6aeecd8f004e4879a73ca9a7 | 18.011 s | 6bec86bb91286daf |
| casasem-2026-11-08-2 | 2026-11-08T18:00:00-03:00 | SCHEDULED | 6aeecec4004e4879a73d1634 | 17.913 s | c44701af820b64ff |

Quatro vídeos prontos e aceitos pelo Buffer, cobrindo 07/11 e 08/11 às 10h/18h BRT. Eles ainda não estão publicados. O teste extra da madrugada só deixou de ocupar uma reserva recorrente depois de prova pública, escopo do proprietário e hash confirmado. O ID interno 3 não habilita um terceiro horário diário normal.

## Ciclo real e recuperação

1. Novo vídeo criado pelo workflow existente [42339330707](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42339330707), publicado e confirmado.
2. Reposição automática licenciada: [42342940314](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42342940314) e [42344976190](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42344976190), com um vídeo válido cada.
3. Recuperação de estoque parcial: monitor [42347927467](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42347927467) disparou produção. A produção sem material válido [42347970977](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42347970977) falhou explicitamente; filmagem congelada não foi liberada.
4. Aquisição oficial [42348967448](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42348967448) → produção automática por `workflow_run` [42349031125](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42349031125) → publicador [42349698545](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42349698545): um vídeo válido; outro candidato rejeitado por congelamento.
5. Aquisição oficial [42349777554](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42349777554) → produção automática [42349828692](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42349828692) → publicador [42350065198](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42350065198): quarta posição preenchida. Monitor [42350121522](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42350121522) confirmou `ready=4` e `STOCK_TARGET_MET`.

Os disparos iniciais de teste foram autorizados nesta sessão; as passagens aquisição → produção → publicador → monitor aconteceram pelos gatilhos existentes na nuvem. A manutenção foi limitada por recibos persistentes por etapa/janela UTC de seis horas. Resposta de disparo incerta continua retida, sem repetição cega. O consumo já confirmado possui recibo; não gera outro envio do mesmo vídeo.

A rota generativa permaneceu indisponível para uso comercial durante todos esses ciclos. O fallback real adquiriu novas filmagens Pixabay, conferiu licença vinculada aos bytes, novidade visual/textual, roteiro, Kokoro `pf_dora` pt-BR CPU, legendas medidas, renderização e armazenamento em Releases. Não houve nova geração GPU nem ativação de serviço pago.

## Auditoria separada da produção

[Snapshot somente de leitura](mission102-evidence/continuity-final-audit.json): contagem independente da fila, IDs únicos, hashes dos MP4 baixados dos Releases, licenças vinculadas aos hashes das fontes e comparação perceptual entre as fontes utilizadas. Zero chamadas de criação ou disparo nesse auditor. Validação FFmpeg separada dos arquivos finais: decode, H.264/AAC, 1080×1920, duração, alinhamento dos fluxos, volume, silêncio, preto e congelamento. Todos os cinco vídeos desta missão passaram. Contatos visuais dos quatro itens de reserva foram inspecionados nesta sessão; os registros originais de revisão automática não foram reescritos como revisão humana.

Última suíte após as alterações de código: **377 testes aprovados**; os mesmos testes obrigatórios também passaram nos workflows reais. Incluem respostas incertas sem reenvio, checkpoint antes de createPost/dispatch, limites gratuitos, conflitos CAS de históricos >1MB, replay de fontes em outra resolução, recuperação de classificação somente com evidência, voz principal/fallback e congelamento com FFmpeg real. Mudanças posteriores apenas de auditoria/documentação não repetem essa suíte indiscriminadamente.

## Licenças e IA preservada

Pixabay: [política oficial e resumo vinculados](pixabay_license_policy.json), API oficial por ID/autor/arquivo e SHA dos bytes em `quality.source_rights` e `production_state.json`. Filmagens usadas: 34772, 163116, 34091, 33220, 27178, 34817 e 34730. A montagem é adaptada e narrada, com créditos públicos; não se afirma exclusividade das filmagens nem endosso de produto.

Kokoro/pf_dora e dependências: [auditoria de componentes](MISSION-9.1-LICENSES.md); verificador CPU SmolVLM fixado por revisão, Apache-2.0, sem código remoto. [Reconsulta atual da rota Wan](mission102-evidence/ai-route-current.json): o upstream Wan é Apache-2.0, mas os pesos convertidos/compilados e a LoRA exatos usados nos seis clipes não têm a cadeia comercial histórica completa demonstrada. Todos os seis hashes continuam preservados e `commercial_license_clearance=false`.

[Quinto clipe](mission102-evidence/ai-clips-current.json): bytes diferentes da referência histórica Pexels 9473227, porém semelhança perceptual excessiva; distâncias mínimas 4, 9, 8, 5, 9, com três de cinco amostras dentro do limiar 8. Não há evidência para liberar o clipe como falso positivo. Gate mantido; arquivo e histórico preservados.

## Operação recorrente e custo

[Workflows e execuções reais](mission102-evidence/continuity-workflows.json): aquisição, produção, publicador, estoque e coletor IA ativos. O monitor teve execução real por `schedule` em 07/11; os ciclos subsequentes por `workflow_run` foram exercitados. Slots são calculados com `America/Sao_Paulo`. Agendamentos de reposição: 03:20/08:20/16:20/20:20; aquisição 07:30/15:30; monitor seis vezes/dia. Publicador prepara antes dos slots e reconcilia depois.

Há atraso real na criação de execuções por cron do GitHub. O diário de 06:20 UTC ainda não apareceu na consulta final desta auditoria; não se declara que esse cron novo já disparou. A janela Buffer de 52 horas permite executar os quatro agendamentos sem depender de o runner acordar no minuto da publicação. MP4s ficam em Releases mensais imutáveis, sem depender de computador pessoal, preservando limites locais de 20 MB/arquivo e 64 arquivos/mês. Históricos grandes são verificados contra o SHA do blob/CAS.

[Limites oficiais reconsultados](mission102-evidence/current-free-limits.json): Buffer Free, dez agendamentos simultâneos por canal e 1.000 requisições por canal/mês; política local de 900/30 dias. Reserva atual ocupa quatro posições. GitHub declara runners padrão gratuitos em repositórios públicos; este repositório é público e usa `ubuntu-latest`. Cache observado <1 GB, abaixo do limite gratuito existente. Nenhuma assinatura, infraestrutura ou crédito pago ativado. Limites e backoff continuam bloqueando tentativas, em vez de cobrar ou repetir.

A prova atual demonstra publicação pública, aquisição recorrente, quatro reposições reais, agenda de dois dias e recuperação sem duplicação. **Não demonstra sessenta vídeos originais por mês nem fornecimento contínuo ilimitado.** Mantida a meta de 10h/18h enquanto houver material novo aprovado e cota gratuita; escassez falha visivelmente e aciona recuperação limitada. A rota Wan comercial continua bloqueada. Não se declara continuidade irrestrita ou duas publicações diárias sustentáveis por um período ainda não observado.

[Ambiente efetivamente aplicado](mission102-evidence/runtime-current.json): versão publicada identificada, revisão observada igual à configurada, observações atuais e rede `unrestricted/enforced`. GitHub fetch/push/dispatch, Pixabay autenticado, Hugging Face e Buffer funcionaram. Um 403 em endpoint administrativo sem escopo não é falta de rede; páginas/arquivos públicos recusados pelo serviço foram tratados sem trocar permissões comerciais nem expor credenciais. Nenhuma republicação manual do ambiente foi solicitada.
