# Alternativas de avatar e capacidade gratuita — 5.2

Esta missão não modifica produção convencional. Uma inferência bem-sucedida não comprova operação de 60 vídeos/mês.

## Recursos observados

Work: nproc9/afinidade, cgroup cpu.max800000/100000=8CPU, memory.max8589934592=8GiB, semnvidia-smi,30GBdisco. O limite do cgroup prevalece sobre os9,97GB exibidos porfree. InferênciaFP32 anterior14GB não cabe aqui.

GitHub público padrão: documentação consultada informa4vCPU,16GBRAM,14GBSSD nominal, semGPU, gratuito para repositórios públicos em runners padrão. Experimento mede disco/RAM reais e recusa baixar se insuficientes. Limite desta prova18min, subprocesso480s; não é limite máximo geral deActions. Não usado larger runner, cartão ou assinatura. https://docs.github.com/en/actions/reference/runners/github-hosted-runners

## Candidato efetivamente executado nesta missão

EchoMimicACC: mesmo código pinado, mas denoiser/motionmodule acelerados e pipelineACC oficiais. CFG1 não duplica batch; contexto4 reduz tamanho da chamada. Seis passos são default desse caminho, não redução arbitrária da base. Alvo5s,256px,8fps,40frames. ModeloApache2.0; LICENSEexata dohubpinSHA43070e2d4e532684de521b885f385d0841030efa2b1a20bafb76133a5e1379c1. VAE MIT, base Apache2, Whisper/MTCNN MIT conforme auditoria recuperada. README declara intenção de pesquisa e responsabilidade do usuário, sem cláusula 'research only' na licença. Isso não certifica direitos sobre todo dataset/identidade; usa retratooriginal e vozjálicenciada, não exemplos humanos do projeto.

https://github.com/antgroup/echomimic/tree/c32b3a557003f84ead1483a2d2386035685d984d
https://huggingface.co/BadToBest/EchoMimic/blob/987c98d1d00a5fd062c5f087719af663fa90bc53/LICENSE

## Candidatos recuperados/pesquisados, não executados novamente

- EchoMimicbase: tentativas históricas reais, patchesCPU e timeout180s, semMP4. Não repetida a mesma configuração.
- SadTalker: caminhoCPU histórico, componentesBFM ainda sem proveniência/autorização comercial resolvida; não usar para produção enquanto pendente. Não equivale a dizer que todo códigoSadTalker proíbe comércio.
- Wav2Lipoficial: restrição comercial histórica; não escolhido nem executado.
- LivePortrait: animação guiada por movimento, não gera sozinho fala nova sincronizada; componentes de terceiros ainda precisam validação. Não nova instalação nem inferência nesta missão.
- MuseTalk: READMEoficial atual permite uso comercial do códigoMIT e modelo principal, mas exige cumprir licenças dos componentesWhisper/VAE/DWPose/S3FD e restringe seus testdata a pesquisa não comercial. CaminhoGPU documentado; CPU e dependências exatas não validadas aqui. Não declarar inviabilidade universal ou licença proibitiva do modelo principal.

https://github.com/TMElyralab/MuseTalk#disclaimerlicense
https://github.com/KlingAIResearch/LivePortrait

## Serviços realmente consultados, sem geração cobrada

Runwayconectado: autenticado, nenhum modelo de vídeo disponível na conta atual. Não ativado trial, upgrade ou compra. Bloqueio de acesso atual, não inferência fracassada.

OpenArtconectado: planoFree,40créditos. Catálogo consultado; cotação explícita PixVerseV6,text2video,5s,360p,9:16,áudioativado,1vídeo=50créditos. Saldo insuficiente. Nenhuma geração/crédito consumido. Não produzir imagemestática ou clipe semáudio como substituto. Outros preços/configurações variam; não extrapolar essa cotação para todo serviço. Não há renovação de créditos verificada para60/mês.

## ZeroGPU: alternativa possível, ainda não implementada

Documentaçãooficial consultada: APIsGradio; quota diária120s não autenticado (poolcompartilhado),300s contafree, reset24hapósprimeirouso. Hospedagem própria gratuita condicionada acontaverificada commais30dias; até2Spaces. GPUdinâmica48GB a1×quota;96GB a2×. Não presumida conta elegível nem token disponível.

Para dois vídeos/dia no planoFree, cada geração precisaria consumir no máximo150sdeGPU, incluindo desperdícios/retries no orçamento. Em30dias seriam9000sGPU; isso não garante fila, disponibilidade, qualidade ou permissão de um Space específico. Não se pode usar o tempoV100 divulgado peloEchoMimic como mediçãoZeroGPU. Nenhuma inferênciaZeroGPUexecutada nesta sessão; classificaçãoEapenas como caminho de infraestrutura possível, não como solução jáviável.

https://huggingface.co/docs/hub/spaces-api-endpoints
https://huggingface.co/docs/hub/spaces-zerogpu

## Regra de conclusão

A: falta de RAM noWork para o perfilFP32observado, não impossibilidade de todosmodelos.
B: modelosGPU podem ser tecnicamente viáveis em outra infraestrutura, masGPU não está disponível neste runner.
C: BFM/Wav2Lip e dependências não resolvidas não são contornadas.
D: contasconectadas não permitem a prova solicitada com os recursosobservados;60mensais não comprovados.
E: ZeroGPU e adaptações adicionais são candidatos, não integraçõescomprovadas.

Nenhum modelo foi declarado avatarfuncional semMP4 e revisão de movimento labial.

## Verificação independente das demonstrações oficiais

EchoMimic Space BadToBest/EchoMimic: público, ungated, revisão909816072e9ac5910197c34e28d8e6f89103722c. API runtime=CONFIG_ERROR; hardwarecurrentnull/requestedzero-a10g. Requirements torch>=2.0.1,<=2.2.2 incompatíveis com versõesZeroGPUatuais a partir2.8. Entrywebgui.py, Gradio4.38.1, decoradorGPUduration300, show_api=False. Não foi feita inferência. https://huggingface.co/spaces/BadToBest/EchoMimic

MuseTalk Space TMElyralab/MuseTalk: público, ungated, revisão59976c128aea3c517339d247016b70f6c15f14d9. API runtime=RUNTIME_ERROR; hardwarecurrentnull/requesteda10g-small, Docker. Erro de modelos ausentes: MuseTalk/SDVAE/Whisper/DWPose/SyncNet/FaceParse/ResNet. CarddoSpace declaraCreativeML-OpenRAIL-M, não a licençaMITdoSDK. Não feita inferência, nem aprovada licença de toda composição. https://huggingface.co/spaces/TMElyralab/MuseTalk

Esses resultados mostram que as demonstrações oficiais consultadas não são endpoints prontos para integração; não demonstram impossibilidade dos modelos em outra instalação. Dados obtidos pelo revisor independente nesta sessão.
