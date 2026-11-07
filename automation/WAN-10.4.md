# Rota Wan 2.2 — missão 10.4

Primeiro vídeo inteiramente gerado por IA publicado e verificado publicamente:
[TikTok 7705426078436838676](https://www.tiktok.com/@.casasemesforo/video/7705426078436838676),
07/11/2026 às **10:48:31 em Brasília**. Buffer `6aef299f229bf05daf51f11e`;
ID interno `casasem-2026-11-07-wan104`. A confirmação inclui reprodução pública
sem login, legenda correspondente e rótulo TikTok “Creator labeled as AI-generated”.
`sent` e `scheduled` isolados continuam insuficientes.

O perfil novo usa `FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers`, derivado de
Wan2.2-TI2V-5B e explicitamente Apache-2.0, pelo Space público gratuito
`Upsampler/wan-2-2-5b-video`. É uma variante 5B; não é o A14B dos seis arquivos antigos.
O Space carrega todos os componentes desse repositório, sem a extração Kijai,
sem pesos cbensimon e sem pacote AOTI. Revisões, licença, contrato e custo zero
ficam em `experimental81/wan104_components.json`; divergência bloqueia chamadas.

O MP4 possui 15,000 s, 1080×1920, H.264/AAC, Kokoro CPU **pf_dora pt-br**,
legendas com duração medida, três cenas distintas sem loops e identificação de IA
na imagem e no envio Buffer. Original, fontes e hashes estão em Releases.
[Auditoria e evidências](AUDIT-10.4.md) registram integridade e confirmação pública.

As três descrições de cenas e as falas de `experimental81/wan104.py` foram
redigidas para a missão autorizada pelo proprietário. Não há imagem de entrada
de terceiros nesse perfil. Isso não concede direitos aos seis clipes anteriores
nem os apresenta como resultados do modelo novo.

Compartilha o ledger de cota já existente na branch experimental. Cada tentativa
reserva 60 segundos antes do envio (fórmula do servidor pede 53) e persiste intent antes de submit. O consumo
real continua desconhecido; o provedor é autoritativo. Não compra capacidade,
não solicita GPU própria e não repete resultados incertos. Cada MP4 válido é
preservado como Release e inventário, com fonte, SHA e evidência de geração.

O teste inicial no Space KingNish retornou `AppError`, erro explícito na resposta
concluída do servidor Gradio, sem saída entregue. A reconciliação específica
preserva seu fingerprint, a classificação anterior e os 75 segundos reservados.
Não se repete a solicitação. Timeouts e respostas de transporte incertas
continuam `UNKNOWN_NO_RETRY`; não recebem a mesma liberação.

## Reposição e publicação

O workflow existente `ai30-free-collector.yml` executa em main às
06:10, 12:10, 16:10 e 22:10 UTC. Verifica identidade Free, licenças e revisões
antes da inferência. Após três fontes válidas, uma etapa CPU separada revisa,
narra, legenda, monta e encaminha para a **fila e publicador Buffer existentes**.
O produtor diário também tenta aproveitar fontes Wan prontas antes da reposição
Pixabay obrigatória. Mantém até quatro vídeos prontos e os horários
**10h e 18h America/Sao_Paulo**. Falha após gravar a fila recupera o checkpoint
sem gerar, renderizar ou publicar novamente.

`activated_after_public_trial` só foi ativado depois da prova pública; a rotina
reconfere hash, ID Buffer e URL no estado canônico. Coleta, montagem, fila,
agendamento e publicação permanecem estados separados.

## Limites gratuitos

Hugging Face documenta 300 segundos por janela móvel de 24h para Free.
A política local admite 291 s e reserva 60 s por cena: **180 s por vídeo de 15 s**.
Dois vídeos de IA novos exigiriam 360 s e **não cabem nessa política gratuita**.
O débito remoto efetivo não foi fornecido. Na janela atual, 75 s da primeira
falha mais 180 s das cenas válidas foram preservados; testes reais retornaram
`WAIT_FREE_QUOTA`, zero chamadas GPU. Primeira renovação elegível registrada:
08/11/2026 13:06:35 UTC. Cron e fila do provedor podem atrasar.

Uma produção gratuita diária permanente ainda não foi demonstrada. Quando
faltar IA, Pixabay continua sujeito a licença, originalidade e qualidade;
candidatos rejeitados não são publicados para preencher horários. Banco factual,
revisões fixadas, disponibilidade dos Spaces e armazenamento são finitos;
esgotamento suspende a rota afetada sem contratar recursos.
Uma janela nova, partindo de zero cenas, comporta um vídeo completo e pode
preservar cenas parciais para a seguinte; isso não comprova uma taxa diária.

## A14B anterior

O Wan2.2-I2V-A14B oficial é Apache-2.0 e não está bloqueado por sua licença.
Continuam pendentes os direitos da extração LoRA rank128 e dos componentes
cbensimon usados no Space anterior. `lightx2v/Wan2.2-Distill-Loras` é uma
alternativa Apache-2.0 estruturalmente compatível, mas o Space anterior não aceita
trocar componentes pela API. Não foi alegado teste de execução dessa substituição.

Os seis arquivos e seu inventário continuam idênticos, sem licença retroativa.
As seis referências PNG foram reconstruídas com reprodução exata do hash da
solicitação original. O quinto mantém o bloqueio por semelhança histórica;
não houve prova de falso positivo.
