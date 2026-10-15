# CasaSemEsforço — operação e limites

Status em 15/10/2026: AUTOMAÇÃO PARCIAL. Renderização não equivale a publicação.

## Identidade verificada

Metricool brand 7212680, TikTok @.casasemesforo. O histórico do Metricool retornou posts deste perfil em 03, 04, 11 e 12/10/2026. Nenhum agendamento foi retornado para 15–18/10. Não usar o teste privado sandbox-test-001 como prova de publicação pública.

## Criação

O workflow existente roda às 08:30 America/Sao_Paulo, com slots pretendidos às 10h e 18h. FFmpeg gera H.264 1080x1920, AAC, yuv420p, faststart. Piper 1.3.0 sintetiza voz brasileira Faber localmente em CPU, sem API paga, créditos, Vidnoz ou CapCut. Model card: https://huggingface.co/rhasspy/piper-voices/blob/main/pt/pt_BR/faber/medium/MODEL_CARD (dataset CC0; repositório de vozes MIT). Hash do modelo fixado no código.

Filmagens Pexels existentes: 9473227, 9472849 e 9462884, sob https://www.pexels.com/license/. Cenas são identificadas como ilustrativas; não prometem uma demonstração exata de cada conselho, resultado garantido ou endosso da pessoa filmada. O material bruto não é redistribuído. Catálogo de seis roteiros sem reciclagem automática: no máximo três dias com dois por dia. Isso NÃO sustenta produção original permanente. Ao esgotar roteiros, retorna CATALOG_EXHAUSTED. Ampliar fontes e catálogo com revisão editorial continua pendente.

A validação técnica exige 15–28s, codecs, dimensões, tamanho, decodificação e áudio não silencioso. Gera SHA-256 e metadados. Aprovação editorial e consentimento de publicação ficam separados. Um técnico aprovado nunca vira automaticamente um vídeo editorialmente aprovado.

## Publicação: bloqueios oficiais

- Metricool Free: até 20 publicações por mês, insuficiente para 60–62. O plano real da conta não é exposto pelo conector; não foi presumido nem alterado.
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
