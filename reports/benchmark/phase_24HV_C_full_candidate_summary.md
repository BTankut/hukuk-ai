# Phase 24HV-C Full Candidate Summary

## Run

- api_url: `http://127.0.0.1:8044/v1`
- run_dir: `reports/benchmark/runs/phase_24HV_C_full_candidate`
- include_trace: `true`

## Score

- raw_score_proxy: `727.39 / 1000`
- pass_proxy: `74 / 100`
- base_trace_on_raw_score_proxy: `805.09`
- base_trace_on_pass_proxy: `89`
- raw_delta_vs_base: `-77.70`
- pass_delta_vs_base: `-15`

## Hard Counters

- contract_valid: `100`
- unsupported_confident_answer: `0`
- answer_contract_invalid: `0`
- source_key_v2_collision: `0`
- binding_collision: `0`
- legacy_source_key_collision: `4`
- wrong_document: `18`
- base_wrong_document: `3`
- hallucinated_identifier: `22`
- base_hallucinated_identifier: `7`

## Gates

- green_lane: `pass`
- minimum_gate: `FAIL`
- preferred_gate: `FAIL`

## Focus Rows

| QID | Base | Candidate | Delta | Candidate Selected Main Span | Candidate Failure Classes |
| --- | ---: | ---: | ---: | --- | --- |
| KANUN-08 | 1.45 FAIL | 8.22 PASS | +6.77 | `TKHK m.18/f.0` | `missing_required_content_signal | partial_grounding_only` |
| TEB-04 | 0.00 FAIL | 8.15 PASS | +8.15 | `19631 m.0/f.0` | `` |
| TUZUK-05 | 3.25 FAIL | 10.00 PASS | +6.75 | `` | `` |
| YON-05 | 5.75 FAIL | 7.55 PASS | +1.80 | `23722 m.5/f.0` | `missing_required_content_signal | partial_grounding_only` |
| MULGA-01 | 8.37 PASS | 8.37 PASS | +0.00 | `YOK_DISIPLIN_2012 m.18/f.0` | `missing_required_content_signal | partial_grounding_only` |
| MULGA-05 | 7.10 PASS | 7.10 PASS | +0.00 | `6570 m.GEC1/f.0` | `missing_required_content_signal | partial_grounding_only` |
| TEB-06 | 8.90 PASS | 8.90 PASS | +0.00 | `23093 m.13/f.0` | `` |
| CBY-06 | 6.80 FAIL | 6.80 FAIL | +0.00 | `20046801 m.14/f.0` | `missing_required_content_signal | partial_grounding_only` |
| KANUN-12 | 8.99 PASS | 8.99 PASS | +0.00 | `5651 m.6/f.0` | `missing_required_content_signal | partial_grounding_only` |
| YON-04 | 8.22 PASS | 8.22 PASS | +0.00 | `phase24n:yonetmelik:30224:m10:f0:from2018-01-01:to9999-12-31` | `missing_required_content_signal | partial_grounding_only` |
| TUZUK-04 | 4.63 FAIL | 4.63 FAIL | +0.00 | `859727 m.4/f.0` | `missing_required_content_signal | wrong_family | hallucinated_identifier | partial_grounding_only` |
| CBG-01 | 8.65 PASS | 8.65 PASS | +0.00 | `2024/7 m.0/f.0` | `missing_required_content_signal | partial_grounding_only` |
| CBKAR-08 | 9.25 PASS | 9.25 PASS | +0.00 | `9903 geçici m.1/f.0` | `` |

## Interpretation

- Candidate recovers the Phase24HU target rows in full scope: `KANUN-08`, `TEB-04`, `TUZUK-05`, and `YON-05` are PASS.
- Full quality gate fails badly versus current trace-on base: raw score and pass count both regress.
- Hard safety counters are clean except legacy source-key collisions, but wrong-document and hallucinated-identifier failure classes increase versus base.
- This is not integration-ready and must not be cut over.
