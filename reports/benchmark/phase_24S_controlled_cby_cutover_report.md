# Phase 24S Controlled CBY Cutover Outcome Report

Generated at UTC: `2026-05-05T08:26:10Z`  
Git HEAD before final report commit: `07a8131004d98892c7223e6c2a0988b50da77ee9`

## 1. Commit SHA List

```text
Phase24S-A candidate manifest = 51a629d
Phase24S-B live backup/rollback plan = bf99691
Phase24S-C controlled CBY cutover = af4b869
Phase24S-D post-cutover targeted smoke = fe10184
Phase24S-E post-cutover full benchmark = fbcb42d
Phase24S-E rollback after full gate failure = 454603f
Phase24S-G residual register update = b6f23f3
Phase24S-H TEB-04 raw intake reminder = 07a8131
Phase24S final report = pending_this_commit
```

## 2. Candidate Manifest

Artifacts:

```text
reports/benchmark/phase_24S_A_cby_cutover_candidate_manifest.md
reports/benchmark/phase_24S_A_cby_cutover_candidate_manifest.json
```

Candidate collection:

```text
base_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
base_entity_count = 349403
cby_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
cby_entity_count = 349405
candidate_scope = CBY-06 materialization improvement only
model = hukuk-ai-poc / /models/merged_model_fabric_stage_20260321
```

## 3. Pre-Cutover Backup

Artifacts:

```text
reports/benchmark/phase_24S_B_pre_cutover_live_backup.md
reports/benchmark/phase_24S_B_pre_cutover_live_backup.json
reports/benchmark/phase_24S_B_rollback_plan.md
```

Pre-cutover live `8000` was verified on the base collection, lane `phase22f_s7_full_shadow`, entity count `349403`, model `hukuk-ai-poc`.

## 4. Cutover Execution

Artifacts:

```text
reports/benchmark/phase_24S_C_cutover_execution_log.md
reports/benchmark/phase_24S_C_post_cutover_runtime_provenance.json
```

Controlled benchmark-only cutover passed provenance after re-execution under detached `tmux` process management:

```text
lane = phase24s_cby_benchmark_only
api_version = 2026-05-05-phase24s-cby-benchmark-only-cutover
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
entity_count = 349405
model_contract = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
```

The first short-lived shell background launch returned one healthy response but did not persist. Live was immediately restored to base, then the same CBY cutover was re-executed through `tmux`; all C provenance checks passed before any D/E benchmark evidence was accepted.

## 5. Post-Cutover Targeted Smoke

Artifact:

```text
reports/benchmark/phase_24S_D_post_cutover_targeted_smoke.md
```

Result:

```text
targeted_gate = PASS
raw_score_proxy = 85.41 / 110
pass_proxy = 9 / 11
CBY-06 = 8.58 PASS
critical_guard_regression_vs_Phase24R_CBY = false
contract_valid = 11/11
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
TUZUK-04_active_current_law_claim = false
```

`MULGA-05` and `TUZUK-04` remained residual FAIL rows, unchanged from the Phase24R CBY targeted reference, and did not violate the D acceptance guard.

## 6. Post-Cutover Full Benchmark

Artifacts:

```text
reports/benchmark/phase_24S_E_post_cutover_full_summary.md
reports/benchmark/phase_24S_E_delta_vs_phase23RE.md
reports/benchmark/phase_24S_E_green_lane_summary.md
```

Result:

```text
full_gate = FAIL
raw_score_proxy = 727.18 / 1000
pass_proxy = 73 / 100
wrong_family = 8
wrong_document = 21
hallucinated_identifier = 25
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = FAIL
```

Delta vs Phase23R-E stable baseline:

```text
raw_score_proxy_delta = -89.68
pass_proxy_delta = -18
wrong_family_delta = +2
wrong_document_delta = +17
hallucinated_identifier_delta = +21
```

## 7. Stability Result

Phase 24S-F stability was not run. The Phase 24S-E full benchmark minimum gate failed, and the brief requires rollback/hard stop before stability.

## 8. Rollback Performed

Artifacts:

```text
reports/benchmark/phase_24S_E_post_gate_rollback_execution_log.md
reports/benchmark/phase_24S_E_post_gate_rollback_runtime_provenance.json
```

Rollback was performed and verified:

```text
rollback_verified = PASS
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
lane = phase22f_s7_full_shadow
api_version = 2026-05-03-phase23R-E-benchmark-only-cutover
model = hukuk-ai-poc
```

## 9. Residual Register Update

Artifacts:

```text
reports/benchmark/phase_24S_G_residual_register_update.md
reports/benchmark/phase_24S_G_residual_register_update.csv
```

Residual state:

```text
open_fail_residual_rows = 27
wrong_family_fail_rows = 6
wrong_document_fail_rows = 21
hallucinated_identifier_fail_rows = 23
TEB-04_raw_intake_blocker_rows = 1
CBY-06_validated_candidate_not_live_rows = 1
```

## 10. TEB-04 Raw Intake Reminder

Artifact:

```text
reports/benchmark/phase_24S_H_teb04_manual_raw_intake_reminder.md
```

Status:

```text
TEB-04 = blocked_not_materialized
expected_official_raw_pdf = reports/benchmark/source_acquisition/phase_24R/raw/kdv_gut_2025_official_manual.pdf
expected_file_exists = false
```

Existing Phase24P `.pdf`-named files are JSON/HTML or partial artifacts and do not close the official browser-saved GIB PDF blocker.

## 11. Productization Decision

```text
productization = CLOSED
reason = Phase24S-E full benchmark minimum gate failed and rollback was required
```

## 12. Internal Eval Decision

```text
internal_eval = CLOSED
reason = full benchmark green lane failed; stability not run
```

## 13. Fine-Tuning Decision

```text
fine_tuning = CLOSED
reason = no accepted post-cutover full gate; no training data decision authorized
```

## 14. Final Live 8000 State

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"phase22f_s7_full_shadow","api_version":"2026-05-03-phase23R-E-benchmark-only-cutover","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

Additional final state:

```text
process_manager = tmux session hukuk_ai_live_8000
pid = 46587
milvus_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
milvus_entity_count = 349403
DGX_MODEL = /models/merged_model_fabric_stage_20260321
```

## 15. Next Recommended Phase

Open a systemic recovery phase before any further cutover:

```text
Phase24T recommended scope:
1. diagnose why Phase24S/Phase24R full runs on the current base/CBY collections are far below Phase23R-E despite contract safety
2. restore source/document identity and canonical span recall without QID-specific runtime rules
3. keep CBY-06 candidate evidence preserved but not live until full gate recovery
4. complete TEB-04 official browser-saved PDF raw intake separately
5. rerun matched A/B and controlled cutover only after Phase23R-E-level full score is recovered
```

## Final Decision

Phase 24S controlled CBY cutover outcome: `FAILED_FULL_GATE_ROLLED_BACK`.

The CBY collection remains useful as evidence for `CBY-06`, but it is not live and is not productization-ready.
