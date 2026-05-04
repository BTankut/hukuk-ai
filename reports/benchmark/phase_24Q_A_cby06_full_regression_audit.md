# Phase 24Q-A CBY-Only Full Regression Audit

## Scope

`Phase23R-E` baseline is compared to `Phase24P-R` CBY-only full shadow. No private answer key was opened; this audit uses the already-produced scored run artifacts.

## Summary

```text
total_rows = 100
phase23RE_raw_score_proxy = 816.86
phase24PR_raw_score_proxy = 806.87
raw_score_delta = -9.99
phase23RE_pass_proxy = 91
phase24PR_pass_proxy = 90
pass_to_fail_count = 5
fail_to_pass_count = 4
phase24PR_cby_new_span_rows = 2
phase24PR_cby_new_span_unrelated_rows = 1
phase24PR_cby_new_span_unrelated_regression_rows = 0
```

## Pass To Fail Rows

| qid | phase23RE | phase24PR | delta | root_cause | safe_action |
|---|---:|---:|---:|---|---|
| KANUN-02 | 8.65 | 3.25 | -5.40 | existing_residual_shift | do_not_attribute_to_cby_span; require matched base-vs-cby rerun on same runtime before merge |
| KANUN-08 | 7.55 | 1.45 | -6.10 | existing_residual_shift | do_not_attribute_to_cby_span; require matched base-vs-cby rerun on same runtime before merge |
| YON-05 | 9.55 | 5.75 | -3.80 | existing_residual_shift | do_not_attribute_to_cby_span; require matched base-vs-cby rerun on same runtime before merge |
| YON-08 | 7.25 | 6.80 | -0.45 | existing_residual_shift | do_not_attribute_to_cby_span; require matched base-vs-cby rerun on same runtime before merge |
| MULGA-04 | 7.55 | 0.00 | -7.55 | existing_residual_shift | do_not_attribute_to_cby_span; require matched base-vs-cby rerun on same runtime before merge |

## Fail To Pass Rows

| qid | phase23RE | phase24PR | delta | cby_span_in_evidence | root_cause |
|---|---:|---:|---:|---:|---|
| KANUN-12 | 1.45 | 8.99 | 7.54 | false | selector_nondeterminism |
| YON-04 | 3.25 | 8.22 | 4.97 | false | selector_nondeterminism |
| CBY-04 | 6.85 | 7.12 | 0.27 | false | no_meaningful_regression |
| CBY-06 | 6.80 | 8.58 | 1.78 | true | no_meaningful_regression |

## CBY New Span Visibility

| qid | phase23RE | phase24PR | delta | cby_span_in_evidence | root_cause |
|---|---:|---:|---:|---:|---|
| CBY-05 | 8.00 | 8.00 | 0.00 | true | no_meaningful_regression |
| CBY-06 | 6.80 | 8.58 | 1.78 | true | no_meaningful_regression |

## Root Cause Counts

```text
existing_residual_shift = 5
no_meaningful_regression = 87
selector_nondeterminism = 7
trace_or_scoring_artifact = 1
```

## CBY Span Interference Finding

```text
CBY new span in unrelated pass-to-fail rows = 0
CBY new span in unrelated negative-delta rows = 0
cby_span_interference_detected = false
```

The new CBY materialized span appears in the Phase24P-R evidence for `CBY-06` and also in `CBY-05`. `CBY-05` stayed `PASS` with an unchanged 8.00 score, so this is benign same-family neighbor visibility, not an unrelated regression. None of the five pass-to-fail rows contains the new CBY span in Phase24P-R evidence.

## Runtime Provenance Note

```text
Phase23R-E api_url = http://127.0.0.1:8000/v1
Phase23R-E git_sha = b34ed1c8c72cd9c1108282eda50d53dd4d35c032
Phase23R-E milvus_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
Phase24P-R api_url = http://127.0.0.1:8034/v1
Phase24P-R git_sha = 100c6238fb6ea1dd609e36da88ce4d549cdb4436
Phase24P-R milvus_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
Model binding stayed constant = /models/merged_model_fabric_stage_20260321
```

The comparison is not a same-runtime A/B pair. Between the two run SHAs, gateway and selector-related files changed (`answer_synthesis.py`, `source_identity.py`, `source_supplements.py`, `chat.py`). Therefore the safe attribution is: CBY-06 span is locally valid, but the full-run drop is confounded by runtime provenance mismatch and existing residual shift.

## Decision

CBY-06 materialization is locally valid but not merge-safe as a full candidate. Do not cut over the CBY-only collection. If CBY is revisited, use a matched same-runtime base-vs-CBY pair so that existing residual shift and runtime provenance mismatch are controlled.
