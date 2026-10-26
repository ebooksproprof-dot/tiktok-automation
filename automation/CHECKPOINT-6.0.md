# CasaSemEsforço 6.0 — integration blocked, configuration and intake implemented

Date: 2026-10-26. Recovered main at `5b7bf625bcb34cc5415335b446210a8b5e0fa7fc`, including CHECKPOINT-5.2 and AUDIT-5.2. No restart. No preexisting production file modified.

## Live checks and exact blockers

* GitHub connector read/write permission confirmed; clone recovered. 275 existing tests passed before changes.
* Symphony Studio opened in cloud browser and Get started redirected to TikTok for Business login. No authenticated account access. Secure authentication form validation returned locator_invalid; credentials were neither obtained nor entered. Account entitlement, avatar compatibility, Keren API voice ID and locale mapping remain unverified.
* Official Symphony API page confirms digital-avatar endpoints exist. Its View docs link redirects to Lark login, so no authenticated API contract was obtained. No endpoints, OAuth scopes, response codes, voice IDs or prices invented. No generation request sent.
* Official Studio credit documentation says avatar videos do NOT consume Symphony credits. Credit-consuming features renew Monday 00:00 UTC (Sunday 21:00 Brasília), with no rollover. This is Studio policy, NOT a verified API allowance. API capacity fields remain null; no fabricated renewal manager.
* Metricool connector authenticated successfully. Brand 7212680, network `@.casasemesforo`, timezone America/Sao_Paulo. Query 2026-10-26 through 2026-11-26 returned no scheduled posts. Account plan not exposed by this operation.
* Official Metricool Free limit is 20 posts/month; external API requires Advanced or Custom. Free MCP access is not proof GitHub Actions can reuse ChatGPT credentials. Two daily posts would need 60 in a 30-day month. No purchase, upgrade, token extraction or paid integration attempted.
* Existing Buffer route preserved. Persisted state has 12 publicly verified historic records, latest 22 October 10:00; not independently rechecked live this session. Latest inspected failed runner 40342799656 failed at daily coverage, after queue reconciliation/persistence. It must not be reported as a working two-per-day service.

## Delivered functionality

`symphony.json` locks user requirements: avatar 7616458821397659655, Keren, pt-BR, 1080x1920, 10h/18h America/Sao_Paulo, R$0, no identity fallback. Configured does not mean generated/validated. API IDs remain null.

`symphony_intake.py` implements OFFLINE script intake, atomic JSON persistence, normalized exact-script duplicate rejection, bounded queue, and local MP4 intake. Two original pt-BR scripts are pending in `symphony_queue.json`; no MP4 exists. It is not a generation pipeline or capacity manager.

MP4 intake requires matching identity declarations, source evidence reference, script hash and file hash; uses existing real ffprobe/FFmpeg validation and rejects duplicate media. Declarations are not proof of identity. Technical success never approves identity, lip-sync or publication. Local import records its path and `media_persisted=false`; it does not upload or durably store media. Keep the MP4 separately until an approved persistent upload is implemented. Do not commit local import records containing sensitive paths/evidence URLs.

New workflow `symphony-readiness.yml` runs regression tests/status on relevant pushes or manual dispatch. Read-only permissions, standard public runner, no secrets, no generation, no scheduled polling and no publishing. A green run means configuration/intake validation only.

Existing schedules, queue, consent requirements, Buffer, acquisition, renderers, history and prior avatar experiments remain untouched. Existing renderer still uses its original voice; it is not Keren and is not relabeled Symphony. No fallback avatar/voice was used for this mission.

## Reproduction

```sh
python -m unittest discover -s automation/tests -v
python automation/symphony_intake.py status
python automation/symphony_intake.py enqueue --script-file /path/original-pt-BR.txt
python automation/symphony_intake.py import --id symphony-ID --video /path/final.mp4 --manifest /path/evidence.json
```

Import manifest fields: `avatar_id`, `voice_name`, `locale`, `script_sha256`, `sha256`, `source_evidence`. Never include credentials or signed download URLs. Export evidence must be reviewed before any publishing adapter can accept the candidate. No auto-promotion command exists. Concurrent queue writes must share the existing `casasemesforco-state` lock; CLI atomic replacement protects interruption, not multiple simultaneous writers.

## Validation evidence and pending tests

281 unit/regression tests passed locally (275 preexisting + 6 new). New tests simulate candidate metadata/validator outcomes; they are NOT real Symphony generation tests. Real checks: repository recovery, Studio navigation/login requirement, official documentation reads, Metricool connection and empty scheduling query, CLI persistence/status. No real MP4 generated/downloaded; no avatar/Keren/pt-BR audio/lip-sync/facial motion/subtitle/black-frame/audio QA executed on Symphony media. No API authentication, generation, quota exhaustion/renewal, scheduling, new publication or unattended end-to-end continuation proven.

Independent reviewer ran tests and examined base and patch. Identified missing candidate media locator; fixed with local_media_path and media_persisted=false. Review confirmed no existing production files modified. Same-presenter visuals must be separated from novel B-roll duplicate checks in any future adapter.

## Resume in priority order

1. Authenticate Studio securely; verify selected avatar and Keren and produce a real MP4 only if the action is free.
2. Obtain official API access/documentation and verify account free entitlement, authentication method, exact avatar/voice/locale mappings, download rights, commercial/affiliate terms, duration/rate limits and AI labeling. Studio UI selection alone is insufficient.
3. Implement API adapter only against that verified contract. Persist remote job IDs before polling; never retry uncertain create requests without official idempotency/reconciliation. Derive cooldown/renewal only from documented responses.
4. Verify candidate identity and real audiovisual quality. Store MP4 durably with hash and provenance. Preserve the fixed presenter while checking originality of script and product demonstration separately.
5. Verify Metricool plan/token availability without upgrades. If Free, preserve official Buffer alternative already implemented; do not bypass platform limits. Validate actual publishing and AI/commercial disclosures before claiming success.
6. Only after these gates pass connect queue consumption, capacity/reserve production and cloud schedules. No promise of exact GitHub cron delivery or permanent free API entitlement.

Sources consulted:
* https://ads.tiktok.com/creative/creativeCenter/tools/api
* https://bytedance.larkoffice.com/wiki/KcOawZdBwiiI0MkTOU8c6a2Lnac (redirected to login)
* https://ads.tiktok.com/resources/help/article/about-symphony-credits
* https://help.metricool.com/plans-add-ons-and-api-access-explained-xux1u

Mission status: PARTIAL. No new publication. No additional purchase or paid resource enabled. R$0 end-to-end operation is unconfirmed.

## Remote persistence verified

Implementation committed to main: 2cc7728febb3db144dbd3100a9be6cfa03623886. GitHub Actions run 40380548084 (Symphony configuration and intake validation) completed successfully in the cloud. This is regression/configuration validation only, not a real generation or publication test.

https://github.com/ebooksproprof-dot/tiktok-automation/actions/runs/40380548084

