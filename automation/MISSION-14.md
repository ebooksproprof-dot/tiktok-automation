# CasaSemEsforço 14.0 — implementação e limites

A missão continua o HEAD `441df70c9f3ed3f8c51f349bb2d7409b28e68588`; fila,
recibos, cotas e inventário não foram reconstruídos. O checkpoint local é
`checkpoint/mission14-before-441df70`.

## Voz e direitos

Modelo **ResembleAI/Chatterbox-Multilingual-pt-br**, revisão
`b3952f18bc2eaa72b9bd7c17d2c4653bcad4770d`, Chatterbox Multilingual V3 Single
Language Pack, locale pt-BR, language ID `pt`. Não é o modelo de Portugal.
T3 `t3_pt_br.safetensors` (SHA256 publicado no model card verificado), decoder
`s3gen_v3.pt`, tokenizer expandido 2454/8194. Companion `ve.pt` e `conds.pt`
vêm da revisão `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18` do modelo base.
O código oficial específico do Space é fixado em
`9e515821e826e207cd617a0fdd0223899ed108ea`, com SHA256 de cada arquivo Python
em `chatterbox_v3_sources.json`. O pacote genérico chatterbox-tts 0.1.7 não é
usado como se carregasse automaticamente esses pesos V3.

**Identidade feminina: pendente.** `voice_identity.json` mantém o bloqueio.
Não há referência própria/autorizada no checkout. Não foram baixados ou
clonados os exemplos públicos `pt_br_f2.wav`. O teste técnico usa apenas os
condicionamentos internos distribuídos com o checkpoint MIT e não comprova
uma voz feminina aprovada. Nenhum resultado desse teste entra no estoque.

Para ativar: registrar titular, autorização expressa para síntese comercial,
prova dos direitos, hash de WAV mono PCM16 de 5–12 segundos e aprovação auditiva
da identidade em `voice_identity.json`; guardar a referência em armazenamento
privado persistente. A integração aceita o secret criptografado Actions
`CHATTERBOX_REFERENCE_WAV_B64`, materializado com umask 077 em RUNNER_TEMP,
verificado pelo hash e nunca incluído em artifacts/Releases/Git. Nenhum secret
foi criado ou lido nesta missão. Não basta alterar somente o status para APPROVED.

O modelo e o Chatterbox principal declaram **MIT**. Há componentes derivados
do CosyVoice sob **Apache-2.0**, inclusive no decoder; portanto não se afirma
que todos os componentes sejam MIT. Dependências principais: PyTorch/torchaudio
(BSD), Transformers/diffusers/safetensors/huggingface-hub (Apache-2.0), librosa
(ISC), NumPy (BSD), Perth (MIT), S3Tokenizer (Apache-2.0). Manter avisos dos
respectivos pacotes. FFmpeg com libx264 no runner é uma distribuição GPL;
Pillow e fontes DejaVu têm licenças próprias permissivas. A licença dos pesos
não concede direitos sobre gravações de terceiros. Evidência e fontes:

