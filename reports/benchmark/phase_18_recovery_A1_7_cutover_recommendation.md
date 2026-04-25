# Phase 18 Recovery A1.7 Cutover Recommendation

## Recommendation

- decision: `NO_CUTOVER`
- live_8000_changed: `False`
- candidate_gateway_stopped_after_run: `True`

## Rationale

Candidate full run did not pass the A1.7 acceptance gate.

| Metric | Actual | Required | Status |
|---|---:|---:|---|
| `raw_score_proxy` | `729.1` | `>= 735` | `FAIL` |
| `pass_proxy` | `71` | `>= 73` | `FAIL` |
| `wrong_family` | `17` | `<= 15` | `FAIL` |
| `wrong_document` | `17` | `<= 15` | `FAIL` |
| `hallucinated_identifier` | `24` | `<= 23` | `FAIL` |
| `unsupported_confident_claim` | `0` | `<= 8` | `PASS` |
| `contract_valid` | `100/100 invalid=0` | `100/100` | `PASS` |
| `green_lane` | `pass` | `PASS` | `PASS` |
| `corpus_materialization_required_count` | `1` | `<= 6` | `PASS` |
| `canonical_span_materialized_count` | `99` | `>= 90` | `PASS` |

## Next Work

- Do not resume Phase 18 code ablation yet.
- Do not switch live `8000` to `mevzuat_faz1_shadow_20260418_compat1024` yet.
- Perform targeted source/index audit for remaining `YONETMELIK`, `MULGA`, and strong-family regressions (`UY`, `KKY`, `KHK`, `TUZUK`).
- Focus on family routing and document selection; the corpus binding issue is materially improved but not cutover-ready.

## Cutover Blockers

- raw_score_proxy `729.1` is below `735`.
- pass_proxy `71` is below `73`.
- wrong_family `17` is above `15`.
- wrong_document `17` is above `15`.
- hallucinated_identifier `24` is above `23`.
