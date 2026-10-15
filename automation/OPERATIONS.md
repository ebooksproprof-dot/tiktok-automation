# CasaSemEsforço — operação e limites

Status em 15/10/2026: AUTOMAÇÃO PARCIAL. Renderização não equivale a publicação.

## Identidade verificada

Metricool brand 7212680, TikTok @.casasemesforo. O histórico do Metricool retornou posts deste perfil em 03, 04, 11 e 12/10/2026. Nenhum agendamento foi retornado para 15–18/10. Não usar o teste privado sandbox-test-001 como prova de publicação pública.

## Criação

O workflow existente roda às 08:30 America/Sao_Paulo, com slots pretendidos às 10h e 18h. FFmpeg gera H.264 1080x1920, AAC, yuv420p, faststart. Piper 1.3.0 sintetiza voz brasileira Faber localmente em CPU, sem API paga, créditos, Vidnoz ou CapCut. Model card: https://huggingface.co/rhasspy/piper-voices/blob/main/pt/pt_BR/faber/medium/MODEL_CARD (dataset CC0; repositório de vozes MIT). Hash do modelo fixado no código.

Filmagens Pexels existentes: 9473227, 9472849 e 9462884, sob https://www.pexels.com/license/. Cenas são identificadas como ilustrativas; não prometem uma demonstração exata de cada conselho, resultado garantido ou endosso da pessoa filmada. O material bruto não é redistribuído. Catálogo de seis roteiros sem reciclagem automática: no máximo três dias com dois por dia. Isso NÃO sustenta produção original permanente. Ao esgotar roteiros, retorna CATALOG_EXHAUSTED. Ampliar fontes e catálogo com revisão editorial continua pendente.

A validação técnica exige 15–28s, codecs, dimensões, tamanho, decodificação e áudio não silencioso. Gera SHA-256 e metadados. Aprovação editorial e consentimento de publicação ficam separados. Um técnico aprovado nunca vira automaticamente um vídeo editorialmente aprovado.

## Publicação: bloqueios oficiais

- Metricool Free: até 20 publicações por mês, insuficiente para 60–62. O usuário confirmou Free em 15/10/2026; plano não foi alterado.
- API REST do Metricool: apenas Advanced/Custom. O MCP do ChatGPT funciona em Free, mas não concede credenciais REST ao GitHub Actions.
- Direct Post próprio: requer auditoria para conteúdo público. Diretrizes excluem utilitário interno destinado apenas às contas da própria equipe. Exigem preview e controles/consentimentos oficiais por post.
- Não é correto resolver isso fabricando approved/consented_at nem prometendo que a aprovação do app sozinho garante autonomia.

Fontes verificadas em 15/10/2026:
https://help.metricool.com/pt/principais-diferencas-entre-os-planos-free-e-pagos-bl0v9
https://help.metricool.com/plans-add-ons-and-api-access-explained-xux1u
https://developers.tiktok.com/docs/en/content-sharing-guidelines

## Recuperação e duplicatas

- Grupos de concorrência compartilhados entre os dois workflows existentes evitam escrita concorrente de estado.
- Arquivos JSON gravados com substituição atômica.
- Conta esperada fixa e prefixo HTTPS explicitamente verificado exigidos antes de enviar.
- Bytes hospedados são validados novamente e comparados ao hash editorial.
- IDs e hashes previnem reenvio. Intenção SUBMISSION_UNKNOWN é persistida no GitHub antes da operação sem idempotência; erro/timeout incerto exige reconciliação, nunca reenvio cego.
- publish_id é persistido e consultado. Apenas PUBLISH_COMPLETE público com ID público retornado gera publicly_verified e URL.
- Vídeos vencidos sem aprovação provocam saída de falha, com contagens no resumo do Actions. Alertas do GitHub dependem das preferências de notificações do usuário; entrega de email não foi testada.
- Download de mídia tenta três vezes; renderização tenta duas composições. Não há retry cego de publicação.

## Custo e limites

