# CasaSemEsforço: enviar um lote sem abrir o Work

Esta é uma solução híbrida: você gera e revisa os vídeos no Symphony; o GitHub importa, valida, guarda, reserva horários e tenta agendar no Buffer. A geração Symphony por API continua desativada, sem acesso gratuito comprovado. Não foi substituído avatar ou voz.

## Preparar o lote

1. No seu navegador normal, gere vídeos com avatar **7616458821397659655**, voz **Keren**, português brasileiro. Exporte MP4 vertical **1080×1920**, H.264/AAC, entre **15 e 28 segundos**, até **20 MB**. Estes são limites conservadores do validador existente, não limites anunciados do Symphony.
2. Assista a cada vídeo. Confira avatar, voz, sincronização labial, legendas, gancho, demonstração, ausência de silêncio/preto e direitos sobre todos os materiais. Salve o roteiro em `roteiro.txt`.
3. Na pasta do repositório, execute o comando abaixo com Python 3. Ele calcula o hash e cria `bancada-01.json`. Não precisa do Work nem de token. Repita para os demais vídeos.

```sh
python automation/stock_import.py manifest --video bancada-01.mp4 --script-file roteiro.txt --topic "Organização da bancada" --caption "Uma dica prática para organizar a bancada. #organizacao" --source-evidence "Export Symphony revisado pelo titular" --commercial-content false --reviewed-all
```

`--reviewed-all` declara que você fez as revisões e autoriza publicar este arquivo específico. Não use se houver dúvida. Para conteúdo de afiliados/publicitário, declare `--commercial-content true`: o arquivo fica no estoque, mas a publicação automática fica bloqueada enquanto o disclosure comercial nativo não estiver suportado pela integração verificada. Uma legenda sozinha não resolve esse requisito.

4. Abra [a entrada de vídeos](https://github.com/ebooksproprof-dot/tiktok-automation/releases/tag/stock-inbox), clique em editar a Release e arraste os pares `bancada-01.mp4` + `bancada-01.json`. Salve. Os dois nomes devem ser iguais antes da extensão, sem espaços/acentos. A Release é pública, assim como as já usadas pelo projeto; não envie dados pessoais, segredos nem materiais sem direitos.
5. Pronto: o workflow **CasaSemEsforco Persistent Video Stock** verifica novas entradas seis vezes ao dia. Para importar imediatamente, use **Actions → CasaSemEsforco Persistent Video Stock → Run workflow**, deixando a opção de apenas checar desmarcada. Isso funciona sem Work. O estoque só aumenta após validação e gravação bem-sucedidas.

## O que acompanhar

- [Estoque persistente](https://github.com/ebooksproprof-dot/tiktok-automation/blob/main/automation/video_stock.json): quantidade pronta, horários, tentativas, erros, IDs e evidências.
- [Execuções](https://github.com/ebooksproprof-dot/tiktok-automation/actions/workflows/video-stock.yml): resumo operacional. `low_stock=true` significa menos de sete vídeos aptos; prepare lote para atingir 14–28.
- Os horários são **10h e 18h em America/Sao_Paulo**. O Buffer recebe agendamentos antecipados; o cron GitHub pode atrasar. O sistema não promete pontualidade absoluta nem publica atrasado para preencher lacunas.
- `SCHEDULED` pode ser reserva interna: confira `remote_id` para saber se Buffer confirmou o agendamento. `PUBLISHED` exige consulta independente com status enviado e link da conta correta. Envio de requisição não é confirmação.
- `UNKNOWN` congela reenvios. Não apague esse registro para “tentar de novo”. Inspecione o histórico e o agendamento no provedor, confirme a identidade e só então faça recuperação revisada. Não existe reset automático de tentativa.
- Não remova nem substitua MP4/JSON já importados. O hash é revalidado antes de enviar, mas o provedor pode baixar o vídeo depois do agendamento. Mantenha os assets durante todo o ciclo.

## Arquitetura e orçamento

MP4 ficam em GitHub Releases; somente metadados pequenos ficam no Git. Artifacts temporários não são o estoque. O estado usa GitHub Contents API com comparação de SHA e o mesmo lock `casasemesforco-state` dos workflows existentes. A reserva e o consumo de API são gravados remotamente antes da chamada externa. Uma falha de persistência interrompe o envio.

O fluxo preserva os renderizadores/filas anteriores e consulta hashes e horários legados para evitar colisões. Conteúdo antigo com outra voz não é promovido a estoque Symphony. Nenhum vídeo é duplicado para preencher vaga. O sistema detecta duplicatas exatas de arquivo/roteiro; não certifica sozinho originalidade perceptual de filmagens.

Buffer tem até dez posts simultâneos no plano gratuito, portanto o estoque excedente permanece no GitHub. O limite local compartilhado é conservador: 90 chamadas/15min, 90/dia, 900/30 dias; headers mais restritivos e Retry-After prevalecem. O consumo conhecido é persistido, aguarda a janela liberar e volta automaticamente, sem reenviar mutações incertas. Isso é controle de publicação, **não de créditos Symphony**.

Nenhum serviço pago, assinatura, anúncio ou larger runner foi habilitado. O repositório é público e usa runner padrão. Alterações futuras de plano/preço continuam sujeitas aos fornecedores; não há comprovação de geração Symphony por API a R$0. Até obter habilitação oficial, não há gerador automático nem renovação automática de capacidade de geração.

## Testes e limites

Os testes incluem MP4 sintético real em FFmpeg (formato, duração, áudio), testes simulados de APIs e regressão do projeto. O teste sintético não contém a avatar oficial e nunca é publicado. O probe de nuvem usa um arquivo de metadados separado para testar persistência/releitura/conflito de escrita; não cria posts.

Uma ficha declarada pelo usuário não é reconhecimento automático de Keren, avatar, idioma, legendas ou lip-sync. Ainda é necessário um MP4 Symphony real revisado para provar o fluxo de publicação de ponta a ponta. Consulte CHECKPOINT-7.0.md para a evidência executada nesta missão.
