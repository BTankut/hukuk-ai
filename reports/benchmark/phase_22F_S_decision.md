# Phase 22F-S Decision

Date: 2026-05-01

## Decision

```text
Option B — Targeted/regression pass, full benchmark below productization gate.
```

## Basis

Passed:

```text
S-D targeted smoke: PASS
S-E regression guard: PASS
unsupported_confident_answer: 0
answer_contract_invalid: 0
source_key_v2_collision: 0
binding_collision: 0
repealed_as_active_count: 0
TEB-06: PASS
```

Failed:

```text
S-F full shadow benchmark: FAIL
raw_score_proxy: 796.52 < 800 minimum
pass_proxy: 82 < 89 minimum
wrong_family: 16 > 5
hallucinated_identifier: 14 > 4
```

## Productization Gate

```text
Productization: CLOSED
Controlled cutover: NOT AUTHORIZED
Live 8000: UNCHANGED
Shadow candidate 8018: KEEP FOR ANALYSIS
```

## Fine-Tuning Gate

```text
Fine-tuning: CLOSED
No model changes authorized by Phase 22F-S
```

## Next Recommended Work

Open a residual audit before any further implementation:

```text
Phase 22F-S-R — residual family identity / hallucinated identifier audit
```

Audit scope:

```text
wrong_family rows
hallucinated_identifier rows
MULGA over-normalization impact on non-MULGA families
TEBLIGLER TEB-03/TEB-04 regression surface
KANUN rows converted to MULGA claim family
TUZUK/KHK/KKY/UY non-law family preservation
```

Stop conditions remain:

```text
No live cutover
No source acquisition
No corpus backfill
No retrieval top-k changes
No QID-specific branch
No answer-key use
```
