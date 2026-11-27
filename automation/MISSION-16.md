# Missão 16 — política e retomada fotorrealista

Partida em main `3e6ccac`, preservando todos os commits posteriores a `9d258ad`.
Checkpoint remoto: `checkpoint/mission16-before-3e6ccac`. Sem force push.

O proprietário reprovou o visual ilustrado da Missão 15. A decisão persistente
está em `editorial_decisions.json`, vinculada aos hashes das versões conhecidas,
e no histórico de `mission15-evidence/episode/video-review.json`. O WAV, o roteiro,
o MP4 reprovado e as provas anteriores não foram apagados.

`photoreal_policy.reject_incompatible` bloqueia a origem ilustrada e os arquivos
reprovados antes da voz. A verificação é aplicada ao estágio da Missão 15, à
biblioteca visual e à política de saída usada por Buffer, TikTok direto e estoque.
`require_photoreal` exige um recibo independente vinculado ao hash do MP4, às
fontes originais e aos oito critérios de revisão. Alterar um booleano no relatório
técnico não cria esse recibo. O método de avaliação e a presença de revisão humana
são campos distintos; testes automatizados não se apresentam como escuta ou
avaliação humana.

O registro `photoreal_reviews.json` separa fontes, narrativa e vídeo completo.
Atualmente não há vídeo final aprovado. As duas fontes novas têm aparência
fotorrealista, mas uma não demonstra as gotas e a outra mostra apoio inadequado.
Não foram usadas para fabricar uma montagem de 30 segundos.

A política de definição mede o original e seu recorte real. O mínimo normal é
720×1280; 576×1024 só pode ser considerado com comparação registrada de ampliação
convencional de até 1,875× e revisão de nitidez. Abaixo desse piso, a fonte é
rejeitada. Esses são limites conservadores do projeto, não requisitos oficiais do
TikTok. Uma exportação 1080×1920 não altera a definição nativa nem a aprovação.

## Geração e continuidade

`experimental81/wan16.py` reutiliza o cliente, a gravação CAS, o ledger compartilhado
e o armazenamento por hash do coletor existente. Space/modelo/revisões permanecem
fixados e a conta deve ser Free, sem PRO. Cada execução faz no máximo uma chamada,
em 576×1024, 8 passos e 5 segundos, respeitando os controles publicados do Space.
O limite superior da reserva do próprio provedor é 110 segundos; o ledger registra
isso como estimativa conservadora, nunca como débito observado.

As duas chamadas reais produziram arquivos persistentes de 5,041667 s. A terceira
execução automática foi retida pelo planejamento de cota, sem chamar GPU. Nenhuma
identidade, IP, fila ou contador foi trocado para obter outra cota.

O plano contém oito tomadas finitas. O modo `auto` escolhe somente uma tomada
nunca solicitada; resultados incertos e falhas continuam registrados. Rejeição de
cota pelo provedor impõe espera conservadora de 24 horas. O cron 09:55/21:55 UTC
continua o episódio quando a janela legítima permitir. Ao esgotar o plano, aguarda
revisão; não entra em um ciclo infinito de novas sementes.

O CLI do coletor antigo conserva seu perfil e suas provas, mas não gera novos
480×832 para produção profissional. A geração em definição maior está no fluxo
limitado da Missão 16 e usa o mesmo ledger; não é um novo publicador.

`mission16_episode.json` registra a nova identidade de episódio, o WAV e roteiro
preservados, fontes geradas, segundos qualificados, bloqueios e arquivos próprios.
Não existe MP4 B final. O áudio só poderá ser reutilizado em uma montagem após
aprovação explícita da identidade Lara. Nenhuma nova síntese foi feita nesta missão.

## Aquisição e direitos

A busca da Missão 16 usa o mesmo cliente identificado e os mesmos validadores de
origem, bytes e direitos do pipeline existente. Não troca para proxies ou outra
identidade quando uma fonte retorna 403. Os erros agora preservam o código HTTP
sem expor credenciais. Metadados explicitamente ilustrados/animados são rejeitados
antes do download; o conteúdo restante ainda precisa de revisão visual.

O primeiro fluxo real obteve sete filmagens, três com autorização documental
vinculada aos bytes. A triagem também encontrou ambiguidade em “rack” (redes,
bibliotecas) e “glass” (fabricação/porta de lavadora). As novas consultas exigem
contexto doméstico combinado; o recorte central do filme de lavagem de copo
também permanece em revisão, pois perde a ação principal.

Uma dependência ausente (`playwright`) impedia a rota existente de atualização da
licença em quatro candidatos. O workflow passou a instalar a dependência e seu
navegador quando necessário. Não se aproveita um erro de importação para declarar
direitos verificados. Somente manifestos e folhas anotadas são artefatos; os
originais de terceiros não são redistribuídos por Release.

## Aprovação e publicação

O áudio da Missão 15 mantém seus hashes, os ASRs de 60 palavras e a proteção da
referência privada. Aprovar Lara só resolve a identidade vocal. O episódio A
continua proibido e a versão B depende de fontes, narrativa, enquadramento,
legendas, originalidade, validação final e recibo fotorrealista próprios.

Buffer, teto de três por sete dias, intervalo mínimo de 48 horas e preferência
10h/18h BRT foram preservados. Custo adicional R$0; sem GPU paga, ElevenLabs ou
computador pessoal. O estoque continua zerado de forma explícita. Não há promessa
de uma frequência semanal antes de existir reposição qualificada demonstrada.

[Relatório e provas reais](mission16-evidence/REPORT.md).
