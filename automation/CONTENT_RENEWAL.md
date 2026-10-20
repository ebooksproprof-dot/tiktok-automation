# Renovação de conteúdo — contrato versão 1

O gerador continua deliberadamente limitado pelo conteúdo revisado. Não há API de IA ilimitada nem coleta automática de mídia ativada. O arquivo `catalog_extension.json` permite acrescentar lotes sem modificar Python. Seu estado inicial vazio é intencional: exemplos fictícios dos testes nunca entram na produção.

Cada item de `items` exige:
- `id`: slug exclusivo, sem sobrescrever conceitos existentes.
- `category`: limpeza, organizacao, preparacao, conservacao ou rotina.
- `reviewed: true` e `reviewed_at`: registro da revisão efetivamente feita, não aprovação automática de publicação.
- `hook`, `steps`, `cta`: texto pt-BR; instruções contextualizadas e verificadas, sem alegações inventadas.
- `media`: uma a três fontes, cada uma com `id`, `url`, `source_page`, `license_url`, `author`, `context` e `sha256`.

Primeiro fornecedor aceito: arquivos HTTPS de videos.pexels.com, com página original www.pexels.com/video/ e licença https://www.pexels.com/license/. A presença desses campos não comprova a licença por si só: o revisor deve conferir a página e os direitos antes de marcar o item revisado. Outros fornecedores exigem adaptador próprio e revisão, não mudar a allowlist indiscriminadamente.

Fluxo de entrada:
1. Escolher um tema ainda não utilizado e uma filmagem realmente contextual; verificar origem/licença/autor.
2. Baixar e assistir à mídia, conferir tamanho e obter SHA-256. Não copiar vídeos alheios do TikTok.
3. Registrar os campos no JSON; não colocar chaves, tokens ou URLs assinadas.
4. Executar `python -m unittest discover -s automation/tests -q` e `python automation/readiness.py`.
5. Commitar o lote. A criação diária detecta a alteração, verifica os bytes, compara fontes/histórico, narra e renderiza. Os vídeos continuam com aprovação editorial de publicação desativada até inspeção do resultado.

Limites: 120 itens por lote; download existente de até 250 MB por fonte; vídeo final de até 20 MB. Catálogo com 60 roteiros e cinco filmagens não equivale a 60 vídeos originais. O diagnóstico conta fontes elegíveis e informa somente um limite superior. Comparações de trigramas e dHashes são heurísticas, não avaliação semântica perfeita.

Próximo bloqueio real: obter uma alimentação contínua de filmagens autorizadas e resolver a revisão dos resultados. Não inserir conteúdo genérico/repetido apenas para alcançar a meta diária. Nenhum serviço pago foi ativado.
