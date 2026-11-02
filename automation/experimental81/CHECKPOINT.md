# CasaSemEsforço 8.1 — checkpoints incrementais

## Checkpoint 1 — recuperação, 02/11/2026

Branch experimental: `feature/ai-video-hybrid-30s`, criada da main
`ed8566b9ffb5dc554fb967119dd64d49b5865d9e` (Checkpoint durable video inventory).
Branch remota relida e SHA confirmado. Repositório existente recuperado por clone.
Checkpoints 7.0, 6.0 e infraestrutura de renderização, narração/EffectCraft e estoque
inspecionados. Nenhuma branch8.1 existia na listagem inicial. Sem merge para main.

Concluído: separação experimental, configuração desativada por padrão e orçamento0.
Infraestrutura preservada: 21 workflows existentes, fila, estado, Buffer, estoque,
histórico e narração. Nova experiência não autoriza publicação nem altera agendamentos.

Arquivos previstos: apenas novos módulos em `automation/experimental81`, testes
isolados `automation/tests/test_*81.py` e workflow experimental próprio. O validador
antigo 15–28s será preservado; o perfil30s ficará em módulo separado.

Bloqueios conhecidos: nenhum acesso gratuito recorrente a GPU/gerador comprovado;
créditos Studio não equivalem a créditos API; efeito visual/narração real exigem teste.
Nenhum MP4 IA novo produzido neste checkpoint. Teste do Hugging Face em andamento.

Próxima prioridade: confirmar chamada real autorizada ao gerador principal e persistir
o primeiro componente30s testado. Não interpretar Space público como API ilimitada.

## Retomada segura

Leia este arquivo na branch experimental, confira o SHA remoto e os relatórios
ao lado. Nunca limpe fila/estado de produção. Experimentos não publicam vídeos.
