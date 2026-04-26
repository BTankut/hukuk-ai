# Phase 18 Recovery A1.10 Cutover Decision

## Decision

Controlled live cutover retry: `PASS`.

`Phase 18 Recovery Baseline` is accepted for live `8000` on the full mevzuat corpus.

## Gates

- Hard quality gate: `PASS`
- Adverse delta gate: `PASS`
- Row-level drift warning gate: `PASS`
- Critical watch family gate: `PASS`
- Green lane: `pass`

## Directional Candidate/Live Comparison

| Metric | Candidate | A1.10 Live | Live - Candidate | Gate | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| raw_score_proxy | 766.48 | 756.61 | -9.87 | >= -10 | PASS |
| pass_proxy | 80.00 | 79.00 | -1.00 | >= -2 | PASS |
| wrong_family | 11.00 | 10.00 | -1.00 | <= +2 | PASS |
| wrong_document | 12.00 | 9.00 | -3.00 | <= +2 | PASS |
| hallucinated_identifier | 16.00 | 11.00 | -5.00 | <= +3 | PASS |

## Row-Level Drift Warning

- candidate PASS -> live FAIL count: `6` (CBY-01, CBY-06, KANUN-15, TEB-01, TEB-03, YON-05)
- candidate FAIL -> live PASS count: `5` (CBY-03, KHK-06, KKY-02, KKY-04, YON-03)
- gate: `6 <= 5 + 3` => `PASS`

## Critical Watch Families

| Family | Live Result | Gate | Status |
| --- | ---: | ---: | --- |
| CB_GENELGE | 4/4 | >= 4/4 | PASS |
| MULGA | 3/5 | >= 3/5 | PASS |
| UY | 10/10 | >= 9/10 | PASS |
| YONETMELIK | 6/10 | >= 6/10 | PASS |

## Final Runtime State Required

Live `8000` must remain bound to:

```text
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
DGX_MODEL=/models/merged_model_fabric_stage_20260321
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

Productization remains closed. Fine-tuning remains closed. Next work is behavior-preserving `chat.py` decomposition, then Phase 18 slot-completion redesign.
