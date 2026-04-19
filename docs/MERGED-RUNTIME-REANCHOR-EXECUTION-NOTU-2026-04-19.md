# Merged Runtime Reanchor Execution Notu 2026-04-19

## Required Execution Fields

- `runtime_lane_before = baseline_lane@8000 -> btankut@192.168.12.236 -> Qwen/Qwen3.5-35B-A3B-FP8`
- `runtime_lane_after = merged_lane@8000 -> btankut@192.168.12.243 -> /models/merged_model_fabric_stage_20260321`
- `authoritative_lane_after = merged_lane`
- `baseline_lane_preserved = true`
- `model_line_label_present = true`
- `execution_error_count = 0`

## Executed Sequence

1. Baseline parity/fallback lane bagimsiz olarak `8004` uzerinde acildi.
2. Merged lane ayni mevzuat collection ile `8005` probe lane uzerinde dogrulandi.
3. Eski `8000` baseline active lane durduruldu.
4. Active runtime `8000` merged lane altinda yeniden acildi.
5. Probe lane temizlendi; final topology `8000 merged` + `8004 baseline` olarak freeze edildi.

## Direct Runtime Evidence

- active merged env:
  - `DGX_BASE_URL=http://127.0.0.1:30014/v1`
  - `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
  - `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
- preserved baseline env:
  - `DGX_BASE_URL=http://127.0.0.1:30012/v1`
  - `DGX_MODEL=Qwen/Qwen3.5-35B-A3B-FP8`
  - `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`

## Smoke Summary

- active merged `8000` health = `200`
- active merged `8000` models = `hukuk-ai-poc`
- active merged `8000` mevzuat query smoke = `PASS`
- active merged `8000` native dialog smoke = `PASS`
- preserved baseline `8004` health = `200`
- preserved baseline `8004` mevzuat query smoke = `PASS`
