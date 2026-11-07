# Auditoria CasaSemEsforço 10.4 — 07/11/2026

## Publicação real

[Vídeo de IA no TikTok](https://www.tiktok.com/@.casasemesforo/video/7705426078436838676):
ID público `7705426078436838676`, Buffer `6aef299f229bf05daf51f11e`, conta
`.casasemesforo`, ID interno `casasem-2026-11-07-wan104`.
Criação pública: **10:48:31 BRT / 13:48:31 UTC**. O `sentAt` Buffer posterior,
13:50:13.458 UTC, foi preservado como evidência distinta.

[Geração real](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42376012055),
[montagem real](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42377548608),
[confirmação de leitura](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42378917911).
A primeira consulta encontrou `SENDING` e falhou corretamente; a segunda
reconciliou o **mesmo ID**, sem novo envio. Estado `PUBLISH_COMPLETE`, com
reprodução pública sem autenticação. Uma sessão separada da submissão confirmou
avanço do vídeo, legenda, conta e rótulo IA às 13:54:55 UTC.
[Provas JSON](mission104-evidence/publication.json) e
[captura pública](mission104-evidence/public-ai-proof.png).

MP4: **15,000 s / 1080×1920 / H.264 + AAC**, SHA-256
`fd9a43b7150e4743e380e60dd88c2dd30ba13bed4a597d7da0adb5f74fea1da4`.
[Original preservado](https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-2026-11/casasem-2026-11-07-wan104-fd9a43b7150e4743.mp4).
Três cenas efetivamente T2V, zero filmagens de banco. Kokoro ONNX 0.6.1 CPU,
**pf_dora pt-br**, fala e legendas medidas; identificação IA na imagem, legenda
e parâmetro Buffer. A interface mostrou “Creator labeled as AI-generated”;
o campo JSON `aigcLabel` era nulo e não foi apresentado como confirmação.

## Licenças e componentes exatos

Revisões completas, fontes oficiais e hashes LFS:
[licensing.json](mission104-evidence/licensing.json).

| Componente | Evidência e decisão |
|---|---|
| [Wan-AI/Wan2.2-I2V-A14B-Diffusers](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B-Diffusers) | Revisão `596658fd…`, Apache-2.0 explícita. Modelo principal autorizado sob suas condições. |
| LoRA `Kijai/WanVideo_comfy/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank128_bf16.safetensors` | LFS `5c324ada09cfa447844f5d9a57240463a515de38270ef40c7513d74be3e64e72`. Sem declaração explícita dessa extração. [Pergunta específica #133](https://huggingface.co/Kijai/WanVideo_comfy/discussions/133) sem resposta. Apache upstream não comprova sozinho os direitos dessa extração. |
| `cbensimon/Wan2.2-I2V-A14B-bf16-Diffusers` | Revisão `1f424b0c…`, licença não declarada. Shards BF16 não são os mesmos bytes dos shards FP32 oficiais; não foi alegada equivalência integral sem prova. |
| `cbensimon/WanTransformer3DModel-sm120-cu130-raa` | Revisão `81e794f8…`. Pacote AOTI de 1.800.335 bytes inspecionado: kernels/código compilado, sem pesos aprendidos; licença não declarada. Excluído da nova rota. |
| [lightx2v/Wan2.2-Distill-Loras](https://huggingface.co/lightx2v/Wan2.2-Distill-Loras) | Revisão `57adea58…`, Apache-2.0. Cabeçalhos high/low I2V rank64 analisados; compatibilidade estrutural. O Space original fixa os loaders e não admite substituição por parâmetro. Nenhum teste A14B de execução alegado. |
| [FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers](https://huggingface.co/FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers/blob/3e187042a324f6f5fb68fd22110a78725253de8f/README.md) | Revisão `3e187042…`, Apache-2.0, derivado oficial TI2V 5B. **Modelo realmente usado no vídeo novo**, distinto do A14B antigo. |
| [Wan-AI/Wan2.2-TI2V-5B-Diffusers](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers) | Revisão `b8fff731…`, Apache-2.0 explícita. Backbone declarado do FastWan. |
| [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | Revisão `f3ff3571…`, Apache-2.0. Voz principal pf_dora preservada. |

Space executado: `Upsampler/wan-2-2-5b-video`, revisão
`1b51b45ea9dffb46932592cdc4d9572af9577189`, carregando transformer,
text encoder e VAE do FastWan 5B. Não usa a cadeia Kijai/cbensimon/AOTI.
Código e runtime públicos conferidos antes das chamadas; modelo/revisão
registrados em cada resultado. Servidor de terceiros não fornece atestação
criptográfica de memória: a prova é código/runtime públicos e recibos reais.

[Cartão oficial](mission104-evidence/fastwan-model-card.md) e
[termos oficiais consultados](mission104-evidence/current-service-terms-summary.json).
Não há redistribuição de pesos pelo aplicativo. Licenças/avisos upstream e
alterações devem acompanhar eventual redistribuição de pesos/código; permissão
comercial não substitui direitos de terceiros. Cenas novas usam descrições
originais, sem imagens de referência, marcas ou endosso comercial.

A narração usou os arquivos int8 e voices do Release `model-files-v1.1` do
mantenedor kokoro-onnx, conferidos por tamanho e SHA:
[prova dos assets exatos](mission104-evidence/voice-exact-assets.json).
Pesos/voz Apache-2.0, wrapper MIT; auditoria das dependências, FFmpeg e fontes
preservada em [MISSION-9.1-LICENSES.md](MISSION-9.1-LICENSES.md). Encoder upstream
Google UMT5-XXL também declara Apache-2.0; SmolVLM usa revisão fixa Apache-2.0.

## Seis clipes anteriores

Branch inicial `3f8d609843d9691ecd16e392958e4a3062e798ad`. O inventário antigo
permaneceu **idêntico byte a byte**; apenas o ledger compartilhado recebeu novos
checkpoints. Seis MP4 de 5,0625 s com SHA, integridade e movimento verificados:
[resultados](mission104-evidence/old-clips-verified.json).

Referências Pexels `9472849`, `9462884`, `9473227`: três vídeos exatos conferidos
e seis PNG reconstruídos com reprodução dos **seis hashes completos das
solicitações originais**. [Auditoria](mission104-evidence/legacy-references-audit.json).
Licença e termos Pexels consultados, incluindo adaptação comercial sujeita aos
usos proibidos. Isso não resolve os componentes de modelo pendentes: os seis
continuam bloqueados, sem licença retroativa ou atribuição ao novo 5B.

Quinto clipe: hash distinto, mas distâncias dHash `[4,8,7,5,6]` contra a fonte
histórica `9473227`. Política existente: distância ≤8 em pelo menos 60% das
amostras. Há semelhança visual excessiva, sem duplicação binária. Não foi
demonstrado falso positivo; proteção e exclusão permanecem.

## Qualidade e recuperação

Fontes novas: hash/decode/movimento, revisão semântica CPU SmolVLM fixada e
comparação perceptual com fila, histórico e seis clipes antigos. A montagem
tem gancho, organização coerente, falas sem alegações de eficácia de produto,
três segmentos distintos e duração reduzida sem loops.
[Contato visual](mission104-evidence/first-ai-contact.jpg).

Validação separada do MP4 baixado do Release: zero pretos >300 ms, silêncios
>800 ms ou congelamentos >1 s; decode íntegro, média −15,4 dB, diferença final
áudio/vídeo 23 ms. [Prova](mission104-evidence/independent-final-av.json).
`editorial_approved=false/publication_enabled=false` nessa ferramenta significa
que o validador técnico isolado não concede autorização editorial; a política
editorial/publicação foi conferida separadamente na fila. Não se alegou revisão
humana ou sincronismo labial para cenas sem apresentador. O agente inspecionou
as imagens, além dos controles CPU.

Primeira tentativa KingNish: `AppError` explícito de resposta concluída, sem
arquivo entregue. Reconciliação específica preservou fingerprint, classificação
anterior e 75 s reservados, sem repetir a solicitação. Timeout/erro de transporte
continua incerto e bloqueia retry. Intenção durável antes de submit, cada fonte
útil em Release; falha de checkpoint após gravar a fila recupera o episódio
determinístico sem gerar/renderizar/reenviar.

## Workflows e continuidade

Ativação somente após prova pública ligada a hash, Buffer ID e URL. Coletor e
etapa CPU reutilizam o workflow existente; produtor diário prioriza Wan pronto
e conserva Pixabay. Mesmo publicador, concorrência de estado e CAS, sem alterar
os posts convencionais. Horários calculados em `America/Sao_Paulo`.

| Workflow ativo em main | UTC | Função |
|---|---|---|
| AI30 Free Collector | 06:10, 12:10, 16:10, 22:10 | Cota, geração e preservação; revisão/montagem quando houver fontes. |
| official media acquisition | 10:30, 18:30 | Aquisição Pixabay limitada. |
| Daily Video Creation | 06:20, 11:20, 19:20, 23:20 e após aquisição | Até quatro prontos, máximo dois renders por execução. |
| TikTok Online Runner | 12:07/20:07 e verificações 13:17/14:17/21:17/22:17 | Buffer para **10h/18h BRT** e confirmação posterior. |
| Persistent Video Stock | 00:37/06:37/12:37/18:37 e 13:37/21:37 | Consumo confirmado e reposição limitada. |

Execução independe do computador pessoal; cron GitHub pode atrasar. O post
convencional das 10h publicou em paralelo:
[7705413968000568594](https://www.tiktok.com/@.casasemesforo/video/7705413968000568594).
Reservas existentes de 07/11 18h e 08/11 10h/18h preservadas.

Rotina real pós-deploy
[42382114492](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42382114492):
`WAIT_FREE_QUOTA`, **zero chamadas GPU**, quatro solicitações e 255 s reservados
mantidos. Recibo do inventário reconciliado para `PUBLISH_COMPLETE`, separado
do estado anterior de entrada na fila. [Provas](mission104-evidence/continuity.json).

[Aquisição 42380651250](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42380651250)
obteve dois candidatos. [Produtor 42380698445](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42380698445)
rejeitou fontes congeladas/contexto inadequado, criou zero e **falhou**.
Preservou três vídeos prontos. Na recuperação real
[42382116816](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42382116816),
sem novas chamadas IA, o produtor aprovou fontes Pixabay `34209`/`34211`, montou
um vídeo novo de 18,333333 s com pf_dora e elevou o estoque **de três para quatro**.
SHA `1c5bca90c1319f0e2de6d886795538fa0212906d84e4862d7378d71f0e7e57a4`.
[Metadados, licenças e validações](mission104-evidence/recovered-conventional-post.json).
O publicador existente confirmou Buffer `6aef3909d6bbae6fa1928169`, **SCHEDULED**
para 09/11 às 10h BRT em
[42382881253](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42382881253).
Esse vídeo futuro não foi declarado publicado. O consumo confirmado do teste
IA também gerou um único evento durável de reposição no monitor.

## Limites gratuitos

[Provas de limites](mission104-evidence/free-limits.json): Free HF 300 s por
janela de 24h; política local 291 s; reserva 60 s por clipe/180 s por vídeo de
15 s. Servidor solicita 53 s por clipe; débito efetivo remoto desconhecido.
**Dois vídeos IA novos exigem 360 s e não cabem**. Partindo de zero cenas, uma
janela comporta um vídeo completo, com sobras parciais preserváveis para a
seguinte. Até quatro cenas novas de 60 s cabem em 291 s; a transição de cenas
entre janelas não comprova uma taxa diária sustentável. Primeira
renovação elegível atual 08/11/2026 13:06:35 UTC. Um ciclo não prova produção
gratuita diária permanente.

Documentos atuais permitem dois Spaces ZeroGPU próprios para contas Free
elegíveis. Não se afirmou que hospedagem necessariamente exige plano pago.
Elegibilidade/escopo de escrita e runtime A14B substituto não foram validados;
a solução executada usa o Space gratuito existente.

Repositório público, Ubuntu padrão, Kokoro/SmolVLM em CPU, Releases existentes;
nenhuma compra, assinatura, upgrade ou GPU paga ativada. Buffer conserva limites
Free e locais. Fontes e MP4 têm limites semanais/mensais de quantidade/tamanho;
revisões futuras arquivam JSON/JPG/SRT por três dias. O primeiro artefato incluiu
pesos de voz redundantes; foi preservado para não perder evidência, e o upload
futuro foi corrigido. Download local desse artefato recebeu 403 do endpoint
auxiliar; GitHub/HF/Buffer funcionaram. Fatura e armazenamento global da conta
não foram certificados; não se alegou ausência de cobrança preexistente.

Banco factual e fontes finitos: esgotamento é detectado antes de gastar GPU.
Meta dois posts/dia com IA/Pixabay continua condicionada a aprovação e cotas.
**Sessenta inéditos/mês e duas gerações IA diárias gratuitas não comprovados.**

## Engenharia e segurança

HEAD inicial main `8a1d76e8a9bf3a18d66a77f15609e3d087d6e6fd`. Trabalho baseado
na main recuperada, preservando branches/worktrees e incorporando checkpoints
automáticos por fast-forward/rebase, sem force-push ou reescrita de históricos.
Commits de código: `ce91d49`, `e137714`, `9924fd2`, `62e70fa`, `70dfc9d`.
Todos os 18 IDs Buffer preexistentes e seus hashes permaneceram iguais.

**401 testes aprovados** após a última mudança de código; 24 testes dirigidos
também passaram no coletor real pós-deploy. Os 401 passaram ainda no produtor
real que completou a recuperação. Incluem licença/revisão, modelo
antigo sem liberação retroativa, reserva antes de API, quota preservada, incerteza
sem retry, teste público único, colisões de horário, ativação somente com prova
pública, recuperação de checkpoint e esgotamento factual antes de GPU. YAML
também analisado. Geração, montagem, envio e confirmação realmente executados.

Secrets GitHub existentes usados sem copiá-los para código/evidências. Um erro
do CLI mostrou link temporário de download somente de leitura de artefato,
expirado às 14:21:43 UTC; excluído das evidências versionadas. Não era chave
permanente. [Ambiente publicado aplicado](mission104-evidence/runtime-current.json)
com revisão observada igual à publicada e rede `unrestricted/enforced`;
nenhuma republicação manual ou contratação solicitada.

Conclusão delimitada: **vídeo Wan2.2 5B real publicado e rota gratuita integrada**.
Cadeia A14B antiga pendente; recorrência limitada pelas condições verificadas
acima, sem promessa de geração gratuita ilimitada.
