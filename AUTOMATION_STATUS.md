# CasaSemEsforço 3.0 — checkpoint 2026-10-20 UTC

Estado: PARCIAL. Publicação Buffer funcional; produção editorial contínua não comprovada.

## Base confirmada antes das alterações
- HEAD dcdf1161c12e867b5ef5dbabd6893bf36afe7fcd.
- Runner 39336473612: autenticação Buffer correta, 47 testes, sete publicações verificadas pelo provedor (cinco Buffer, duas Metricool). Não inspecionadas independentemente na página pública nesta retomada.
- Renderizador FFmpeg/Piper, Releases mensais, fila e estado persistentes. Código atual já tinha 11 fontes visuais e revisão de composição 4.
- Problema real: fontes reutilizadas entre temas; SHA do MP4 final não detecta cenas repetidas.

## Marco 1
Biblioteca visual integrada ao renderizador e aos dois publicadores: SHA por arquivo, cinco fingerprints perceptuais por fonte, histórico em fila/estado e bloqueio conservador de reutilização. 53 testes locais passaram, preservando os 47 anteriores. Fingerprint é heurístico; não comprova originalidade semântica. Fontes antigas sem fingerprints são comparadas por URL; backfill ainda necessário para detectar reencodes históricos. Nenhuma mídia inadequada deve ser aprovada só para manter frequência.

## Continuidade
Integrar gate no renderizador/publicador, testar regressões, produzir três exemplos com cenas distintas, modularizar narração e avaliar ferramentas oficiais. Preservar posts já enviados; não repetir o teste público anterior. Não há credenciais neste documento.

## Marco 2
- Commit visual: 0bcc392517fd78abd338cfe38032c74f3a30ebb4.
- Narração isolada em interface speak(text, wav), Piper CPU, frases completas e legendas por trecho temporal medido. Voz/modelo com hash fixado; runtime ONNX fixado.
- Três provas locais em andamento: bancada, piso e gaveta, fontes independentes. Não publicadas e não enfileiradas pelo script preview_batch.
- Releases agora limitados a seis coleções mensais de até 64 arquivos/20MB. Não há exclusão automática de histórico; ao atingir teto, exige política de arquivo/revisão.
- OpenCut atual anuncia headless como futuro; não substitui FFmpeg. Craft oficial storytold; EffectCraft em PoC isolada. VoiceStudio é candidato experimental, não instalado como dependência obrigatória.
