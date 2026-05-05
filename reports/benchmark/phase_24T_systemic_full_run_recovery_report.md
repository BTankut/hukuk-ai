# Phase 24T Systemic Full-Run Recovery Diagnostic Report

Generated at UTC: `2026-05-05T11:23:29Z`  
Git HEAD before final report commit: `189bcdb36a78142931d76cd334e3021adc3cd45a`

## Commit SHA List

```text
Phase24T-A provenance diff = 6e3a7dc
Phase24T-B score delta attribution = ab73dc6
Phase24T-C document identity regression audit = 6b84189
Phase24T-D Phase23R-E baseline reproduction = 392f4b1
Phase24T-E recovery design = 189bcdb
Phase24T-F final report = pending_this_commit
```

## Provenance Diff

Artifacts:

```text
reports/benchmark/phase_24T_A_full_run_provenance_diff.md
reports/benchmark/phase_24T_A_full_run_provenance_diff.json
```

Key result:

```text
Phase23R-E good baseline include_trace = true
Phase24R BASE full include_trace = false
Phase24R CBY full include_trace = false
Phase24S CBY live full include_trace = false
runner_hash = unchanged
scorer_hash = unchanged
config_hash = unchanged
source_catalog_hash = unchanged
source_supplement_hash = changed
```

Decision: Phase24R/S low full scores are not score-equivalent evidence against Phase23R-E because the runner provenance is materially different.

## Score Delta Attribution

Artifacts:

```text
reports/benchmark/phase_24T_B_score_delta_attribution.md
reports/benchmark/phase_24T_B_score_delta_attribution.csv
```

Result:

```text
rows_compared = 100/100
Phase23R-E raw/pass = 816.86 / 91
Phase24R BASE trace-off raw/pass = 725.40 / 72
raw_delta = -91.46
pass_delta = -19
pass_to_fail = 22
new_wrong_document_rows = 20
new_hallucinated_identifier_rows = 21
suspected_root_cause dominant = trace_artifact_missing (100/100 rows)
```

Interpretation: the major full-run score collapse is explained by trace-derived selected-source fields being absent in the Phase24R BASE trace-off run.

## Document Identity Regression Audit

Artifacts:

```text
reports/benchmark/phase_24T_C_document_identity_regression_audit.md
reports/benchmark/phase_24T_C_document_identity_regression_audit.csv
```

Result:

```text
audit_rows = 91
regression_point.scorer_only = 91
phase23RE_evidence_present_and_phase24R_missing = 91
retrieval_topk_diff_available = false
selector_diff_available = false for scorer_only rows
```

Interpretation: Phase24T-C does not prove dense retrieval, metadata lookup, rerank, or source identity selection regression. The Phase24R trace-off selected document/source-key/binding-key fields are missing, so the safe recovery action is trace-on matched rerun before any logic change.

## Phase23R-E Baseline Reproduction

Artifact:

```text
reports/benchmark/phase_24T_D_phase23RE_baseline_reproduction.md
```

Current-code trace-on run:

```text
run_dir = reports/benchmark/runs/phase_24T_D_phase23RE_reproduction_trace_on_20260505T101732Z
include_trace = true
api_url = http://127.0.0.1:8000/v1
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
```

Score result:

```text
Phase23R-E = 816.86 / 91
Phase24R BASE trace-off = 725.40 / 72
Phase24T-D current trace-on = 805.09 / 89
trace_on_recovery_vs_24R_BASE = +79.69 raw / +17 pass
remaining_gap_vs_Phase23R-E = -11.77 raw / -2 pass
```

Decision: current code does not fully reproduce Phase23R-E. Trace normalization fixes most of the apparent regression, but a smaller code/source supplement drift remains.

## Recovery Design

Artifact:

```text
reports/benchmark/phase_24T_E_recovery_design.md
```

Selected path:

```text
Option A first: normalize full benchmark command/provenance to include_trace=true
Option B second: isolate current code/source supplement drift since Phase23R-E
Option C not primary: collection binding mismatch not proven
Option D deferred: source identity logic regression not proven until trace-on matched evidence exists
Option E temporary hold: CBY merge line stays blocked
```

Most likely narrow drift surface:

```text
source_supplement_hash changed: a301cdd8... -> 282503e9...
changed file: api-gateway/src/rag/source_supplements.py
key commit: ddcadd2 Execute Phase 24O shadow residual remediation
new default behavior: ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=true dynamic supplements
remaining drift rows include: MULGA-04, KANUN-08, KANUN-02, YON-05, YON-08
```

## Productization Decision

```text
productization = CLOSED
reason = Phase24S full gate failed; Phase24T found benchmark provenance non-equivalence plus remaining current-code drift
```

## Internal Eval Decision

```text
internal_eval = CLOSED
reason = no trace-normalized matched full green lane exists after Phase24S rollback
```

## Fine-Tuning Decision

```text
fine_tuning = CLOSED
reason = diagnostic phase only; no accepted data/runtime state for training
```

## Final Live 8000 State

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"phase22f_s7_full_shadow","api_version":"2026-05-03-phase23R-E-benchmark-only-cutover","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

Additional state:

```text
process_manager = tmux session hukuk_ai_live_8000
pid = 46587
model = hukuk-ai-poc
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
DGX_MODEL = /models/merged_model_fabric_stage_20260321
live_8000_changed_in_phase24T = false
```

## Next Recommended Phase

```text
Phase24U — Trace-Normalized Matched A/B and Source Supplement Drift Isolation
```

Required work:

1. Run non-live BASE and CBY matched full benchmarks with `include_trace=True`.
2. Mark prior Phase24R/S trace-off full runs as non-score-comparable, not as productization evidence.
3. Run a non-live base-collection ablation with `ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=false` to isolate the remaining 805.09/89 vs 816.86/91 drift.
4. If ablation restores Phase23R-E, redesign source supplement loading/gating systemically.
5. If ablation does not restore Phase23R-E, open commit-level code regression audit between `b34ed1c` and current head.
6. Revisit CBY only after trace-normalized BASE is back at Phase23R-E-level quality.

## Final Diagnostic Decision

```text
phase24t_outcome = DIAGNOSTIC_COMPLETE_NO_RUNTIME_CHANGE
primary_root_cause_of_725_score = trace_off_non_equivalent_full_benchmark
secondary_root_cause_remaining = current_code_or_source_supplement_drift
next_phase = Phase24U
```
