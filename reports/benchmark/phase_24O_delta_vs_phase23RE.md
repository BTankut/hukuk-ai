# Phase 24O Delta vs Phase23R-E Baseline

Baseline from Phase 24O brief:

```text
raw_score_proxy = 816.86
pass_proxy = 91/100
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

Phase 24O full shadow:

```text
raw_score_proxy = 805.09
pass_proxy = 89/100
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
raw_score_proxy: -11.77
pass_proxy: -2
wrong_family: +2
wrong_document: -1
hallucinated_identifier: +3
contract/unsupported safety: unchanged PASS
collision safety: unchanged PASS
```

## Interpretation

Phase 24O improved targeted source identity for `KANUN-12` and `YON-04`, and fixed the unsafe active-current-law surface for `TUZUK-04`. However, those gains did not offset broader proxy regressions in full shadow scoring. The most important blockers are still materialization/scorer taxonomy rather than unsupported confident answers:

- `TEB-04`: correct KDV GUT source but wrong section-level span (`m.0` appendix/document-level materialization).
- `CBY-06`: missing/unused `11153` amendment `m.11` span.
- `KKY-01` and `KKY-03`: legal family `YONETMELIK` vs benchmark/domain family compatibility and final source identifier materialization.
- `TUZUK-05`: explicit stop-loss.

## Decision

Do not cut over Phase 24O candidate to live. Keep live `8000` on the Phase23R-E benchmark-only lane.
