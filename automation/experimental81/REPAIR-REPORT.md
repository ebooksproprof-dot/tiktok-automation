# Correção CasaSemEsforço — 05/11/2026 (Brasília)

Base de desenvolvimento: `ff2776ff43c707ad525e35b188fafac1af921653`.

## Resultado confirmado

- Reproduzida com os seis MP4 existentes a falha `ValueError: Caption cannot fit safely; shorten editorial text`, em `caption_layout.layout`, chamada por `render.compose`. O roteiro inteiro de uma frase não cabe em duas linhas seguras. Não é falta de clipes ou de créditos.
- Corrigida a divisão de legendas usando medidas da fonte, preservando palavras e limites de cada frase. Tempos internos proporcionais ao texto; não se afirma alinhamento palavra por palavra.
- Montagem real pelo caminho `auto_finish --render-local`: 29,977 s, 1080×1920, H.264 yuv420p/AAC, 9.877.241 bytes, SHA-256 `46e80ddf7a7258f0a731e111aea9d63d9c10b295ec98abab00433ef5aafe4892`. Decodificação completa, áudio, ausência de preto/silêncio prolongado e alinhamento dos streams aprovados.
- Fallbacks reais com 3, 4 e 5 cenas: 14,975 s / 19,975 s / 24,977 s. Não houve loop ou geração de IA nova. Os mesmos gates de procedência, consentimento, direitos e rótulo IA continuam obrigatórios no publicador. Fallback automático exige exaustão de cota confirmada.
- 401 testes passaram antes da correção; 414 após, incluindo regressões e verificações com FFmpeg. Evidências, hashes dos arquivos preservados e metadados em `evidence/repair-validation.json`. Os MP4 e as vozes ficam fora do checkout, em `/workspace/ai30-validation`, sem acrescentar binários ao Git.
- Inventário, ledger, fila, histórico visual e estado de publicações não foram reescritos. Os seis fontes foram baixados de Releases e conferidos por SHA-256. Uma futura conclusão de episódio arquivará os registros completos dos clipes no histórico antes de avançar o inventário.

## Workflow e publicador

O collector obrigatório agora falha quando a montagem falha ou é pulada por falha de pré-requisito. A tentativa opcional de coleta ainda pode esgotar cota sem descartar os clipes existentes. Um workflow verde nunca é declarado prova de publicação.

Preservados os cron existentes do publicador e os slots 10h/18h America/Sao_Paulo. A montagem passa a procurar ambos, inclusive respeitando reservas antigas no formato Metricool. Corrigidos: consultas a posts cancelados editorialmente; sucesso aparente durante a espera de reconciliação de posts sem evidência; limite `MAX_NEW_POSTS_PER_RUN` ignorado; timestamps inválidos na confirmação; URLs públicas antigas mantidas após perda de confirmação. Preservados checkpoints antes da mutação remota, reconciliação após resultado incerto e todos os controles de cota/backoff.

As páginas públicas dos runs [42105299182](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42105299182), [42097979809](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42097979809) e [42088832562](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42088832562) mostram erro GraphQL genérico ou backoff. A consulta indevida de cancelados é um defeito reproduzido; ainda não se pode afirmar que seja a única causa remota. Acrescentado diagnóstico de códigos GraphQL permitidos, sem imprimir mensagens/credenciais do provedor. Não se reiniciou nem ampliou cota.

## Bloqueios externos e publicação

**Nenhuma publicação nova confirmada. Nenhuma nova chamada de geração foi feita.**

1. A API GitHub (`api.github.com`) foi negada pela política de rede; `git ls-remote` e downloads públicos por HTTPS funcionam. O log completo de 42117313305 não pôde ser lido. A página pública confirma saída 2 da montagem e workflow Success; a causa acima foi reproduzida localmente, não extraída de um traceback remoto que o código antigo ocultava.
2. Licenças do código Wan/LightX2V (Apache-2.0) e wrapper Kokoro (MIT) foram consultadas e hashadas. Isso não resolve os termos dos pesos/LoRA/revisões exatos, referências Pexels e voz. O inventário declara `commercial_license_clearance=false` para todos os seis clipes. Não foi alterado para simular aprovação. Novos gates exigem evidência por hash e componente antes de upload/fila e novamente antes de publicar; a dispensa de prévia não marca `editorial_approved=true`.
3. O ambiente não fornece variável/binding Buffer local. Isso não prova ausência ou invalidade dos secrets já existentes no Actions. Não é preciso criar credenciais TikTok paralelas: primeiro liberar a API GitHub para verificar o runner e seus requisitos existentes. Se o Buffer devolver autenticação negada, renovar apenas `BUFFER_API_KEY` em GitHub Actions Secrets; se desconectado, reconectar a conta exata `@.casasemesforo` no Buffer com publicação automática e plano sem custo adicional.
4. Foram salvos no rascunho do ambiente `install_script`, `start_skill` e domínios de diagnóstico/licença/publicação. O salvamento não aplica rede nem publica a configuração: revisar/salvar nas configurações e publicar o ambiente para retomar as operações bloqueadas. Não inserir segredos no chat ou no Git.

Após liberar acesso: verificar os termos exatos e registrar evidência vinculada aos hashes; checar a conexão Buffer sem submissão; executar o collector existente sem gerar novamente os seis clipes; reconciliar a fila antes de submeter uma única peça; aguardar confirmação `sent` + timestamp válido + URL `/@.casasemesforo/video/ID` obtida em leitura posterior. Não contar posts antigos, upload, render ou agendamento como cumprimento desta missão. Disponibilidade recorrente de ZeroGPU e capacidade gratuita diária não foram demonstradas.
