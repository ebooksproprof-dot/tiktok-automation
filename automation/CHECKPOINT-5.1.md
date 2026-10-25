# CasaSemEsforço 5.1 — entrega de 25/10/2026

**Estado: PARCIAL.** Melhorias de legenda implementadas, comparadas em MP4 real e ativadas para futuras renderizações. Nenhuma apresentadora animada produzida. Nenhum consentimento, agendamento ou publicação alterado.

## Recuperação e commits

HEAD inicial remoto confirmado: `41c3bcc6ab8c038a80d1a2367cd76ebe6cc520a4`.

- `59f0688e957a`: módulo medido, integração opt-in, testes e workflow de prova.
- `6a818c37617b`: cliente de download alinhado ao pipeline e checkpoint intermediário.
- `da9a5c10286c`: auditoria independente e matriz das dez ferramentas.
- Commit de entrega posterior: ativação do estilo validado, métricas e este relatório. Consultar HEAD remoto; os workflows também podem criar commits.

## Código e integração

`caption_layout.py` usa Pillow 12.3.0 e a fonte DejaVu existente para medir os glifos. Mantém até duas linhas em 864 pixels, reduz tamanho de 58 até 42 quando necessário e bloqueia texto que não cabe. Não trunca palavras. Adiciona entrada de 80 ms, trata porcentagens como texto literal e usa intervalos semiabertos para evitar sobreposição nas trocas.

`render_daily.py` recebe `CAPTION_STYLE=measured-v51`; o workflow diário instala a dependência explícita e seleciona esse estilo. `legacy` continua disponível por configuração. `COMPOSITION_REVISION=6` não foi alterada: vídeos pendentes existentes não são regenerados por essa melhoria. A falha de layout é explícita, sem conteúdo cortado aprovado silenciosamente.

## MP4s persistidos e comparação

Release: https://github.com/ebooksproprof-dot/tiktok-automation/releases/tag/validation-v51-2026-10-25

- A, controle de legendas: https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/validation-v51-2026-10-25/comparison-A-39fb91cf11dc1586.mp4
- B, legendas medidas: https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/validation-v51-2026-10-25/comparison-B-e08af76d3a48571a.mp4

Ambos: 17,9 s, 1080×1920, H.264/AAC, Kokoro pf_dora, média -15,2 dB, zero intervalos pretos >=300 ms e zero silêncios >=800 ms. Diferença de término áudio/vídeo: 7 ms. Mesma voz PCM e mesma filmagem, fonte Pixabay133319 previamente revisada com hash/licença/créditos preservados. Não são dois novos conteúdos de reserva.

| Métrica | A | B |
|---|---:|---:|
| Composição final | 5,051 s | 5,046 s |
| Maior linha de legenda | 951,70 px | 860,20 px |
| Tamanho MP4 | 1.804.980 bytes | 1.866.149 bytes |
| Maior RSS de processo filho | 603.824 KiB | 607.892 KiB |

Síntese compartilhada: 18,418 s. Enquadramento compartilhado: 11,484 s. Tempos excluem instalação/download; RSS não é a soma dos processos. Diferença de 5 ms no render não comprova ganho de desempenho. Três blocos mudaram de largura; margem medida melhorou, sem alegação de aumento de retenção ou naturalidade vocal.

Seis quadros de cada variante foram inspecionados: texto legível, caneca e celular integrais. A cena ilustra bebida perto de aparelhos; não demonstra rearranjo nem eficácia de um produto. Sem avaliação auditiva conclusiva. A/B usa tomada contínua para isolar legendas e não compara todo o plano de cortes diário. Os arquivos anteriores permanecem intactos.

## Nuvem, falhas e testes

Primeiro run40224046801: 275 testes passaram, mas o download recebeu403 antes de renderizar. Corrigido o identificador User-Agent para o cliente já usado na produção, mantendo hash e orçamento de download. Segundo run40224179335/job121261945620: **success**, 275 testes, dois MP4s e assets lidos novamente após upload ao Release.

Regressão local: 275 testes. Revisão independente documentada em AUDIT-5.1.md. Workers sem Pillow/DejaVu pulam cinco testes específicos; o workflow de prova e o diário instalam as dependências. A prova comprova o módulo na nuvem; ainda não comprova operação diária sustentada após ativação.

## Ferramentas e avatar

Inventário completo em TOOLS-5.1.md. FFmpeg/Kokoro/Piper preservados; Pillow integrado para medição tipográfica. EffectCraft permanece protótipo CPU: comparação anterior não justificou substituição. OpenCut não possui caminho headless validado. FilmCraft/PhotoCraft/VectorCraft/Remotion não receberam integração de produção. VoiceStudio mantém gate de licença dos pesos; nenhum aceite feito.

EchoMimic continua sem MP4. Tentativa anterior já usava 256px,36frames,4steps e excedeu180s, com aproximadamente14GB de RSS. Não repetida sem hipótese nova. Não houve sincronização labial validada. Nenhuma cena estática é apresentada como avatar.

## Operação e próximo passo

Custo adicional contratado R$0. Fila e consentimentos preservados; zero envios experimentais. Último inventário4.6: oito MP4s tecnicamente válidos, onze pendentes no total, zero autorizados. Não reclassificar arquivos como aprovados por passarem em QA.

Próximo passo técnico: verificar a primeira renderização editorial futura com `caption_style=measured-v51`, mantendo bloqueio de duplicação e consentimento. Para avatar, selecionar nova hipótese compatível com recursos/licenças antes de outro experimento; os editores não substituem um motor de animação. Renovação de filmagens e aprovação editorial continuam necessárias para sustentar dois vídeos/dia.
