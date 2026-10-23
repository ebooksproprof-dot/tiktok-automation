# CasaSemEsforço 4.3 — checkpoint persistente

Estado: PARCIAL. Recuperado 64e3133 posterior a 8f3824afce. Implementação salva em d918f90, 931cb33 e f8edcc5; execução diária acrescentou 1b3bafb.

## Entregas confirmadas

Release: https://github.com/ebooksproprof-dot/tiktok-automation/releases/tag/validation-v43-2026-10-23

- B: secador corrigido, 17,08 s, render cloud 52,075 s, SHA 0164541ca8dca409eada309fbc7a85d82b7e84458a313889527b23696f666501.
- C: cuba/medidas, 19,533 s, render cloud 59,151 s, SHA 597a3a1cf01cb87f1b2d43f165c9701f2cbc5adb78f08c8549e376e5d10801f8.
- Ambos 1080×1920, Kokoro pf_dora, decode integral, zero preto >=300ms e silêncio >=800ms. Delta final AV 13,3/24,3ms. Sem avatar, escuta ou aprovação para TikTok. Relatório cloud com SHA conferido em validation-4.3-cloud-evidence.json.
- Quadro original integral (antes crop horizontal retinha 31,64%); foreground menor, fundo desfocado e texto fora da imagem útil. Secador agora visível lateralmente, sem garantia de visibilidade em todos os frames. C mostra lavagem de mãos/cuba, não eficácia de produto; iluminação escura. Não há evidência de melhor retenção ou voz. C1/C2 anteriores preservados, sem novas versões.

## Integração e continuidade

Native preserve_full integrado ao renderer por fonte revisada; gate de capacidade antes de sintetizar; gate de alinhamento AV; inferência das provas sem rede via seccomp; telemetria ONNX explicitamente desativada. Catálogo +2 itens, com proveniência/SHA e sem aprovação de publicação. Aquisição usa contato visual integral e query de esponja mais pertinente, mantendo revisão semântica e limites existentes.

Daily 40013644972 concluiu com 230 testes e gerou casasem-2026-10-23-2, 17,08s, estilo casasem-v43-preserve-full, salvo em Release media-2026-10. Está approved=false/consented_at=null. Runner 40013923518: 12 publicações históricas verificadas, zero envios; cobertura falha por aprovação/rota/consentimento. Última publicação registrada 22/10 10h: https://www.tiktok.com/@.casasemesforo/video/7699477167792753927 . Nenhum agendamento Buffer confirmado. Seis itens pendentes, incluindo slots vencidos; não reenviar automaticamente.

## Avatar e ferramentas

EchoMimic V1 isolado, código/pesos fixados, CPU, sem aceite adicional. Primeira tentativa parou no apt. Segunda 40013645148 instalou dependências, baixou 12,33GB e executou entrypoint, mas torch.load do face_locator tentou CUDA. 71,271s, pico filho 14.108.044KiB; não foi demonstrado OOM nem inferência completa. Sem MP4 ou sincronização labial. Relatório preservado avatar-4.3-attempt2.json. Uma correção CPU precisa de nova evidência antes de qualquer integração.

EffectCraft CPU comparado 3x: mediana 0,914s versus FFmpeg0,253s para composição sintética de 1s; SSIM0,998459. Sem benefício demonstrado para integrar. OpenCut/FilmCraft/PhotoCraft/VectorCraft/Remotion não integrados nesta etapa; VoiceStudio sem aceite. Kokoro/Piper existentes preservados.

## Auditoria e retomada

AUDIT-4.3.md: segunda revisão independente, 230 testes locais aprovados, 230 também na nuvem. Achados de fonte repetida e validação insuficiente do smoke corrigidos. Custo adicional contratado R$0; nenhuma GPU paga. Dois vídeos diários publicados sem intervenção NÃO comprovados: catálogo finito, aprovações e avatar pendentes.

Próximo passo: ler este checkpoint e eventual adendo do avatar; revisar B/C e o lote de fila via BATCH_APPROVAL.md (até14), com consentimento explícito e horários futuros. Adquirir/revisar cenas novas, não reciclar fontes publicadas. Não repetir três baselines4.1, instalaçãoKokoro ou pesquisas já documentadas.
