# Renovação de conteúdo — contrato versão 1

O gerador continua deliberadamente limitado pelo conteúdo revisado. Não há API de IA ilimitada nem coleta automática de mídia ativada. O arquivo `catalog_extension.json` permite acrescentar lotes sem modificar Python. O primeiro lote contém um tema real sobre organização de livros, com fonte conferida. Exemplos fictícios dos testes nunca entram na produção.

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
# Aquisição oficial — continuação 20/10/2026

## Versão 3.1

Fontes configuráveis: `MEDIA_PROVIDER_ORDER=pixabay,wikimedia,pexels`.
Pixabay usa `PIXABAY_API_KEY`; Pexels usa `PEXELS_API_KEY`; Wikimedia Commons não
requer chave para esta consulta pública. O workflow informa apenas presença booleana.
API indisponível é ignorada até a próxima execução, sem tempestade de retentativas.
Cada fornecedor tem no máximo quatro buscas, com cache de 24h. O limite global
continua quatro downloads e dois candidatos por execução. Fluxo manual/push,
sem coleta diária habilitada até validar condições e qualidade em uso real.

Pixabay: API oficial de vídeos, safesearch, tags contextuais, autor, licença e dimensões.
A documentação restringe consultas automatizadas em massa e downloads sistemáticos;
este coletor limitado responde a execução solicitada, não rastreia o catálogo inteiro.
Não afirmar autorização irrestrita para cron permanente sem avaliar esse uso.

Commons: API action=query/imageinfo com extmetadata individual. Aceita CC0 1.0 e
CC BY 3.0/4.0; rejeita autor ausente, restrições declaradas, licença desconhecida,
NC, ND e ShareAlike (este último exige tratamento específico ainda não implementado).
A seleção exige vídeo, resolução vertical adequada e contexto no título/descrição.
Não transforma imagens estáticas em preenchimento genérico.

`CREDITS.txt` acompanha artifacts de revisão com autor, título quando disponível,
página original, licença/link e indicação de adaptações. Na promoção editorial,
esses créditos devem constar no vídeo ou descrição pública; arquivos do inbox não
são consumidos automaticamente pelo renderer. Portanto créditos apenas armazenados
não são apresentados como cumprimento de atribuição numa publicação inexistente.
O catálogo revisado agora aceita as três origens. Quando uma fonte é promovida com
revisão explícita, renderer acrescenta créditos à descrição pública e o gate de
envio recusa descrição sem esses créditos. O limite de 2200 caracteres é verificado
sem truncar atribuições. A revisão de contexto continua necessária.
Recuperação: `--recover wikimedia:ID` / `--recover pixabay:ID`; IDs sem prefixo
continuam sendo Pexels. SHA obrigatório e extensão original preservada.

Referências: https://pixabay.com/api/docs/ , https://pixabay.com/service/license-summary/ ,
https://www.mediawiki.org/wiki/API:Imageinfo e
https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia .

As seções abaixo descrevem a primeira versão Pexels; a configuração acima prevalece.

`media_acquisition.py` implementa um fornecedor Pexels isolado (`search`) e uma
etapa comum de seleção/download/validação. Usa apenas a API oficial, nunca scraping.
Configurar `PEXELS_API_KEY` diretamente nos secrets do GitHub, nunca em conversa.
Workflow `acquire-media.yml`: manual ou ao alterar o coletor; sem cron até comprovar
autorização e aquisição real. Não altera Buffer nem a fila de produção.

Limites por execução: quatro consultas, quatro tentativas de download, dois arquivos
aceitos, 250 MiB por arquivo, 15 minutos, backlog máximo de 120 registros.
Cache de pesquisa de 24 horas; metadados persistidos em Git. Downloads ficam em
artifacts por três dias, não são armazenamento permanente. URLs/origem/SHA/dHash
permanecem no inbox; recuperação futura exige baixar novamente e conferir SHA.

Filtros: autoria, origem HTTPS permitida, palavras do assunto no endereço original,
vertical >=1080x1920, duração real entre 28 e 300 segundos, SHA e fingerprints contra
fila, estado, histórico legado e inbox. A correspondência lexical NÃO equivale a
inspeção semântica. Todo resultado permanece `pending_visual_review`, sem aprovação.
Promoção ao catálogo revisado continua necessária; não há promessa de autonomia
editorial nem 60 vídeos mensais. Atribuição Pexels/autor/página fica em cada registro
e deve acompanhar a promoção e os créditos. Não usar filmagens como prova de produto.

Documentação oficial consultada: https://www.pexels.com/api/documentation/ e
https://www.pexels.com/license/ . Limite padrão documentado: 200 requisições/hora e
20.000/mês; a conta pode ter limites diferentes. A implementação não compra planos.
Pixabay avaliado, não ativado: https://pixabay.com/api/docs/ restringe consultas
automatizadas em massa e downloads sistemáticos; não presumir autorização para
fallback autônomo. Outros fornecedores precisam autorização/licença próprias.

Recuperação tardia: `python automation/media_acquisition.py --recover ID` baixa
novamente a fonte do inbox e exige o SHA original antes de disponibilizar o arquivo.
Não modifica aprovação nem histórico. Rejeições ficam em quarentena por sete dias.
