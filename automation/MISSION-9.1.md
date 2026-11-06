# CasaSemEsforço 9.1 — 06/11/2026

**Uma publicação nova real confirmada. Sistema ainda PARCIAL; não declarar CASASEMESFORÇO OPERACIONAL.**

## Resultado novo

- TikTok: https://www.tiktok.com/@.casasemesforo/video/7704915298847132980
- Post do projeto: `casasem-2026-11-06-1`; Buffer `6aed59747b7e47e8f40a39a7`.
- Buffer confirmou `sent` + publicação automática + timestamp válido + permalink do perfil exato. Estado `PUBLISH_COMPLETE`, `publicly_verified=true`, persistido na main pelo Actions. São 17 registros históricos verificados, dos quais **um é novo nesta missão**.
- [Renderização, preservação e fila](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42162321026): 341 testes e montagem real na nuvem.
- [Aceite Buffer](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42163112491): 342 testes, um novo envio, estado SCHEDULED; não foi tratado como publicado naquele momento.
- [Reexecução idempotente](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42164108196): 344 testes, zero chamadas Buffer e zero novos envios.
- [Confirmação real](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42164621731): 344 testes, somente reconciliação do ID existente; total verificado aumentou de 16 para 17.

O primeiro teste foi solicitado para poucos minutos adiante, fora dos slots regulares, com exceção explícita registrada na fila. Continua consumindo uma das duas reservas máximas do dia. Agendamentos recorrentes seguem 10h/18h America/Sao_Paulo.

## Arquivo publicado e direitos

[MP4 preservado](https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-2026-11/casasem-2026-11-06-1-38174601f1dcf86f.mp4): SHA-256 `38174601f1dcf86f7af67f6fadce118870dcc60339a6e53d06329dc7f8b7d372`, 2.187.388 bytes, 15,166667s, 1080×1920, H.264/AAC, áudio -15,3dB. Zero intervalos pretos ≥300ms ou silêncios ≥800ms; diferença final AV 0,029667s. Narração Kokoro pf_dora pt-BR CPU; legendas medidas por trecho. Decode e hash reconferidos após download independente do Release, contact sheet final revisada. Não foi feita escuta humana nem certificação de alinhamento fonético.

Os seis clipes de IA foram conferidos por SHA e preservados, mas a cadeia comercial dos pesos convertidos/AOTI e suas revisões na geração não foi comprovada. Nenhuma flag foi liberada sem evidência. Em conformidade com o fallback autorizado, usamos filmagem **real** gratuita já existente no inbox: Pixabay 34821, jaumeps99, licença individual/termo oficial verificados. Roteiro e narração são contextuais, os créditos permanecem na descrição; a montagem não alega que essa filmagem seja gerada por IA. Zero novas solicitações de geração de clipes, zero créditos novos de IA.

Detalhes: [licenças](MISSION-9.1-LICENSES.md), [auditoria técnica](AUDIT-9.1.md), [estado confirmado](mission91-evidence/publication-confirmed.json).

## Três bloqueios examinados

1. **Rede resolvida:** esta nova tarefa usa versão `cecfgver_6aed221edb8c819aa43725243923e272`, diferente da retomada anterior; unrestricted/enforced e observações atuais. Fetch/push/dispatch e consultas às fontes oficiais funcionaram. 403 ao listar secrets/permissões do repositório é permissão específica da integração, não internet bloqueada. Buffer autenticou e publicou pelo secret existente no Actions; não se pediu token nem republicação do ambiente.
2. **Licenças AI continuam pendentes; substituição concluída:** código do Space revela Wan2.2 base, conversões cbensimon, LoRA Wan2.1 extraída por Kijai e pacote AOTI. Apache-2.0 do upstream não foi usado como prova automática da cadeia histórica exata. Os seis continuam `commercial_license_clearance=false`; a peça publicada possui outra fonte gratuita verificada.
3. **Quinto clipe excluído da peça pública:** não é duplicação binária. Tem semelhança excessiva com a própria referência Pexels 9473227 já histórica; cinco distâncias mínimas 4/8/7/5/6. A inspeção visual confirma a mesma cena geral. Nenhuma evidência de erro de inventário ou falso positivo suficiente para suspender o gate. Arquivo/histórico preservados; nenhuma montagem pública usou esse clipe.

## Continuidade e custos

Workflows de aquisição, criação, coletor e publicação estão ativos na main; execução e armazenamento não dependem de PC pessoal ligado. Preservados: crons, Releases, limites gratuitos, deduplicação e recuperação de resultados incertos. O coletor agora falha se a etapa obrigatória apenas aguarda material/cota e verifica licença antes de renderizar. O publicador verifica a primeira passagem por dueAt sem adiar desnecessariamente 30min e oferece confirmação explícita somente por leitura (`confirm_post_id`), sem createPost e respeitando os orçamentos.

**Não há vídeos aprovados ainda não submetidos no estado conferido. Os próximos slots 10h/18h não estão cobertos.** A criação existente não recebeu aprovação artificial de novos materiais, e os seis clipes bloqueados não contam como estoque. Não se demonstrou reposição autônoma de cenas originais licenciadas; por isso a frequência contínua sustentável ainda não está validada. Uma publicação isolada não comprova 2/dia. A capacidade de novas publicações coberta pelo estoque já aprovado restante é **zero**; há uma publicação isolada comprovada, sem frequência recorrente comprovada.

- Buffer Free: dez posts simultâneos por canal, reabastecíveis; 1.000 chamadas/canal/30d. Controle local de 900/30d mantido. Esses limites, isoladamente, não impedem 2/dia.
- Metricool Free: 20 posts/mês, insuficientes para 60; nenhuma nova publicação agendada por ele. Consulta auxiliar de analytics ainda não mostrava o vídeo recém-publicado; não foi usada para negar ou confirmar a publicação.
- ZeroGPU Free: 300s/dia; estimativa de 45s/clipe implica 540s para dois vídeos de 30s. Dois vídeos de 15s estimam 270s antes de rejeições/falhas, sem garantia. Nenhuma cota foi reiniciada/ampliada.
- GitHub: repositório público, runners padrão, nenhum serviço pago ativado; orçamento de armazenamento existente preservado, inclusive o limite de seis coleções mensais. Operação indefinida exige política de arquivo/reposição, não remoção silenciosa de histórico.

**Custo adicional contratado: R$0.** Nenhuma compra, assinatura, GPU paga ou nova rota de publicação foi ativada.

## Pendência concreta

Para avançar de PARCIAL a operação recorrente: disponibilizar material novo/licenciado e uma reposição editorial efetivamente validada para os próximos slots, ou obter comprovação aplicável aos derivados/revisões dos clipes AI antes de liberá-los. O local de inspeção é `automation/experimental81/auto_inventory.json` na branch `feature/ai-video-hybrid-30s` e os repositórios exatos listados no relatório de licenças. A publicação já foi autorizada e realizada; não falta nova autorização TikTok/Buffer ou publicação do ambiente. Não reenviar o ID desta prova.
