# Backend OAuth TikTok (Netlify)

Este backend recebe o callback do Login Kit, troca o authorization code por tokens no servidor e mantém access_token/refresh_token em Netlify Blobs.

## Variáveis obrigatórias no Netlify

- TIKTOK_CLIENT_KEY
- TIKTOK_CLIENT_SECRET
- TIKTOK_REDIRECT_URI
- TIKTOK_SCOPES (recomendado: user.info.basic,video.publish)
- RUNNER_SHARED_SECRET

Nunca coloque esses valores no repositório.

## Rotas depois do deploy

- /tiktok/login
- /tiktok/callback
- /tiktok/token (protegida por RUNNER_SHARED_SECRET)
- /tiktok/health

O TIKTOK_REDIRECT_URI deve ser exatamente:
https://SEU-SITE-NETLIFY.netlify.app/tiktok/callback

Registre esse mesmo endereço no Login Kit > Web > Redirect URI.
