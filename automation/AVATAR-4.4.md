# Avatar 4.4 — propagação CPU na atenção de referência

Retoma exatamente a falha do run 40014366737: `ReferenceAttentionControl`
criava máscaras com `device=torch.device("cuda")` mesmo com UNets em CPU.
Resultado anterior: 73,726 segundos, pico RSS 14.104.688 KiB, nenhum MP4.
Não foi demonstrado timeout nem OOM nessa execução.

A correção AST em `avatar43_smoke.py` modifica somente os defaults conferidos
dos métodos `register_reference_hooks` e `update` na classe upstream pinada.
Quando device/dtype são omitidos, obtém os valores dos parâmetros do UNet.
Argumentos explícitos são preservados. O dtype da transferência do banco de
atenção acompanha o modelo, evitando impor float16 no caminho CPU fp32.
Não simula disponibilidade CUDA, não intercepta torch globalmente e não substitui
inferência por animação de imagem. Mudança inesperada no código upstream bloqueia
o patch. Hashes original e modificado são registrados no relatório.

Os testes novos executam a lógica modificada de propagação, preservação de
argumentos explícitos, independência de dispositivo fixo e rejeição de drift.
Esses testes não comprovam inferência, boca sincronizada ou qualidade visual.
O workflow existente dispara com a alteração do script, mantém dez minutos,
CPU e limites de download/RAM/disco. O relatório só declara vídeo após MP4 com
áudio e vídeo válidos, duração e dimensões corretas e decodificação completa.

O retrato e a voz Kokoro C3 são reutilizados; não se sintetiza nova voz. Cada
runner GitHub é efêmero: a instalação isolada e download de pesos podem precisar
ser repetidos; não existe cache de modelos persistente configurado. Isso não é
reinstalação de um ambiente de produção existente. Nenhuma publicação é feita.

Resultado da nova execução cloud: pendente de push/execução. Não há novo MP4
de avatar comprovado por esta alteração de código.

Fonte examinada:
https://github.com/antgroup/echomimic/blob/c32b3a557003f84ead1483a2d2386035685d984d/src/models/mutual_self_attention.py

## Execução real concluída

Run40015884986 / job120627699722. O patch superou o erroCUDA: áudio, latentes, face mask e atenção foram preparados emCPU; loopdiffusion iniciou0/4. Subprocesso excedeu180segundos (total214,131s; picoRSSfilho14.108.036KiB), semMP4. Relatório avatar-4.4-result.json, artifact12528422677 SHA7003817c43aa28aab6f7ae16bbdd39064d71d322f97335c2f46e3b62819c7612. Não foi demonstrada impossibilidadeCPU geral; orçamento e qualidade comercial não validados. Não integrar na produção.
