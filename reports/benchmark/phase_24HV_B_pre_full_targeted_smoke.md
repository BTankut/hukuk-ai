# Phase 24HV-B Pre-Full Targeted Smoke

## Run

- api_url: `http://127.0.0.1:8044/v1`
- run_dir: `reports/benchmark/runs/phase_24HV_B_pre_full_targeted_smoke`
- include_trace: `true`

## Summary

- raw_score_proxy: `104.83 / 130`
- pass_proxy: `11 / 13`
- fail_proxy: `2 / 13`
- contract_invalid: `0`
- unsupported_confident_answer: `0`
- answer_contract_missing: `0`
- source_key_v2_collision: `0`
- binding_collision: `0`
- legacy_source_key_collision: `1`

## Gate Decision

- pre_full_targeted_smoke_gate: `PASS`
- full_candidate_benchmark_allowed: `true`

## Delta vs Phase 24HU Focused Smoke

| QID | Phase24HU | Phase24HV-B | Delta | Selected Main Span | Failure Classes |
| --- | ---: | ---: | ---: | --- | --- |
| KANUN-08 | 8.22 PASS | 8.22 PASS | +0.00 | `TKHK m.18/f.0` | `missing_required_content_signal | partial_grounding_only` |
| TEB-04 | 8.15 PASS | 8.15 PASS | +0.00 | `19631 m.0/f.0` | `` |
| TUZUK-05 | 10.00 PASS | 10.00 PASS | +0.00 | `` | `` |
| YON-05 | 7.55 PASS | 7.55 PASS | +0.00 | `23722 m.5/f.0` | `missing_required_content_signal | partial_grounding_only` |
| MULGA-01 | 8.37 PASS | 8.37 PASS | +0.00 | `YOK_DISIPLIN_2012 m.18/f.0` | `missing_required_content_signal | partial_grounding_only` |
| MULGA-05 | 7.10 PASS | 7.10 PASS | +0.00 | `6570 m.GEC1/f.0` | `missing_required_content_signal | partial_grounding_only` |
| TEB-06 | 8.90 PASS | 8.90 PASS | +0.00 | `23093 m.13/f.0` | `` |
| CBY-06 | 6.80 FAIL | 6.80 FAIL | +0.00 | `20046801 m.14/f.0` | `missing_required_content_signal | partial_grounding_only` |
| KANUN-12 | 8.99 PASS | 8.99 PASS | +0.00 | `5651 m.6/f.0` | `missing_required_content_signal | partial_grounding_only` |
| YON-04 | 8.22 PASS | 8.22 PASS | +0.00 | `phase24n:yonetmelik:30224:m10:f0:from2018-01-01:to9999-12-31` | `missing_required_content_signal | partial_grounding_only` |
| TUZUK-04 | 4.63 FAIL | 4.63 FAIL | +0.00 | `859727 m.4/f.0` | `missing_required_content_signal | wrong_family | hallucinated_identifier | partial_grounding_only` |
| CBG-01 | 8.65 PASS | 8.65 PASS | +0.00 | `2024/7 m.0/f.0` | `missing_required_content_signal | partial_grounding_only` |
| CBKAR-08 | 9.25 PASS | 9.25 PASS | +0.00 | `9903 geçici m.1/f.0` | `` |

## Acceptance Notes

- `KANUN-08` remains PASS and primary source remains `TKHK m.18/f.0`.
- `TEB-04`, `TUZUK-05`, and `YON-05` remain PASS.
- `MULGA-01`, `MULGA-05`, and `TEB-06` scores are unchanged vs Phase24HU focused smoke.
- `TUZUK-04` remains a known residual FAIL but did not regress in score.
- The legacy source-key collision on `CBKAR-08` is unchanged and is not a source_key_v2 or binding collision.

## Stop Rule Result

- No Phase 24HV stop rule triggered by pre-full targeted smoke.
