# Revisão e consentimento em lote

Este comando reduz a aprovação a um manifesto para até14 vídeos/7dias. Não realiza
chamadas de rede, não agenda no Buffer e não publica. Revisão humana continua necessária
para coerência visual, direitos, alegações comerciais e aceitação do MP4 exato.

1. Atualize a cópia do repositório e exporte um arquivo novo:

```sh
python automation/batch_approval.py --export /tmp/casasem-review.json
```

2. Assista a cada `video_url` e confira roteiro, direitos/créditos e horário. Remova do
manifesto os itens que não deseja aprovar. Nos restantes, registre
`editorial_approved: true` e `review` com a descrição da revisão (mínimo20 caracteres).
Somente após autorização explícita, preencha `approved: true`, `route: "buffer"` e
`consented_at` com o instante real, incluindo fuso. Preserve todos os hashes e campos
de identidade exportados. Nunca copie o timestamp do exemplo como consentimento.

3. Valide sem alterações:

```sh
python automation/batch_approval.py --manifest /tmp/casasem-review.json
```

4. Após autorização e dry-run aprovado, aplique explicitamente:

```sh
python automation/batch_approval.py --manifest /tmp/casasem-review.json --apply
```

O arquivo queue.json só é substituído após validar todo o lote. Salve a alteração
revisada no GitHub para que o Runner existente a processe dentro da janela Buffer.
O envio revalida bytes hospedados, limites, horários e duplicação. Aprovação não é
evidência de agendamento/publicação. Posts já submetidos não são reautorizados.

Se fila/estado mudaram, exporte novamente e reconfira as evidências; não altere hashes
para forçar aprovação. Horários vencidos são rejeitados, nunca remapeados silenciosamente.
O uso deve ocorrer no fluxo serializado de estado ou em cópia atualizada sem outro
processo escritor; este CLI não substitui a serialização dos workflows existentes.