Repositório público com runner Ubuntu padrão: execução Actions gratuita conforme https://docs.github.com/en/actions/concepts/billing-and-usage. Nenhum runner pago, serviço de créditos, cache ou artifact persistente foi adicionado. Workflow de criação limitado a 30 minutos. Novos arquivos até 20 MB; total de mídia limitado conservadoramente a 200 MB. Ao atingir o limite, para e avisa. O histórico Git ainda cresce: apagar arquivos não recupera o histórico. Não foi reescrito histórico. Hospedagem GitHub Pages é limitada; não constitui armazenamento ilimitado de vídeos. Não foi possível consultar faturamento/cotas da conta pelos conectores disponíveis.

Agendamentos GitHub podem atrasar. Repositórios públicos sem atividade por 60 dias podem ter schedules desativados. Portanto, não prometer pontualidade exata nem operação eterna sem manutenção.

## Testes

`python -m unittest discover -s automation/tests -v`

Cobrem identidade, consentimento, duração permitida, origem URL, separação técnico/editorial, teste privado versus post público, reenvio incerto e falha de persistência.

A tarefa ChatGPT existente CasaSemEsforço Diário deve ser usada para monitoramento/revisão e não como uma segunda fonte independente de geração/publicação. Não criar outra automação.

## Evidências executadas nesta sessão

- Alterações-base: commit 4dd8be44757ff67a318df206ee89c5c8b2dade43; revisão visual 46cd4a985bb18f98c4d9428528282d277eb52aef. Filas/workflows verificam o estado atual de main após adquirir a concorrência.
- Dois renders completos na nuvem: run 38812556550; dez testes passaram. Arquivos finais: casasem-2026-10-15-1-v2.mp4 (17,3s; 4.955.574 bytes) e casasem-2026-10-15-2-v2.mp4 (18,2s; 5.366.677 bytes). Ambos 1080x1920, H.264/AAC, áudio médio -16,4/-16,5 dB.
- Download HTTPS dos dois arquivos respondeu 200. SHA-256: 3457d840c9528b884fe72acde40958a6453e298dfca5793577d4090f59144054 e cbb87850eccfdca9f6a3efd20a9831bdcd7e29b476cc3a893b6dce2ea668fc8f.
- Diagnóstico real do runner: run 38812708271 retornou saída 2 e PUBLIC_VERIFIED_TOTAL=0, BLOCKED=2. Comportamento esperado para fila sem os controles oficiais exigidos.
- Teste único autorizado pelo usuário foi submetido pelo conector Metricool, não pelo GitHub. Post 397237451 / uuid 1522154177497940541, autoPublish=true, conta @.casasemesforo, horário aceito 15/10/2026 18:52 America/Sao_Paulo. A criação do agendamento foi confirmada por leitura posterior. Consultar state.json para confirmação pública atual; PENDING não significa publicado.
- O parâmetro mediaFiles do conector trata caminhos locais, não URLs. A tentativa inicial com URL foi rejeitada antes da criação. Confirmou-se fila vazia e foi feita uma única criação com a URL no campo media de info. Não repetir criação após resposta incerta.
- Não houve contratação, upgrade ou compra de créditos. Não se comprovou capacidade gratuita permanente de 60–62 posts/mês. Consulta do plano no painel parou na tela de login; não foram coletadas credenciais.

### Resultado final do teste de publicação

Metricool retornou PUBLISHED para o post 397237451, com autoPublish=true, TikTok video ID 7697016021223230726 e URL https://www.tiktok.com/@.casasemesforo/video/7697016021223230726. Estado e fila reconciliados. A consulta web direta do TikTok não abriu neste ambiente; a confirmação foi obtida do status do provedor TikTok no Metricool. Não atribuir ao teste prova de agendamento autônomo pelo GitHub, pois o agendamento foi feito pelo conector desta sessão.

Conclusão: AUTOMAÇÃO PARCIAL. A criação em nuvem e uma publicação real foram comprovadas. A recorrência completa de dois posts/dia, a capacidade gratuita mensal e renovação editorial permanente continuam sem comprovação. Não foi contratado nenhum serviço pago.

## Alternativa Buffer Free preparada em 15/10/2026

