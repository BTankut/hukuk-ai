# Phase 18 Recovery A1.6 Full Collection Candidate Smoke

## Purpose

Follow-up to `phase_18_recovery_A1_5_environment_data_parity.md`.

A1.5 found that live port `8000` serves `MILVUS_COLLECTION=mevzuat_e5_shadow`, which has only `12,923` rows and is missing benchmark-critical families/documents. This smoke tested whether the existing large 1024-dim collection can recover Phase 17F-like behavior without changing live `8000`.

## Non-Destructive Runtime

Temporary gateway only:

- Port: `8018`
- DGX base URL: `http://192.168.12.243:30000/v1`
- DGX model: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Milvus rows: `349191`
- Embedding backend: `remote`
- Embedding base URL: `http://127.0.0.1:8081/v1`
- Guardrails: `false`
- Presidio: `false`

Live `8000` was not changed. Temporary `8018` was stopped after the smoke.

## Collection Inventory Finding

Available Milvus collections include:

| Collection | Rows | Dim |
|---|---:|---:|
| `mevzuat_e5_shadow` | `12923` | `1024` |
| `mevzuat_faz1_shadow_20260418_compat1024` | `349191` | `1024` |
| `mevzuat_faz1_shadow_20260416` | `349191` | `256` |
| `mevzuat_bge_m3_shadow` | `3390` | `1024` |

The large `mevzuat_faz1_shadow_20260418_compat1024` collection contains A1.5-missing sources, including:

- `4857` / `IK` / İş Kanunu
- `1362` / Cumhurbaşkanı Kararı
- `13354` / tebliğ
- `18615` / yönetmelik/kky-family source rows

## Smoke Run

Run artifact:

- `reports/benchmark/runs/20260425T_phase18_recovery_A1_6_full_collection_candidate_smoke20`

Compared against the same 20-QID A0 subset:

| Runtime | Score | Pass | wrong_family | wrong_document |
|---|---:|---:|---:|---:|
| live `8000` / `mevzuat_e5_shadow` A0 | `88.77 / 200` | `6 / 20` | `7` | `12` |
| temporary `8018` / `mevzuat_faz1_shadow_20260418_compat1024` | `133.86 / 200` | `13 / 20` | `3` | `4` |

Gate status from A1.5:

- score `>= 130 / 200`: pass
- pass `>= 12 / 20`: pass
- wrong family `<= 2`: fail by one
- wrong document `<= 5`: pass

## Per-Family Result

| Family | Pass |
|---|---:|
| `CB_GENELGE` | `4 / 4` |
| `CB_KARAR` | `2 / 3` |
| `KANUN` | `3 / 3` |
| `MULGA` | `2 / 5` |
| `TEBLIGLER` | `2 / 2` |
| `YONETMELIK` | `0 / 3` |

## Interpretation

The main A1.5 root cause is confirmed and narrowed:

- Live `8000` is bound to a narrow/incomplete Milvus collection.
- The existing large 1024-dim collection materially recovers behavior.
- Remaining failures are concentrated in `MULGA` and `YONETMELIK`, not broad corpus absence.

This means the next safe action is not Phase 18 ablation. It is a controlled runtime collection binding remediation:

1. Start a candidate gateway with `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`.
2. Run the full 100 benchmark on the candidate gateway.
3. If acceptable, switch live serving binding from `mevzuat_e5_shadow` to the full collection through the existing controlled cutover process.
4. Then re-run Phase 17F-code smoke and full benchmark before any Phase 18 ablation resumes.

Do not point live `8000` at the candidate collection until the full 100 run and cutover gate are complete.
