# CasaSemEsforço 5.2 — avatar exclusivamente

HEAD inicial remoto:127e3dac4413083affc229bc2d8b7bb5b3be4a29, posterior a142ef2489448. Checkpoint e auditoria5.1 recuperados. Nenhuma alteração em produção convencional, fila, Buffer ou consentimentos.

Ambiente Work: afinidade9 CPUs; quota cgroup8CPU; RAM efetiva8GiB, sem GPU detectada/nvidia-smi; aproximadamente30GB disco livre. Não comporta picoFP32 anterior14GB. Runner público GitHub padrão tem4vCPU/16GB documentados, semGPU, disco efetivo medido pelo experimento.

Hipótese nova: EchoMimic ACC oficial, no mesmo pin c32b3a557003f84ead1483a2d2386035685d984d, pesos hub987c98d1d00a5fd062c5f087719af663fa90bc53. Diferente do experimento4.4: denoising_unet_acc.pth/motion_module_acc.pth + pipeline_echo_mimic_acc.py, seis passos oficiais e CFG1 sem duplicar batch. Contexto4/overlap1 reduz ativações por chamada, sem promessa de menor tempo total. Saída alvo5s/256×256/8fps/40frames, seed420, timeoutinferência480s. Não é configuração comercial comprovada.

Licenças recuperadas: código/hubApache2.0, VAE MIT, baseimagevariationsApache2.0, Whisper/MTCNN MIT, vozKokoro previamentevalidada. Gate verifica LICENSE dohubpin antes da inferência e registraSHA. Sem modelo gated/contrato/pagamento. Reutiliza retratooriginal e primeiros5s doMP4KokoroC3 verificadoporhash; sem sínteseouclonagemnova.

Novos arquivos isolados: avatar52_accelerated.py, save_avatar52.py e workflowavatar52-accelerated.yml. Reutiliza patchesCPU játestados emavatar43_smoke.py sem modificar essearquivo. Nove testesexistentesdoshelpersCPU passaram; compilaçãoPythonpassou. Execução real disparada no commit21df8001d7134445aa5c11908f229ab477c13d21, run40249889872, job121339279512; inferência em andamento.

Reprodução: workflow Avatar5.2, ubuntu24.04/Python3.10/dependênciaspinadas herdadasdoexperimento. python automation/avatar52_accelerated.py. Script salva relatório porfase e logs, inventaria pesos até13GB/RAM/disco antes de inferir. Workflow18min; inferência8min; artifactssempre eReleaseevidências emfalha controlada. Nenhum arquivo é avatarcomprovado sem decodificaçãoMP4 e inspeção posteriorboca/rosto.

Próximo passo: acompanharjob, salvarJSON/MP4 imediatamente, revisar movimento e lipsync somente seexistirarquivo. Não repetir tentativa idêntica sefalhar.

## Primeira prova real concluída

Run40249889872 gerou MP4 real de5s/256×256/8fps,40quadros,vozKokoro. Tempo total508,051s; picoRSSfilho14.108.444KiB; CPU4Xeon6973P-C,16.765.378.560bytesRAM,CUDAfalse. Release https://github.com/ebooksproprof-dot/tiktok-automation/releases/tag/avatar-v52-2026-10-25 . MP4 https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/avatar-v52-2026-10-25/avatar52-accelerated-d3192975cd013f14.mp4 .

Auditoriaindependente: hashcorreto,decodificaçãointegral,zero preto/silêncio,volume−18dB. Vintequadros mostram movimento de cabeça/olhos e levesmudançaslabiais, mas bocaquasefechada e borrões. **Não certificada sincronização convincente**. Não classificar qualidadecomercial comoalcançada. Resultado emavatar-5.2-context4-result.json.

Segunda experiência controlada: restaurar contexto12/overlap3 upstream,mesmos40frames/8fps/5s,voz,retrato,seed420,CFG1,seispassos. Hipótese: maiscontextotemporal melhoraarticulação. Janela aumentaRAM; não garantebenefício. Timeoutinferência600s,totaljob20min,semloops. Nãoésegunda fala/consistênciacomprovada; compara umaúnicavariávelprincipal. Pipelineconvencional intacto.
