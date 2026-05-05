# Phase 24U Trace-Normalized Ablation Outcome Report

Generated UTC: `2026-05-05T15:38:08Z`  
Report HEAD before final-report commit: `e448950a0203376b732977de4ba0adfdf014ec4a`

## 1. Commit SHA List

```text
e448950 Record Phase 24U trace-normalized ablation decision
b7f304f Attribute Phase 24U source supplement drift rows
43869fd Run Phase 24U source supplement ablation
c351588 Run Phase 24U CBY trace-on full benchmark
84e9c22 Run Phase 24U BASE trace-on full benchmark
66de153 Plan Phase 24U trace-normalized matched A/B
Phase24U final report = pending_this_commit
```

## 2. Trace-Normalized A/B Plan

Artifacts:

```text
reports/benchmark/phase_24U_A_trace_normalized_ab_plan.md
reports/benchmark/phase_24U_A_trace_normalized_ab_plan.json
```

Plan result:

```text
live_8000_change = false
BASE_API = http://127.0.0.1:8037/v1
CBY_API = http://127.0.0.1:8038/v1
ABLATION_API = http://127.0.0.1:8039/v1
matched_runtime_git_sha = 66de1538b6f007d29f6b50189d53b0d3116dd97e
model = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
include_trace = true
```

## 3. BASE Trace-On Full Result

Artifacts:

```text
reports/benchmark/phase_24U_B_base_trace_on_full_summary.md
reports/benchmark/phase_24U_B_base_trace_on_green_lane_summary.md
```

Result:

```text
run_dir = reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
raw_score_proxy = 805.09 / 1000
pass_proxy = 89 / 100
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
run_clean_green_lane = PASS
phase23RE_score_parity = FAIL
```

Interpretation: BASE cleanly reproduces Phase24T-D current trace-on (`805.09 / 89`) but remains below Phase23R-E (`816.86 / 91`).

## 4. CBY Trace-On Full Result

Artifacts:

```text
reports/benchmark/phase_24U_C_cby_trace_on_full_summary.md
reports/benchmark/phase_24U_C_cby_vs_base_trace_on_delta.md
reports/benchmark/phase_24U_C_cby_trace_on_green_lane_summary.md
```

Result:

```text
run_dir = reports/benchmark/runs/phase_24U_C_cby_trace_on_full_20260505T131540Z
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
entity_count = 349405
raw_score_proxy = 807.27 / 1000
pass_proxy = 90 / 100
delta_vs_BASE = +2.18 raw / +1 pass
wrong_family_delta = +0
wrong_document_delta = +0
hallucinated_identifier_delta = +0
cby_consideration_gate = PASS
phase23RE_score_parity = FAIL
cutover_authorized = NO
```

Interpretation: CBY is clean and narrowly beneficial, mainly by moving `CBY-06` from FAIL to PASS. It is not enough to authorize cutover because BASE drift remains unresolved.

## 5. Source Supplement Ablation Result

Artifacts:

```text
reports/benchmark/phase_24U_D_source_supplement_ablation_summary.md
reports/benchmark/phase_24U_D_ablation_vs_current_trace_on_delta.md
reports/benchmark/phase_24U_D_ablation_green_lane_summary.md
```

Result:

```text
run_dir = reports/benchmark/runs/phase_24U_D_source_supplement_ablation_full_20260505T143052Z
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
ENABLE_PHASE24N_SOURCE_SUPPLEMENTS = false
raw_score_proxy = 804.42 / 1000
pass_proxy = 89 / 100
delta_vs_current_BASE = -0.67 raw / +0 pass
phase23RE_restored = FAIL
source_supplement_drift_confirmed = NO
```

Interpretation: disabling source supplements did not restore Phase23R-E and slightly worsened current BASE. Source supplement drift is not sufficient as the remaining root-cause explanation.

## 6. Drift Row Attribution

Artifacts:

```text
reports/benchmark/phase_24U_E_drift_row_attribution.md
reports/benchmark/phase_24U_E_drift_row_attribution.csv
```

Result:

```text
rows_attributed = 8
fixed_by_ablation = 0
worsened_by_ablation = 1
unchanged = 7
phase23_pass_to_current_fail = 5
phase23_fail_to_current_pass = 3
current_to_ablation_pass_changes = 0
```

Key rows:

```text
regressed_vs_Phase23RE = KANUN-02, KANUN-08, MULGA-04, YON-05, YON-08
positive_current_vs_Phase23RE = CBY-04, KANUN-12, YON-04
worsened_by_ablation = YON-04
```

## 7. Decision

Artifact:

```text
reports/benchmark/phase_24U_trace_normalized_ablation_decision.md
```

Decision:

```text
selected_option = Option D — Code regression not supplement-related
source_supplement_drift_confirmed = false
current_code_reproduces_phase23RE = false
cby_trace_on_clean_but_base_still_drifted = true
next_phase = commit-level regression audit between Phase23R-E accepted state and current HEAD
```

## 8. Productization Decision

```text
productization = CLOSED
reason = BASE remains below Phase23R-E and CBY cutover is not authorized while baseline drift is unresolved
```

## 9. Internal Eval Decision

```text
internal_eval = CLOSED
reason = no Phase23R-E parity restoration and no accepted live/cutover runtime state
```

## 10. Fine-Tuning Decision

```text
fine_tuning = CLOSED
reason = diagnostic/ablation phase only; no accepted remediation data or runtime state for training
```

## 11. Final Live 8000 State

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"phase22f_s7_full_shadow","api_version":"2026-05-03-phase23R-E-benchmark-only-cutover","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

Additional state:

```text
process_manager = tmux session hukuk_ai_live_8000
pid = 46587
model = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
live_8000_changed_in_phase24U = false
non_live_candidate_ports_8037_8038_8039 = stopped/free
```

## 12. Next Recommended Phase

```text
Phase24V — Commit-Level Regression Audit from Phase23R-E Accepted State to Current HEAD
```

Required next work:

1. Compare Phase23R-E accepted code/config hashes and current HEAD for selector/source identity, answer slot synthesis, confidence/completeness policy, and scorer behavior.
2. Prioritize regressed rows `KANUN-02`, `KANUN-08`, `MULGA-04`, `YON-05`, and `YON-08` without QID-specific runtime branches.
3. Preserve positive current improvements on `CBY-04`, `KANUN-12`, and `YON-04`.
4. Keep CBY collection as a clean candidate, but do not cut over until BASE parity is restored or a formally accepted new baseline is approved.

## Final Status

```text
phase24u_outcome = DIAGNOSTIC_COMPLETE_NO_LIVE_RUNTIME_CHANGE
major_phase24r_s_score_collapse = trace-off non-equivalent evidence, already confirmed in Phase24T
remaining_gap_vs_Phase23R-E = not fixed by source supplement ablation
next_phase = commit-level regression audit
```
