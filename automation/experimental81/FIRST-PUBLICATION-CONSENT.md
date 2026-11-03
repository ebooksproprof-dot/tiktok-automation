# CasaSemEsforço — autorização de primeiro teste público com IA

**Autorização expressa do titular na conversa em 03/11/2026:**
"O usuário quer tentar a primeira publicação como teste real assim que a cota gratuita estiver disponível; dispensa uma rodada separada de prévia/aprovação editorial por mensagem, para esse primeiro vídeo 100% IA de 30 segundos."

Essa autorização **não comprova** que existem seis cenas geradas, que o TikTok aceitou o arquivo, nem que a qualidade do material atende ao objetivo. Esta nota só preserva a intenção de tentar o primeiro teste real quando houver condições.

## Escopo autorizado
- Somente **um primeiro vídeo original com 30 segundos inteiramente compostos por cenas em movimento geradas por IA**; narração Kokoro PT-BR e legendas.
- Conta TikTok oficial previamente verificada: `@.casasemesforo`. Preferência de horário 10h America/Sao_Paulo, se o slot estiver livre.
- Usar o mesmo Buffer / mesmo histórico de posts e verificar duplas postagens antes e depois. AI content label obrigatório na plataforma.
- Custo adicional R$0 e nenhum uso de GPU paga, cartão, créditos comprados ou múltiplas contas.
- Não introduzir filmagens de arquivo para completar os 30 segundos e não repetir os mesmos cinco segundos seis vezes.
- O dono autorizou **dispensar mensagem de prévia/novo aceite editorial** para o primeiro teste, **não** autorizou inventar revisão visual, direitos, qualidade, consentimento de APIs ou fingir que publicou.

## Pré-condições mínimas antes de qualquer chamada de publicação
1. Arquivo MP4 completo realmente existente, verificado SHA-256 e metadados: 30.0s±0.15, 1080x1920 H264 yuv420p AAC, áudio sincronizado, sem quadros pretos/corrompidos.
2. Seis segmentos IA únicos, cada um com evidência de geração real e procedência. Direitos comerciais do modelo, componentes e referências de imagem verificados. Exigir que objeto/ação do vídeo não contradiga o roteiro; conteúdo não pode fazer alegações falsas.
3. Dois componentes independentes, origem e publicação: idempotência em estoque e Buffer, conta exata, slot não ocupado, limite de plano respeitado, consentimento e rótulo de conteúdo IA.
4. Publicação em modo automático permitido pelo Buffer, sem criar uma nova rota paralela de TikTok Direct Post. Guardar ID remoto, reconciliar envio incerto; post agendado não é sinônimo de post público.
5. Se houver falha de geração ou cota insuficiente, **não publicar** vídeo parcial/híbrido; acumular clipes com hashes diferentes quando permitido ou registrar o bloqueio.
6. Não marcar `editorial_approved=true` se uma avaliação editorial efetiva não ocorreu. A dispensa de prévia do titular é diferente de inventar revisão de qualidade.

## Estado atual
- A branch `feature/ai-video-hybrid-30s` possui o modo `AI_ONLY` e controle preventivo de cota, mas não há ainda seis clipes utilizáveis/30s final 100% IA nem integração final de publicação.
- O workflow experimental roda testes, mas **não** gera diariamente e **não** publica.
- A tarefa diária **CasaSemEsforço Diário** foi atualizada em 03/11/2026 para verificar a renovação de cota, tentar gerar progressivamente e, se e somente se possível, publicar a primeira peça apta. Nenhuma tarefa duplicada criada.
- Sem direitos comerciais pendentes verificados, sem primeiro MP4 100% IA e sem validação técnica real, este arquivo **não habilita por si só publicação**.

Se retomar no Work/Codex, ler `CHECKPOINT-8.2.md`, esta autorização e PR #3. Preservar o pipeline real atual, sem merge automático.
