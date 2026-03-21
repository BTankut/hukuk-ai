# DGX1 Merged Endpoint Bridge

Date: 2026-03-21
Scope: attach the repo's local candidate gateway to the new OpenAI-compatible merged-model endpoint exposed on `dgxnode1`
Decision: accept `dgxnode1:30000/v1` as a valid serving endpoint for the current merged `807` candidate and freeze a repo-native local bridge for follow-up eval/smoke work

## Verified Endpoint

- remote base URL: `http://dgx1:30000/v1`
- model id: `/models/merged_model_fabric_stage_20260321`
- remote `GET /v1/models` returned the expected model with:
  - `max_model_len=8192`

## Repo Change

- added launcher:
  - `scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh`

This launcher opens:

- local tunnel:
  - `127.0.0.1:30004 -> dgxnode1:127.0.0.1:30000`
- local candidate gateway:
  - `127.0.0.1:8004`

with:

- `DGX_BASE_URL=http://127.0.0.1:30004/v1`
- `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
- `guardrails=enabled`
- `reranker=off`
- `milvus=on`

## Verification

- local gateway health:
  - `http://127.0.0.1:8004/v1/health` => `ok`
- cited smoke:
  - query: `TBK m.49 neyi duzenler? Kisa ve kaynakli cevap ver.`
  - result: PASS
  - citation: `TBK m.49`
  - blocked: `false`

## Notes

- the model was copied to `dgxnode1` over the `192.168.101.x` fabric lane and staged at:
  - `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/merged_model_fabric_stage_20260321`
- the local bridge is intentionally isolated on `8004` so it does not disturb the existing `8000` baseline lane or the older `8003` node3 measurement lane

## Next Step

1. run matched smoke/eval slices against `8004`
2. compare node1 merged endpoint behavior against the earlier node3 merged lane
3. decide whether node1 becomes the new preferred merged serving lane for continued eval work
