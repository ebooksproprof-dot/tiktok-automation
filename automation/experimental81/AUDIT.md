# Auditoria independente — CasaSemEsforço 8.1

Data: 02/11/2026. Auditor diferente dos autores do gerador e compositor.
Escopo: módulos `hf_probe.py`, `render.py`, `quality.py`, `cloud_run.py`,
`persist.py`, configuração experimental e workflow `ai-video-experimental81.yml`.
Base recuperada pelo executor: `ed8566b9ffb5dc554fb967119dd64d49b5865d9e`.
Branch: `feature/ai-video-hybrid-30s`. Esta auditoria não autoriza merge/publicação.

## Testes independentes executados

`python -m unittest discover -s automation/tests -v` executado pelo auditor:
**358 testes passaram em 10,446 segundos, sem skips**, após as correções do compositor
e inclusão do adaptador/testes Wan. A rodada anterior tinha352 testes aprovados.
Inclui arquivos MP4 sintéticos reais com FFmpeg/ffprobe; resposta de gerador bem-sucedida
nos testes unitários é simulada e não constitui geração IA real. Execução local,
não substitui a evidência GitHub Actions que o executor deve registrar no checkpoint.

Leitura posterior incluiu `wan_probe.py`: exige callback de reserva remota quando
executado em GitHub Actions, rejeita falta do ledger antes de qualquer chamada de
geração, valida o esquema publicado e mantém falhas sem reenvio automático. O modo
CLI permanece desabilitado por padrão e requer confirmação de direitos da referência.

`git diff --name-only` permaneceu vazio para arquivos rastreados da base: não foram
alterados validador antigo, fila, estado, Buffer, agendamentos ou workflows de produção.
Os arquivos novos são isolados na experiência e nos testes. O workflow novo restringe
a branch experimental, não possui cron nem credenciais TikTok/Buffer e força
`AI_VIDEO_EXPERIMENTAL_ENABLED=false`. O workflow não chama publicadores.

## Defeitos encontrados e correções verificadas

1. **Identidade do render dependia do caminho local.** O mesmo conteúdo restaurado
   em outro runner poderia receber outro nome. Corrigido: caminhos de mídia/narração
   são removidos do manifesto usado para o hash; permanece identidade por conteúdo,
   parâmetros, roteiro e revisão do renderer. Teste cobre independência do caminho.
2. **Legendas partidas proporcionalmente ao tamanho do texto.** Isso não comprova
   alinhamento real de palavras. Corrigido para uma legenda por frase, usando duração
   efetivamente medida da fala. É sincronização por frase, não forced alignment.
3. **Concorrência/gravação de relatório.** Compositor passou a serializar pelo lock
   local e a trocar o JSON por rename atômico. MP4 parcial não é considerado saída
   válida; reexecução confere hash e decodificação antes de reutilizar resultado.
4. **Classificação de timeout.** A palavra “token” em uma exceção podia classificar
   timeout como autenticação. Corrigido: tipo TimeoutError é verificado primeiro.
   O bloqueio UNKNOWN já era seguro; a categoria agora preserva melhor a causa.

## Salvaguardas confirmadas

- O perfil30s é novo e opt-in; `profile=legacy` delega ao validador antigo inalterado.
- Validação verifica duração30s±0,15s,1080×1920,H.264,yuv420p,AAC,tamanho,alinhamento
  de streams, decodificação integral, quadros pretos e silêncio não revisado.
- A/B/C são calculados com duração disponível real. Falta de IA não é ocultada:
  `REFERENCE_ONLY` declara zero segundos IA e exibe isso no vídeo.
- Não há `-stream_loop`, repetição de intervalos nem extensão artificial de clipes.
  Hash duplicado é rejeitado. Segmentos de uma mesma fonte usam intervalos disjuntos.
- Metadados AI exigem modelo, evidência e revisão visual declarada. Isso não prova
  sozinho fidelidade anatômica, produto ou licença de entradas de terceiros.
- Cliente HF usa `token=False`, sem conta faturável; não solicita upgrade ou compra.
  Descobre a API publicada e verifica o esquema antes de chamar. Intenção local
  é gravada antes de submit e resultados incertos/failed não são reenviados automaticamente.
