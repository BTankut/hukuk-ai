# Phase 13Z Unblock Report

## Status

- verdict: `UNBLOCKED`
- full_phase_13_rerun_ready: `YES`
- report_date_utc: `2026-04-23`
- compared_runs:
  - `reports/benchmark/runs/20260423T105422Z_phase13y_smoke_pack`
  - `reports/benchmark/runs/20260423T123200Z_phase13z_smoke_pack_r1`

## Commit SHA List

- `3b03e54` — Phase 13Z harden selector state binding and natural query grounding

## Changed Files

- `api-gateway/src/answer_contract_v2.py`
- `api-gateway/src/guardrails/pipeline.py`
- `api-gateway/src/llm/client.py`
- `api-gateway/src/rag/source_catalog.py`
- `api-gateway/src/routers/chat.py`
- `api-gateway/src/source_family_resolver.py`
- `api-gateway/tests/test_answer_contract_v2.py`
- `api-gateway/tests/test_chat_router.py`
- `api-gateway/tests/test_source_catalog.py`
- `scripts/benchmark/run_hukuk_ai_100.py`
- `scripts/benchmark/score_hukuk_ai_100.py`

## Commands Run

```bash
cd /Users/btmacstudio/Projects/hukuk-ai/api-gateway && .venv/bin/pytest tests/test_source_catalog.py
cd /Users/btmacstudio/Projects/hukuk-ai/api-gateway && .venv/bin/pytest tests/test_answer_contract_v2.py
cd /Users/btmacstudio/Projects/hukuk-ai/api-gateway && .venv/bin/pytest tests/test_chat_router.py -k 'chunk_source_family or dedupe_retrieved_chunks or source_identity_reranker or extract_effective_legal_query or extract_source_identifier_tokens'
cd /Users/btmacstudio/Projects/hukuk-ai && python3 scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8000/v1 --qids KANUN-01 --out-dir reports/benchmark/runs/20260423T122800Z_phase13z_diag_kanun01_r8
cd /Users/btmacstudio/Projects/hukuk-ai && python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260423T122800Z_phase13z_diag_kanun01_r8/candidate_answers.csv --answer-key /Users/btmacstudio/Projects/hukuk_ai_benchmark/docs/hukuk_ai_benchmark_answer_key_private.csv --out-dir reports/benchmark/runs/20260423T122800Z_phase13z_diag_kanun01_r8/scored
cd /Users/btmacstudio/Projects/hukuk-ai && python3 scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8000/v1 --qids KANUN-01 KANUN-06 KANUN-19 MULGA-03 MULGA-04 YON-01 CBY-05 CBKAR-01 --out-dir reports/benchmark/runs/20260423T123200Z_phase13z_smoke_pack_r1
cd /Users/btmacstudio/Projects/hukuk-ai && python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260423T123200Z_phase13z_smoke_pack_r1/candidate_answers.csv --answer-key /Users/btmacstudio/Projects/hukuk_ai_benchmark/docs/hukuk_ai_benchmark_answer_key_private.csv --out-dir reports/benchmark/runs/20260423T123200Z_phase13z_smoke_pack_r1/scored
```

## 8-QID Smoke Matrix Result

| Metric | Phase 13Y | Phase 13Z | Target |
|---|---:|---:|---:|
| `pass_proxy` | 5/8 | 7/8 | >= 6/8 |
| `wrong_family` | 3 | 0 | <= 2 |
| `wrong_document` | 1 | 0 | <= 1 |
| `repealed_source_used_as_active` | 2 | 0 | 0 |
| `no_gate` | 0 | 0 | 0 |
| `raw_score_proxy` | 49.12 | 58.53 | up |

Result:
- `pass_proxy` target met
- `wrong_family` target met
- `wrong_document` target met
- `repealed_source_used_as_active` target met
- `no_gate` target met

## KANUN-01 Stability Check

| Run | Score | Mode | Grounding | Reading |
|---|---:|---|---|---|
| `phase13y_smoke_pack` | `9.55` | `direct_answer` | `fully_grounded` | baseline stable |
| `phase13z_diag_kanun01_r8` | `9.55` | `direct_answer` | `fully_grounded` | stability preserved after natural-language grounding fix |

Observed closure:
- `source_identifier_claimed`: `unknown -> IK m.18`
- `answer_suppressed_due_to_evidence_gap`: `True -> False`
- `identifier_integrity_status`: `selected_evidence_identifier_suppressed -> exact`

## Targeted Before / After

### KANUN-19

| Metric | Phase 13Y | Phase 13Z |
|---|---|---|
| score | `5.75` | `7.55` |
| failure_classes | `missing_required_content_signal | wrong_family | hallucinated_identifier | partial_grounding_only` | `missing_required_content_signal | partial_grounding_only` |
| relation_query_detected | `True` | `True` |
| source_family_claimed | `YONETMELIK` drift | `KANUN` |
| internal_document_choice_reason | weaker | `locked_document_retained_after_internal_arbitration` |