- [Model card brasileiro](https://huggingface.co/ResembleAI/Chatterbox-Multilingual-pt-br/blob/b3952f18bc2eaa72b9bd7c17d2c4653bcad4770d/README.md)
- [Código específico oficial](https://huggingface.co/spaces/ResembleAI/Chatterbox-Multilingual-TTS-pt-br/tree/9e515821e826e207cd617a0fdd0223899ed108ea)
- [MIT upstream](https://github.com/resemble-ai/chatterbox/blob/ab55923c27757c90cfcc407baa57dc25a7d25217/LICENSE)

## Arquitetura sem cobrança

Somente CPU de runner padrão para repositório público; sem GPU paga, Inference
Endpoints ou serviço tarifado. Chatterbox roda em venv separado do SmolVLM:
PyTorch/torchaudio 2.8.0+cpu, Transformers 4.46.3 e dependências fixadas em
`requirements-chatterbox-v3.txt`. O revisor visual continua com seu ambiente
atual. ASR faster-whisper 1.2.1 é isolado em outra venv. O revisor visual é
liberado antes de carregar TTS. O benchmark original revelou pico alto de RAM;
o carregamento passa a atribuir tensors diretamente e usar mmap do decoder.
O relatório de medição real distingue os dois carregadores.

A API oficial do Space foi investigada como alternativa legítima, sem assumir
SLA de produção. A documentação HF permite API de Spaces, com filas, cota e
autenticação conforme a conta. Isso não equivale a capacidade garantida grátis.
Nenhuma fila, conta, IP ou cota foi contornada. A rota de produção escolhida é
CPU; o Space não é fallback silencioso. A referência licenciada continua
obrigatória em qualquer rota.

Fluxo: roteiro → Chatterbox → PCM16 WAV → cache durável → normalização
(-16 LUFS, -1.5 dBTP, tempo limitado a 0.90–1.10) → ASR PT → legendas medidas
→ revisão visual → MP4. Não há `apad`, silêncio de preenchimento nem corte da
fala para ajustar 30 segundos. Roteiros incompatíveis são retidos para edição.
ASR exige concordância integral das palavras normalizadas; divergências retêm o áudio, sem alegar medir
naturalidade. Identidade exige revisão perceptiva separada.

Cada fala é cacheada por texto, modelo, referência e parâmetros estáveis.
`narration_store.py` persiste somente falas geradas na Release
`narration-v14-cache` antes de FFmpeg. Respostas incertas são reconciliadas pelo
nome único, sem sobrescrever ativos; manifesto verifica SHA256. Restauração
não trata erro de rede/autenticação como cache vazio. A referência nunca entra
nesse cache público. Nenhum cache de voz de produção foi criado sem autorização.

## Tela cheia e legendas

Causa observada no arquivo histórico: MP4 já era 1080×1920 / 9:16 / SAR 1:1 /
30fps. A política `preserve_full` colocava a ação em janela de até 720 pixels
sobre fundo desfocado. `before-ffprobe.json` e `before.jpg` documentam o exemplo.
Não foi provada uma transformação adicional do Buffer/TikTok nessa missão.

Novos compositores usam escala proporcional/crop, SAR 1:1, 30fps, H.264,
yuv420p, AAC, remoção de metadados e faststart. Rejeitam crop que preserve
menos de 80% da fonte e ampliação acima de 1.5×. Não adotam fundo desfocado
como tela cheia nem deformam objetos. Revisão semântica do crop permanece
obrigatória. Validação verifica DAR, SAR, rotação, FPS, átomos moov/mdat,
decode completo e bordas pretas incorporadas em cinco amostras.

Legendas medidas limitadas a 744px, texto entre x=132 e 876, duas linhas a
partir de y=1080. Esse espaço reserva margens para ações laterais e descrição.
Foi consultado e baixado o template oficial In-Feed LTR; trata-se de uma
referência conservadora para orgânico, não de promessa de UI idêntica em todo
aparelho. A própria TikTok informa variação por formato, legenda e dispositivo.

- [TikTok: safe zones e downloads oficiais](https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads?lang=en)
- [Template oficial consultado](https://lf-tt4b.tiktokcdn.com/obj/i18nblog/tt4b_cms/en-US/5jqet0ab9qci-10e7f5Vig4uhAscNP8XPB0.zip)
- [HF: API de Spaces e limites](https://huggingface.co/docs/hub/spaces-api-endpoints)

## Wan, estoque, originalidade e continuidade

O coletor Wan existente e seu ledger de cotas continuam. Episódios novos pedem
seis cenas distintas de aproximadamente cinco segundos, preservando as duas
cenas e as sete entradas do banco atual. Identidades/hash/proveniência e estado
dos pedidos não são apagados. Checks antigos de 15s ficam legíveis para
reconciliar histórico, mas a nova barreira de publicação exige missão 14/30s.
Os atuais 480×832 NÃO passam na exigência de resolução para tela cheia. A rota
Wan gratuita precisa de fonte melhor ou complemento licenciado aprovado antes
de gerar estoque 1080p aceitável. Não se ampliou artificialmente esses drafts.
Seis roteiros do catálogo foram desenvolvidos para conteúdo maior; a duração
final sempre vem do áudio real, não da contagem de palavras.

Deduplicação persistente continua comparando instruções sem ordem, sinônimos,
metadados editoriais e fingerprints visuais multicrop. O cooldown agora rejeita
mesmo problema OU mesma solução e ganchos quase iguais, além do hash. Testes
usam roteiros dos recibos reais anteriores e sua inversão de frases. Não há
repostagem para preencher calendário.

Teto inicial: 3 por sete dias móveis, intervalo mínimo de 48h, 10h/18h BRT,
reserva até 31 dias e no máximo um novo vídeo/run por padrão. É teto de
qualidade, não frequência demonstrada. O monitor de entrega audita reservas
reais; não acusa ausência de dois posts obrigatórios por dia. Reposição
existente conserva CAS, lease, intents antes de chamadas, tratamento de
resposta incerta e confirmação pública independente. ASR/identidade/qualidade
pendentes bloqueiam novas publicações, mas não apagam recibos ou progresso.

## Verificação e operação

```
python -m unittest discover -s automation/tests -v
python automation/chatterbox_benchmark.py
```

`mission14-proof.yml` executa benchmark CPU real em runner padrão e preserva
WAV/JSON de prova. Nunca publica. Testes de serviços usam mocks e a simulação
v14 cobre oito semanas com cotas, indisponibilidade, retomada e cadência
limitada. Simulações antigas de 2/dia são regressões históricas explicitamente
isoladas; não são evidência de produção atual. Testes FFmpeg geram e decodificam
arquivos reais, incluindo rejeição de barras pretas.

Veja `mission14-evidence/REPORT.md` para resultados finais, links, tempos,
commits, estoque e limitações. Não declarar a missão operacional sem esses
resultados e uma referência feminina autorizada e aprovada.
