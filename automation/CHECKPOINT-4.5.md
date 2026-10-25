# Checkpoint 4.5 — 25/10/2026

Estado PARCIAL. HEAD inicial remoto faf113364b296b7af82f28b94db79c653326d625, posterior ao checkpoint informado pelo usuário. Nenhum histórico ou consentimento alterado.

Correção funcional: aquisição pode tentar duas fontes por consulta/provedor quando a primeira falha na validação. Mantidos quatro downloads totais por execução, duas aquisições, cache, rejeições e revisão editorial. Falhas de cota, autenticação, servidor ou transporte interrompem aquele provedor; não são tratadas como convite a nova tentativa.

Regressão local: 268 testes aprovados, incluindo três cenários novos de recuperação, teto global e interrupção de provedor. Testes novos usam respostas simuladas; não provam aquisição real ou nova produção. Push dispara aquisição existente, cujo resultado deve ser conferido antes de afirmar operação real.

Estado recuperado: dez itens não submetidos, zero autorizados; 12 publicações históricas verificadas. Vídeos de 24/10 e 25/10 já existem na fila, produzidos anteriormente: não contar como novos nesta etapa. Reserva de seis vídeos futuros válidos não certificada. Nenhum novo vídeo, agendamento ou publicação executado neste checkpoint.

Avatar: não repetir a inferência EchoMimic sem hipótese nova; resultado anterior atingiu difusão CPU e excedeu orçamento sem MP4. FFmpeg/Kokoro/Piper preservados.

Próximo passo: conferir a execução de aquisição disparada por este commit, revisar cenas novas e seu vínculo com os roteiros, renderizar somente candidatos inéditos revisados e atualizar o lote em public/review44.html. Consentimento explícito segue obrigatório. Custos adicionais contratados: R$0. Continuidade sustentada de dois vídeos publicados por dia ainda não comprovada.
