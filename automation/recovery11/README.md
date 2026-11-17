# CasaSemEsforço — evidências da recuperação 11.0

**Resultado parcial comprovado: dois vídeos Wan novos aprovados e agendados no Buffer. Nenhuma publicação nova está confirmada: os horários ainda são futuros. A meta contínua de dois vídeos/dia a R$0 não foi demonstrada.**

## 1. Causas da paralisação

- Aquisição: banco de 24 consultas, palavras exigidas nas tags e navegação limitada à terceira página repetiam buscas esgotadas. A API Pixabay respondia, mas os candidatos elegíveis eram conhecidos. Pexels não tinha credencial.
- Licença: a política Pixabay de 07/11 expirou após sete dias; a renovação dependia exclusivamente de navegador e dava timeout. Termos e documentação oficiais foram novamente obtidos em 17/11, por HTTPS no Codex Cloud. **O teste posterior no runner GitHub recebeu HTTP 403:** a renovação automática nesse ambiente ainda depende de acesso externo. Não foi removido o vencimento para contornar a verificação de direitos.
- Wan: o revisor SmolVLM chamou toalhas de “white books”/“rolled-up books” no episódio 2, slot 1. A correção vale somente para o SHA inspecionado, preservando o laudo original e as amostras. Livros continuam não sendo evidência de toalhas.
- Concorrência: testes de configuração disputavam o bloqueio de produção e cancelavam jobs pendentes. Além disso, quatro reservas convencionais impediam montar cenas Wan completas.
- Revisão: descrições truncadas do fundo também omitiam os utensílios. A pergunta passou a focar os objetos, com uma segunda análise neutra e limitada; os critérios de aceitação e os bloqueios de segurança foram preservados.

## 2. Arquivos corrigidos

`media_acquisition.py`, `media_providers.py`, `source_license.py`, `pixabay_license_policy.json`, `autonomous_production.py`, `semantic_review.py`, `experimental81/wan104.py`, `experimental81/wan104_finish.py`, `wan104_source_reviews.json`, `buffer_runner.py`, `caption_layout.py`, testes e workflows de produção/publicação. Foi acrescentada uma auditoria somente de consultas. O publicador Buffer existente foi preservado.

Há 126 consultas compostas, temas intercalados, cache de 24h e até quatro requisições por provedor/run. Páginas esgotadas avançam sem fazer um crawl. Commons agora chega ao produtor, exigindo arquivo/autor/licença comercial exatos e créditos. “Iron” industrial e tecido de costura não são demonstrações domésticas. Revisões Wan são persistidas por SHA; uma cena rejeitada é arquivada e substituída com limite, preservando as demais e todas as reservas de quota.

## 3. Histórico e commits

