# Rota Wan 2.2 — missão 10.4

Implementação em validação. Não inferir publicação ou ativação recorrente de um
teste de coleta. O Buffer e a reposição Pixabay existentes permanecem ativos.

O perfil novo usa `FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers`, derivado de
Wan2.2-TI2V-5B e explicitamente Apache-2.0, pelo Space público gratuito
`Upsampler/wan-2-2-5b-video`. É uma variante 5B; não é o A14B dos seis arquivos antigos.
O Space carrega todos os componentes desse repositório, sem a extração Kijai,
sem pesos cbensimon e sem pacote AOTI. Revisões, licença, contrato e custo zero
ficam em `experimental81/wan104_components.json`; divergência bloqueia chamadas.

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
