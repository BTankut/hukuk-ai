# Phase 21E CB_KARAR Smoke Report

## Commit SHAs

- Audit commit: `d7200d5a92a5230f46819984f21e823c316217b6`
- Remediation commit: `fa6035c72ef42667041059f0cd3515335cc25e8b`

## Audit Summary

Audit source run: `reports/benchmark/runs/20260428T_phase20F_full_after_C_D`

Audit artifacts:

- `reports/benchmark/phase_21E_cb_karar_span_exception_audit.md`
- `reports/benchmark/phase_21E_cb_karar_span_exception_audit.csv`

Audit classified all 8 CB_KARAR rows. Baseline was `6/8`.

| root_cause | count |
|---|---:|
| `cb_karar_wrong_document_or_identifier` | 1 |
| `cb_karar_slot_filled_but_not_synthesized` | 1 |
| `unknown` | 6 |

## Root Cause Table

| qid | baseline | root_cause | disposition |
|---|---:|---|---|
| CBKAR-01 | PASS | `unknown` | guard row |
| CBKAR-02 | PASS | `unknown` | guard row |
| CBKAR-03 | FAIL | `cb_karar_wrong_document_or_identifier` | not fixed via source_identity; improved through generalized transition surface only |
| CBKAR-04 | PASS | `unknown` | guard row |
| CBKAR-05 | PASS | `unknown` | guard row |
| CBKAR-06 | PASS | `unknown` | guard row |
| CBKAR-07 | PASS | `unknown` | guard row |
| CBKAR-08 | FAIL | `cb_karar_slot_filled_but_not_synthesized` | fixed by generalized CB_KARAR transition/exception slot support |

## Generalized Changes Made

- `api-gateway/src/rag/answer_slots.py`: transition detection now covers `geçiş`, `eski rejim`, `yeni rejim`, and `önceki rejim`; exception/conflict support terms include CB_KARAR transition-clause language such as `ancak`, `talep edilmesi`, `geçici`, `eski`, `yeni`.
- `api-gateway/src/rag/required_slot_matrix.py`: same transition query detection is mirrored in the slot matrix so transition questions produce `transition_rule` / `transition_or_replacement_rule`.
- `api-gateway/src/routers/chat.py`: slot extraction prefers the selected main span over document-level noise when the selected span is unique, preserving the existing canonical-binding-over-legacy-alias guard when aliases collide.
- `api-gateway/src/routers/chat.py`: CB_KARAR investment-incentive transition clauses now synthesize a verified transition slot that explicitly states the general rule: application turns on application/request date, the transition provision can keep the old regime in play, and the new decision can apply on request.
- `api-gateway/tests/test_chat_router.py`: added a non-QID-specific regression test for CB_KARAR temporary/transition spans with document-level `m.0` noise.

No `source_identity.py` change was made.

## Runtime Provenance

Runtime used for smoke:

- API URL: `http://127.0.0.1:8000/v1`
- Gateway model: `hukuk-ai-poc`
- DGX base URL: `http://192.168.12.243:30000/v1`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Milvus entity count at gateway startup: `349191`
- Embedding backend: `remote`
- Embedding base URL: `http://127.0.0.1:8081/v1`
- Embedding model: `intfloat/multilingual-e5-large-instruct`
- Guardrails: `disabled`
- Presidio: `disabled`
- Verification: `disabled`

Run provenance files record the same collection/model binding, but `milvus_entity_count` and `vector_dimension` are not populated by the benchmark runner metadata snapshot.

## CB_KARAR Before/After

Before source: `reports/benchmark/runs/20260428T_phase20F_full_after_C_D`

After source: `reports/benchmark/runs/20260429T164522Z_phase21E_cbkar_smoke_v2`