Checkpoint recuperável anterior às mudanças: [`checkpoint/mission11-20261117`, `e589b34`](https://github.com/ebooksproprof-dot/tiktok-automation/tree/checkpoint/mission11-20261117). O checkout inicial em `d052222` foi atualizado por fast-forward. Inventários, Releases e histórico foram mantidos; nenhuma credencial ou cobrança foi alterada. Lista de commits: [commits.json](commits.json).

Houve regressões intermediárias de paginação manual e de dependência Pillow num teste, posteriormente corrigidas. A versão final passou na suíte. Um glifo cosmético de quebra de linha em renders anteriores motivou composição de linhas separadas; prova FFmpeg em [caption-lines-smoke.png](caption-lines-smoke.png). Os dois vídeos Wan já agendados foram preservados, inclusive esse detalhe cosmético.

## 4. Testes A–G

**423 testes locais aprovados**, sem skips: [tests.json](tests.json). Incluem simulação de dez dias, consumo/reposição, quotas, indisponibilidade temporária, reinício, horários de Brasília, originalidade, substituição de cena e recuperação de vaga após cancelamento conclusivo. Simulação não prova dez dias de disponibilidade real.

- **A:** aquisição real encontrou e baixou novos candidatos, inclusive nos runs [43996569346](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/43996569346) e [43999899794](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/43999899794). Candidatos não equivalem a estoque aprovado.
- **B/C:** episódio 2 reprocessado com as três cenas preservadas; episódio 3 gerado nesta sessão, com duas aprovações preservadas durante a substituição isolada da terceira cena. Dois MP4s de 15s, 1080×1920, Kokoro `pf_dora`, legendas, SHA conferido, sem congelamento, tela preta ou silêncio prolongado. Provas: [episódio 2](wan-episode2-mp4-validation.json), [episódio 3](wan-episode3-mp4-validation.json). Run final Wan: [44000487401](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/44000487401).
- **D/E/G:** regressões de estoque vazio, prioridade/overflow, falha de aquisição sem bloquear produção, vagas 10h/18h BRT, processos reiniciados e ausência de duplicação.
- **F:** publicador executado, agendamentos lidos de volta do provedor; ainda não são publicações. Os runs [44000894739](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/44000894739) e [44001255436](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/44001255436) falharam depois na cobertura histórica de 16/11, sem apagar os horários perdidos.

## 5–8. Estoque, fontes e próximos horários

**Estoque aprovado: 2; meta: 4; reposição necessária: 2.**

| Vídeo | BRT | Buffer ID | Estado confirmado |
|---|---|---|---|
| `casasem-2026-11-17-1` | 17/11 10h | `6afbb82f4b26315855b516cc` | `scheduled` |
| `casasem-2026-11-17-2` | 17/11 18h | `6afbb8564b26315855b51cc0` | `scheduled` |

O episódio Wan seguinte está em coleta, sem clipes pendentes. A avaliação somente de leitura do planejador encontrou quatro pedidos/240s reservados, retornando `WAIT_FREE_QUOTA` até **18/11/2026 01:49:56 UTC**, sem nova chamada GPU: [quota-planner.json](quota-planner.json). Isso não é saldo real retornado pelo provedor.

A rota licenciada gerou dois renders, mas a revisão audiovisual final detectou fricção de mãos sem comprovação de lavagem com água/sabonete, enquanto as narrações mencionavam pia ou enxágue. **Ambos foram reprovados e cancelados pelo Buffer**, sem publicação: `6afbbd594b26315855b6a0dc` e `6afbbdf2df36f4d825627b29`. Arquivos e laudos foram preservados. O critério foi corrigido e caches positivos são reavaliados pela política atual. A [validação técnica licenciada](licensed-mp4-validation.json) não equivale a aceitação editorial. Vagas só podem ser recuperadas após exclusão conclusiva, com ID novo; estados incertos continuam bloqueando reutilização.

## 9. Publicações efetivamente confirmadas

Última publicação continua sendo **13/11 às 18h**, enviada pelo Buffer às 18h03. Reprodução pública reconfirmada sem login em 17/11, com legenda correspondente e reprodução avançando: [vídeo 7707764157134703879](https://www.tiktok.com/@.casasemesforo/video/7707764157134703879), [prova](public-playback-20261117.json). Isso não conta como publicação nova nesta missão. Nenhum horário perdido foi preenchido retrospectivamente.

## 10. Capacidade gratuita e classificação

Repositório público, runners Linux padrão, CPU para montagem/Kokoro/revisão e Hugging Face Free verificado. Nenhum faturamento ou serviço pago foi ativado. O controle conservador reserva 60s/clipe e retém 3% de 300s estimados/24h: até quatro clipes por janela, compartilhados com falhas/substituições. Um vídeo Wan exige três clipes. O consumo real GPU não foi informado. Dois vídeos Wan por dia não estão demonstrados; o complemento licenciado precisa produzir material aprovado.

| Estado | Componente / limite |
|---|---|
| **CORRIGIDO E TESTADO** | Aquisição, gates, continuidade simulada, montagem Wan e dois agendamentos reais. |
| **OPERACIONAL COM PUBLICAÇÃO CONFIRMADA** | Buffer no canal correto e publicação histórica de 13/11 reconfirmada; não os novos vídeos. |
| **IMPLEMENTADO MAS AINDA NÃO COMPROVADO** | Publicação dos novos vídeos, reposição licenciada aprovada e frequência sustentável de dois/dia. |
| **BLOQUEADO POR DEPENDÊNCIA EXTERNA** | Pexels sem chave (opcional); renovação HTTPS de licença no runner retornando 403. Novas tentativas Wan também aguardam o controle de quota, sem reset ou cobrança. |

A política Pixabay atual tem validade de sete dias a partir da recuperação de 17/11; o fallback por navegador teve timeouts anteriormente. Não há evidência de renovação automática bem-sucedida no runner. Os workflows de coleta, produção, monitoramento e confirmação continuam agendados em nuvem, inclusive verificações após 10h/18h. A frequência desejada permanece não comprovada. Auditoria final [44004824483](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/44004824483), concluída: leitura do Buffer em 17/11 às 02:47:46 UTC confirmou exatamente os dois Wan agendados, sem os dois cancelados na fila pendente. O teste HTTPS voltou a receber 403. Snapshot com timestamps e dados do provedor: [snapshot.json](snapshot.json).
