# CasaSemEsforço — automação parcial

Leia [OPERATIONS.md](OPERATIONS.md) para limites, recuperação, custos e fontes oficiais.

- Criação: workflow existente às 08:30 de Brasília, até dois vídeos por dia. FFmpeg + Piper local, sem créditos de IA.
- Catálogo atual: seis roteiros não repetidos, capacidade inicial de três dias; ampliar o catálogo e as fontes continua necessário.
- Teste de criação: [run 38812556550](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/38812556550). Dois MP4 narrados em 1080x1920, 17,3s e 18,2s, verificados em 15/10/2026.
- Publicador: valida identidade @.casasemesforo, consentimentos oficiais, prefixo verificado e qualidade. Não atribui sucesso público ao teste privado antigo.
- Teste de diagnóstico: [run 38812708271](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/38812708271). Saída 2 esperada: dois vídeos vencidos sem aprovação; zero publicações públicas verificadas.
- Um teste Metricool foi aceito para 15/10 às 18:52, autoPublish=true, post 397237451 / uuid 1522154177497940541. Ver o resultado atual em state.json; agendamento não é prova de publicação.
- A tarefa ChatGPT CasaSemEsforço Diário foi atualizada sem duplicação para consultar este pipeline e respeitar limites/qualidade.

**Não há comprovação de publicação diária autônoma de dois vídeos com R$0.** Metricool Free permite 20 posts/mês; REST exige Advanced/Custom. O plano efetivo não foi exposto pelo conector, e o painel pediu login. A API própria TikTok exige requisitos oficiais e não aceita utilitário interno como finalidade. Não fabricar aprovações nem contornar restrições.

Nunca colocar tokens, client secrets ou refresh tokens neste repositório público. O broker existente foi preservado. Variável TIKTOK_VERIFIED_VIDEO_PREFIX só deve ser preenchida com um prefixo efetivamente verificado na plataforma.

Testes locais: `python -m unittest discover -s automation/tests -v`.
