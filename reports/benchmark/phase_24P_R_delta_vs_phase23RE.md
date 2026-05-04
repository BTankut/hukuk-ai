# Phase 24P-R Delta vs Phase23R-E

Baseline Phase23R-E:

```text
raw_score_proxy = 816.86
pass_proxy = 91
wrong_family = 6
wrong_document = 4
hallucinated_identifier = 4
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

Phase 24P-R full shadow:

```text
raw_score_proxy = 806.87
pass_proxy = 90
wrong_family = 8
wrong_document = 3
hallucinated_identifier = 7
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = FAIL
```

## Delta

```text
raw_score_proxy = -9.99
pass_proxy = -1
wrong_family = +2
wrong_document = -1
hallucinated_identifier = +3
contract/unsupported safety = unchanged PASS
collision safety = unchanged PASS
```

## Delta vs Phase 24O

```text
raw_score_proxy = +1.78
pass_proxy = +1
wrong_family = unchanged at 8
wrong_document = unchanged at 3
hallucinated_identifier = unchanged at 7
CBY-06 = improved to PASS
TEB-04 = unchanged FAIL
```

## Interpretation

Phase 24P-R successfully isolates and fixes the CBY-06 amendment materialization gap, but this single-target improvement is not enough to restore the Phase23R-E full-corpus green lane. The remaining full gate blockers are TEB-04 section materialization, taxonomy/family residuals, and stop-loss source ambiguity rows.
