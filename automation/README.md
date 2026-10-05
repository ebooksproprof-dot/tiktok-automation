# Execução online do TikTok

Este diretório contém o runner online preparado para GitHub Actions.

## O que já está pronto

- Execução automática na nuvem a cada 30 minutos.
- Execução manual pelo botão **Run workflow**.
- Leitura de uma fila de posts em `queue.json`.
- Bloqueio de publicação quando `approved` não é `true` ou `consented_at` está vazio.
- Consulta obrigatória das opções atuais da conta via Creator Info.
- Publicação via Content Posting API usando `PULL_FROM_URL`.
- Acompanhamento do `publish_id` pelo endpoint de status.
- Registro em `state.json` para evitar repostar o mesmo item.

## O que falta antes de uma publicação real

1. O app TikTok precisa concluir a configuração/revisão necessária para `video.publish`.
2. A conta TikTok precisa autorizar o app e gerar um access token.
3. O token deve ser salvo em **Settings > Secrets and variables > Actions** com o nome:
   `TIKTOK_ACCESS_TOKEN`
4. O URL do vídeo precisa estar em HTTPS e sob domínio ou URL prefix verificado no TikTok.
5. Adicionar um item aprovado à fila.

## Exemplo de item na fila

```json
{
  "id": "video-001",
  "scheduled_at": "2026-10-06T18:00:00Z",
  "approved": true,
  "consented_at": "2026-10-06T17:30:00Z",
  "video_url": "https://SEU-PREFIXO-VERIFICADO/videos/video-001.mp4",
  "title": "Legenda editada e aprovada pelo usuário",
  "privacy_level": "SELF_ONLY",
  "disable_comment": false,
  "disable_duet": false,
  "disable_stitch": false,
  "is_aigc": false
}
```

Enquanto o cliente do TikTok não estiver auditado/aprovado para publicação pública, use as limitações e níveis de privacidade permitidos pelo próprio TikTok.

**Nunca coloque client secret, access token ou refresh token dentro deste repositório público.**
