# Phase 24HS-B - Ambiguous Tuzuk Source Stop Condition

## Scope

- Target failure: `TUZUK-05`.
- Baseline run: `reports/benchmark/runs/phase_24HR_option_C_targeted_candidate_smoke`.
- Candidate run: `reports/benchmark/runs/phase_24HS_focused_non_live_candidate_smoke_final_v6`.
- Non-live endpoint: `http://127.0.0.1:8041/v1`.
- Live `8000`: not modified.

## Baseline Failure

| QID | Baseline primary source | Baseline score | Failure |
| --- | --- | ---: | --- |
| `TUZUK-05` | `GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK`, `madde:92` | `3.25 FAIL` | unrelated concrete tüzük selected for an abstract hierarchy/source-identity-unresolved question |

The row was legally ambiguous: the user question asks a general hierarchy/conflict principle, but the exact concrete tüzük identity is not confirmed. The safe behavior is to stop arbitrary concrete tüzük election and disclose source identity uncertainty.

## Systemic Stop Condition Implemented

Implemented in `api-gateway/src/rag/source_identity.py` and surfaced in `api-gateway/src/routers/chat.py`:

- If the preferred family includes `tuzuk`,
- and the query is an abstract tüzük hierarchy/conflict question,
- and no concrete tüzük identity appears in the user query,
- then the pre-generation family pool returns no arbitrary concrete chunks and marks:

```text
family_gate_status=ambiguous_source_identity_stop
family_gate_reason=abstract_tuzuk_hierarchy_without_confirmed_concrete_source
source_identity_stop_condition_applied=True
manual_review_required=True
```

The chat router then emits a controlled `insufficient_grounding` / source-identity-unresolved answer rather than selecting a random tüzük.

## Candidate Result

| QID | Candidate primary surface | Candidate score | Result |
| --- | --- | ---: | --- |
| `TUZUK-05` | `ilgili yürürlükteki tüzük hükümleri (exact source identity unresolved)`, `unknown`, `general_hierarchy` | `10.00 PASS` | no unrelated concrete tüzük selected |

Candidate answer states that a single verified tüzük source could not be identified and that manual legal review is required for exact source identity. It still gives the general hierarchy rule at low confidence without concrete source fabrication.

## Decision

The Phase 24HS ambiguous tüzük stop condition is accepted for focused candidate use. The rule is systemic and does not branch on `TUZUK-05`.