Buffer documenta API incluída no Free, uma chave, 100 requisições/dia e 3.000/30 dias. São 10 posts SIMULTÂNEOS na fila por canal; as vagas são liberadas após publicar, não é limite mensal. TikTok admite publicação automática. Esses limites são compatíveis, em princípio, com dois posts por dia. Isso ainda NÃO foi testado nesta conta.

Fontes oficiais:
- https://buffer.com/api
- https://support.buffer.com/articles/how-many-posts-can-i-schedule-in-advance-Kmy2IEecqm
- https://support.buffer.com/articles/using-tiktok-with-buffer-oGEroY9Of2
- https://developers.buffer.com/reference.html
- https://developers.buffer.com/guides/hosting-media.html

`buffer_runner.py` foi integrado como opção no workflow de publicação existente, sem criar outro agendamento. Não foi ativado. Usa os mesmos IDs, hashes, fila, estado e checkpoint durável. Exige nome exato da conta, canal conectado/desbloqueado e modo automático. Limita a oito chamadas por execução, 60/dia e 1.800/30 dias, deixando margem no Free. Uso por outros clientes não está incluído nesse contador; erros HTTP/limite interrompem a execução, sem contratar recursos. Consultas podem ser repetidas na próxima execução; criações ambíguas ficam bloqueadas para reconciliação.

Agendamento só é aceito após leitura posterior do post, canal, modo automático e horário. Publicação exige `sent`, `sentAt` e URL TikTok da conta exata devolvidos pela API. Esse resultado é evidência do provedor, não uma verificação independente da página pública. Notificação/manual nunca conta como publicação automática. Buffer mantém a conexão TikTok; se exigir nova autorização, o runner bloqueia e a reconexão do titular será necessária.

O workflow agora tem seis execuções por dia: 09:07 e 17:07 para agendar; 10:17, 11:17, 18:17 e 19:17 para verificar (Brasília). A criação continua às 08:30; slots editoriais continuam 10h/18h. Atrasos do GitHub são possíveis. Nenhum slot vencido é convertido silenciosamente em publicação imediata.

### Ativação inicial pendente (sem pagamento)

1. O titular precisa acessar/criar sua conta Buffer Free e conectar `@.casasemesforo` em https://account.buffer.com/channels, autorizando o fluxo oficial. Confirmar perfil público e publicação automática; não aceitar plano pago. A busca de plugins não retornou Buffer disponível nesta sessão. Nenhuma conta/sessão Buffer autenticada foi acessada.
2. Gerar a chave pessoal em Settings > API e salvá-la SOMENTE no secret `BUFFER_API_KEY` em https://github.com/ebooksproprof-dot/tiktok-automation/settings/secrets/actions. Nunca enviar a chave no chat, commit ou variável pública.
3. Em Actions > TikTok Online Runner > Run workflow, marcar `buffer_check_only`. Com uma única organização, o diagnóstico descobre o canal de nome exato e informa `BUFFER_CHANNEL_ID`; salvar esse ID como variável do repositório e repetir o diagnóstico. Não há publicação nesse modo.
4. Após diagnóstico válido, atribuir apenas vídeos novos e revisados a `publication_provider: buffer`, manter hash validado e horário futuro, e definir a variável `PUBLISHING_PROVIDER=buffer`. `approved/consented_at` do aplicativo Direct Post próprio não são fabricados nem reutilizados como consentimento Buffer. O post já publicado pelo Metricool continua protegido.
5. Executar um teste real pelo Actions e verificar a URL retornada antes de declarar operação autônoma. A chave/conexão e essa validação real continuam pendentes; os 20 testes locais passaram, mas usam respostas simuladas para Buffer.

O catálogo finito, revisão editorial, expansão das filmagens e armazenamento sustentável continuam pendentes. Conectar Buffer não resolve esses limites de produção. Não habilitar publicação de vídeos sem revisão de qualidade para mascarar essa pendência. A tarefa ChatGPT existente deve respeitar `publication_provider` e estado compartilhado, sem publicar a mesma mídia por Metricool em paralelo.
