# Avatar 4.3 — experimento EchoMimic CPU isolado

Retomada de 23/10/2026. Workflow `avatar43-smoke.yml` tenta gerar três segundos
em 256×256, 12 fps, quatro passos de denoising, no máximo duas threads CPU.
Não é configuração de qualidade comercial. Não publica, não altera filas,
não recebe secrets e não participa dos workflows diários.

Revisão do código: `c32b3a557003f84ead1483a2d2386035685d984d`.
Revisão do hub de pesos: `987c98d1d00a5fd062c5f087719af663fa90bc53`.
O script muda literais CUDA para CPU no entrypoint e usa fp32. Registra hashes
do original e modificado. Compatibilidade CPU dos módulos internos é parte
do experimento, não uma propriedade previamente comprovada.

## Licenças verificadas antes da tentativa

- EchoMimic código e hub oficial de pesos: Apache 2.0.
- VAE `stabilityai/sd-vae-ft-mse`: model card declara MIT.
- Base `lambdalabs/sd-image-variations-diffusers`: model card declara Apache 2.0.
- Whisper: MIT; MTCNN via facenet-pytorch: MIT.
- Voz Kokoro reutilizada do MP4 C3 da validação 4.1 já persistida: SHA256
  `ba6632efac13a27e72af60d467f5a4f7f52f4d48aaa1d38e560025923ad59b87`.
  Download limitado a 20 MB/90 segundos; extração dos três primeiros segundos
  em WAV 16 kHz mono. Sem reinstalação de Kokoro ou nova avaliação por escuta.

Nenhum modelo gated ou API paga é usado. Não foi realizado aceite de licença
adicional. O retrato é o asset original já preservado no projeto.

## Limites e evidências

O job limita o total a dez minutos, instalação a quatro, experimento a cinco
e subprocesso de inferência a 180 segundos. Antes de baixar pesos, inventaria
arquivos exatos, bloqueia acima de 13 GB, verifica RAM física mínima de 12 GB
e espaço para pesos, maior arquivo em transferência e 1 GB extra. Isso não
garante que a RAM de inferência bastará; OOM/timeout são resultados possíveis.

`report.json` é atualizado a cada fase; `execution.log` registra subprocessos.
O artifact coleta somente JSON, logs e MP4, mesmo em falha. Fonte e pesos não
são enviados ao artifact. Falha na instalação deixa relatório inicial explícito.
O nome de uma etapa ou execução do processo não comprova inferência concluída:
`avatar_video_produced` só muda após validação PyAV: exatamente um stream de
vídeo e um de áudio, ambos com duração 3 s ±0,3 s, dimensões 256×256 e decodificação
integral de ambos com quadros não vazios. Não depende de ffprobe.
O MP4, se existir, ainda exige revisão de boca, identidade e qualidade.

Validação local: compilação Python e parsing YAML aprovados. Resultado cloud
deve ser registrado pelo executor após o push; esta nota não afirma que o
avatar foi gerado. Nenhum teste da produção foi substituído por este experimento.

## Segunda tentativa após falha de infraestrutura

A execução 40012677208 esgotou o limite de instalação durante apt/FFmpeg,
antes do pip. A segunda tentativa remove completamente apt: usa FFmpeg do wheel
imageio-ffmpeg, exposto por symlink local no PATH. Mantém o limite total de dez
minutos e instalação pip de quatro minutos. Essa alteração resolve o caminho
de dependência observado; ainda não comprova inferência ou qualidade de avatar.

Fontes oficiais:
- https://github.com/antgroup/echomimic/blob/main/LICENSE
- https://huggingface.co/BadToBest/EchoMimic/blob/main/LICENSE
- https://huggingface.co/stabilityai/sd-vae-ft-mse/blob/main/README.md
- https://huggingface.co/lambdalabs/sd-image-variations-diffusers/blob/main/README.md
- https://github.com/openai/whisper/blob/main/LICENSE
- https://github.com/timesler/facenet-pytorch/blob/master/LICENSE.md
