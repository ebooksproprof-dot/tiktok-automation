# Auditoria independente do experimento de avatar 5.2

Revisor separado, somente leitura, examinou o código pinado do EchoMimic, novo script, workflow e persistência. Não alterou fila nem arquivos de produção.

## Hipótese nova confirmada

O entrypoint acelerado oficial usa CFG1 e seis passos, com pesos denoising_unet_acc/motion_module_acc e pipeline_echo_mimic_acc. O pipeline ACC contém o ramo sem classifier-free guidance; aplicar apenasCFG1 ao pipeline antigo não seria equivalente. A implementação usa o caminho oficial completo.

O agendador temporal aceita contexto4/overlap1. Positional encoding tem máximo32, sem mínimo12. Janelas menores diminuem ativações por chamada, mas não garantem menor tempo: há mais chamadas. Baixa resolução256px e8fps são diagnóstico, não qualidade comercial assegurada. Os patchesCPU anteriores se aplicam aos mesmos três carregamentos e métodos de atenção; não simulamCUDA.

## Licença e recursos

LICENSE do hub exato987c98d1d00a5fd062c5f087719af663fa90bc53 lida independentemente:11356bytes,SHA25643070e2d4e532684de521b885f385d0841030efa2b1a20bafb76133a5e1379c1,Apache2.0. Gate do experimento confere essehash antes da inferência. O README declara intenção de pesquisa e responsabilidade do usuário, sem 'research only' na licença. Proveniência dos demais componentes recuperada daauditoria4.3; não representa garantia sobre todosdatasets.

Corrigido antes do push conforme revisão: usar RAMefetiva=min(física,cgroup), elevar totaljob18min para reservar persistência após inferência480s. Limite13GB para pesos; diretório de modelos não é uploadado. GH_TOKEN somente na etapa de persistência, não na inferência. Não há secrets TikTok/Buffer no experimento.

## Testes e preservação

Nove testes de patchesCPU passaram. Regressão independente275testes passou em0,317s. Esses testes não são prova de avatar. ParsingYAML e compilaçãoPython aprovados. Os arquivos de produção convencionais não fazem parte do patch5.2.

DecodificaçãoMP4 exigida antes de avatar_video_produced, mas isso ainda não comprova boca/realismo/sincronização. Revisão visual e áudio continuam pendentes até existir arquivo.

Primeiro commit21df8001d713,run40249889872/job121339279512: em andamento no checkpoint. Resultado real deve ser anexado, sem converter timeout/erro em sucesso.

## Auditoria da primeira saída real

MP4SHA d3192975cd013f145f8ef8ac20acc496be5dbbd34451771ded1a48f118870b7a conferido após download.5s,256×256,40quadros,áudio,decodificação integral,volume−18dB,sem preto>=300ms/silêncio>=800ms. Vintequadros inspecionados: movimento de cabeça/olhos e movimento labialdiscreto, mas bocaquasefechada emváriosquadros e borrões. **Sincronizaçãolabialconvincente não certificada; qualidade comercial não aprovada.** Não existe avaliação de consistênciaentreduasfalas.

Compare remoto127e3dac4413→25ef17058090: apenas seisarquivosisoladosdeavatar/documentação alterados; produção/fila/Buffer/consentimentos intactos. Regressãoindependente275testes,0,309s. Isso não substituiQAaudiovisual.

Configuração da segunda prova revisada: contexto12/overlap3,mesmafala/retrato/seed/CFG/steps/FPS,600sinferência e20minjob. Assets porhash preservamprimeira saída. Run40250835376 emexecução; semresultadoantecipado.
