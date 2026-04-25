# Phase 18A Required Slot Matrix Report

Date: 2026-04-25

## Scope

Implemented Phase 18A required slot matrix cleanup after Phase 17F conditional acceptance.

This phase is intentionally contract-preserving:

- Existing `must_have_fact_slots` runtime gating remains unchanged.
- New task/family/query required slot matrix is emitted as trace/report metadata.
- Benchmark CSV and scorer outputs now carry the Phase 18A slot-matrix fields for per-QID inspection.

## Implementation

Added:

- `api-gateway/src/rag/required_slot_matrix.json`
- `api-gateway/src/rag/required_slot_matrix.py`

Integrated into:

- `api-gateway/src/routers/chat.py`
- `scripts/benchmark/run_hukuk_ai_100.py`
- `scripts/benchmark/score_hukuk_ai_100.py`
- `api-gateway/tests/test_chat_router.py`

New contract/trace fields:

- `required_slot_matrix_version`
- `required_slot_task_type`
- `required_slot_answer_template`
- `required_slot_source_families`
- `required_slot_family_labels`
- `required_slot_task_slots`
- `required_slot_family_additions`
- `required_slot_query_additions`
- `required_slot_matrix_slots`
- `required_slot_runtime_slots`
- `required_slot_critical_slots`
- `required_slot_resolution_reason`

## Verification

Commands run:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/required_slot_matrix.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "slot_matrix or completeness_synthesis or answer_slot_synthesis_hint"
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --help
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --help
git diff --check -- api-gateway/src/routers/chat.py api-gateway/src/rag/required_slot_matrix.py api-gateway/src/rag/required_slot_matrix.json api-gateway/tests/test_chat_router.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py
```

Result:

- Targeted tests passed: `13 passed`.
- Syntax/import checks passed.
- Benchmark runner/scorer help checks passed.
- Diff whitespace check passed.

Additional full-file check:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py
```

Result: failed on 5 existing non-Phase18A expectations:

- `test_source_family_prior_keeps_investment_program_decision_as_cb_karar_candidate`
- `test_law_filter_passed_to_retriever`
- `test_explicit_article_refs_are_force_included`
- `test_cross_law_questions_trigger_per_law_candidate_generation`
- `test_concept_anchor_rules_force_include_exact_articles`

These failures are outside the Phase18A slot-matrix write set and align with the pre-existing dirty resolver/retrieval behavior in the working tree. They were not fixed in this commit to avoid mixing unrelated changes.

## Status

Phase 18A Commit 1 is complete and ready for Phase 18B evidence-to-slot extraction.