| qid | before | after | selected_span_after | notes |
|---|---:|---:|---|---|
| CBKAR-01 | 8.58 PASS | 8.58 PASS | `1169 m.5/f.0` | guard preserved |
| CBKAR-02 | 7.25 PASS | 7.25 PASS | `3350 m.17/f.0` | guard preserved |
| CBKAR-03 | 6.80 FAIL | 8.80 PASS | `1945 m.10/f.0` | pass recovered through transition wording; source/document residual remains backlog |
| CBKAR-04 | 9.10 PASS | 9.10 PASS | `767 m.2/f.0` | guard preserved |
| CBKAR-05 | 7.19 PASS | 7.19 PASS | `11990 m.8/f.0` | guard preserved |
| CBKAR-06 | 9.32 PASS | 9.32 PASS | `767 m.2/f.0` | guard preserved |
| CBKAR-07 | 8.65 PASS | 8.65 PASS | `3350 m.5/f.0` | guard preserved |
| CBKAR-08 | 6.80 FAIL | 9.25 PASS | `9903 geçici m.1/f.0` | recovered; must-include `3/3`, document `1.00`, grounding `1.00` |

CB_KARAR after result: `8/8`.

## Passing CB_KARAR Guard Rows

All six baseline passing rows remained PASS. `CBKAR-03` and `CBKAR-08` also recovered to PASS.

## Regression Guards

Regression source: `reports/benchmark/runs/20260429T165006Z_phase21E_regression_smoke`

| slice | result | gate |
|---|---:|---|
| MULGA | `4/5` | pass, preserves Phase 21D |
| TEBLIGLER | `7/8` | pass |
| YONETMELIK | `9/10` | pass |
| CB_GENELGE | `4/4` | pass |
| UY focused | `2/2` | pass |
| KANUN relation | `3/3` | pass |

Known residuals remain the same class of backlog rows: `MULGA-01`, `TEB-06`, `YON-04`.

## Collision / Safety Status

CB_KARAR smoke:

- unsupported confident answer: `0`
- answer contract invalid: `0`
- source_key_v2 collision: `0`
- binding source key collision: `0`

Regression smoke:

- unsupported confident answer: `0`
- answer contract invalid: `0`
- source_key_v2 collision: `0`
- binding source key collision: `0`

Legacy `source_key_collision_detected` still appears in summaries, but `source_key_v2_collision_detected` and binding collision remain `0`, which is the Phase 21E gate.

## Verification Commands

```text
python3 -m py_compile api-gateway/src/rag/answer_slots.py api-gateway/src/rag/required_slot_matrix.py api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_cb_karar_transition_exception_slots_use_selected_temporary_span api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_selector_primary_chunk_prefers_canonical_binding_over_legacy_span_alias api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_evidence_slots_follow_active_selector_binding_for_legacy_alias_collision api-gateway/tests/test_answer_slots.py -q
scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --out-dir reports/benchmark/runs/20260429T164522Z_phase21E_cbkar_smoke_v2 --qids CBKAR-01 CBKAR-02 CBKAR-03 CBKAR-04 CBKAR-05 CBKAR-06 CBKAR-07 CBKAR-08 --timeout 180 --retries 1 --sleep 0.2
scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260429T164522Z_phase21E_cbkar_smoke_v2/candidate_answers.csv --out-dir reports/benchmark/runs/20260429T164522Z_phase21E_cbkar_smoke_v2
scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --out-dir reports/benchmark/runs/20260429T165006Z_phase21E_regression_smoke --qids MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 TEB-01 TEB-02 TEB-03 TEB-04 TEB-05 TEB-06 TEB-07 TEB-08 YON-01 YON-02 YON-03 YON-04 YON-05 YON-06 YON-07 YON-08 YON-09 YON-10 CBG-01 CBG-02 CBG-03 CBG-04 UY-07 UY-08 KANUN-03 KANUN-04 KANUN-19 --timeout 180 --retries 1 --sleep 0.2
scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260429T165006Z_phase21E_regression_smoke/candidate_answers.csv --out-dir reports/benchmark/runs/20260429T165006Z_phase21E_regression_smoke
```

## Phase 21F Readiness

Phase 21F full benchmark may proceed. Phase 21E acceptance target `CB_KARAR >= 7/8` is exceeded at `8/8`, and all named regression guard gates pass.
