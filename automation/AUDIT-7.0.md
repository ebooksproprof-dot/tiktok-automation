# Auditoria independente da missão 7.0

Data: 2026-10-28. Revisão por agente diferente dos autores de importação/publicação.
Base recuperada `12228ab`; primeiro commit remoto do núcleo informado pelo executor:
`f80705a1d4fd1bf8c6fcb821f4f92f65c5f1601a`.

## Escopo e evidência

Leitura independente de `stock_import.py`, `stock_publish.py`, `stock_runner.py`,
`video-stock.yml`, armazenamento CAS, interfaces legadas, estado real existente e
testes. Execução independente de `python -m unittest discover -s automation/tests -v`:
**325 testes passaram em 3,352 segundos**, sem falhas. Inclui geração/decodificação de
MP4 sintético por FFmpeg e rejeição de duração, formato e ausência de áudio.
Essa execução é local; não é teste real Symphony, Buffer ou publicação TikTok.
Nenhum vídeo de teste foi enviado a uma rede social pela auditoria.

## Defeitos encontrados e corrigidos antes da entrega

1. O publicador rejeitava qualquer timestamp legado em objeto, inclusive publicações
   históricas. O estado real possuía três desses objetos. Correção: normalização por
   `daily_coverage.stamp`, com fuso explícito, e comparação somente com a reserva
   candidata. Teste cobre data histórica e conflito real de horário.
2. A interface de importação não preservava inicialmente todos os campos exigidos
   pelo publicador. Foram mantidos campos explícitos de revisão, legenda, conteúdo
   comercial, origem e consentimento; o importador associa a autorização declarada
   à data de revisão. As declarações não são certificação automática de identidade.
3. Horários locais vencidos sem tentativa externa mantinham vídeos presos. Agora
   somente itens sem tentativa e sem ID remoto retornam à reserva futura. Histórico
   `MISSED_SLOT` mantém o horário anterior. Itens tentados/UNKNOWN não são reenviados.
4. Conteúdo comercial cuja divulgação não é suportada pelo adaptador verificado
   consumia lugares úteis. Agora permanece no estoque, retido, sem reservar horário.
   O relatório distingue estoque total, publicável e comercial retido.

## Salvaguardas verificadas

- SHA do GitHub como compare-and-swap para o arquivo de estoque; conflito impede
  continuação da tentativa externa. Checkpoint não depende do diretório temporário.
- `PUBLISHING` persistido remotamente antes de `createPost`; reserva correspondente
  no estado legado antes do envio; falha posterior conserva bloqueio de duplicação.
- Respostas incertas viram UNKNOWN; não existe redefinição automática de tentativas.
- Confirmação usa leitura posterior, estado enviado, identificador e permalink da
  conta exata, por meio da lógica existente de `buffer_runner.record_remote`.
- Hash do vídeo e roteiro normalizado consultados no estoque e histórico legado.
- Arquivos de entrada restritos à Release e ao repositório oficial, limite de tamanho,
  validação efetiva FFmpeg e hash vinculado ao manifesto.
- Todos os workflows operacionais novos compartilham `casasemesforco-state` com os
  existentes; o novo workflow não faz git push de uma cópia obsoleta do estoque.
- Nenhum endpoint de crédito Symphony ou autorização gratuita foi inventado.

## Limites que permanecem

- Não houve MP4 Symphony real disponível para esta auditoria; voz Keren, avatar,
  sincronização perceptual e qualidade criativa dependem da revisão do proprietário.
- Testes mock de resposta Buffer não demonstram publicação real. O checkpoint final
  deve informar separadamente qualquer verificação de conta/execução cloud realizada
  pelo executor e sua evidência.
- Releases pertencem ao proprietário e podem ser apagadas/substituídas. Não apagar
  nem substituir arquivos aprovados/agendados. O hash é conferido novamente antes
  da submissão, mas o publicador não controla uma alteração feita pelo proprietário
  depois dessa conferência e antes do download do provedor.
- O esquema de metadados cresce com o histórico para conservar deduplicação. Excesso
  dos limites de leitura da API do GitHub falha fechado; não há promessa de escala
  indefinida ou retenção imune a exclusão pelo administrador.
- Conteúdo afiliado/comercial é retido enquanto não houver integração oficial de
  divulgação comercial verificada. Isso reduz o estoque publicável legitimamente.
- Cron GitHub pode atrasar. Agendamento remoto antecipado reduz essa dependência,
  mas não oferece SLA de execução no segundo exato.
- Não foram contratados serviços, habilitados planos pagos nem simulada aprovação
  da API Symphony. R$0 de operação contínua depende dos serviços e limites reais.

Conclusão: núcleo e integrações locais passaram pelos testes disponíveis, com
recuperação conservadora e preservação do legado. Publicação real de um novo vídeo
Symphony e operação mensal sustentada continuam exigindo evidência externa própria.

## Verificação cloud posterior pelo executor

GitHub Actions run [40732150395](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40732150395)
concluiu com sucesso: 325 testes em 2,530 s, sem skips. O runner executou prova real
de gravação/releitura e rejeição CAS no GitHub; consulta real Buffer confirmou canal
correto e conexão automática. Estoque 0, envios 0. A primeira execução tinha cinco
testes opcionais pulados; Pillow/fontes foram instalados e a segunda eliminou os skips.
Esta nota registra evidências coletadas pelo executor, não publicação auditada no TikTok.
