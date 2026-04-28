# Phase 20E Family Slice Baseline And Blocker Report

Date: 2026-04-28

Status: BLOCKED FOR RUNTIME CHANGES IN PHASE 20E SCOPE

## Scope

This phase ran the requested family-slice smoke set after Phase 20D, before making any new runtime changes.

No runtime behavior change was made in Phase 20E because the failing target gaps are dominated by source/document/span or private-rubric auto-fail conditions. Those are outside the allowed Phase 20E slot/synthesis scope unless a separate source/span mini-brief is opened.

## Runtime Provenance

- Run: `reports/benchmark/runs/20260428T_phase20E_family_slices_baseline_envparity`
- API URL: `http://127.0.0.1:8000/v1`
- Model id: `hukuk-ai-poc`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Milvus entity count: `349191`
- Vector dimension: `1024`
- Embedding backend/model: `remote` / `intfloat/multilingual-e5-large-instruct`
- Guardrails: `disabled`
- Presidio: `disabled`
- Runtime provenance git sha: `0b774bb3cddac7b35ff6b38e531587eb66e3608c`

## Slice Results

Detail CSV: `reports/benchmark/phase_20E_family_slice_baseline.csv`

| Slice | Target | Current | Status |
| --- | ---: | ---: | --- |
| MULGA | >= 4/5 | 3/5 | blocked |
| TEBLIGLER | >= 6/8 | 4/8 | blocked |
| YONETMELIK | >= 7/10 | 6/10 | blocked |
| CB_KARAR | >= 7/8 | 6/8 | blocked |

Safety metrics:

- `contract_valid = 31/31`
- `unsupported_confident_answer_count = 0`
- `repealed_as_active_count = 0`
- `source_key_v2_collision_detected_count = 0`
- `binding_source_key_collision_detected_count = 0`

## Blocking Analysis

MULGA target requires one additional pass, but both failing rows are source/span blocked:

- `MULGA-01`: wrong article and insufficient canonical span evidence.
- `MULGA-05`: wrong document, wrong article, hallucinated identifier.

TEBLIGLER target requires two additional passes. Four rows fail:

- `TEB-01`: exact family/document/article but auto-fail remains; changing this via answer text would require private-rubric tuning risk.
- `TEB-03`: wrong family / hallucinated identifier.
- `TEB-06`: wrong document / hallucinated identifier.
- `TEB-07`: wrong family and wrong document.

YONETMELIK target requires one additional pass. Four rows fail:

- `YON-04`: wrong document.
- `YON-05`: wrong document / hallucinated identifier.
- `YON-06`: wrong family and wrong document.
- `YON-08`: wrong family / hallucinated identifier.

CB_KARAR target requires one additional pass. Two rows fail:

- `CBKAR-03`: slot/synthesis candidate, but score is stuck at `6.80` with missing-required-content and partial-grounding only.
- `CBKAR-08`: slot/synthesis candidate, but also carries `exception_or_limitation` missing and score `6.80`.

`CBKAR-03` and `CBKAR-08` are the only plausible slot/synthesis candidates. However, a change that specifically lifts those two rows would be too close to QID/private-rubric tuning unless generalized and validated in the full benchmark. I did not apply such a change inside Phase 20E.

## Decision

Phase 20E should not introduce runtime code changes under the current brief. The safe next step is a separate mini-brief for source/span-family remediation or a full benchmark gate to quantify whether Phase 20C/D improvements are sufficient despite family-slice targets not being met.

Productization and fine-tuning remain closed.
