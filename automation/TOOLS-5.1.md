# CasaSemEsforço 5.1 — inventário verificável de ferramentas

Revisão em 25/10/2026. Recupera `TOOLS-4.3.md`, `VOICE-4.1.md`, `AVATAR-4.1.md`,
`AVATAR-4.3.md` e `AVATAR-4.4.md`; não repete instalação ou benchmark já concluído.
READMEs oficiais, metadados de licença e releases foram consultados novamente para
resolver a disponibilidade atual. Versão disponível não significa versão testada.
Não foram alterados consentimentos, fila, histórico ou motores por esta auditoria.

## Estado das dez ferramentas

| Ferramenta / implementação exata | Versão disponível ou pin comprovado | Estado no CasaSemEsforço | Função, automação e decisão |
|---|---|---|---|
| [OpenCut](https://github.com/OpenCut-app/OpenCut) | Reescrita em `main`; nenhum pin instalado comprovado | INVIÁVEL NO AMBIENTE ATUAL para o caminho headless solicitado | README atual continua anunciando Editor API, MCP e headless como futuros. A versão classic é editor interativo. Não há exportação headless validada aqui; composição continua em FFmpeg. Isto não é uma afirmação de impossibilidade futura. |
| [EffectCraft](https://github.com/storytold/effectcraft) | Disponível v0.17.0; **testado e pinado v0.11.1** | PROTÓTIPO | CLI CPU real via `effectcraft_adapter.py`, hash fixado. Teste 4.3: mediana 0,914 s contra 0,253 s FFmpeg para composição de 1 s, SSIM 0,998459. Não demonstrou ganho nesta tarefa. Manter adaptador isolado, sem atualizar binário silenciosamente. |
| [FilmCraft](https://github.com/storytold/filmcraft) | Disponível v0.13.0; sem versão executada com render comprovado | NÃO AVALIADA em execução completa | Editor Rust alpha; comandos CLI, MCP headless e caminho CPU documentados. Archive histórico verificado não equivale a instalação funcional. Requer prova de exportação e benefício antes da integração. |
| [PhotoCraft](https://github.com/storytold/photocraft) | Disponível v0.16.0; não instalado no projeto | NÃO AVALIADA em execução | Editor raster Rust alpha, CLI `run`/`batch` e compositores CPU/GPU documentados. Pode preparar assets; não gera por si uma apresentadora animada. A medição tipográfica desta missão pode ser resolvida diretamente por Pillow, sem adicionar um editor inteiro. |
| [VectorCraft](https://github.com/storytold/vectorcraft) | Disponível v0.17.0; não instalado no projeto | NÃO AVALIADA em execução | CLI/MCP, exportação vetorial e composição documentadas, alpha. Potencial para ícones e identidade; sem benefício demonstrado para os elementos simples já produzidos pelo FFmpeg. |
| [VoiceStudio](https://github.com/debpalash/VoiceStudio), motor Supertonic-3 | ~99M parâmetros ONNX, ~400 MB; não instalado/pinado | INVIÁVEL NO AMBIENTE ATUAL sem autorização específica dos pesos | CPU e vozes femininas documentados. Primeiro uso exige aceite explícito; não foi aceito em nome do usuário. Nenhuma comparação auditiva ou síntese foi feita com esse motor. Preservar Kokoro e Piper. |
| [Remotion](https://www.remotion.dev/docs/renderer/render-media) | Nenhum pacote/pin Remotion em `package.json` atual | NÃO AVALIADA em execução neste projeto | React/Node/Chromium, API `renderMedia` e execução server-side disponíveis. Não exige comprar GPU para composição simples, mas não há medição local/cloud de RAM/tempo. Sem benchmark ou benefício demonstrado; não foi integrado apenas para aumentar a lista de ferramentas. |
| [FFmpeg](https://ffmpeg.org/) | Local 6.1.1-3ubuntu5; workflows usam pacote Ubuntu, não versão global fixa | INTEGRADA E VALIDADA | CLI CPU, enquadramento integral, áudio, textos, H.264/AAC, validação e MP4s reais; duas threads no encoder. Permanece renderer de produção. Registrar a versão efetiva de cada runner ao comparar desempenho. |
| [Kokoro-ONNX](https://github.com/thewh1teagle/kokoro-onnx) / [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | wrapper 0.6.1; v1.0 int8, voz `pf_dora`, ONNX Runtime 1.31.0 nos workflows | INTEGRADA E VALIDADA | CPU, interface `speak(text, wav_path)`, hashes/tamanhos fixados, seleção diária explícita. Benchmark histórico: 27,26 s de síntese, 334,5 MiB RSS. Voz feminina catalogada; superioridade perceptiva não comprovada por escuta. |
| [Piper](https://github.com/OHF-Voice/piper1-gpl) / [Faber](https://huggingface.co/rhasspy/piper-voices/blob/main/pt/pt_BR/faber/medium/MODEL_CARD) | piper-tts 1.3.0; `pt_BR-faber-medium` com hash fixado | INTEGRADA E VALIDADA | Alternativa CPU configurável, não fallback silencioso. Benchmark histórico: 1,19 s de síntese e 230,3 MiB RSS. Preservado sem reinstalação nesta auditoria. |

Não há prova atual de um editor novo instalado mas não integrado: o ambiente é
efêmero, e downloads de sessões antigas não certificam instalação presente.
Os números de CPU/RAM das ferramentas não executadas são **não medidos**, não zero.
Nenhum custo foi contratado. A execução futura gratuita depende das cotas reais do
GitHub; uma prova curta não certifica disponibilidade permanente nem dois vídeos/dia.

## Licenças: código, pesos, dados e assets são camadas distintas

- OpenCut: código MIT, conforme [LICENSE](https://github.com/OpenCut-app/OpenCut/blob/main/LICENSE). A licença não transforma uma funcionalidade futura em API disponível.
- EffectCraft, FilmCraft, PhotoCraft e VectorCraft: READMEs oficiais declaram **MIT OR Apache-2.0**, à escolha. A API GitHub identifica Apache-2.0, mas isso não elimina a opção MIT documentada. Uso comercial do código é permitido sob os respectivos termos. Assets, fontes, exemplos e marcas mantêm licenças separadas. Em particular, a marca EffectCraft tem restrição própria; não copiar logotipos nem usar exemplos como identidade CasaSemEsforço. Nenhum peso generativo desses editores foi escolhido ou validado.
- VoiceStudio: código **AGPL-3.0**, não MIT. O SDK Supertonic-3 declara MIT, porém seus pesos usam licença própria OpenRAIL-M e gate de aceite. Essas concessões não são intercambiáveis. [Documento do motor](https://github.com/debpalash/VoiceStudio/blob/main/docs/engines/supertonic3.md) revalidado: exige revisão/aceite explícito, ~400 MB, CPU. Sem aceite, não baixar/sintetizar por um caminho alternativo para contornar o gate.
- Remotion: [licença própria](https://www.remotion.dev/docs/license/pricing), gratuita para indivíduos/empresas de até três pessoas, incluindo automação e uso comercial, sujeita aos termos. Fora dessa elegibilidade há licença paga. Não foi tratada como MIT nem presumida elegibilidade organizacional ilimitada. Não contratar serviço Lambda ou outro serviço pago.
- FFmpeg: [LGPL-2.1+ com componentes GPL opcionais](https://ffmpeg.org/legal.html). O binário observado possui `--enable-gpl` e `libx264`; portanto não o descrever simplesmente como LGPL. Uso comercial é compatível com os termos aplicáveis; redistribuição de binários tem obrigações. O projeto utiliza o executável do sistema e não redistribui pesos ou binários do FFmpeg.
- Kokoro: pesos do model card oficial **Apache-2.0**; wrapper **MIT**; eSpeak NG **GPL**. Assets pinados já descritos em `VOICE-4.1.md`, sem contrato gated novo. A licença dos pesos não é uma licença de todos os possíveis datasets, gravações, nomes ou identidades; não há clonagem de pessoa identificável nesta implementação.
- Piper 1.3: projeto atual `OHF-Voice/piper1-gpl` **GPL-3.0**. O repositório `rhasspy/piper-voices` informa **MIT**; model card Faber declara dataset **CC0** e finetuning de Lessac. Essas licenças não devem ser reduzidas a “Piper é MIT”. Preservar avisos ao redistribuir componentes.
- Pillow 12.3.0, usado pela melhoria tipográfica 5.1: [MIT-CMU](https://pillow.readthedocs.io/en/stable/about.html), sem modelo ou GPU. A distribuição instalada deve conservar seus avisos. DejaVu é fonte do pacote já usado, com licença própria; não assumir que a licença Python cobre a fonte.

## Avatar: resultado preservado, sem sucesso fabricado

EchoMimic continua **PROTÓTIPO**. Código pinado
`c32b3a557003f84ead1483a2d2386035685d984d`, pesos
`987c98d1d00a5fd062c5f087719af663fa90bc53`. As camadas Apache-2.0/MIT
dos componentes examinados estão discriminadas em `AVATAR-4.3.md`.
A última tentativa CPU corrigiu dispositivos e iniciou difusão; excedeu 180 s
(total 214,131 s, pico RSS filho 14.108.036 KiB), **sem MP4**. Isso é limite
experimental medido, não prova de impossibilidade de todo avatar CPU.

SadTalker permanece com proveniência/autorização comercial BFM não resolvida;
Wav2Lip oficial restringe uso comercial; MuseTalk não tem prova CPU adequada no
projeto; LivePortrait depende de resolver modelos de terceiros e driver de
movimento, que por si não produz fala nova sincronizada. Não repetir esses
experimentos sem hipótese técnica nova e assets comercialmente compatíveis.
Uma imagem estática, voz ou editor de vídeo não satisfaz avatar animado.

## Próxima decisão técnica

A prova 5.1 compara **legendas** sobre a mesma filmagem e voz. Ela pode validar
geometria, legibilidade, fronteiras de tempo e custo de renderização. Não comprova
naturalidade vocal, retenção, sincronização labial ou superioridade cinematográfica.
Só ativar o novo estilo no workflow diário após MP4 real e revisão. Não aumentar
`COMPOSITION_REVISION` para forçar regeneração dos arquivos existentes.

Para avançar os editores Craft, escolher um único efeito que o FFmpeg atual não
resolva adequadamente, fixar versão/hash, medir a mesma cena com os dois motores e
integrar somente após saída reproduzível e benefício. Isso não desbloqueia o avatar.
