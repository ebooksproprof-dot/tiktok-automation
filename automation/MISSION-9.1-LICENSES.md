# Licenças — missão 9.1, 06/11/2026

Fontes oficiais consultadas com HTTP 200 nesta tarefa. Snapshots, revisões e SHA-256 em `mission91-evidence/`. Consentimento de publicação não substitui licença. Nenhuma flag comercial dos seis clipes de IA foi alterada.

## Componentes efetivamente carregados pelo Space

O código `app.py` do Space `zerogpu-aoti/wan2-2-fp8da-aoti-faster`, revisão observada `1ff7432a88d7827eb787ef10c15cbc5c85c841a2`, revela:

| Componente | Evidência oficial | Resultado |
| --- | --- | --- |
| Wan2.2-I2V-A14B-Diffusers, pipeline/VAE/text encoder | https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B-Diffusers ; revisão `596658fd9ca6b7b71d5057529bbf319ecbc61d74`, metadata Apache-2.0 | Uso comercial permitido sob Apache-2.0; não resolve demais componentes |
| Transformers convertidos bf16 | https://huggingface.co/cbensimon/Wan2.2-I2V-A14B-bf16-Diffusers/tree/1f424b0caf6617cfb63822bb0298331bcf44e0e1 | Sem model card/licença na árvore/API; cadeia e revisão usada em cada geração não registradas |
| LoRA **Wan2.1**, aplicada ao Wan2.2 | `Kijai/WanVideo_comfy/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank128_bf16.safetensors`, revisão `8260d429d19fd7a72304cad059160b95d843913f` | README identifica extração do upstream abaixo; não confundir com Wan2.2-Lightning |
| Upstream da LoRA | https://huggingface.co/lightx2v/Wan2.1-I2V-14B-480P-StepDistill-CfgDistill-Lightx2v ; revisão `9bedb7ceaf40d43b47d892382612ff157ca15c52`, Apache-2.0 | Permite uso comercial do upstream; não há hash da conversão usado na geração |
| Pacote compilado AOTI, blocos transformer | https://huggingface.co/cbensimon/WanTransformer3DModel-sm120-cu130-raa/tree/81e794f80b118f78d9f1f7fec4efe445c392eb61 | README/configuração identificados; metadata sem licença; revisão da geração não fixada |
| Quantização | `torchao`: Int8WeightOnlyConfig para encoder, Float8DynamicActivationFloat8WeightConfig para transformers | Operações em runtime identificadas; não são uma licença independente dos pesos |
| Referências dos seis clipes | https://www.pexels.com/license/ ; Pexels 9472849 (slots 0/1), 9462884 (2/3), 9473227 (4/5) | Página permite uso e adaptação gratuitos/comerciais. Não resolve pesos derivados nem novidade visual |

**Conclusão:** autorização comercial completa dos seis arquivos não demonstrada. Preservar `commercial_license_clearance=false`. A ausência de licença declarada não prova proibição, mas não é evidência suficiente para liberar o gate exigido. O inventário não registra a revisão do Space/pesos na geração, por isso a inspeção atual não reconstrói sozinha a cadeia histórica exata. Não solicitar nova geração no mesmo serviço apenas para contornar isso.

## Substituição gratuita autorizada

- Filmagem real já adquirida no projeto: Pixabay **34821**, autor **jaumeps99**, https://pixabay.com/videos/id-34821/ . A página oficial associa `contentUrl` ao MP4 exato e declara licença Pixabay, download gratuito, duração 16s.
- SHA-256 conferido: `e7da0c5ea4f76261bbb8871409695d16b9cb97c3c15c00282942785f454c0fae`; duração medida 15,92s; 3840×2160; 33.732.874 bytes. Inventário já continha revisão visual de 30/10. Nova contact sheet conferida nesta tarefa: vassoura recolhendo resíduos em pá junto a sofá, sem rosto identificável ou marca legível.
- Termo vinculante https://pixabay.com/service/terms/ , seção 5: "royalty-free right to download, use, copy, modify or adapt the Content for commercial or non-commercial purposes". Proíbe distribuição standalone, uso enganoso, endosso e usos comerciais de marcas reconhecíveis. Seção 6 dispensa crédito; preservamos crédito de autor, página e licença na descrição.
- A montagem acrescenta roteiro educativo contextual, narração original pt-BR, legendas medidas e identidade gráfica. Não é redistribuição do arquivo original; não alega endosso, exclusividade, resultado de produto ou que as cenas foram geradas por IA.

## Voz, ferramentas e fontes

- Kokoro-82M v1.0 / pf_dora pt-br: https://huggingface.co/hexgrad/Kokoro-82M , revisão `f3ff3571791e39611d31c381e3a41a3af07b4987`, Apache-2.0. README permite produção/comércio; VOICES identifica pf_dora. Assets int8 e voices fixados por tamanho/hash em `female_narration.py` e reconferidos na carga. A narração é sintética; não há clonagem de cliente ou testemunho real.
- Conversão/runtime kokoro-onnx 0.6.1: https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE , MIT. Assets oficiais https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1 . Licença MIT do wrapper não é usada como licença dos pesos.
- ONNX Runtime CPU (MIT), eSpeak NG (GPL-3.0-or-later), FFmpeg/libx264 (GPL) e DejaVu Sans (licença DejaVu/Bitstream Vera) permitem este uso comercial. Não são redistribuídos binários ou pesos no repositório. Nenhuma licença de música é necessária: o áudio original da filmagem é removido, usando somente a narração sintetizada.

O gate visual e a validação audiovisual permanecem obrigatórios. Uma renderização válida, licença verificada ou aceitação no Buffer não equivale a publicação confirmada.
