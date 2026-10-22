# Auditoria independente — CasaSemEsforço 4.1

Data: 22/10/2026. Auditor: agente separado de quem implementou os componentes.
Base recuperada: `b0ebf68` (4.0). Escopo: revisão de código, workflows, testes e evidências locais 4.1; nenhuma publicação, aprovação real ou alteração de fila executada pelo auditor.

**Resultado: PARCIAL. Nenhum bloqueador de segurança identificado para salvar a integração revisada. Isso não aprova os vídeos editorialmente nem comprova a meta de dois vídeos novos por dia. Avatar animado não entregue.**

## Verificação executada

Comando independente: `python -m unittest discover -s automation/tests`.
Resultado: **215 testes aprovados**, execução local de 0,141 s; base anterior 192. Os testes unitários não executam os modelos pesados, não medem naturalidade e não equivalem à operação diária sustentada.

Foram revisados `female_narration.py`, `narration.py`, `render_daily.py`, `compare_voices.py`, `avatar_backend.py`, `batch_approval.py`, `validation_v41.py`, `save_validation_v41.py`, seus testes, os workflows diário e de validação, e os relatórios `voice-4.1-evidence.json`, `validation-4.1-local-evidence.json` e `avatar-4.1-probe.json`.

## Controles preservados e novos

| Área | Conclusão da revisão |
|---|---|
| Voz | Seleção explícita `kokoro-female` somente no passo diário de renderização. Interface legada mantém Piper por padrão; erro não escolhe serviço pago ou outra voz silenciosamente. Metadados registram `voice.name` real. |
| Modelos | Download com tamanho máximo e SHA-256 fixados; cache corrompido é rejeitado, arquivo parcial removido. ONNX usa CPU, com limites de threads. Dependências diretas do workflow têm versões fixadas. |
| Preservação | `composition_revision` não foi elevado. MP4s e aprovações existentes não são invalidados para impor uma nova renderização. |
| Aprovação em lote | Manifesto vincula snapshots completos, roteiro, SHA, URL, horário e identificação. Exige consentimento explícito e revisão editorial; dry-run padrão. Rejeita itens usados, alterados, expirados e duplicados antes da gravação atômica. Nenhuma chamada Buffer. |
| Concorrência | Aplicação de lote deve ser serializada com os demais escritores. A conferência de bytes antes de `replace` não é um bloqueio distribuído; não executar aprovação enquanto outro processo altera fila/estado. |
| Provas | Mantêm gates históricos e de semelhança, identificam formato C, ausência de avatar e `publication_allowed=false`. Comparam hashes de fila, estado e histórico antes/depois. Não entram na fila de publicação. |
| Workflow de provas | Runner Ubuntu CPU, limite de 25 minutos, sem credenciais Buffer/TikTok, sem cron de publicação. `contents: write` usado para Releases. Falha não é convertida em sucesso de produção. |
| Persistência | Assets com nomes derivados de hash, sem sobrescrita; limite local de 120 MB e acumulado de 240 MB/30 assets; rejeita listagem truncada. Confere tamanho, digest e URL por leitura da API após upload. Lote incompleto fica explicitamente identificado. |
| Segredos e custo | Nenhuma credencial literal identificada nos novos componentes revisados. Token GitHub via ambiente; nenhuma API paga, compra, GPU paga ou redefinição de quota introduzida. Não é auditoria integral de todo o histórico git. |

Problema encontrado e corrigido durante revisão: o script de provas dependia inicialmente de cache em checkout irmão. Agora esse cache é opcional; em runner limpo usa o downloader existente, com limite de tamanho, tentativas limitadas e SHA conferido. Não é necessário possuir o ambiente temporário local para executar o workflow.

## Evidência técnica e limites de qualidade

Benchmark de voz no mesmo roteiro, em processos separados, conforme relatório persistido:

| Motor | Síntese | Áudio | Pico RSS |
|---|---:|---:|---:|
| Piper | 1,19 s | 17,27 s | 230,3 MiB |
| Kokoro pf_dora | 27,26 s | 18,37 s | 334,5 MiB |

Kokoro é mais lento neste teste, mas executou em CPU. A voz feminina foi sintetizada de fato. Não houve escuta independente, avaliação de pronúncia, pesquisa com público ou comprovação de superioridade de naturalidade. A normalização final continua no FFmpeg.

Três provas locais C1/C2/C3 constam no relatório: 1080×1920, 17,27/17,61/17,99 s; renderização 50,64/48,20/62,21 s; decodificação completa e zero intervalos pretos de pelo menos 0,3 s ou silêncios de pelo menos 0,8 s nos limiares documentados. Esses números foram conferidos no relatório de execução, não reproduzidos pelo auditor com outra renderização. Máximos RSS Python/filho são separados, não consumo agregado.

