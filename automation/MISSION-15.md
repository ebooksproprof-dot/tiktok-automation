# CasaSemEsforço 15 — episódio completo, revisão e continuação

Partida real: main `ee11e9b`, não ffd63f4. Os commits posteriores alteravam
inventários, cache de pesquisa, saúde e estado; nenhum foi descartado.
Checkpoint remoto: `checkpoint/mission15-before-ee11e9b`.

## Identidade vocal

A candidata selecionada para escuta é **unmute-lara**. A licença comercial da
referência foi resolvida: doação voluntária Kyutai Unmute, CC0, com termos de
consentimento que expressamente permitem transformação, uso comercial e
projetos derivados de TTS. Não foi usada uma voz da demonstração Chatterbox.
Kokoro pf_dora foi investigada, mas não foi usada como referência porque a
proveniência e os direitos específicos dessa transformação não foram esclarecidos
pela documentação por voz. Voz interna do modelo já havia apresentado dúvidas
no episódio técnico da missão 14 e não tem feminilidade brasileira comprovada.

**Aprovação perceptual continua pendente.** Os metadados publicados das doações
não comprovam gênero ou sotaque brasileiro da referência. O resultado é produzido
pelo checkpoint brasileiro, mas sua feminilidade, sotaque, naturalidade e clareza
precisam de escuta humana. Não foram inferidos desses atributos por ASR.

