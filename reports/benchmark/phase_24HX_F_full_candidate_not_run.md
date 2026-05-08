# Phase 24HX-F Full Candidate Not Run

Generated: 2026-05-08

## Decision

Phase24HX-F full candidate benchmark was not run.

## Reason

Phase24HX-E family-slice validation failed the stop rule:

```text
wrong_document explosion persists in family-slice smoke
```

Family-slice comparison:

| Metric | Base | Phase24HW selected | Phase24HX constrained |
| --- | ---: | ---: | ---: |
| 29-row score | 214.40 | 153.59 | 160.64 |
| 29-row pass | 23/29 | 11/29 | 11/29 |
| Target pass | 0/4 | 4/4 | 2/4 |
| Regression-slice pass | 16/16 | 0/16 | 2/16 |
| Guard pass | 7/9 | 7/9 | 7/9 |
| Wrong-document count | 2 | 13 | 13 |
| Hallucinated-identifier count | 4 | 15 | 16 |

Hard counters were clean, but the source-selection failure mode remained too large for a full 100-question candidate run.

## Operational State

No full candidate run was started.

Live `8000` was not modified.

