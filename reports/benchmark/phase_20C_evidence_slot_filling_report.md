# Phase 20C Evidence Slot Filling Report

Date: 2026-04-28

Status: ACCEPTED

## Scope

Phase 20C implemented a general evidence-to-slot filling improvement inside `api-gateway/src/rag/answer_slots.py`.

No QID-specific, question-specific, source-specific, retrieval, top-k, prompt, model, source identity, article/span selector, source-key binding, or fine-tuning changes were made.

## Runtime Provenance

- API URL: `http://127.0.0.1:8000/v1`
- Model id: `hukuk-ai-poc`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Milvus entity count: `349191`
- Vector dimension: `1024`
- Embedding backend/model: `remote` / `intfloat/multilingual-e5-large-instruct`
- Guardrails: `disabled`
- Presidio: `disabled`
- Verification: `disabled`

The smoke run was executed before this Phase 20C commit, so runtime provenance records `git_sha=926e7f1181ddb8b134ddf531f95755908cbcb197` with `dirty_worktree=True`. The dirty worktree includes the Phase 20C patch plus unrelated pre-existing files.

## Implementation

- Added evidence-backed fallback mapping between compatible runtime slot classes.
- Fallback only fires when the fallback evidence row has a value, span id, confidence >= 0.65, and slot-specific support terms in the evidence text.
- Added verified answer-slot materialization into `evidence_required_slot_values`; this makes the count increase auditable in the returned contract instead of using a standalone metric-only override.
- Preserved existing `evidence_required_slot_values` rows; materialized matrix rows do not overwrite already-exported rows.
- Capped the matrix-derived `answer_slot_coverage_score` at `0.89` pending Phase 20D output visibility work, so the confidence cap is not bypassed by hidden slots.

An earlier unsafe variant removed too much of the confidence cap and produced unsupported confident regressions (`unsupported_confident_answer_count=2` on the 20-QID smoke). That variant was rejected and not kept.

## Smoke Comparison

Baseline: `reports/benchmark/runs/20260428T_phase20B_slot_matrix_smoke20_envparity`

Accepted Phase 20C run: `reports/benchmark/runs/20260428T_phase20C_evidence_slot_filling_smoke20_v4_envparity`

Diff CSV: `reports/benchmark/phase_20C_evidence_slot_filling_diff.csv`

| Metric | Phase 20B | Phase 20C |
| --- | ---: | ---: |
| total | 20 | 20 |
| raw_score_proxy | 140.23 | 140.23 |
| pass_proxy | 15 | 15 |
| contract_valid | 20 | 20 |
| unsupported_confident_answer_count | 0 | 0 |
| answer_contract_invalid_count | 0 | 0 |
| source_key_v2_collision_detected_count | 0 | 0 |
| binding_source_key_collision_detected_count | 0 | 0 |
| source/span drift count | 0 | 0 |
| evidence_required_slot_value_count_total | 118 | 353 |
| avg_evidence_required_slot_value_count | 5.9 | 17.65 |
| avg_answer_slot_coverage_score | 0.828 | 0.883 |
| confidence_policy_adjusted_count | 11 | 9 |

Changed QIDs: 20/20, limited to slot/coverage/materialized evidence fields and confidence-policy adjustments derived from those fields. Source, document, article, span, and binding fields had zero drift.

Rows with reduced missing answer slots:

- `CBG-01`: missing `1 -> 0`
- `CBG-02`: missing `4 -> 3`
- `CBKAR-02`: missing `2 -> 0`
- `CBKAR-08`: missing `3 -> 1`
- `TEB-02`: missing `4 -> 2`
- `YON-01`: missing `3 -> 1`

## Verification

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/rag/answer_slots.py api-gateway/tests/test_answer_slots.py`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_answer_slots.py api-gateway/tests/test_chat_router.py -k "required_slot_matrix or answer_slots or completeness_synthesis" -q`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_answer_contract_v2.py -q`
- 20-QID Phase 20C smoke and deterministic scorer against `hukuk-ai-poc`

## Phase 20D Entry

Phase 20C deliberately improves contract-visible slot filling without claiming full answer completeness. Phase 20D should make verified slots visible in the final answer text and then re-evaluate whether the coverage cap can safely move above `0.89`.