- [Coleção CC0 e revisão fixada](https://huggingface.co/kyutai/tts-voices/blob/323332d33f997de8394f24a193e1a76df720e01a/README.md#voice-donations)
- [Consentimento comercial e de transformação, seção 5](https://kyutai.org/next/legal/Terms%20of%20Use%20-%20Unmute%20Voice%20Donation%20Project%20v1.pdf)
- [Pacote auditivo e hashes](mission15-evidence/VOICE-REVIEW.md)
- [Página com duas vozes e episódio completo](https://ebooksproprof-dot.github.io/tiktok-automation/public/mission15-voice-review.html)

A cópia original fica em `/workspace/shared/casasem-voice15/`, diretório 700 e
WAV 600 no Cloud. Actions recupera a mesma referência licenciada de revisão
imutável, verifica SHA/PCM16/mono/5–12s e mantém a cópia apenas no diretório
privado RUNNER_TEMP. O workflow `mission15-reference-check.yml` comprovou
recuperação duas vezes e modo 600. A persistência da fonte é o repositório
licenciado; não se afirma que RUNNER_TEMP seja armazenamento permanente.
Nenhuma gravação original foi colocada em Git, Release ou artifact. Só falas
novas sintetizadas aparecem publicamente.

## Áudio corrigido

A candidata Lara produziu a amostra de 22 palavras com correspondência integral;
Hannah teve divergência em “por uso” e não foi preferida. O episódio usa frases
completas, referência fixa, seed 15, temperature .65, CFG .5 e expressividade .5.
Cinco falas somaram 31,28s; normalização sem truncamento resultou em 30,014s,
com tempo 1,0427×, dentro da faixa previamente aprovada de 0,90–1,10.

As **60 palavras** do episódio coincidiram no ASR. Pontuação/capitalização não
alteram o resultado. O normalizador textual rigoroso anterior foi preservado.
Uma proposta de edição do normalizador foi bloqueada pelo filtro de conteúdo
durante a sessão e não foi reenviada por outro caminho. A melhoria implementada
consiste em confirmação por outro checkpoint ASR, preservação das duas
transcrições e retenção das divergências sem solução. O segundo checkpoint só
pode resolver uma troca de baixa confiança quando todos os tokens disputados
são incertos, a outra transcrição coincide integralmente e não há omissão.
Erros de alta confiança e truncamentos continuam retidos.

No áudio antigo, small e medium divergiram no início e ambos reconheceram
“comportamento” no lugar de “compartimento”; ele permanece retido. O novo roteiro
e a nova referência produziram conteúdo integral sem afrouxar a comparação.
ASR não prova naturalidade ou pronúncia auditiva perfeita.

Relatórios ASR ficam vinculados ao SHA do WAV e ao roteiro esperado, mantendo a
transcrição observada. Legendas do episódio usam timestamps das palavras
reconhecidas, permitidos somente após igualdade da sequência completa.

## Vídeo e origem das cenas

O episódio “Copos secos antes de guardar” tem cinco cenas ilustradas autorais:
água no fundo, apoio no escorredor, espaçamento sem empilhar, inspeção da borda
e fundo, e armazenamento estável. É conteúdo editorial, não um padrão de
calibração. **É uma animação por código, com zero novas cenas Wan**, sem promessa
de mostrar uma experiência física real. O desenho é nativo 1080×1920 e não usa
filmagens de licença incerta, upscale ou loops de clipes.

O Wan preservado continua com duas cenas de 480×832 no episódio 6 e sete
entradas no banco. As duas cenas foram recuperadas e inspecionadas, sem descarte
ou reclassificação artificial como Full HD. O coletor tinha uma parada prematura
em três cenas, corrigida para seis; os limites e o ledger compartilhado seguem
intactos. O Space fixado expõe altura máxima de 1024 na interface; não foi enviada
resolução acima desse limite. Não houve nova chamada GPU para material que já
sabíamos inadequado à exigência de qualidade.

A busca oficial Pixabay fez quatro consultas limitadas e preservou metadados.
O job não obteve fontes de vídeo baixadas para revisão; acessos locais a CDN
retornaram 403. Não houve troca de IP, credenciais ou contorno de restrições.
A animação é uma alternativa editorial explícita para fornecer um episódio
completo com direitos próprios enquanto a rota fotorealista continua limitada.
Não se apresenta essa alternativa como teste concluído de produção Wan em HD.

O detector global de congelamento acusou falsos positivos no fundo estático da
ilustração. A verificação especializada examinou **900 quadros da área da ação**,
excluindo cabeçalhos e legendas: 741 pares com movimento acima do ruído de
compressão, no máximo 12 quadros sem mudança. A mesma verificação rejeita uma
cena congelada em teste real. O detector convencional de estoque/Wan não foi
alterado. Não se aprovou uma cena congelada nem se contou só movimento de texto.

## Como liberar sem repetir a síntese

Apenas o proprietário deve ouvir a candidata e confirmar feminilidade, português
brasileiro, naturalidade e clareza. O pacote permanece pendente até isso ocorrer.

Depois de ouvir, o proprietário pode executar **CasaSemEsforco Mission15 owner
voice approval**, selecionar `approve_female_ptbr_natural_clear=true` e informar:

`8fea595097a2281149a9bbc1287d2b387bab562442afb9a537cafdf11c902fbf`

O workflow exige actor `ebooksproprof-dot` e vincula a aprovação ao sample,
referência, modelo e parâmetros. Não foi executado nesta sessão sem aprovação.
A identidade aprovada é reutilizada; alterações exigem nova revisão.

O workflow de continuação faz validação real do vídeo, hash do WAV/transcrição,
originalidade, direitos, enquadramento e cadência. Só então insere na fila
existente, salva a saída no ledger e aciona o publicador Buffer existente.
Retentativas recuperam a mesma entrada por `origin_draft_id`, sem novo upload
ou publicação duplicada; recibos concluídos não são rebaixados.

A fila não recebe o padrão técnico da missão 14. O novo episódio fica em revisão
com publicação pendente até a identidade ser aprovada. Aceitação pelo Buffer,
agendamento e publicação pública continuam sendo estados diferentes.

## Operação

O Buffer foi verificado em somente leitura. Corrigida falha de persistência do
monitor: o cliente durável atualizava `state.json` local ao salvar cotas remotamente,
mas o workflow só adicionava `operational_health.json`, bloqueando o rebase por
árvore suja. Agora ele inclui seu próprio estado antes de persistir; a retomada
real passou. Os controles CAS/lease e de publicação incerta foram mantidos.

Cadência: até três por sete dias móveis, mínimo 48h, 10h/18h BRT quando houver
material apto. R$0 adicionais. Sem GPU paga, ElevenLabs, contratação de serviços
ou dependência de computador pessoal. Produção fotorealista Wan sustentada ainda
não foi demonstrada; o primeiro episódio ilustrado não prova cadência semanal.
