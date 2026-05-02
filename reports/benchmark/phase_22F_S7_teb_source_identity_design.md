# Phase 22F-S7 TEB Source Identity Design

## Objective

Recover the KDV General Application Communique source for KDV teblig questions without changing live `8000`, base/live Milvus collections, broad top-k, prompts, model, corpus materialization, or answer synthesis.

This design is limited to `TEBLIGLER` source identity and metadata-guided recall.

## S6 Starting Point

`TEB-04` currently selects:

- `ELEKTRONİK TEBLİGAT SİSTEMİ GENEL TEBLİĞİ (SIRA NO: 1)`
- `24345 m.1`

Correct source:

- `source_key=19631`
- `KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ`
- family `teblig`
- active

S6 evidence:

- `19631` exists in canonical catalog.
- `19631` exists in Milvus.
- `19631` is absent from runtime top-24, source identity `top_scores`, and S5 `rerank_list`.
- Raw dense search first finds `19631` at rank 130.
- `metadata_lookup_hit=false`.

## Design

Add a generic KDV teblig intent detector and metadata-guided candidate injection. This is not a `TEB-04` branch.

Required query signal bundle:

- source family context must include or imply `teblig`
- query must contain KDV-specific signals such as `kdv` or `katma deger vergisi`
- query must also contain at least one operational signal such as `tevkifat`, `iade`, `konsolide`, `ana teblig`, or `genel uygulama tebligi`

If the bundle is present:

- inject source key `19631` through the same metadata-guided recall path used for source-key candidates
- annotate trace fields:
  - `teb_kdv_signal_detected`
  - `teb_kdv_candidate_injected`
  - `teb_kdv_candidate_source_key`
  - `teb_kdv_candidate_injection_reason`
- keep the candidate in the normal source identity and article selection path
- do not bypass rerank, article selection, or contract validation

## Implementation Surface

Primary files:

- `api-gateway/src/rag/source_identity.py`
- `api-gateway/src/rag/retrieval_orchestration.py`

Tests:

- add focused tests under `tests/`

Avoid:

- `answer_synthesis.py`
- `answer_slots.py`
- `article_span_selection.py`

## Guardrails

The detector must not fire for generic teblig questions. It must not fire for non-KDV tax questions. It must not alter global dense retrieval top-k.

This prevents non-KDV `TEBLIGLER` rows from drifting to `19631`.

## Targeted Gate

Run `TEB-01` through `TEB-08`.

Acceptance:

- `TEB-04` source identity improves toward `19631`.
- `TEBLIGLER >= 7/8` preferred, `>=6/8` minimum.
- `TEB-06` remains PASS.
- No adjacent TEB row incorrectly drifts to `19631`.
- `unsupported_confident_answer = 0`.
- `answer_contract_invalid = 0`.
- source-key collision and binding collision remain `0`.

Productization, fine-tuning, live cutover, source acquisition, and corpus materialization remain closed.
