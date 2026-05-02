# Phase 22F-S4 Decision

Date: 2026-05-02

## Decision

Phase 22F-S4 decision: `Option B — targeted passes but full restore gate remains below required threshold`.

Do not cut over.

## Gate Summary

| Gate | Status | Notes |
| --- | --- | --- |
| S4-C 13-row targeted smoke | PASS | Active non-MULGA overapplication controlled; MULGA historical surface retained |
| S4-D P0 / TEB guard | PASS | MULGA `4/5`, TEBLIGLER `7/8`, `TEB-06=PASS` |
| S4-E regression guard | PASS | CBG `4/4`, CBKAR `8/8`, YON `9/10`, UY `2/2`, KANUN `3/3` |
| S4-F full shadow benchmark | FAIL | wrong_family `8 > 6`, hallucinated_identifier `6 > 5` |
| Green lane | PASS | run validation and public/private guard checks passed |

## Cutover Recommendation

No live cutover.

Keep live `8000` unchanged. The S4 shadow candidate can remain available for analysis on `8018`, but it should not replace the current serving lane.

## Productization Gate

Productization remains closed.

Reason: full restore target failed despite clean safety counters.

## Fine-Tuning Gate

Fine-tuning remains closed.

Reason: the residual failures are deterministic source identity / family and identifier surface issues, not model-training issues.

## Next Work

Open a residual deterministic remediation phase focused on family/identifier precision without changing retrieval top-k, source acquisition, prompt, model, live collection, or benchmark answer-key access.

Priority residuals:

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-04
UY-01
```

Secondary residuals:

```text
MULGA-05
TEB-04
YON-04
TUZUK-05
CBY-06
```

## Hard Stops Preserved

- Live `8000` was not cut over.
- Base/live collection was not modified.
- No model or prompt change was made.
- No productization step was opened.
- No fine-tuning step was opened.
- No QID-specific branch was introduced.
- Benchmark answer key was not used.
