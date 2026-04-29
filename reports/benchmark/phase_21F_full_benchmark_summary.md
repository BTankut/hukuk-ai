# Phase 21F Full Benchmark Summary

Date: 2026-04-29

Status: STRONG_PASS_PHASE21_ACCEPTED

Run: `reports/benchmark/runs/20260429T174747Z_phase21F_full`

## Runtime Provenance

- model: `hukuk-ai-poc`
- api_url: `http://127.0.0.1:8000/v1`
- dgx_model: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- embedding_backend/model: `remote` / `intfloat/multilingual-e5-large-instruct`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- guardrails: `false`
- presidio: `false`
- git_sha: `8eba13879bfb7aef1c9cf81b72df0f053d92bc86`
- dirty_worktree: `True`

## Gate Metrics

| Metric | Observed | Target | Result |
| --- | ---: | ---: | ---: |
| `raw_score_proxy` | 800.55 | >=780 preferred / >=770 minimum | PASS |
| `pass_proxy` | 89/100 | >=83 preferred / >=82 minimum | PASS |
| `fail_proxy` | 11 | informational | - |
| `wrong_family` | 6 | <=8 | PASS |
| `wrong_document` | 5 | <=7 | PASS |
| `hallucinated_identifier` | 5 | <=7 | PASS |
| `unsupported_confident_answer_count` | 0 | 0 | PASS |
| `unsupported_confident_claim` | 0 | <=2 | PASS |
| `answer_contract_invalid_count` | 0 | 0 | PASS |
| `contract_valid` | 100/100 | 100/100 | PASS |
| `green_lane` | pass | PASS | PASS |
| `source_key_v2_collision_detected_count` | 0 | 0 | PASS |
| `binding_source_key_collision_detected_count` | 0 | 0 | PASS |
| `auto_fail_triggered_count` | 2 | informational | - |
| `support_insufficient_for_specific_claim_count` | 8 | informational | - |
| `answer_suppressed_due_to_evidence_gap_count` | 12 | informational | - |

## Interpretation

Phase 21F clears the preferred full benchmark gate: raw score is above 780, pass count is above 83, all hard safety gates are clean, and green-lane validation passed. This is a strong Phase 21 accept, but it is not a productization or fine-tuning opening because a second stability rerun and residual blocker audit are still required.

## Artifact Pointers

- score_summary: `reports/benchmark/runs/20260429T174747Z_phase21F_full/score_summary.md`
- candidate_answers: `reports/benchmark/runs/20260429T174747Z_phase21F_full/candidate_answers.csv`
- scored: `reports/benchmark/runs/20260429T174747Z_phase21F_full/scored.csv`
- trace: `reports/benchmark/runs/20260429T174747Z_phase21F_full/trace.jsonl`
- green_lane: `reports/benchmark/green_lane/20260429T174747Z_phase21F_full`
