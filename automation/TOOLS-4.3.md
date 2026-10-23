# CasaSemEsforço — teste isolado de motores 4.3

## Decisão

Preservar FFmpeg/Piper na produção. EffectCraft 0.11.1 executou em CPU sem interface,
mas este teste simples não demonstra benefício para substituir o pipeline diário.
Nenhuma configuração, dependência, fila, aprovação ou publicação foi alterada.
Custo adicional contratado: R$0.

## Prova executada

O binário oficial Linux foi recuperado após o descarte do workspace anterior.
Seu SHA-256 coincidiu com o pin já existente em `effectcraft_adapter.py`:
`fe78d8df0221d06d5519e02f3c382c1dfcd3241217a0e46644b4598a215b8d61`.
Não foi aceita licença de modelos, usado GPU ou instalado outro pacote Craft.

Composição equivalente em ambos: fundo verde escuro, retângulo verde-claro
760×16 centrado em (540,1080), 1080×1920, 30 fps, 30 quadros, 1 segundo, sem áudio.
O script deriva a cena do fixture original, remove texto/animação e arredondamento,
e desativa GPU e motion blur. Três processos sequenciais por motor; inclui startup,
sem excluir aquecimento. FFmpeg usa libx264/veryfast/CRF23/2 threads; EffectCraft usa
seu encoder H264 padrão. Portanto as configurações de compressão não são idênticas.

| Medida | EffectCraft 0.11.1 | FFmpeg |
|---|---:|---:|
| Execução 1 | 0,914 s | 0,266 s |
| Execução 2 | 0,920 s | 0,253 s |
| Execução 3 | 0,821 s | 0,240 s |
| Mediana | 0,914 s | 0,253 s |
| MP4 final | 7.600 bytes | 4.428 bytes |
| Resolução/quadros/duração | 1080×1920 / 30 / 1 s | 1080×1920 / 30 / 1 s |
| Decodificação integral | Sem erros | Sem erros |

SSIM global entre os vídeos: **0,998459**, sem igualdade pixel a pixel.
Os primeiros quadros de ambos foram inspecionados: mesmo posicionamento e forma,
sem texto ausente, fundo inesperado ou retângulo cortado. A diferença não zero é
compatível com renderização/conversão de cor/compressão distintas; não foi isolada
a contribuição de cada etapa. A alta semelhança desta cena simples não comprova
fidelidade de tipografia, efeitos complexos ou filmagens reais.

FFmpeg teve menor tempo observado nesta carga. Não extrapolar para 15–28 segundos,
narração, legendas, Effects complexos ou throughput no GitHub Actions. Não alegar
melhoria de retenção ou qualidade audiovisual com base neste microbenchmark.

Medições exatas, hashes e comandos: `tools-4.3-evidence.json`.
Reprodução: `python automation/benchmark_tools43.py /caminho/effectcraft-cli`.
O script exige o hash fixado e não faz downloads nem modifica arquivos de produção.
MP4s e PNGs de QA ficam em `tmp/tools-4.3`; são regeneráveis, não são vídeos de
validação editorial nem material para publicação. A evidência inclui os hashes
dos MP4s finais e do fixture derivado.

## Ferramentas e limites recuperados

Fontes oficiais abaixo foram lidas na auditoria de 22/10/2026; não foram
reinstaladas nem declaradas novamente testadas nesta etapa.

| Ferramenta | Evidência recuperada | Decisão 4.3 |
|---|---|---|
| OpenCut | README listava Editor API e headless como futuros na reescrita | Não substituir produção |
| EffectCraft | CLI/CPU confirmado agora; documentação alerta maturidade limitada | PoC opcional, não integrado |
| FilmCraft | CLI/headless documentado, alpha; download 4.2 teve SHA de archive verificado, mas probe não terminou antes do descarte | Não declarar render funcional; não repetir instalação nesta etapa |
| PhotoCraft/VectorCraft | Headless para assets documentado; sem integração no projeto | Não há benefício necessário demonstrado |
| VoiceStudio | CPU possível; Supertonic-3 ONNX exige aceite explícito OpenRAIL-M para pesos | Não contornar aceite, preservar Piper; comparação de vozes não realizada |
| Remotion | API renderMedia documentada; licença gratuita condicionada a indivíduo/empresa de até três pessoas | Sem benchmark ou benefício demonstrado no projeto, não adicionar dependências |

## Fontes

- Binário testado: https://github.com/storytold/effectcraft/releases/tag/v0.11.1
- EffectCraft/CLI/licenças: https://github.com/storytold/effectcraft
- OpenCut: https://github.com/OpenCut-app/OpenCut
- FilmCraft: https://github.com/storytold/filmcraft
- PhotoCraft: https://github.com/storytold/photocraft
- VectorCraft: https://github.com/storytold/vectorcraft
- VoiceStudio: https://github.com/debpalash/VoiceStudio
- Supertonic-3/aceite: https://github.com/debpalash/VoiceStudio/blob/main/docs/engines/supertonic3.md
- Remotion API: https://www.remotion.dev/docs/renderer/render-media
- Remotion licença: https://www.remotion.dev/docs/license/pricing

Próximo passo, somente se um efeito concreto exigir: comparar a mesma composição
real com esse efeito, incluindo áudio e legendas, no runner gratuito. A PoC atual
já responde à viabilidade CPU; não repetir esta pesquisa nem instalar toda a suíte.
