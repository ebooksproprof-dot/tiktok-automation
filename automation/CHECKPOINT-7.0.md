# CasaSemEsforço 7.0 — estoque implantado; produção manual ainda necessária

Data: 28/10/2026. Repositório original preservado. Base recuperada: `12228ab58de977254694566769f39364b60b17e1`. Lidos checkpoints 5.2 e 6.0 (incluindo continuações); não encontrado checkpoint 6.1 separado. Regressão inicial: 281 testes aprovados.

## Entrega efetiva

- `video_stock.py`: estado durável em GitHub Contents com CAS por SHA, identidade fixa, hash de arquivo/roteiro, metadados, histórico, slots 10h/18h São Paulo, reserva antes da chamada externa, UNKNOWN sem reenvio e recuperação de slots nunca tentados.
- `stock_import.py`: detecção de MP4 + JSON na Release pública `stock-inbox`, downloads limitados, validação FFmpeg, comparação com histórico legado, autorização/revisão explícita vinculada ao hash. CLI prepara o JSON sem Work. Nenhum MP4 grande no histórico Git.
- `stock_publish.py`: API oficial Buffer existente, controle de dez agendamentos, no máximo dois envios por execução, cota compartilhada e persistida antes de HTTP, consulta posterior de publicação. Só confirmação com status enviado e permalink exato permite PUBLISHED. Conteúdo comercial retido por falta de disclosure nativo verificado.
- `stock_runner.py` e workflow `video-stock.yml`: seis verificações diárias, importação separada da produção, reserva antecipada e reconciliação. Mesmo lock dos workflows existentes; nenhum renderer, conta ou vínculo substituído.
- Gerador Symphony permanece desabilitado. Avatar `7616458821397659655`, Keren, pt-BR e referência `@vault_shopp` preservados. Declaração de identidade não é prova audiovisual.

## Evidência real em nuvem

Execução [40731631743](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40731631743), job `122969674977`, completou com sucesso em 28/10/2026. Código da execução: `e1985bc9cd9e170aec390bdf419a920c5571a9c7`.

Resultados operacionais persistidos em `automation/video_stock.json`:

```json
{"cloud_readback":true,"stale_writer_rejected":true,"channel_verified":true,"submitted":0,"available":0,"refill_needed":14,"generation_enabled":false}
```

Foi feita uma chamada real de consulta do canal Buffer usando o Secret já existente; validou serviço TikTok, conta `.casasemesforo`, conexão ativa, não pausada e publicação automática (sem modo lembrete). O nome técnico já usado pelo projeto foi preservado; não houve troca de perfil para outro identificador inferido do nome de marca.

Release `stock-inbox` criada de fato e consultada; ainda vazia. A fila foi criada, gravada e relida por outra instância via API. O probe separado `stock_cloud_probe.json` comprovou rejeição de escritor com SHA antigo. Nenhuma requisição de criação de post foi enviada nesta prova.

Na primeira execução cloud: 325 testes descobertos, 320 aprovados e 5 testes opcionais antigos de legendas pulados por ausência de Pillow/fontes. Localmente: todos os 325 passaram, sem skips. Commit `26a16d087c3ba0831d1bcb2413039b2d92ed9bf6` adicionou essas dependências ao workflow. A repetição [40732150395](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40732150395), job `122971015818`, completou com sucesso: **325 testes passaram em 2,530 segundos, sem skips**. Persistência/releitura, rejeição de escritor antigo e conexão real Buffer foram confirmadas novamente. Estoque continuou zero e nenhum post foi criado. Este é o resultado cloud final da implementação.

Metricool: leitura real confirmou um agendamento anterior `408851997`, 28/10 às 18h BRT, PENDING e autoPublish=true. Foi preservado e seu horário entra na exclusão de slots legados. Não é publicação confirmada. A conta não expôs plano por esse conector. O histórico anterior contém 12 registros com evidência pública; esta missão não gerou nova publicação Symphony nem usa esses registros para alegar sucesso novo.

## Matriz de testes solicitada

