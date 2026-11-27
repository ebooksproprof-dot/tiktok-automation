# Missão CasaSemEsforço 14.0 — resultado comprovado

**Implementada na main; operação comercial completa ainda bloqueada.**
Custo adicional contratado: **R$0**. Sem GPU paga, ElevenLabs ou dependência de
computador pessoal. Nenhum vídeo foi enviado ao TikTok nesta missão.

## Entregas e evidências

| Item solicitado | Resultado |
|---|---|
| 1. Arquivos modificados | Relação em `modified-files.json`; integração e configuração em `../MISSION-14.md`. Principais grupos: Chatterbox/worker/cache, narração, renderizadores convencional/Wan, enquadramento, legendas, originalidade, estoque, publicação, workflows e testes. |
| 2. Commits | `8697bb7` integração inicial; `2839d94` memória/ASR/evidências; `f468d57` persistência de provas e roteiros maiores. Commit final de relatório/controles consta no histórico da main. Alterações automáticas concorrentes foram preservadas com fetch/rebase, sem force push. |
| 3. Modelo | ResembleAI/Chatterbox-Multilingual-pt-br, V3 brasileiro, revisão b3952f18bc2eaa72b9bd7c17d2c4653bcad4770d; language_id pt. MIT declarado. |
| 4. Voz feminina | **Não selecionada/ativada**: identidade única configurada como pendente. Nenhum exemplo da demo foi clonado. |
| 5. Direitos da referência | **Pendentes**: não existe prova de referência própria/licenciada/autorizada no checkout. Exigidos titular, autorização comercial, hash e aprovação auditiva. Modelo MIT não substitui esses direitos. |
| 6. Tempo real | GitHub Actions CPU: **32,04s de áudio em 272,263s de inferência; 308,204s com carregamento**, pico **4.584,7 MiB**. O áudio foi normalizado para aproximadamente 30s na prova posterior. Não é benchmark de uma voz feminina aprovada. |
| 7. Infraestrutura gratuita | **Execução técnica comprovada em runner padrão de repositório público**. Sem GPU/serviço faturável. Não comprova qualidade vocal aprovada ou cadência visual sustentável. |
| 8. Demonstração de voz | [WAV técnico de aproximadamente 30s](https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/mission14-evidence/voice.wav). Condicionamento interno do checkpoint, **não é identidade feminina aprovada**. |
| 9. Demonstração MP4 | [MP4 vertical técnico](https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/mission14-evidence/mission14-vertical-30s.mp4). Padrão móvel de calibração original do FFmpeg, sem cenas domésticas/Wan novas; **não é estoque nem vídeo comercial aprovado**. |
| 10. Resolução e formato | Na prova hospedada: **1080×1920, DAR 9:16, SAR 1:1, H.264/yuv420p, 30fps, AAC, rotação 0, faststart, 30,033008s**; 12.079.279 bytes; sem bordas pretas detectadas; delta A/V final 0,015008s. `demo-github-actions.json`. |
| 11. Legendas | Cinco quadros locais revisados visualmente; texto em até duas linhas na zona conservadora, sem corte. [Provas com UI simulada](https://github.com/ebooksproprof-dot/tiktok-automation/releases/tag/mission14-evidence). Template oficial TikTok consultado. Sincronização por limites medidos de fala e subdivisão proporcional; não alegamos alinhamento palavra a palavra nem teste visual no app TikTok atual. |
| 12. Repetição | Cooldown de problema OU solução, aproximação de ganchos, instruções sem ordem/sinônimos e dHash multicrop persistente. Regressão usa textos dos recibos reais, com frases invertidas. Buffer, estoque e rota direta do TikTok revalidam contrato e cadência antes de reservar/criar posts. |
| 13. Estoque | **0 vídeos completos aptos**, episódio Wan 6 com **2 cenas**, banco com **7 entradas** preservadas. Fontes Wan atuais 480×832 não passam na exigência de ampliação máxima. |
| 14. Próximos agendamentos | **Nenhum novo agendamento aprovado**. Seleção: 10h/18h BRT, mínimo 48h, máximo 3 em qualquer janela móvel de sete dias. É teto, não obrigação. |
| 15. Publicações confirmadas | **0 novas nesta missão**. Preservados 41 recibos históricos PUBLISH_COMPLETE e 6 cancelamentos; não foram repostados nem apresentados como novos. Buffer verificado em modo somente leitura. |
| 16. Frequência sustentável | **Atualmente 0/semana aptos**, pelos bloqueios abaixo. Após resolvê-los, começar experimentalmente com 1/semana, até teto de 3, condicionado a estoque validado. Não existe evidência para prometer produção semanal profissional contínua. |

## Testes reais e simulações separados

- [Benchmark CPU real no Actions — sucesso](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/45937825594): revisão 8697bb7, oito falas novas, 24 kHz PCM16, sem referência pública da demo. Dados completos em `cpu-github-actions.json`. Dependências e teste inclusos, workflow total ~6m45s.
- [Montagem e preservação no GitHub — sucesso](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/45938597500): recuperou as falas daquele benchmark, sem sintetizar novamente; normalizou e validou MP4; arquivos duráveis na Release. O relatório, o MP4 e o WAV hospedados foram lidos de volta por HTTPS; hashes coincidiram e o MP4 foi decodificado e validado novamente. `hosted-readback.json`.
- [Buffer real, somente leitura — sucesso](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/45938278594): `channel_verified=true`, `CHECK_ONLY`, persistência cloud/readback e rejeição de escritor obsoleto confirmadas; nenhuma chamada para criar posts.
- **462 testes locais passaram**, incluindo FFmpeg real, rejeição de barras incorporadas, bloqueio de referência ausente, publicação antiga, omissões/repetições no texto reconhecido e inserção de quarto post antes de reservas futuras. Testes de APIs usam mocks. [Suite de 461 testes no Actions — sucesso](https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/45938909599); depois foi acrescentada a regressão da rota direta, incluída nos 462 locais. A execução da revisão final consta no histórico.
- **Simulação de oito semanas**: 56 dias, 14 dias sem cota, 7 falhas temporárias, 26 fornecimentos simulados, 24 consumos simulados, reinício diário via JSON, sem IDs duplicados e respeitando 48h/3 por sete dias. **Zero publicações reais nessa simulação**. `continuity-simulation.json`.
- Áudio técnico local: ASR alinhou 96 das 97 palavras esperadas e retornou 103 palavras, mas sinalizou `compartimento`/`comportamento` e possível fala extra `até a próxima` no fim. `asr-review.json` contém métricas e transcrição completas. **Não foi aprovado**. ASR pode errar ou alucinar: repetição sonora e naturalidade exigem escuta; não se declara defeito auditivo confirmado apenas pela transcrição. Gate final exige concordância integral de palavras normalizadas.
- Na voz efetivamente hospedada, a ASR também reteve o resultado: 97 palavras esperadas, 98 reconhecidas, incluindo divergências de grafia/segmentação e `compartimento`/`comportamento`. `asr-hosted-actions.json`. A fala extra sinalizada no teste local não apareceu nessa transcrição; não se presume que as duas amostras sejam idênticas.
- Naturalidade, identidade feminina, pronúncia auditiva e consistência perceptiva entre vídeos: **pendentes**, não substituídas por métricas técnicas.

## Diagnóstico do vídeo que não preenchia a tela

O MP4 histórico examinado já tinha 1080×1920 / SAR 1:1 / 30fps / H.264/AAC.
Sua duração era 16,104s. O quadro revelou uma janela horizontal central com
fundo desfocado acima/abaixo. A causa está no compositor `preserve_full`, que
limitava a ação a até 720px de altura. A correção substitui esse caminho nos
novos renderizadores por escala proporcional/crop limitado e rejeição da
fonte inadequada. Não foi comprovada transformação adicional do Buffer ou da
reprodução atual do TikTok. Fontes históricas diretas da Pexels retornaram
HTTP 403 no teste atual; não houve tentativa de contornar a restrição.

## Bloqueios e o que falta

1. **Referência feminina PT-BR com autorização comercial e aprovação auditiva**. Nenhuma licença foi inventada. Guardar gravação em armazenamento privado persistente e entregar ao runner por secret, não em Git/Release. A configuração só permite uma identidade/hash estável.
2. **Áudio aprovado**. O benchmark técnico gerou fala, mas a checagem ASR do exemplo de 30s reteve o resultado. A nova identidade precisa de teste de pronúncia, expressividade, clareza e repetição, além da validação automática. Não há fallback para Kokoro/Piper.
3. **Cenas suficientes e de qualidade**. A rota Wan existente produz 480×832 e o episódio está incompleto. Seis cenas únicas são necessárias; não se aceita ampliar >1,5×, repetir, congelar ou inserir silêncio para preencher 30s. Falta comprovar rota gratuita com resolução melhor ou material licenciado compatível.
4. **Produção e publicação de um episódio comercial completo** só podem ocorrer depois desses gates. Reposição e monitor continuam preservando progresso; falha por estoque vazio é reportada como tal, não como publicação bem-sucedida.

Upload local para Releases encontrou HTTP 401 no domínio de uploads, e download
local de artifact encontrou HTTP 403 no storage redirecionado. Não houve troca
de identidade nem tentativa de contornar controles. A própria execução Actions,
com seu token autorizado, recuperou o artifact e preservou a prova em Release
com sucesso. A prova não depende de disco temporário do Codex.

Consulte [MISSION-14.md](../MISSION-14.md) para a arquitetura, direitos,
dependências, mecanismo de referência privada e comandos. Este relatório
**não declara a automação comercial plenamente operacional**.
