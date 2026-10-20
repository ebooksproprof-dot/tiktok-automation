# Auditoria CasaSemEsforço 3.1 — 20/10/2026

Estado geral: PARCIAL. Nenhuma compra/assinatura/GPU paga ativada. Não há evidência
de abastecimento e aprovação editorial autônomos suficientes para 60 vídeos/mês.

## Evidências

- Base709c578; implementações874b68b,2327809,01ad009.
- Aquisição39463815894:102 testes no GitHub; ambas chaves opcionais ausentes.
- Aquisição39464338721:109 testes, Wikimedia responde mas0elegíveis; alerta issues/2.
- Produção39465289889:111 testes, instalação e prova FFmpeg/Piper aprovadas.
  Artifact12285340507 (27/10), relatório completo persistido em review_requests.json.
-113 testes locais finais; falhas de aquisição reportadas, não convertidas em sucesso.
- Auditor independente repetiu113 testes finais, sem novo bloqueador. Artifact cloud
  baixado, SHA conferido e imagens inspecionadas. Não houve nova publicação pública.
- Auditor independente repetiu102,109 e111 testes; correções abaixo verificadas.

## Componentes

| Componente | Estado | Evidência / limite |
| --- | --- | --- |
| Pixabay | Bloqueado externamente | Adaptador/mocks; PIXABAY_API_KEY ausente, sem chamada autenticada real |
| Wikimedia | Funcional com limitações | Consultas reais locais/nuvem;0 cenas elegíveis; CC0/CC BY restritos |
| Pexels | Bloqueado externamente | Adaptador preservado; chave ausente; fontes antigas por URL continuam disponíveis |
| Catálogo/roteiros | Funcional com limitações | Novo roteiro factual; catálogo finito e revisão necessária |
| Seleção visual | Funcional com limitações | Palavras-chave, geometria, duração, revisão de cenas; sem visão semântica autônoma |
| Originalidade | Funcional com limitações | SHA/dHash, histórico e bloqueio de reutilização; heurística, não prova semântica |
| Licenças/créditos | Funcional com limitações | Origem/licença/autor por asset; catálogo revisado gera crédito público; gate exige presença |
| Piper | Funcional | Narração real local e GitHub; pt_BR-faber-medium, hash do modelo verificado |
| FFmpeg | Funcional | Novo MP4 1080x1920 H264/AAC;17,048s;-16,1dB;3 fontes sem loop |
| Planejador | Funcional | Corrigida distribuição para fontes desiguais mantendo offsets não sobrepostos |
| OpenCut | Experimental | README atual ainda anuncia Editor API/headless como futuros |
| FilmCraft | Experimental | Avaliação anterior mantida; nenhuma prova adicional nesta etapa |
| EffectCraft | Experimental | Release atual0.11.1 igual à PoC CPU anterior; fora da produção diária |
| PhotoCraft/VectorCraft | Experimental | Não integrados; sem ganho demonstrado para abastecimento de cenas |
| VoiceStudio | Experimental | README CPU disponível, instalação~5GB; pesos/licenças separados; sem benchmark comparativo |
| GitHub Actions | Funcional com limitações | Render real aprovado; coletor separado do grupo de publicação após cancelamento observado |
| Releases | Funcional com limitações | Integração existente preservada; prova nova em artifact, sem novo upload de Release |
| Buffer | Funcional com limitações |10h confirmado pelo provedor;18h SCHEDULED; sem novo envio nesta etapa |
| Metricool | Funcional com limitações | Publicações históricas; sem nova comprovação de API gratuita autônoma |
| TikTok direto | Bloqueado para comprovação | Aprovação e permissões não demonstradas nesta etapa |
| Fila/recuperação | Funcional com limitações | Nenhum reenvio; arquivo recuperado exige SHA; estado/publicações preservados |
| Alertas | Funcional | Atualização real de issue única de falha, sem tokens/logs privados |
| Segurança | Funcional com limitações | Headers não registrados; redirects rejeitados; origens permitidas; keys só em secrets |
| Custos | Limitado por cotas | Ubuntu padrão; cache24h; downloads limitados; artifacts restritos; R$0 de compras |

## Falhas corrigidas nesta etapa

1. Ausência de Pexels bloqueava toda aquisição: fornecedores opcionais e fallback.
2. Primeiro fornecedor podia esgotar todos downloads: uma tentativa por tema/provedor.
3. Recuperação não recriava créditos: sidecar de atribuição junto dos bytes conferidos.
4. Catálogo só aceitava Pexels: permite novas origens revisadas, com créditos públicos.
5. Coleta concorria com criação pela única posição pendente: grupo próprio para inbox/cache.
6. Fontes curtas eram divididas por número de legendas: divisão proporcional se necessário.
7. Prova explícita poderia ser pulada após falha de produção: depende de instalação/testes,
   não do resultado da produção. A falha original permanece no job.
8. Originais grandes poderiam consumir cota de artifacts: teto8MiB/arquivo; maiores
   usam contact sheet parcial+metadados, mantendo download por SHA para revisão completa.

## Continuidade

Inserir PIXABAY_API_KEY diretamente nos secrets GitHub e executar aquisição oficial.
Não anunciar API autenticada antes de resposta real. Promover apenas cenas com contexto
e direitos revisados. A prova nova está pendente de revisão/publicação; não reenviar
os dois posts de20/10. A abertura automática de novos temas continua limitada por cenas
e aprovação, e não há garantia de60 publicações/mês ou de cotas gratuitas ilimitadas.
