# CasaSemEsforço 9.0 — retomada de 06/11/2026, Brasília

**Missão ainda bloqueada. Nenhuma publicação nova confirmada no TikTok.**

Partida da main remota `ae3a4ab`; alterações anteriores e os arquivos persistidos foram preservados. Os seis clipes continuam no inventário da branch experimental, que permanece a fonte de estado utilizada pelo coletor existente. Não houve nova geração de IA ou solicitação de serviço pago.

## Correções entregues

- Main `cbf4f40`: o publicador agora reconcilia também após o término do workflow AI30 Free Collector. O horário de coleta 09h10 vinha depois da preparação das 09h07; alterações da fila gravadas com `github.token` não disparam o evento push. O evento `workflow_run` resolve esse intervalo sem exigir computador pessoal ligado. Mantidos filtro da main, serialização de estado e crons de preparação/confirmação dos slots 10h/18h America/Sao_Paulo.
- Branch `feature/ai-video-hybrid-30s`, `ec184ff`: corrigida a passagem de metadados da montagem ao publicador. A duração medida 29,977 s era atribuída ao campo que o publicador exige como nominal 30; isso impediria todos esses envios, mesmo com os demais requisitos satisfeitos. O campo nominal agora corresponde ao plano de cenas; duração medida e tolerância continuam verificadas.
- A mesma correção antecipa a rejeição de visuais semelhantes para antes do upload no Release, preservando a conferência posterior e CAS da fila. Nenhuma barreira de direitos, consentimento, IA ou duplicação foi removida.
- Testes locais: 336 na main e 416 na branch do coletor, todos aprovados, sem testes pulados. Novas regressões exercitam a passagem real entre metadados dos dois componentes e impedem upload/escrita de inventário quando o gate visual reprova.

## Montagem real

Os seis MP4 existentes foram novamente conferidos por SHA-256 e montados com o renderizador preservado, usando os módulos compartilhados da main e narração CPU. Resultado: 29,977 s, 1080×1920, H.264 yuv420p/AAC, 9.893.920 bytes, SHA-256 `e6e3c238dc6c80179643b99aa47d83b8fc20b95262690811a0b3f1138bae310a`. Decodificação, streams de áudio/vídeo e detectores de preto/silêncio aprovados. Arquivo local: `/workspace/ai30-validation/mission90/render/experimental81-c93e8b19e3058d3f.mp4`.

Isso é prova técnica de montagem. Não significa autorização comercial, originalidade aprovada ou publicação.

## Bloqueios concretos

1. **Versão do ambiente desta tarefa.** Apesar da publicação informada pelo titular, esta instância continua reportando `spec_revision=1`, versão `cecfgver_6aed1a382044819ab9f1a38f05a3b71d`, política enforced e zero domínios personalizados. Requisições reais a api.github.com, huggingface.co, www.pexels.com e developers.buffer.com foram recusadas no CONNECT do proxy com 403. O rascunho salvo já contém esses domínios. Não se afirma que o titular deixou de publicar: a versão publicada não está refletida na instância observada desta conversa. A ação necessária é vincular/reconectar a tarefa à versão publicada que contém as regras, ou iniciar uma tarefa nessa versão; não há ferramenta disponível aqui para alterar esse vínculo.
2. **Direitos.** Os seis registros continuam com `commercial_license_clearance=false`. Licenças Apache-2.0 dos repositórios de código Wan/LightX2V e MIT do wrapper Kokoro foram verificadas na etapa anterior; ainda faltam os termos/revisões exatos dos pesos, LoRA/quantização, referências Pexels e voz. O acesso bloqueado impede completar essas consultas. Não se fabricou aprovação nem se confundiu consentimento do titular com licença comercial.
3. **Novidade visual.** O quinto clipe (slot 4, hash `1704813d…`) aciona o gate existente contra a fonte Pexels 9473227 registrada no histórico. Os cinco frames amostrados têm distância Hamming mínima entre 4 e 8, dentro do limiar de semelhança usado pelo projeto. É um achado heurístico que exige revisão, não uma prova jurídica de cópia. O clipe foi preservado, e o bloqueio não foi ignorado.
4. **Publicador.** Há 16 publicações antigas confirmadas no estado, nenhuma delas conta como teste novo. Não há credencial Buffer local, mas isso não demonstra ausência do secret já existente no Actions. A API GitHub bloqueada impede disparar o diagnóstico `buffer_check_only` e acompanhar suas respostas autenticadas daqui. Não pedir token TikTok paralelo nem extrair secrets dos runners.

## Automação e limite R$0

[Run 42160430701](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/42160430701) executou a main alterada e terminou verde. Naquele momento, antes da janela de preparação, os slots do dia ainda estavam `NO_VIDEO` sem gerar falha antecipada. Essa conclusão verde não comprova publicação nem disponibilidade de dois vídeos por dia.

O publicador continua preparado para 10h/18h no GitHub Actions, sem depender de computador pessoal. A capacidade para dois vídeos originais de 30 s/dia não está demonstrada: seriam 12 clipes de 5 s; a estimativa do controlador é 12×45 = 540 s de GPU, acima dos 300 s/dia documentados para Free no planejador. Esses números são estimativas existentes, não saldo medido do provedor. Fallbacks menores permanecem possíveis sob os gates existentes, mas não se afirma produção diária garantida. Nenhuma cota foi reiniciada ou ampliada.

## Retomada necessária

Após esta tarefa ter acesso à versão publicada correta: verificar as licenças exatas e vincular evidência aos hashes; revisar o achado de semelhança sem excluir o histórico; testar a conexão Buffer em modo somente leitura; então executar o envio de uma única peça apta pelo publicador durável existente, respeitando slots e idempotência. Exigir leitura posterior com ID/URL real do TikTok e validar os próximos slots antes de declarar a missão concluída.

Metadados, hashes, observação de runtime, respostas de rede, testes e bloqueios: [mission90-evidence.json](mission90-evidence.json).