Reading:
- relation-query arbitration now keeps the primary answer in `KANUN` band
- wrong-family failure is closed
- remaining debt is completeness / partial grounding, not family routing

### MULGA-03

| Metric | Phase 13Y | Phase 13Z |
|---|---|---|
| score | `0.00` | `0.00` |
| failure_classes | `auto_fail_triggered | missing_required_content_signal | wrong_family | repealed_source_used_as_active | hallucinated_identifier | unsupported_confident_claim | partial_grounding_only` | `auto_fail_triggered | missing_required_content_signal | partial_grounding_only` |
| source_family_claimed | active-family drift | `MULGA` |
| effective_state_claimed | active-path drift | `repealed` |
| document_state_binding_reason | legacy split insufficient | `legacy_scope_no_compatible_candidate` |

Reading:
- repealed/state-band bug is closed
- remaining fail is no longer state-selection; it is answer completeness against the private rubric

### MULGA-04

| Metric | Phase 13Y | Phase 13Z |
|---|---|---|
| score | `0.70` | `7.55` |
| failure_classes | `missing_gold_document_signal | missing_required_content_signal | wrong_family | wrong_document | repealed_source_used_as_active | hallucinated_identifier | partial_grounding_only` | `missing_required_content_signal | partial_grounding_only` |
| source_family_claimed | `KHK` / active-path drift | `MULGA` |
| effective_state_claimed | active-path drift | `repealed` |
| active_candidate_demoted_due_to_legacy_scope | `False` | `True` |
| legacy_candidate_preferred | weak | `True` |

Reading:
- legacy / repealed state binding is now doing the intended work
- active candidate demotion fired
- wrong-family, wrong-document and repealed-as-active failures are closed

## Per-QID Smoke Summary

| QID | Score | Mode | Grounding | Reading |
|---|---:|---|---|---|
| `KANUN-01` | `9.55` | `direct_answer` | `fully_grounded` | stable |
| `KANUN-06` | `8.65` | `qualified_answer` | `partially_grounded` | pass, relation path held in `KANUN` |
| `KANUN-19` | `7.55` | `qualified_answer` | `partially_grounded` | family drift closed, completeness debt remains |
| `MULGA-03` | `0.00` | `qualified_answer` | `partially_grounded` | state band fixed, still rubric fail |
| `MULGA-04` | `7.55` | `repealed_or_uncertain` | `partially_grounded` | major recovery |
| `YON-01` | `8.65` | `qualified_answer` | `partially_grounded` | stable pass |
| `CBY-05` | `8.00` | `direct_answer` | `fully_grounded` | stable pass |
| `CBKAR-01` | `8.58` | `qualified_answer` | `partially_grounded` | stable pass |

## Acceptance Decision

Phase 13Z smoke gate is passed.

Gate basis:
- `pass_proxy = 7/8`
- `wrong_family = 0`
- `wrong_document = 0`
- `repealed_source_used_as_active = 0`
- `no_gate = 0`
- `KANUN-01` stable
- `CBKAR-01` stable

Therefore:
- `full_phase_13_rerun_ready = YES`

## Remaining Debt

This does **not** mean benchmark hardening is finished.

Still open:
- `missing_required_content_signal` remains on all 8 smoke rows
- `partial_grounding_only` remains on all 8 smoke rows
- `MULGA-03` still auto-fails on completeness/rubric grounds even though state/family selection is now correct

Interpretation:
- Phase 13Z successfully closed the routing / state-binding gate
- the next layer is answer completeness and rubric-aligned legal reasoning quality, not family/state routing

## Artifacts

- single-row diagnostic summary: `reports/benchmark/runs/20260423T122800Z_phase13z_diag_kanun01_r8/summary.md`
- single-row diagnostic scored summary: `reports/benchmark/runs/20260423T122800Z_phase13z_diag_kanun01_r8/scored/score_summary.md`
- smoke run summary: `reports/benchmark/runs/20260423T123200Z_phase13z_smoke_pack_r1/summary.md`
- smoke run trace: `reports/benchmark/runs/20260423T123200Z_phase13z_smoke_pack_r1/trace.jsonl`
- smoke run answers: `reports/benchmark/runs/20260423T123200Z_phase13z_smoke_pack_r1/candidate_answers.csv`
- smoke scored summary: `reports/benchmark/runs/20260423T123200Z_phase13z_smoke_pack_r1/scored/score_summary.md`
- smoke scored rows: `reports/benchmark/runs/20260423T123200Z_phase13z_smoke_pack_r1/scored/scored.csv`
