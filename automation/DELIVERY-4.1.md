# CasaSemEsforço 4.1 — entrega incremental

Estado: **PARCIAL**. Voz feminina CPU implementada; avatar animado não produzido.

## Checkpoints preservados

- Base 4.0: b0ebf68; não reinstalar ou refazer os testes históricos sem motivo.
- Identidade original/recovery: cddfe5341ce8fc526780dfd3fa56f515e9fe61f7.
- Voz CPU, diagnóstico avatar e revisão em lote: 79ddc58bd43291d865bea770f0305e34055f6609.
- Provas isoladas na nuvem: 22a83f3a32d1f9132076c87a79b8da050a6788df.

## Implementação e limites

Kokoro pf_dora pt-BR é a nova seleção explícita no passo diário de renderização. FFmpeg, composition_style.py, Pixabay, Buffer e GitHub Actions preservados. Piper permanece selecionável e é padrão da interface legada. Falha Kokoro não troca silenciosamente a voz. Não há aumento de composition_revision nem rerender automático dos MP4s existentes. A aprovação de conteúdo não foi alterada.

Gancho, recorte alternado seguro, legendas por frases e marcador final da 4.0 continuam. A mudança medida é voz feminina e consumo CPU; não foi avaliada por escuta a naturalidade, nem medido ganho de retenção. Legendas por chunks proporcionais não equivalem a alinhamento palavra a palavra.

O retrato avatar/presenter-v1.jpg representa uma adulta fictícia original e fixa a identidade futura. Não há animação, movimentos ou sincronização labial produzidos. avatar_backend.py é uma interface de diagnóstico indisponível, não um motor integrado à produção.

## Ferramentas avançadas

| Ferramenta | Situação comprovada |
|---|---|
| Kokoro | Síntese CPU real, comparação com Piper e três provas C; integração diária explícita |
| VoiceStudio/Supertonic3 | Não sintetizado: aceite adicional OpenRAIL-M exigido; não aceito |
| SadTalker | Código suporta CPU; inferência não executada por pendência comercial de assets BFM de terceiros |
| Wav2Lip | Versão oficial restringe uso comercial; não executado |
| MuseTalk | CUDA documentado; CPU gratuito não validado |
| LivePortrait | Pesos InsightFace precisam substituição permissiva; não é por si só lip-sync de áudio |
| EffectCraft | PoC CPU histórica preservada; sem comparação nova que prove superioridade ao FFmpeg |
| OpenCut | Pesquisa anterior: backend headless adequado não comprovado; não instalado novamente |
| FilmCraft | CLI alpha pesquisada, sem render comprovado neste projeto |
| PhotoCraft/VectorCraft | Pesquisa anterior; benefício concreto à produção não comprovado |
| Remotion | Não integrado nem benchmark executado; nenhuma superioridade alegada |
| Runway/OpenArt | Contas gratuitas consultadas; sem geração de vídeo disponível dentro das condições/saldo gratuito observado; nada comprado |

Não chamar as ferramentas apenas pesquisadas de testadas. Fontes e detalhes de licenças em AVATAR-4.1.md, VOICE-4.1.md e AUDIT-4.0.md. Nenhuma licença adicional com aceite foi aceita.

## Provas

C1 sabonete, C2 livros e C3 secador reutilizam intencionalmente as mesmas imagens/roteiros da comparação 4.0. São comparações controladas, não novos conteúdos para publicação. Formatos A/B não foram entregues porque nenhum motor de avatar foi validado.

As três provas locais: 1080×1920; 17,27/17,61/17,99 segundos; render 50,64/48,20/62,21 segundos; zero intervalos pretos >=0,3s ou silêncios >=0,8s. Peak RSS Python até350MiB; FFmpeg até691MiB, máximos separados, não consumo agregado. Sem GPU. Relatório em validation-4.1-local-evidence.json.

Limites visuais: lavagem de mãos é ilustração, não demonstra o suporte sugerido; livraria não prova organização doméstica; C3 corta parcialmente o secador e prioriza o rosto. Pessoas de stock não são a apresentadora virtual. Nenhuma dessas provas foi aprovada, adicionada à fila ou enviada ao TikTok.

## Automação e continuação

A criação e o envio aprovado continuam na nuvem. Meta10h/18h Brasília preservada; GitHub cron não tem garantia de início pontual. A fila previamente aprovada publicou em18–21/10 e22/10 às10h conforme estado Buffer. Isso não prova renovação editorial sustentada. Não há novo envio provocado pelas provas4.1.

Persistem limites: catálogo finito; necessidade de cenas realmente pertinentes; aprovação humana para adequação editorial, voz, consentimento e slot. BATCH_APPROVAL.md permite revisão de até14 itens por lote com manifesto vinculado a hashes/snapshots. Dry-run é padrão; aplicação deve ocorrer serializada, com estado atualizado. Não foi aplicado nenhum lote real.

Custo adicional contratado/observado nesta missão: R$0. Sem GPU paga, assinatura ou reset de cotas. Nenhuma garantia de políticas futuras ou capacidade ilimitada.

Próximo passo exato: recuperar os assets da Release4.1 e o relatório cloud, revisar voz e enquadramento antes de aprovar qualquer conteúdo; ampliar cenas específicas licenciadas; para avatar esclarecer permissões BFM ou encontrar substituto permissivo antes do smokeCPU2s. Não repetir a geração do retrato nem os benchmarks já persistidos.
