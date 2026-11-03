# CasaSemEsforço 8.2 — retomada sem Work (03/11/2026)

**Estado: experimental, isolado e preservado. NÃO AUTORIZADO PARA PUBLICAÇÃO.**

Branch: `feature/ai-video-hybrid-30s` (base 8.1). A branch `main`, a fila Buffer, o histórico do TikTok, os agendamentos e o job diário não foram alterados por esta retomada.

## Evidência nova: o compositor aceita 30 segundos 100% IA

- `automation/experimental81/render.py` agora contém perfil `AI_ONLY=(30,0)`.
- Exige 30 segundos *efetivos* de fontes declaradas como IA. Se a entrada contiver apenas 5 segundos IA e 25 segundos reais, não se apresenta como AI_ONLY.
- Para clipes Wan de 5 segundos, seis clipes distintos formam 30 segundos. Sem repetição de segmentos, sem extensão artificial de duração e sem filme real para completar.
- `test_ai_only81.py` verifica seleção do perfil, composição de seis trechos únicos e falha quando falta mídia IA.
- **Isto comprova o planejamento do compositor, não a geração de seis clipes nem um MP4 100% IA final.**

## O que causou o cancelamento do workflow 8.1 anterior

Run [41480270780](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/41480270780) cancelado após aproximadamente 18 minutos: instalação `apt-get` em espelho lento. Os testes nem iniciaram. Não foi erro no modelo Wan ou na composição.

Correção:
- Workflow `.github/workflows/ai-video-experimental81.yml` separa testes rápidos sem `apt` dos testes de mídia dependentes de CPU/FFmpeg.
- Execução [41578325982](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/41578325982): **43 testes, zero falhas, quatro ignorados por falta de FFmpeg**. Não acionou geração/publicação.
- Execução [41578685065](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/41578685065): **56 testes, zero falhas, quatro ignorados**, incluindo política de cota e CAS com simulações.
- Prova de mídia completa é somente opcional (`workflow_dispatch`, `render_demo=true`) e não foi executada nesta retomada. Pode ainda sofrer lentidão no download das dependências.

## Cota gratuita: previsão, NÃO medição real

`daily_budget.py` e `github_ledger.py` adicionam controle preventivo:
- janela de 24 horas após primeira reserva, e não virada da meia-noite;
- conta anônima documentada: 120 segundos; conta gratuita autenticada: 300 segundos;
- uma estimativa **não medida** de 55 segundos de cota por clipe Wan 480x832, 5 segundos, **4 steps** (derivada de fórmula publicada, com margem);
- máximo matemático estimado de **2 clipes/10s por janela anônima** ou **5 clipes/25s por janela de conta Free autenticada**, se cada chamada for boa, a estimativa refletir o faturamento e o serviço permitir;
- para 30 segundos são necessários seis clipes; a capacidade diária **não está comprovada**, mesmo para Free com 4 steps;
- o teste com 3 steps para reduzir consumo NÃO foi validado visualmente, portanto não está habilitado;
- hash de solicitação não pode ser reutilizado e resultado remoto incerto não pode ser reenviado automaticamente;
- `github_ledger.py` prepara reserva remota via GitHub Contents API com CAS e leitura posterior, exclusivamente na branch experimental. O callback ainda **não está conectado a um job recorrente**.

O código não implementa login HF nem garante cotas/custos. Para evitar cobrança, a implementação anterior chama Gradio `token=False`; não pode supor a cota Free autenticada nem saldo de um usuário.

## Mídia e publicação

O projeto conserva o teste 8.1: dois clipes IA reais Wan 5.0625s (480x832,16fps), qualidade experimental e aprovação comercial pendente; montagem híbrida C de 30s (5s IA+25s materiais de referência), não destinada à publicação. Nenhum clipe IA adicional foi gerado nesta retomada.

A configuração `config.json` expressa meta de **um vídeo 30s 100% IA ao dia**, com `AI_VIDEO_EXPERIMENTAL_ENABLED=false`, `publication_enabled=false`, `production_state_writes_allowed=false`. Não há nova fila de TikTok, cron gerador, postagem programada ou Release 100% IA criada.

Conta alternativa OpenArt Free conectada nesta sessão: 40 créditos disponíveis; menor opção de vídeo listada cobra 50 créditos por geração. **Nenhuma geração foi solicitada e nenhum crédito foi gasto.**

## Prioridades para chegar à automação real

1. Comprovar seis clipes IA únicos com qualidade aceitável e direitos comerciais de todos os modelos/adaptadores, sem usar filmagens reais.
2. Medir o débito verdadeiro de cota por geração e uma janela de renovação completa. Se precisar de menos steps, medir a perda de qualidade, não presumir.
3. Comprovar fornecimento recorrente de ao menos 30 segundos de conteúdo IA *útil* por janela de 24 horas antes de habilitar qualquer cron.
4. Usar apenas contas/cotas oficiais, sem burlar limites ou ativar faturamento automático.
5. Testar compositor/voz Kokoro/legendas e verificação audiovisual integral no runner CPU.
6. Integrar ao estoque com aprovação editorial específica e termos comerciais, antes de qualquer envio por Buffer.
7. Manter proteção global contra duplicatas, preservação do legado e rollback.

## Resultado

**Código novo salvo e os testes rápidos de CI passaram. Não está operando geração diária de 30s nem publicação automática de IA.** O bloqueio atual é a falta de seis cenas IA aprovadas por dia e de consumo/cota real comprovados, além da pendência de licença. Prometer que a renovação das fichas disparará publicação automática seria enganoso.

Para retomar: ler este checkpoint e o [CHECKPOINT 8.1](CHECKPOINT.md), conferir o head da branch, depois investigar uma fonte realmente recorrente de cenas IA e executar provas limitadas, sem alterar `main` antes de aprovar o resultado.
