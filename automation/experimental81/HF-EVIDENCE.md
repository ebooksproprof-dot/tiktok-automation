# Hugging Face / ZeroGPU — mission 8.1 evidence

Observed 2026-11-02. No account created, credential changed, paid endpoint or prepaid account used. This experiment does not authorize publication.

## Main option: one actual request

Public HF API reported `ChopperBlu/ltx-2-5-demo` RUNNING at revision `0bc4ac8cb4d398b035b5f3ae9d5dbd6074918bd6`. Its live Gradio config simultaneously disclosed a model-loading `RepositoryNotFoundError`. Both can be true: a web application running does not mean its model is available. The official requested Space `Lightricks/LTX-2-5` returned HTTP401 to the unauthenticated HF API request; no authentication bypass attempted.

The published `/generate_video` schema was discovered, then called once for test A: drawer organization, 576×1024, 5 seconds, seed8101, conv decoder. It returned AppError with model-loading failure after 28.650 seconds wall time. No MP4 was produced. GPU consumption, remaining quota and queue time were not exposed and remain unknown. A prior local missing `socksio` dependency prevented client creation; installing it fixed that local dependency before the single actual request. This was not an extra generation retry.

Evidence: `evidence/ltx-attempt-A.json`, `live-summary.json`, `chopper-schema-summary.json`. Raw error is a public owner-facing setup error, not a token. Do not retry the broken Space repeatedly.

The maintainer's [source](https://huggingface.co/spaces/ChopperBlu/ltx-2-5-demo/blob/main/app.py) identifies `Lightricks/LTX-2.5-Diffusers`, two-stage distilled inference, text/image inputs, manual durations up to20s and portrait presets. It uses ZeroGPU `xlarge`. [Official model card](https://huggingface.co/Lightricks/LTX-2.5) labels the LTX-2.x Community License and gated access terms. Exact applicable license acceptance and commercial conditions have not been independently completed for this account; no commercial clearance is claimed.

## One alternative: Wan2.2 Fast

Selected `zerogpu-aoti/wan2-2-fp8da-aoti-faster`, revision `1ff7432a88d7827eb787ef10c15cbc5c85c841a2`, public runtime RUNNING. [Published source](https://huggingface.co/spaces/zerogpu-aoti/wan2-2-fp8da-aoti-faster/blob/main/app.py) uses Wan2.2 I2V14B with Lightx2v weights, quantization and compiled transforms. It requires an image, uses16fps and permits up to5 seconds. Portrait frames are approximately480×832. The [base model](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B-Diffusers) is Apache2.0; derivative/LoRA licensing still needs full review before production clearance.

A single test C request uses a cropped licensed source frame from repository `casasem-2026-10-16-1-v2.mp4`, originally Pexels9472849, rather than copying an external seller. The reference is photographed material, not AI output. The single actual request succeeded in68.683s wall time: 5.0625s,480×832,H.264,16fps,no audio,414469bytes,SHA256 `631e17ed61f5a53a2c07b248be01992ce9ff7704efdda2ecbf40498db0ee0239`. Full decode and black-frame inspection passed. Five sampled frames retained recognizable glove/cloth/faucet, but soft detail and motion-deformed edges prevent professional-quality certification. Five seconds are suitable for an explicitly experimental technical montage only. Actual GPU and quota consumption remain unknown. Full evidence in `evidence/wan-attempt-C.json`. Test B has not been executed; no image-to-video product permanence or commercial quality is assumed.

## API use, quotas and cost

[Official ZeroGPU documentation](https://huggingface.co/docs/hub/spaces-zerogpu) describes public use through Gradio, daily tier quotas and size multipliers. At review time it lists2min unauthenticated,5min free-account, and8× more for PRO; `xlarge` consumes2× quota. It says quota resets24h after first use. These are documented tier values, **not this account's measured remaining allowance**. Paid accounts may debit prepaid credits automatically after included quota, so the adapter explicitly sets `token=False` and uses no stored authentication. It neither requests paid capacity nor creates another account. No model runs on the local CPU or browser; remote GPU is required, WebGL is not.

No explicit continuous-workload guarantee for this third-party Space was found. A published public endpoint supports the one bounded evaluation; it is not unlimited automation permission or an availability SLA. Persistent request fingerprints prevent automatic repeat after a submission or uncertain failure. On future use, persist the complete ledger/output directory between runs. No automatic scheduled generation is enabled.

## Capacity: targets are not observed throughput

Using5-second source clips without repetition:

| Composition | IA clips/final | Clips needed/day for2 finals | Clips needed/week for14 finals | Demonstrated sustainable rate |
|---|---:|---:|---:|---|
|30s entirely IA|6|12|84|Not established|
|15s IA +15s real|3|6|42|Not established|
|10s IA +20s real|2|4|28|Not established|
|5s IA +25s real|1|2|14|Not established|

These are arithmetic requirements, not production promises. If actual accepted GPU quota is Q seconds/day, observed per-attempt billed usage g, and usable-clip fraction p, supported useful clips/day would be bounded by floor(Q/g)×p. Neither g nor p has been measured successfully here, so converting GPU minutes to video minutes is unjustified. Wall latency includes transport/queue/model work and is not GPU consumption. Failed or visually rejected clips reduce capacity. No nonzero recurring daily/weekly AI capacity is proven by this session.

## Adapter

`hf_probe.py` is disabled unless `AI_VIDEO_EXPERIMENTAL_ENABLED=true`; endpoint/schema discovery precedes one submission. A record is fsynced before submission; any existing record prevents another attempt. Downloaded MP4 must pass real ffprobe/full decode and a hash check, then remains `GENERATED_PENDING_VISUAL_REVIEW` with publication prohibited. No fallback model is silently chosen. Tests in `test_hf81.py` are mocks of API behavior and explicitly separate from the live evidence above.

`wan_probe.py` implements the actually tested alternative schema with the same disabled default and remote-ledger callback requirement on Actions. It does not auto-retry the live test. Six Wan adapter mock tests passed; ten LTX/interface mock tests passed. This is separate from one failed real LTX request and one successful real Wan request. A successful single sample establishes feasibility, not sustainable daily capacity.