| Teste | Evidência executada / limite |
|---|---|
| 1. Importação MP4 | FFmpeg real sobre arquivo sintético; fluxo de download remoto simulado. Sem MP4 Symphony real recebido. |
| 2. Arquivos novos | Testes de pares, arquivos incompletos e nova execução; consulta real da entrada vazia. |
| 3. Formato | MP4 real correto e rejeição de dimensões incorretas. |
| 4. Duração | MP4 real curto rejeitado; política herdada 15–28 s. |
| 5. Áudio | MP4 real sem áudio rejeitado; validação AAC/volume/silêncio. |
| 6. Duplicação | Hash e roteiro normalizado, inclusive histórico legado. |
| 7. Inserção na fila | Testes candidato → fila → preflight; fila cloud inicializada vazia. |
| 8. Reinício | Store local reaberto e releitura real cloud por outra instância. |
| 9. Horários | 10h/18h São Paulo, UTC e conflitos legados; testes simulados. |
| 10. Concorrência | Dois escritores locais/CAS; stale SHA rejeitado de verdade no GitHub. |
| 11. Falhas | Checkpoint, timeout e interrupção simulados; sem perda de intenção durável. |
| 12. Retentativas | UNKNOWN/FAILED já tentados não voltam a envio; importação incompleta pode ser tentada novamente. |
| 13. Publicados | Estado terminal e histórico conservados; teste de simulação. |
| 14. Publicação única | Mocks verificam no máximo um create e reserva anterior; sem publicação real nova. |
| 15. Cotas | Orçamento Buffer persistido e headers reais consultados; testes de janela/Retry-After. |
| 16. Esgotamento | Simulação de quotas Buffer e dez agendamentos remotos. Não se esgotaram créditos reais. |
| 17. Renovação | Simulação de liberação de janela Buffer; renovação Symphony não implementada. |
| 18. Sem Work | Runner GitHub executou código remotamente; continuidade mensal ainda não observada. |
| 19. Nuvem | GitHub Actions + Releases + estado remoto comprovados na execução acima. |
| 20. Custos | Repo público, runner padrão e nenhum plano pago contratado; sem auditoria de fatura/garantia futura. |
| 21. TikTok real | Conexão Buffer TikTok validada; sem novo envio ao TikTok. |
| 22. Confirmação | Lógica testada com mocks e legado preservado; nova confirmação real indisponível. |

## Situação final por indicador

| Indicador | Situação | Justificativa |
|---|---|---|
| Fila persistente implementada | Sim | CAS, leitura/escrita e conflito cloud comprovados. |
| Importação funcionando | Parcial | Código e MP4 sintético testados; entrada cloud vazia. |
| Estoque funcionando | Parcial | Armazenamento criado; zero vídeos reais, faltam 14 para objetivo inicial. |
| Agendamento funcionando | Parcial | Slots e adaptador testados, canal real válido; nenhum novo vídeo do estoque agendado. |
| Publicação automática confirmada | Não | Nenhuma publicação nova do estoque nesta missão. |
| Capacidade mensal comprovada | Não | Free Buffer permite reabastecer dez slots; 60/mês ainda não observados. |
| Symphony por API disponível | Não | Para esta conta, autorização, allowlist e custo não comprovados. |
| Voz Keren configurada | Parcial | Exigida nos metadados; ID API e áudio real não validados. |
| Avatar oficial configurado | Parcial | ID fixo exigido; sem novo MP4 para comprovar uso. |
| Geração automática em lotes | Não | Desabilitada por falta de acesso oficial comprovado a R$0. |
| Controle de limites | Parcial | Buffer implementado e testado; nenhum saldo Symphony inventado. |
| Retomada automática de geração | Não | Não há gerador habilitado; só janelas Buffer retomam. |
| Funciona sem computador ligado | Parcial | Importação/agendamento rodam cloud; geração e envio inicial do lote são manuais. |
| Funciona sem Work | Parcial | Workflow cloud e procedimento de importação independentes do Work; fluxo completo aguarda mídia. |
| Custo adicional R$0 confirmado | Parcial | Nenhuma contratação/cobrança habilitada; arquitetura pública gratuita atual, sem geração API comprovada. |
| Testes realizados | Sim | 325 locais, probe GitHub e leitura real Buffer; limites explicitados acima. |
| Commit de implementação | Sim | `f80705a` núcleo; `e1985bc` integração; `26a16d0` dependências de regressão cloud. |

## Continuidade sem recomeçar

1. Seguir [STOCK-7.0.md](STOCK-7.0.md): gerar/revisar lote no navegador normal, criar fichas pelo comando e enviar os pares à [Release de entrada](https://github.com/ebooksproprof-dot/tiktok-automation/releases/tag/stock-inbox).
2. Primeiro usar uma dica doméstica realmente não comercial para comprovar o ciclo; declarar corretamente conteúdo afiliado, que permanece retido até suporte oficial de disclosure.
3. Acompanhar `remote_id`, consulta posterior e link público antes de afirmar publicação. Não limpar UNKNOWN para forçar repetição.
4. Meta inicial 14 válidos; ideal 14–28; abaixo de 7 alerta no resumo da execução. Nenhuma repetição para completar horários.
5. Só adicionar geração Symphony após token/permissão/allowlist, ID Keren, catálogo avatar, limites e termos de R$0 oficialmente confirmados. Não tentar controlar Generate pelo navegador Work.

Auditoria em [AUDIT-7.0.md](AUDIT-7.0.md); fontes e limites de planos em [SOURCE-EVIDENCE-7.0.md](SOURCE-EVIDENCE-7.0.md).
