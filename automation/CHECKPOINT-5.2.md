# CasaSemEsforço 5.2 — avatar exclusivamente

HEAD inicial remoto:127e3dac4413083affc229bc2d8b7bb5b3be4a29, posterior a142ef2489448. Checkpoint e auditoria5.1 recuperados. Nenhuma alteração em produção convencional, fila, Buffer ou consentimentos.

Ambiente Work: afinidade9 CPUs; quota cgroup8CPU; RAM efetiva8GiB, sem GPU detectada/nvidia-smi; aproximadamente30GB disco livre. Não comporta picoFP32 anterior14GB. Runner público GitHub padrão tem4vCPU/16GB documentados, semGPU, disco efetivo medido pelo experimento.

Hipótese nova: EchoMimic ACC oficial, no mesmo pin c32b3a557003f84ead1483a2d2386035685d984d, pesos hub987c98d1d00a5fd062c5f087719af663fa90bc53. Diferente do experimento4.4: denoising_unet_acc.pth/motion_module_acc.pth + pipeline_echo_mimic_acc.py, seis passos oficiais e CFG1 sem duplicar batch. Contexto4/overlap1 reduz ativações por chamada, sem promessa de menor tempo total. Saída alvo5s/256×256/8fps/40frames, seed420, timeoutinferência480s. Não é configuração comercial comprovada.

Licenças recuperadas: código/hubApache2.0, VAE MIT, baseimagevariationsApache2.0, Whisper/MTCNN MIT, vozKokoro previamentevalidada. Gate verifica LICENSE dohubpin antes da inferência e registraSHA. Sem modelo gated/contrato/pagamento. Reutiliza retratooriginal e primeiros5s doMP4KokoroC3 verificadoporhash; sem sínteseouclonagemnova.

Novos arquivos isolados: avatar52_accelerated.py, save_avatar52.py e workflowavatar52-accelerated.yml. Reutiliza patchesCPU játestados emavatar43_smoke.py sem modificar essearquivo. Nove testesexistentesdoshelpersCPU passaram; compilaçãoPythonpassou. Execução realpendente apósprimeiropush.

Reprodução: workflow Avatar5.2, ubuntu24.04/Python3.10/dependênciaspinadas herdadasdoexperimento. python automation/avatar52_accelerated.py. Script salva relatório porfase e logs, inventaria pesos até13GB/RAM/disco antes de inferir. Workflow16min; inferência8min; artifactssempre eReleaseevidências emfalha controlada. Nenhum arquivo é avatarcomprovado sem decodificaçãoMP4 e inspeção posteriorboca/rosto.

Próximo passo: acompanharjob, salvarJSON/MP4 imediatamente, revisar movimento e lipsync somente seexistirarquivo. Não repetir tentativa idêntica sefalhar.
