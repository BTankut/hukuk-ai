# Phase 20D Verified Slot Synthesis Report

Date: 2026-04-28

Status: ACCEPTED

## Scope

Phase 20D changed only verified slot synthesis behavior in `api-gateway/src/rag/answer_synthesis.py`.

No QID-specific rule, retrieval tuning, prompt change, source identity change, article/span selector change, source-key binding change, or model/fine-tuning change was made.

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
- Runtime provenance git sha: `95cf0d69f457792c5ae17f2a2671aa43daac9baa`

The run was executed before this Phase 20D commit, so `dirty_worktree=True` is expected for the Phase 20D code delta plus unrelated pre-existing dirty files.

## Implementation

- Expanded verified answer plan mapping to Phase 20 matrix/runtime slot names, including `result_or_holding`, `direct_legal_conclusion`, `hierarchy_or_conflict_rule`, `operative_instruction`, `operative_clause`, `administrative_effect`, `scenario_application`, and transition/current-law slot aliases.
- Deduplicated legal-basis plan values so repeated `governing_source` / `selected_primary_source` / `identifier` values do not bloat the final answer.
- Prevented duplicate `Doğrulanmış cevap planı:` append after a controlled verified-slot replacement already produced a verified surface.
- Preserved trace visibility for already-controlled verified surfaces by returning visible verified slot names even when no second text append is applied.

## Smoke Comparison

Baseline: `reports/benchmark/runs/20260428T_phase20C_evidence_slot_filling_smoke20_v4_envparity`

Accepted Phase 20D run: `reports/benchmark/runs/20260428T_phase20D_verified_slot_synthesis_smoke20_v2_envparity`

Answer diff CSV: `reports/benchmark/phase_20D_verified_slot_synthesis_answer_diff.csv`

| Metric | Phase 20C | Phase 20D |
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
| answer_changed | 16 | 16 |
| regression_flag count | 0 | 0 |
| evidence_required_slot_value_count_total | 353 | 353 |
| avg_answer_slot_coverage_score | 0.883 | 0.883 |
| confidence_policy_adjusted_count | 9 | 9 |

`answer_slot_coverage_score` did not numerically increase beyond Phase 20C because the coverage cap remains controlled below `0.90`; this is intentional until a wider full-run confirms that visible-slot synthesis does not create unsupported confidence. Phase 20D improved answer surface visibility and removed duplicate verified-plan bloat without relaxing the confidence policy.

## Answer Diff Summary

- Answer text changed in 16/20 rows.
- No row had score regression.
- No row changed from pass to fail.
- No row introduced source/span drift.
- No row introduced unsupported confident answer.
- Visible slot changes were primarily deduplication of repeated legal-basis slots and exposure of matrix aliases such as `operative_instruction`, `operative_clause`, and `administrative_effect`.

## Verification

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/rag/answer_synthesis.py api-gateway/tests/test_chat_router.py`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "verified_answer_slot_plan or evidence_slot_synthesis or completeness_synthesis" -q`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_answer_contract_v2.py -q`
- 20-QID Phase 20D smoke and deterministic scorer against `hukuk-ai-poc`

## Phase 20E Entry

Phase 20E should proceed as family-specific slices. The remaining benchmark gap is not from this synthesis layer alone; it is concentrated in family-specific required slots and source/span precision cases that remained unchanged by design.
