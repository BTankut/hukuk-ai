# Model-Line Runtime Lane Envanteri 2026-04-19

## Official Scope

- scope = `repo-visible runtime lane inventory freeze`
- inventory_date = `2026-04-19`
- acceptance_without_model_line_label = `forbidden`

## Runtime Lane Table

| lane_label | upstream_host | upstream_model_id | local_tunnel_port | gateway_port | mevzuat_collection_reference | current_repo_role | governance_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `baseline_lane` | `btankut@192.168.12.236` | `Qwen/Qwen3.5-35B-A3B-FP8` | `30011` | `8000` | `mevzuat_faz1_shadow_20260418_compat1024` | `current_live_mevzuat_runtime` | `preserved_but_non_authoritative_for_new_major_acceptance` |
| `merged_lane` | `btankut@192.168.12.243` | `/models/merged_model_fabric_stage_20260321` | `30004` | `8004` | `mevzuat_faz1_shadow_20260418_compat1024` | `authoritative_target_for_future_major_acceptance` | `authoritative_target_for_future_major_acceptance` |

## Repo Evidence Freeze

- baseline launcher = `scripts/finetune/launch_local_baseline_gateway_dgxnode2.sh`
- merged launcher = `scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh`
- current live gateway process = `.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000`
- current live gateway env:
  - `DGX_BASE_URL=http://127.0.0.1:30011/v1`
  - `DGX_MODEL=Qwen/Qwen3.5-35B-A3B-FP8`
  - `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
- merged lane bridge evidence = `coordination/dgx1-merged-endpoint-bridge-2026-03-21.md`
- merged lane preferred-serving evidence = `coordination/dgx1-merged-serving-decision-2026-03-22.md`
- merged lane active-8000 evidence = `docs/FAZ2C-CONTROLLED-CUTOVER-EXECUTION-RAPORU-2026-03-23.md`

## Binding Interpretation

- `baseline_lane_status = preserved_but_non_authoritative_for_new_major_acceptance`
- `merged_lane_status = authoritative_target_for_future_major_acceptance`
- `merged_first_rule = true`
- `baseline_second_parity_rule = true`
- `acceptance_without_model_line_label = forbidden`

## Inventory Meaning

- Baseline lane silinmeyecek; parity ve fallback icin korunacak.
- Merged lane bundan sonraki yeni major acceptance iddialari icin authoritative hedef hatti olarak kabul edilecek.
- Mevcut repo durumu iki lane'in ayrildigini kanitliyor; sorun lane yoklugu degil, mevzuat acceptance zincirinin lane authority ile kilitlenmemis olmasidir.
