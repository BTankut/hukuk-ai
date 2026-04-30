# Phase 22A Stability Comparison vs Phase21F

Status: STABILITY_PASS

Run: `reports/benchmark/runs/20260430T112106Z_phase22A_stability_full`
Baseline: `reports/benchmark/runs/20260429T174747Z_phase21F_full`

## Runtime Provenance

- model: `hukuk-ai-poc`
- dgx_model: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- guardrails: `false`
- git_sha: `d70da5116590e550a8b25f438320d6be43777f10`

## Stability Metrics

| Metric | Phase22A | Phase21F | Delta | Accept | Result |
| --- | ---: | ---: | ---: | ---: | ---: |
| `raw_score_proxy` | 800.55 | 800.55 | +0.00 | >=790 | PASS |
| `pass_proxy` | 89 | 89 | +0 | >=87 | PASS |
| `wrong_family` | 6 | 6 | +0 | <=8 | PASS |
| `wrong_document` | 5 | 5 | +0 | <=7 | PASS |
| `hallucinated_identifier` | 5 | 5 | +0 | <=7 | PASS |
| `unsupported_confident_claim` | 0 | 0 | +0 | <=2 | PASS |
| `contract_valid` | 100/100 | 100/100 | 0 | 100/100 | PASS |
| `source_key_v2_collision` | 0 | 0 | +0 | 0 | PASS |
| `binding_source_key_collision` | 0 | 0 | +0 | 0 | PASS |
| `green_lane` | pass | pass | - | PASS | PASS |

## Family Stability

| Family | Phase22A Pass/Total | Phase21F Pass/Total | Pass Delta | Phase22A Raw | Phase21F Raw | Raw Delta | Floor | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CB_GENELGE | 4/4 | 4/4 | 0 | 35.20 | 35.20 | +0.00 | >=4/4 | PASS |
| CB_KARAR | 8/8 | 8/8 | 0 | 68.14 | 68.14 | +0.00 | >=7/8 | PASS |
| CB_KARARNAME | 6/6 | 6/6 | 0 | 52.07 | 52.07 | +0.00 | >=6/6 | PASS |
| CB_YONETMELIK | 4/6 | 4/6 | 0 | 46.85 | 46.85 | +0.00 | not specified | - |
| KANUN | 19/21 | 19/21 | 0 | 165.28 | 165.28 | +0.00 | >=19/21 | PASS |
| KHK | 6/6 | 6/6 | 0 | 53.15 | 53.15 | +0.00 | >=6/6 | PASS |
| KKY | 9/11 | 9/11 | 0 | 89.61 | 89.61 | +0.00 | >=9/11 | PASS |
| MULGA | 4/5 | 4/5 | 0 | 32.12 | 32.12 | +0.00 | >=4/5 | PASS |
| TEBLIGLER | 7/8 | 7/8 | 0 | 62.01 | 62.01 | +0.00 | >=6/8 | PASS |
| TUZUK | 3/5 | 3/5 | 0 | 31.15 | 31.15 | +0.00 | not specified | - |
| UY | 10/10 | 10/10 | 0 | 88.32 | 88.32 | +0.00 | >=9/10 | PASS |
| YONETMELIK | 9/10 | 9/10 | 0 | 76.65 | 76.65 | +0.00 | >=7/10 | PASS |

## Green Lane

- status: `pass`
- run_validation: `pass`

## Decision

Phase22A stability gate passed. The full benchmark reproduced Phase21F exactly on headline metrics (`800.55`, `89/100`) under the same merged DGX runtime and same Milvus collection. No runtime code changes were made.
