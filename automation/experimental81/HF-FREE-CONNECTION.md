# CasaSemEsforço — única etapa manual: vincular a conta Hugging Face Free

Situação em 03/11/2026: o pipeline GitHub já consegue gerar e armazenar clipes de 5.0625 s por IA, mas as duas gerações comprovadas foram **anônimas**, usando a cota de 120 s. O acesso aos **300 s diários de uma conta Free** só é possível depois que o titular configure um token de acesso no GitHub Actions.

## Passo de autenticação do titular — NÃO copiar o token para um chat

1. Abra https://huggingface.co/settings/tokens na conta que tem a cota Free e crie **New token**.
2. Dê o nome `CasaSemEsforco-GitHub`. Escolha o papel **read** (sem escrita, sem cartão ou cobrança). Nunca use um token administrativo ou uma chave de pagamento.
3. Copie o token somente para o formulário seguro do GitHub: https://github.com/ebooksproprof-dot/tiktok-automation/settings/secrets/actions
4. Clique em **New repository secret**, digite o nome **`HF_FREE_TOKEN`**, cole o token em **Secret** e clique em **Add secret**.
5. Para testar, abra https://github.com/ebooksproprof-dot/tiktok-automation/actions/workflows/ai30-free-collector.yml e escolha **Run workflow** → branch `main`. Também poderá aguardar o cron já instalado (03:10, 09:10, 13:10 Brasil).
6. Consulte o job **Attempt bounded ZeroGPU generation and persist every useful clip**. Não compartilhe senha nem o texto do token com o assistente.

## Código já preparado

- `auto_collect.free_hf_identity()` verifica no `/api/whoami-v2` que o token é de uma conta **user Free (isPro=false)**, sem plano pago. Conta desconhecida, token inválido e isPro=true são bloqueados.
- `wan_probe.run(..., hf_token=..., steps=3)` envia as requisições oficiais de uma conta Free autenticada; sem token, preserva o modo anônimo de 4 steps.
- `daily_budget.estimated_request_seconds(3)=45`, enquanto 4 steps = 55. Estimativa conservadora da duração **solicitada** ao decorator ZeroGPU, não medição do tempo efetivamente debitado. Seis clipes estimados 6 × 45 = **270s ≤ 300s** com margem de 3%, sem direito a prometer qualidade.
- O controlador limita a seis clipes por execução autenticada, com hashes exclusivos e reservas CAS. A cota real de Hugging Face prevalece sobre estimativas; serviço pode rejeitar ou devolver material ruim.
- Uma migração **anônima → Free** em uma mesma janela preserva todo o consumo anônimo anterior no ledger, não reinicia o período ou permite voltar a anônimo na mesma janela. Os dois primeiros clipes já gerados permanecem no estoque.
- Quando houver seis clipes utilizáveis, `auto_finish.py` tenta montar 30s com Kokoro/FFmpeg e passar pela fila única do Buffer; a efetiva postagem, qualidade audiovisual e compatibilidade de licença precisam ser verificadas. Nenhuma postagem foi comprovada até agora.
- Clipes futuros são armazenados em GitHub Releases **semanais**, evitando ultrapassar o máximo operacional de 95 assets por Release.
- Custo adicional obrigatório R$0. Não habilitar PRO, pay-as-you-go, billing, computadores pessoais ou geradores pagos.

## Diagnóstico

Se o workflow mostrar modo `anonymous`, o Secret não foi recebido, não foi autorizado ou não estava presente naquele runner. Se mostrar `HF_FREE_ACCOUNT_VERIFICATION_FAILED_NO_AUTH_CALL`, revise o token *dentro do GitHub* e não faça cópias em conversas. Se falhar com `QUOTA_OR_GPU_BUDGET`, aguarde a reposição do Hugging Face; não reenvie a mesma solicitação com resultado desconhecido.

O principal bloqueio que o assistente **não pode resolver via conector GitHub atual** é a criação de segredos do repositório, pois não há permissão/ação de administrador para escrever `secrets`. Somente o titular deve preencher o token no formulário seguro.
