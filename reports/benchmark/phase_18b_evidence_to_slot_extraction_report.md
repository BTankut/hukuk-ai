# Phase 18B Evidence-To-Slot Extraction Report

Date: 2026-04-25

## Scope

Implemented the Phase 18B contract layer for evidence-to-slot extraction.

This commit keeps answer synthesis unchanged. It exposes verified slot objects so Phase 18C/18D can calibrate confidence and synthesize answers from slot state instead of raw context summary.

## Implementation

Added contract/trace/report fields:

- `answer_slots`
- `answer_slot_extraction_version`
- `answer_slot_required_count`
- `answer_slot_filled_count`
- `answer_slot_verified_count`
- `answer_slot_missing_count`
- `answer_slot_unsupported_count`
- `answer_slot_extraction_methods`
- `critical_answer_slots_missing`

Each `answer_slots` item follows the Phase 18B schema:

- `slot_name`
- `required`
- `value`
- `evidence_span_keys`
- `evidence_article_or_span`
- `extraction_method`
- `fill_status`
- `verifier_status`
- `confidence_0_100`
- `slot_missing_reason`

Extraction behavior:

- Matrix slots are mapped to existing canonical runtime slots.
- Deterministic metadata slots use source identity, family, identifier, article/span and temporal metadata.
- Hybrid slots reuse selected evidence span extraction and existing slot support heuristics.
- A slot is `verified` only when it has a value, evidence span key and confidence `>= 65`.
- Critical missing matrix slots are surfaced separately for Phase 18C confidence ceilings.

## Verification

Commands run:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/required_slot_matrix.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "phase18 or slot_matrix or completeness_synthesis or answer_slot_synthesis_hint"
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --help
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --help
git diff --check -- api-gateway/src/routers/chat.py api-gateway/src/rag/required_slot_matrix.py api-gateway/tests/test_chat_router.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py
```

Result:

- Targeted Phase18/slot tests passed: `15 passed`.
- Syntax/import checks passed.
- Benchmark runner/scorer help checks passed.
- Diff whitespace check passed.

Known residual:

- Full `api-gateway/tests/test_chat_router.py` still has the same 5 non-Phase18A/B failures observed after Phase18A, tied to existing source-family/retrieval expectation drift in the dirty working tree.

## Status

Phase 18B Commit 2 is complete. Phase 18C should consume `critical_answer_slots_missing`, `answer_slot_verified_count`, and `answer_slot_missing_count` for confidence ceiling policy.
