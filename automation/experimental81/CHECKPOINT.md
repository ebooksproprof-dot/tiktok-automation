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

## Checkpoint 2 — primeiro componente funcional

Recuperação salva e relida no commit `8758939ba29f51367584645c933806471717b91f`.
Baseline local: 327 testes aprovados. Novo `quality.py` implementa perfil30s
com tolerância±0,15s, H.264/yuv420p, AAC,1080×1920,100KB–20MB, decodificação integral,
volume/ausência de áudio, intervalos pretos/silêncio e alinhamento temporal.
O perfil legado delega ao validador existente sem modificar sua regra15–28s.
Sete testes novos passaram em5,593s, incluindo um MP4 sintético30s real, rejeição
desse arquivo pelo perfil antigo, arquivo corrompido e ausência de áudio.
Esse MP4 é fixture temporária de teste e **não é vídeo gerado por IA**.

Tentativa real LTX-A: endpoint `/generate_video` do Space ChopperBlu foi chamado
uma vez,576×1024,5s,seed8101; falhou em28,65s com AppError
`Model loading failed (RepositoryNotFoundError)`. Nenhum MP4 retornado.
Cota/GPU consumidos não expostos, registrados como desconhecidos, não zero.
Evidência `evidence/ltx-attempt-A.json`. Sem repetição do serviço bloqueado.

Pendente: testar uma alternativa I2V com referência licenciada; concluir montagem
com narração PT-BR e preservar um MP4 experimental útil, mesmo sem cenas IA.

## Checkpoint 3 — primeiro MP4 IA real preservado

Validador30s salvo e relido em `efa939bfb9b8c52de82863c55e7385fc71be79a3`.
Alternativa Wan2.2 Fast: **testeC gerou MP4 real**, uma chamada anônima autorizada,
sem conta paga, em68,683s de tempo total. Arquivo `wan-C-631e17ed61f5a53a.mp4`:
5,0625s,480×832,H.264,16fps,sem áudio,414469bytes.
SHA256 `631e17ed61f5a53a2c07b248be01992ce9ff7704efdda2ecbf40498db0ee0239`.
Evidência completa em `evidence/wan-attempt-C.json`; clipe preservado:
[MP4 IA real](https://chatgpt.com/library?file_id=libfile_2f3480460cc081919cd8857a956c4f85&account_id=personal).

Inspeção visual independente: luva/pano/torneira reconhecíveis e fundo estável;
baixa resolução, suavidade/borrão nos contornos mão-pano. **Não certificado como
qualidade profissional**. Não aprovado para publicação. Tempo GPU consumido,
cota consumida e saldo restante desconhecidos;68,683s é tempo total, não GPU medido.

Adaptadores LTX e Wan documentam endpoints descobertos, estado atômico, bloqueio
de repetições incertas e geração desativada por padrão. Execução habilitada no
GitHub Actions exige reserva remota via callback antes da submissão; sem isso
falha fechado. Nenhuma gravação na fila/estoque de publicação.

Próxima prioridade: corrigir qualquer falha de montagem real, renderizar30s,
salvar o resultado e testar o workflow experimental sem merge em main.

### Primeiro híbrido válido e persistido

ConfiguraçãoC real:5s do WanC +25s de intervalos não sobrepostos de filmagens
licenciadas previamente existentes no projeto. **30,000s,1080×1920,H.264/AAC,
7.176.507bytes**, SHA256 `e9d4eec90b61f3e13a97b99359a9a27aea57d5b1c5ca328c643c0a6631f46bce`.
Render FFmpeg17,76s. Voz Kokoro pf_dora PT-BR existente, não Keren; produção
Symphony não alterada. Legendas por limites medidos de frase, não alinhamento por palavra.
Validação integral passou; reexecução validou e reutilizou o mesmo MP4 em2,176s.
[MP4 híbrido preservado](https://chatgpt.com/library?file_id=libfile_8b50a76b559481918268408ed1e33792&account_id=personal).

TesteB Wan também gerou clipe5,0625s em75,695s totais; cota desconhecida.
[MP4 IA caixa organizadora](https://chatgpt.com/library?file_id=libfile_9343df6defd481919c2e8eadf7d9829f&account_id=personal).
Total:2 clipesIA reais/10,125s; nenhuma taxa diária/semanal recorrente comprovada.

Primeira montagem multiarquivo falhou (MP4 intermediário incompleto/moov e timing).
Corrigida com um único filtergraph FFmpeg, limites de threads, lock e validação final.
Não foi chamada de sucesso antes da correção. Evidência `evidence/first-hybrid-C.json`.

Para reproduzir sem gastar outra geração, somente o pequeno clipeIA de414KB entra
como fixture na branch experimental, vinculado a hash e evidência. Vídeos finais
ficam fora do histórico Git. O workflow experimental publica apenas evidências em
Releases, nunca na rede social; geração nova continua desativada.
