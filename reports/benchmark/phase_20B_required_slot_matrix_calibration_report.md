# Phase 20B Required Slot Matrix Calibration Report

Date: 2026-04-28

## Scope

Phase 20B implemented a systemic required-slot matrix calibration in:

```text
api-gateway/src/rag/answer_slots.py
```

No retrieval, source identity, article/span selector, source-key binding, prompt,
or answer synthesis policy was changed.

The calibration is intentionally limited to the allowed Phase 20 runtime surface:

- family/task slot additions are resolved in `answer_slots.py`
- new Phase 20 slot aliases are mapped onto existing runtime slots
- no QID-specific rule or private answer-key training was added

## Calibration Changes

Added Phase 20B calibrated slot aliases:

| Matrix slot | Runtime slot mapping |
|---|---|
| `direct_legal_conclusion` | `result_or_holding` |
| `document_selection_rationale` | `document_selection_reason` |
| `governing_regulation` | `governing_source`, `exact_source_identity` |
| `procedure_or_condition` | `procedure_or_consequence`, `scenario_applicability` |
| `relation_to_law_if_question_asks` | `hierarchy_or_conflict_rule`, `document_selection_reason` |
| `scenario_application` | `scenario_applicability` |
| `supporting_regulation_or_teblig_relation` | `hierarchy_or_conflict_rule`, `document_selection_reason` |

Family/task calibration:

| Family / condition | Added slots |
|---|---|
| `mulga`, `mulga_kanun` | `direct_conclusion` |
| `teblig`, `tebligler` | `exception_or_limitation` |
| `yonetmelik` | `governing_regulation`, `article_or_span`, `scope`, `procedure_or_condition`, `exception_or_limitation`, `direct_conclusion` |
| `yonetmelik` relation query | `relation_to_law_if_question_asks` |
| `cb_karar` relation query | `supporting_regulation_or_teblig_relation` |

The calibrated rows expose matrix version suffix:

```text
phase18a-2026-04-25+phase20b
```

## Slot Matrix Diff

Diff artifact:

```text
reports/benchmark/phase_20B_slot_matrix_diff.csv
```

Compared against R8-F 20-QID smoke:

| Metric | Result |
|---|---:|
| compared rows | 20 |
| slot/matrix changed rows | 12 |
| source/span changed rows | 0 |
| pass/fail changed rows | 0 |
| total score delta | 0.00 |

Rows with calibrated slot fields:

| QID | Required slots | Filled slots | Missing slots |
|---|---:|---:|---:|
| `CBKAR-01` | 14 -> 15 | 14 -> 15 | 0 -> 0 |
| `CBKAR-02` | 16 -> 17 | 14 -> 15 | 2 -> 2 |
| `CBKAR-08` | 18 -> 19 | 15 -> 16 | 3 -> 3 |
| `MULGA-01` | 11 -> 17 | 11 -> 17 | 0 -> 0 |
| `MULGA-02` | 10 -> 16 | 9 -> 15 | 0 -> 0 |
| `MULGA-03` | 11 -> 11 | 11 -> 11 | 0 -> 0 |
| `MULGA-05` | 11 -> 11 | 11 -> 11 | 0 -> 0 |
| `TEB-01` | 18 -> 18 | 18 -> 18 | 0 -> 0 |
| `TEB-02` | 18 -> 18 | 14 -> 14 | 4 -> 4 |
| `YON-01` | 13 -> 19 | 10 -> 16 | 3 -> 3 |
| `YON-02` | 9 -> 15 | 9 -> 15 | 0 -> 0 |
| `YON-03` | 9 -> 15 | 9 -> 14 | 0 -> 1 |

## Focused Tests

Commands:

```text
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/rag/answer_slots.py \
  api-gateway/tests/test_answer_slots.py

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_answer_slots.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "required_slot_matrix or answer_slots or completeness_synthesis" -q
```

Results:

| Gate | Result |
|---|---:|
| `py_compile` | PASS |
| `test_answer_slots.py` | 4 passed |
| `test_chat_router.py` focused slot/completeness filter | 12 passed |

## 20-QID Smoke

Run directory:

```text
reports/benchmark/runs/20260428T_phase20B_slot_matrix_smoke20_envparity
```

Compared with R8-F smoke:

| Metric | R8-F smoke | Phase 20B smoke | Delta / Status |
|---|---:|---:|---:|
| `raw_score_proxy` | 140.23 / 200 | 140.23 / 200 | 0.00 |
| `pass_proxy` | 15 / 20 | 15 / 20 | 0 |
| `fail_proxy` | 5 / 20 | 5 / 20 | 0 |
| `contract_valid` | 20 / 20 | 20 / 20 | PASS |
| `unsupported_confident_answer_count` | 0 | 0 | PASS |
| `answer_contract_invalid_count` | 0 | 0 | PASS |
| `source_key_v2_collision_detected_count` | 0 | 0 | PASS |
| `binding_source_key_collision_detected_count` | 0 | 0 | PASS |
| `selector_exact_article_hit_rate` | 0.75 | 0.75 | 0.00 |
| `selector_same_document_hit_rate` | 1.00 | 1.00 | 0.00 |
| `avg_answer_slot_coverage_score` | 0.828 | 0.828 | 0.000 |
| `minimum_answer_facts_present_count` | 18 | 18 | 0 |
| `canonical_missing_required_content_signal` | 20 | 20 | 0 |
| `canonical_partial_grounding_only` | 20 | 20 | 0 |

Runtime rubric class after Phase 20B smoke:

| Class | Count |
|---|---:|
| `rubric_sufficient` | 18 |
| `legally_aligned_but_partial` | 2 |

## Runtime Provenance

| Field | Value |
|---|---|
| Gateway API URL | `http://127.0.0.1:8000/v1` |
| Gateway model | `hukuk-ai-poc` |
| DGX base URL | `http://192.168.12.243:30000/v1` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024` |
| Milvus entity count | `349191` |
| Vector dimension | `1024` |
| Embedding backend | `remote` |
| Embedding base URL | `http://127.0.0.1:8081/v1` |
| Embedding model | `intfloat/multilingual-e5-large-instruct` |
| Guardrails | `false` / health `disabled` |
| Presidio | `false` |

The smoke run was intentionally executed before the Phase 20B commit, so
`dirty_worktree=True` is expected in the run provenance. The runtime environment
and model/corpus provenance match the required Phase 20 gate.

## Decision

Phase 20B passes the controlled 20-QID smoke.

The next safe intervention area is Phase 20C: evidence-to-slot filling for the
slots still missing after calibration, especially:

- `exception_or_limitation`
- `hierarchy_or_conflict_rule`
- `scenario_applicability`
- `procedure_or_consequence`
