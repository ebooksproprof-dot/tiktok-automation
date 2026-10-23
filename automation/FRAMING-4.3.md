# Provas B/C: produto visível, sem avatar

`framing.py` preserva o quadro inteiro em uma caixa sem texto entre y=500 e y=1220. O fundo desfocado preenche o formato vertical. Legendas continuam em y=1320; gancho em y=265. O produto fica menor do que no recorte central, mas suas laterais deixam de ser descartadas. Para uma fonte 3840×2160, o recorte vertical conservava somente 31,64% da largura; a nova composição conserva 100%. Não há promessa de ganho de retenção ou qualidade vocal.

`validation_v43.py` gera somente duas provas novas, nunca os três baselines 4.1. B/C são identificadores das provas, não formatos de avatar. Ambas são formato C (filmagem licenciada e voz feminina Kokoro). Não altera o renderer diário, não escreve fila/estado/histórico, preserva verificação de duplicação e confere integridade dos arquivos de estado. Outputs têm `approved=false`, `published=false`, `publication_allowed=false`.

## Seleção visual

- **B / Pixabay 37325:** original inspecionado sem recorte na missão anterior: secador aparece nos seis quadros amostrados. Prova anterior cortava as laterais e concentrava o rosto. Roteiro novo descreve movimento visível, não armazenamento não demonstrado ou resultado de eficácia.
- **C / Pixabay 38115:** original recuperado com SHA do inbox e inspecionado em seis quadros nesta sessão. Cuba e mãos claramente visíveis. A busca dizia limpeza de bancada, mas a cena é lavagem de mãos: foi rejeitada para demonstração de limpeza e selecionada somente para um roteiro de escolha de cuba pelas medidas/instalação. Não promete qualidade, eficácia ou desempenho de modelo específico.
- **Rejeitado / Pixabay 51807:** visualmente pertinente a torneira, mas a auditoria encontrou uso já publicado em 21/10. Descartado para C nova. A proteção de histórico não foi removida.
- Fontes 37325 e 38115 passaram pelo detector visual contra fila, estado e histórico persistido nesta sessão.

A voz não foi ouvida nesta sessão. Não se afirma naturalidade, pronúncia correta ou sincronização labial. Não há apresentadora virtual: as pessoas das fontes são reais e não representam depoimentos ou endossos.

## Execução portátil

```sh
python -m pip install kokoro-onnx==0.6.1
python automation/offline_exec.py python automation/validation_v43.py
```

Antes da síntese, os modelos e as fontes precisam estar baixados e verificados. `offline_exec.py` bloqueia egress no kernel, incluindo subprocessos; não basta a configuração de telemetria do ONNX. Duas tentativas anteriores foram rejeitadas pela revisão automática e não autorizam envio de telemetria.

FFmpeg/FFprobe e DejaVu Sans devem estar instalados, como no workflow existente. Cache de modelo opcional via `KOKORO_CACHE`; padrão `tmp/validation-v43/voice-assets`. Mídias são recuperadas pelo downloader existente, com limite de bytes/retries e SHA do inbox. Nenhuma dependência de diretório de outra sessão.

MP4s, JSONs de evidência e contact sheets ficam em `tmp/validation-v43`. Os relatórios incluem hashes, resolução/duração, detecção de preto/silêncio, tempo de render e pico RSS por processo. Medidas não provam operação diária sustentada ou desempenho perceptivo. As fontes devem continuar sujeitas à revisão editorial e de consentimento antes de eventual publicação; B reutiliza imagem de prova anterior.

## Resultado local verificado

As duas provas concluíram sob isolamento de rede no kernel, com fila/estado/histórico inalterados. B: 17,155s, render 49,33s. C: 19,467s, render 57,583s. Ambas 1080×1920, decode completo, zero preto ≥0,3s e zero silêncio ≥0,8s. Diferença entre término de áudio/vídeo: B 21,7ms; C 7,7ms — isso não mede sincronização labial.

Contact sheets inspecionadas: secador lateral agora visível; cuba e mãos visíveis; legendas fora do produto. A fonte da cuba é escura e o quadro preservado fica menor: não se afirma excelência audiovisual ou melhora de retenção. Nenhum áudio foi ouvido. Evidências completas em `framing-4.3-local-evidence.json`; MP4s e relatórios destinados ao GitHub Releases.
