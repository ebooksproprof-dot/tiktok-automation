# Auditoria técnica 9.1

Escopo: retomada da main `05bfc62`, ambiente efetivamente aplicado, material existente, recuperação de uma prova gratuita e fluxo de publicação existente. Não é certificação jurídica ou avaliação independente por revisor humano. Houve segunda passagem de revisão técnica e validação do arquivo da nuvem em processo separado; as limitações abaixo não são apagadas por testes verdes.

## Verificações e correções

- **Estado preservado:** branch inicial `work` limpa em `2f01b0d`; main recuperada do remoto; trabalho em branches novas baseadas na main e na feature existente. Sem reset, force push ou exclusão. Commits concorrentes do Actions incorporados por rebase.
- **Rede:** nova configuração `cecfgver_6aed221edb8c819aa43725243923e272`, unrestricted/enforced e observações atuais. Git fetch/push, dispatch e consultas públicas funcionaram. 403 de `/actions/secrets` e `/actions/permissions` significa permissão insuficiente nesses endpoints, não domínio bloqueado. CDN Pixabay respondeu 200 com User-Agent do aplicativo. Não se solicitou republicação do ambiente.
- **Licenças:** cadeia exata do Space recuperada; descoberta LoRA Wan2.1, conversões bf16 e AOTI. Falta de comprovação dos derivados/revisões históricas mantém os seis clipes sem autorização comercial. Nova prova usa fonte Pixabay individualmente verificada, voz Kokoro e CPU, com créditos. Ver `MISSION-9.1-LICENSES.md`.
- **Quinto clipe:** todos os seis SHA reconferidos; nova amostragem reproduz distâncias 4/8/7/5/6 contra Pexels 9473227. Mesma referência visual da geração e do histórico, arquivos diferentes. Classificação: semelhança visual excessiva, não duplicação binária; não há evidência de inventário errado ou justificativa para desligar o gate. Não usado na prova pública.
- **Prova curta:** roteiro contextual, 15,166667s sem loop, 1080×1920, Kokoro pf_dora, legendas medidas; preto/silêncio acima dos limites = zero. Readback independente do Release e inspeção da contact sheet final. Não foi realizada escuta humana nem alinhamento fonético palavra a palavra.
- **Idempotência:** a prova verifica conceito e roteiro já reservados, source hash, originalidade contra fila/estado/histórico, capacidade máxima de duas reservas/dia, readback do Release e revalidação pelo publicador. Reexecução após fila gravada recusa nova peça. Buffer continua sendo o único publicador usado; checkpoint precede createPost e resultados incertos não são reenviados.
- **Estados distintos:** montagem/fila não publicam. `NOT_READY`/`WAITING_FOR_QUOTA_CONFIRMATION` agora retornam erro na etapa obrigatória do coletor. Licença é checada antes de gastar CPU renderizando. `PUBLISHED` exige resposta real `sent`, modo automático, timestamp e permalink do perfil exato.
- **Monitoramento:** primeira leitura após dueAt não é mais adiada por uma confirmação recente de agendamento; retentativas posteriores continuam limitadas a 30min. Regressão cobre a fronteira e a restauração do throttle após tentativa/timeout.
- **Infraestrutura:** crons e workflows recorrentes ativos, sem PC pessoal. Horários padrão preservados (10h/18h BRT); o primeiro teste explicitamente imediato usa exceção registrada, consumindo uma das duas reservas diárias. Instalação do runner evita apt quando ferramentas já existem. Não se habilitou runner maior, pagamento, assinatura ou nova rota de publicação.

## Evidência de testes

- Diagnóstico Buffer real, run `42161484178`: 336 testes, canal correto e automático, nenhum createPost.
- Main com a prova: 341 testes locais; 341 testes na nuvem no run `42162321026`.
- Correção da primeira tentativa: `MEDIA_STORAGE=release` estava afetando fixtures de teste; variável limitada à etapa real de renderização. Run `42162148165` falhou antes de renderizar/enviar e não foi tratado como publicação.
- Coletor: 91 testes pertinentes locais e 91 no run `42162290740`; inclui dois novos testes para impedir sucesso falso e renderização sem licença. Não repetir as 416 regressões anteriores como se fossem evidência nova.
- Reconciliação Buffer: 58 testes pertinentes locais aprovados, incluindo a primeira checagem após o horário marcado e confirmação explícita somente por leitura.
- Reexecução real `42164108196`: 344 testes cloud, zero chamadas Buffer, zero reenvios; mesmo ID remoto preservado enquanto o post aguardava dueAt. Modo `--confirm-post` exige reserva existente e evidência pública, não chama createPost e conserva o orçamento/cooldowns.

## Limites de continuidade

Buffer Free: dez posts simultaneamente na fila, 1.000 chamadas/canal/30d; controle local de 900/30d preservado. Duas publicações/dia não são excluídas por esses limites isoladamente. Metricool Free: 20 posts/mês e entitlement API gratuito não demonstrado; não usado como rota paralela.

ZeroGPU Free: 300s/dia, anônimo 120s/dia; resets 24h após primeiro uso, não meia-noite. Estimativa existente de 45s/clipe: dois vídeos de 30s exigiriam 540s. Dois de 15s exigiriam 270s **antes de falhas, rejeições e espera**; isso não é capacidade sustentada comprovada. Os seis clipes atuais permanecem bloqueados por direitos, e as referências finitas já possuem histórico visual.

A prova gratuita consome uma fonte inédita revisada; não demonstra reposição automática diária. O acervo permanente e os metadados foram preservados, mas o limite intencional de seis coleções mensais também impede prometer operação indefinida sem política de arquivo. Não se declara 2/dia nem CASASEMESFORÇO OPERACIONAL com essas pendências.

A confirmação nova de publicação deve ser registrada em `MISSION-9.1.md` e no snapshot de estado correspondente; o sucesso da prova de renderização não a substitui.
