# Phase 15B Answer Slot Tracing Schema

- implementation: `api-gateway/src/routers/chat.py`
- exported_fields: `answer_slot_evidence_map`, `answer_slot_coverage_score`, `answer_slot_missing_reasons`
- benchmark_passthrough: `scripts/benchmark/run_hukuk_ai_100.py`, `scripts/benchmark/score_hukuk_ai_100.py`

## Slot Map

- `result_or_holding`: result or legal holding surface.
- `governing_source`: governing primary or secondary source.
- `exact_source_identity`: exact source identifier or citation.
- `article_or_span`: selected article/span evidence.
- `temporal_validity`: effective-state and temporal qualification support.
- `exception_or_limitation`: exception, limitation, exemption, or non-applicability support.
- `scenario_applicability`: facts-to-rule applicability support.
- `procedure_or_consequence`: procedure, deadline, obligation, sanction, or consequence support.
- `document_selection_reason`: why this document governs the answer.
- `hierarchy_or_conflict_rule`: hierarchy, conflict, or primary-vs-secondary source rationale.

## Row Shape

Each `answer_slot_evidence_map` item has:

- `answer_slot`
- `evidence_span_id`
- `evidence_article`
- `slot_confidence`
- `slot_missing_reason`

The map is diagnostic. It does not add question-specific routing behavior; it exposes whether the answer slots are backed by selected evidence spans.