As fontes e roteiros são intencionalmente os mesmos da comparação 4.0. Os três arquivos são distintos entre si, mas **não são três conteúdos inéditos para publicação**. Não se afirma melhoria de edição: preservam `composition_style.py` e legendas por trechos proporcionais, sem alinhamento palavra a palavra comprovado.

Há bloqueios editoriais: C1 mostra lavagem, não demonstra o apoio de sabonete citado; C2 é livraria, não demonstra organização doméstica; C3 corta parte do secador e enfatiza o rosto. São ilustrações técnicas, não evidência de desempenho de produtos. Pessoas reais presentes no stock não são a apresentadora virtual. Nenhum dos três deve receber aprovação automática com base apenas no teste técnico.

## Avatar e ferramentas pesquisadas

`avatar_backend.py` falha de modo explícito quando solicitado um motor não validado; seleção A/B informa fallback C. Testes confirmam esse comportamento, não qualidade de avatar. Há retrato de identidade, porém **nenhum vídeo da personagem, animação ou lip-sync foi produzido**.

SadTalker tem caminho CPU no código; ausência de inferência nesta missão e pendências dos assets de terceiros não demonstram impossibilidade universal de execução gratuita. MuseTalk documenta CUDA; CPU não foi validado. Wav2Lip oficial tem restrição comercial. LivePortrait exige atenção aos pesos InsightFace e não é, isoladamente, um sistema de fala sincronizada. VoiceStudio/Supertonic3 não foi sintetizado: seu aceite adicional não foi concedido. O bloqueio não deve ser atribuído falsamente à ausência de CPU.

OpenCut, FilmCraft, PhotoCraft, VectorCraft e Remotion não foram integrados nesta alteração. A prova CPU histórica de EffectCraft não constitui benchmark novo que justifique substituir FFmpeg. Não classificar pesquisa ou inspeção de código como teste de renderização.

## Operação diária e evidência externa

O estado recuperado registra publicação Buffer confirmada em 22/10 às 10h e histórico anterior; isso foi tratado como evidência do estado persistido, sem nova verificação direta da página pública TikTok pelo auditor. O próximo item de 18h estava sem aprovação. Testes e provas 4.1 não geraram envio novo.

Na conclusão desta revisão, a execução cloud `39832771366` foi informada pela coordenação como tendo passado instalação/regressão e iniciado renderização. **Seu resultado final, assets da Release e execução diária posterior não foram ainda verificados por este auditor.** Acrescentar o resultado cloud à entrega somente após consultar a execução e os assets. O texto fixo “Local CPU proof” no gerador deve ser interpretado com o ambiente real do relatório; não serve como prova de onde um run posterior aconteceu.

Catálogo editorial continua finito; não há comprovação de renovação ilimitada de cenas pertinentes. O fluxo em lote reduz intervenção, mas preserva julgamento humano sobre enquadramento, correspondência visual/roteiro, pronúncia e consentimento. O cron não garante início exatamente às 10h/18h. R$0 descreve custo adicional observado/nenhum serviço pago introduzido; não certifica quotas futuras ilimitadas.

## Fontes e retomada

Evidências primárias locais: arquivos e relatórios enumerados acima; `VOICE-4.1.md`, `AVATAR-4.1.md`, `BATCH_APPROVAL.md`, `DELIVERY-4.1.md`, `automation/state.json` e `automation/queue.json`. A documentação de licenças recuperada pela equipe aponta as fontes abaixo; esta auditoria não é uma análise jurídica independente de todos os pesos ou termos de terceiros.

- Kokoro: https://huggingface.co/hexgrad/Kokoro-82M e https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Wrapper e assets: https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE e https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1
- VoiceStudio: https://github.com/debpalash/VoiceStudio/blob/main/docs/engines/supertonic3.md
- SadTalker CPU: https://github.com/OpenTalker/SadTalker/blob/main/inference.py
- BFM: https://faces.dmi.unibas.ch/bfm/content/basel_face_model/downloads/BFM_NonCommercial_License_Agreement.pdf
- MuseTalk: https://github.com/TMElyralab/MuseTalk
- Wav2Lip: https://github.com/Rudrabha/Wav2Lip/blob/master/README.md
- LivePortrait: https://github.com/KlingAIResearch/LivePortrait/blob/main/LICENSE

Próximo passo: verificar conclusão e assets do run cloud; ouvir a voz e revisar enquadramento; adquirir cenas específicas licenciadas antes de aprovar um lote. Para avatar, resolver a proveniência comercial dos assets e executar smoke test CPU curto antes de qualquer integração diária. Não repetir os benchmarks ou instalar novamente componentes já comprovados sem uma hipótese concreta a testar.