- Não existe conversão fictícia entre minutos GPU e segundos úteis. Campos não
  expostos pelo serviço permanecem desconhecidos.
- `persist.py` usa Release experimental separada, nome com hash, readback do digest,
  tamanho e URL após upload. Não grava nos estoques/filas usados para publicação.
- Runner é Ubuntu padrão público. Nenhuma dependência de GPU paga, WebGL, navegador
  ou software Craft adicional foi introduzida.

## EffectCraft: teste novo, opcional, separado

O auditor baixou o binário oficial **0.11.1** e conferiu o SHA já fixado no projeto:
`fe78d8df0221d06d5519e02f3c382c1dfcd3241217a0e46644b4598a215b8d61`.
Não houve instalação de outro produto Craft nem aceite de plano pago.

Com `gpu_acceleration=false`, o fixture gráfico original produziu MP4 **1,0s,
1080×1920,H.264,30quadros,45.091bytes**, sem áudio, em **1,522s** de tempo de processo.
Decodificação integral passou. O quadro15 foi inspecionado visualmente: nome
CasaSemEsforço, subtítulo “Uma casa mais prática” e barra verde renderizaram legíveis.
Isso é uma prova atual de execução CPU/headless e tipografia básica, não integração
nem avaliação de um vídeo30s com filmagens/narração. Nenhum benefício mensurável
para substituir FFmpeg foi demonstrado. **FFmpeg permanece principal**.

Código reproduzível: `effectcraft_smoke.py`. Evidência:
`evidence/effectcraft81-evidence.json`. MP4 produzido localmente:
`tmp/experimental81/effectcraft-smoke/effectcraft81-headless.mp4`.
O executor deve persistir o binário de saída antes de usá-lo como entregável.

```sh
python automation/experimental81/effectcraft_smoke.py --binary /caminho/effectcraft-cli --output tmp/experimental81/effectcraft-smoke
```

## Limitações e itens que não devem ser alegados como concluídos

O auditor conferiu separadamente o arquivo real Wan do teste C:
SHA `631e17ed61f5a53a2c07b248be01992ce9ff7704efdda2ecbf40498db0ee0239`,
5,0625s,480×832,16fps,H.264,414.469bytes,sem áudio. A imagem de contato com cinco
amostras mantém torneira/azulejos coerentes e luva/pano reconhecíveis, mas mostra
borramento significativo de bordas e pouca definição fina. Essa inspeção amostral
não comprova anatomia/física quadro a quadro nem qualidade profissional. O arquivo
real é distinto dos testes sintéticos; a tentativa LTX A retornou falha do servidor.
Tempo de parede68,683s do Wan não é consumo GPU ou cota, que não foram expostos.

- O ledger HF atual precisa ser preservado/restaurado entre runners. Uma pasta
  temporária nova não oferece idempotência global. O workflow entregue mantém a
  geração desabilitada; habilitação cloud futura exige checkpoint remoto ANTES
  da chamada para evitar repetição se o runner morrer antes de publicar artifacts.
- A publicação experimental permanece proibida. Resultado técnico não é autorização
  editorial; os campos `approved` e `publication_enabled` continuam falsos.
- Filmar novamente, recodificar ou fornecer fontes com URLs diferentes pode escapar
  à detecção exata de duplicação. Não foi implementada certificação de originalidade
  perceptual universal. Fontes/intervalos revisados continuam necessários.
- Kokoro PT-BR existente é identificado explicitamente; não é voz Keren e não deve
  ser apresentado como tal. Nenhuma seleção do Symphony de produção foi alterada.
- Fontes externas podem indisponibilizar URLs; hashes divergentes interrompem o
  uso. Não há promessa de serviço gratuito permanente nem capacidade14/semana.
- Teste EffectCraft não comprova acabamento profissional. Testes unitários de API
  não comprovam geração; detalhes reais das tentativas HF estão no relatório próprio.

Conclusão: implementação **experimental/parcial**, com isolamento verificável e
correções de reinício/legendas. Classificar geração real e capacidade exclusivamente
pelos resultados externos efetivamente obtidos, separando-os da prova do compositor.
