# Phase 24R Matched A/B and TEB Intake Outcome Report

## Commit SHA List

```text
Phase24R-A plan = a1122c3
Phase24R-B runtime pair verification = f15a0de
Phase24R-C targeted A/B smoke = 5ee5fa2
Phase24R-D full A/B benchmark = c301ddd
Phase24R-E CBY merge decision = 871c3bf
Phase24R-F TEB raw intake = d269da7
Phase24R-G trace compliance = 797b5b0
Phase24R final report = 258aab4
```

## Matched A/B Plan

```text
BASE_API = http://127.0.0.1:8035/v1
CBY_API = http://127.0.0.1:8036/v1
BASE_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
CBY_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
only_runtime_difference = MILVUS_COLLECTION plus port/lane labels
```

## Runtime Pair Verification

```text
both_runtimes_healthy = true
both_models_ok = true
collections_loaded = true
BASE entity_count = 349403
CBY entity_count = 349405
same git_sha = a1122c31614d643098cf11d944d63ea9a797bbff
same DGX_MODEL = /models/merged_model_fabric_stage_20260321
same embedding_model = intfloat/multilingual-e5-large-instruct
```

The candidate pair was stopped after the evidence run. Live `8000` was not modified.

## Targeted A/B Smoke

```text
targeted_status = PASS
BASE raw_score_proxy = 83.63
CBY raw_score_proxy = 85.41
BASE pass_proxy = 8
CBY pass_proxy = 9
CBY-06 = 6.80 FAIL -> 8.58 PASS
critical_guard_regression = false
contract_valid_all = true
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
TUZUK-04_active_current_law_claim = false
```

## Full A/B Benchmark

```text
full_status = MATCHED_AB_GREEN_LANE_PASS
BASE raw_score_proxy = 725.40
CBY raw_score_proxy = 727.18
raw_score_delta = +1.78
BASE pass_proxy = 72
CBY pass_proxy = 73
pass_delta = +1
changed_rows = CBY-06 only
CBY wrong_family <= BASE wrong_family = true
CBY wrong_document <= BASE wrong_document = true
CBY hallucinated_identifier <= BASE hallucinated_identifier = true
CBY contract_valid = 100/100
CBY unsupported_confident_answer = 0
CBY answer_contract_invalid = 0
CBY source_key_v2_collision = 0
CBY binding_collision = 0
```

The matched full A/B benchmark proves CBY collection is non-regressive versus the current BASE lane and improves only the intended `CBY-06` row.

## CBY Merge Decision

```text
selected_option = Option A - CBY collection is merge-safe
open_future_controlled_cutover_or_merge_brief = true
auto_cutover = false
live_8000_modified = false
```

This is not a productization decision. It only authorizes a future controlled cutover/merge brief if the product owner wants to promote the CBY collection.

## TEB-04 Manual Raw Intake

```text
expected_path = reports/benchmark/source_acquisition/phase_24R/raw/kdv_gut_2025_official_manual.pdf
file_exists = false
sha256 = absent
safe_for_teb04_materialization = false
teb04_materialization_allowed = false
```

TEB-04 remains blocked until the browser-saved official GIB PDF, SHA-256, byte size, source URL, and acquisition record are committed.

## Trace Compliance

```text
compliance_passed = true
large_trace_files_committed = false
phase24r_run_dirs_committed = false
max_local_trace_size = 6.6 MB
summary_artifacts_committed = true
```

## Productization / Eval / Fine-Tuning

```text
productization = closed
internal_eval = closed
fine_tuning = closed
model_prompt_topk_changes = none
qid_specific_runtime_branch = none
```

## Final Live 8000 State

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"phase22f_s7_full_shadow","api_version":"2026-05-03-phase23R-E-benchmark-only-cutover","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

## Next Recommended Phase

```text
Phase24S - controlled CBY collection cutover/merge readiness
```

The next brief should be a controlled cutover/merge readiness gate for the CBY collection only. It should include pre-switch live binding proof, rollback command, post-switch targeted smoke, post-switch full or sampled verification as required by the product owner, and trace artifact compliance. TEB-04 should stay on a separate raw-intake/materialization track until the official PDF is hashable.
