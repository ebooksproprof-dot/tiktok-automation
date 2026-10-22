# Voz feminina CPU — checkpoint 4.1

Motor implementado: **Kokoro-82M v1.0 int8, pf_dora, pt-br**, com kokoro-onnx 0.6.1 e ONNX Runtime CPU (2 threads). Não substitui implicitamente Piper; não chama API de síntese nem fallback pago. Assets fixados por tamanho e SHA-256; cache corrompido ou download incompleto bloqueiam a síntese.

Fontes oficiais verificadas em 22/10/2026:

- Pesos Kokoro: https://huggingface.co/hexgrad/Kokoro-82M — Apache-2.0; model card permite produção e aplicações comerciais.
- Voz feminina brasileira pf_dora: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Exemplo oficial pt-br: https://github.com/thewh1teagle/kokoro-onnx/blob/main/examples/portuguese.py
- Wrapper MIT: https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE
- Assets públicos: https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1

Não foi aceito contrato adicional, diálogo de aceite ou licença gated. Os assets são baixados das URLs públicas do mantenedor. A licença Apache-2.0 exige preservar avisos ao redistribuir pesos; este repositório não incorpora os pesos.

## Comparação executada

Mesmo roteiro de seis frases em `compare_voices.py`; processos Linux separados; nenhum GPU. Evidência estruturada: `voice-4.1-evidence.json`.

| Medida | Piper pt_BR-faber-medium | Kokoro pf_dora |
|---|---:|---:|
| Inicialização com cache | 1,62 s | 1,28 s |
| Síntese | 1,19 s | 27,26 s |
| Duração WAV | 17,27 s | 18,37 s |
| Pico RSS processo | 230,3 MiB | 334,5 MiB |
| Custo adicional desta execução | R$0 | R$0 |

Kokoro ficou mais lento; a medida local é compatível com lotes pequenos em CPU, mas não prova cota, SLA ou dois vídeos/dia sustentados no GitHub Actions. Modelo e vozes ocupam aproximadamente 142 MB antes das bibliotecas. Os dois WAVs decodificam e não contêm silêncio contínuo >=0,8s a -45dB. O renderer mantém normalização loudnorm -16 LUFS.

A voz é feminina segundo o catálogo oficial. Não foi feita escuta humana nem avaliação de pronúncia/naturalidade: não se afirma ganho perceptivo. Legendas usam limites medidos de cada frase; subdivisões de frases são proporcionais ao texto, não alinhamento fonético/palavra a palavra.

## Reproduzir

Reutilize o ambiente Piper existente; acrescente somente `kokoro-onnx==0.6.1`. Execute cada motor em processo separado para medir RSS:

```sh
python automation/compare_voices.py --engine piper --cache tmp/piper-assets --output tmp/voice-comparison/piper
python automation/compare_voices.py --engine kokoro --cache tmp/kokoro-assets --output tmp/voice-comparison/kokoro
```

`KokoroFemaleEngine(cache)` implementa `speak(text, wav_path)` usado pelo `narration.synthesize`. Falha explícita para texto vazio/acima de 600 caracteres, pesos alterados e saída não mono/24 kHz/finita. Não oculta erros com outra voz.

`validation_v41.py` cria três provas C1–C3 com imagens e roteiros da comparação 4.0, voz feminina e composição atual. Usa arquivos de mídia previamente verificados; preserva verificações de histórico e diversidade; marca provas sem aprovação; confere hashes de fila, estado e histórico ao terminar. Não são vídeos com avatar nem novas demonstrações de desempenho. Reutilizar a mesma imagem entre versões é intencional para comparar voz/edição, e não serve como conteúdo novo publicável.

## VoiceStudio

O candidato recuperado é VoiceStudio/Supertonic3. Documentação oficial: https://github.com/debpalash/VoiceStudio/blob/main/docs/engines/supertonic3.md . Declara ONNX CPU (~99M parâmetros, ~400MB), vozes femininas F3/F4/F5 e **diálogo obrigatório de aceite da licença OpenRAIL-M** dos pesos. Não foi aceito nem sintetizado: o bloqueio é autorização de licença, não CPU. O nome VoiceStudio isoladamente não identifica todas as implementações homônimas; esta conclusão vale para esse projeto. Kokoro oferece uma alternativa testada sem esse gate.

## Integração diária 4.1

O passo de criação diária seleciona explicitamente `NARRATION_ENGINE=kokoro-female`. A interface conserva Piper como padrão para chamadas antigas e rollback explícito. Não há fallback silencioso. MP4s existentes não são regenerados; o metadado `quality.voice` registra o motor realmente utilizado. A aprovação editorial continua obrigatória, inclusive para avaliar pronúncia e adequação de cada nova voz.

O fonemizador utiliza eSpeak NG (GPL); uso comercial é permitido sujeito às obrigações aplicáveis de redistribuição. Pesos e dependências não são incorporados a este repositório.
