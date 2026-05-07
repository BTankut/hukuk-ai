# Phase 24HV Full Candidate Validation Report

## Commit SHA List

```text
47a94e6 Verify Phase 24HV candidate runtime provenance
79515c4 Run Phase 24HV pre-full targeted smoke
48b94e4 Run Phase 24HV full candidate benchmark
fbe1508 Analyze Phase 24HV candidate delta
8a8a658 Record Phase 24HV integration readiness decision
2286f6e Check Phase 24HV TEB-04 raw intake status
```

## Candidate Runtime Provenance

Output:

```text
reports/benchmark/phase_24HV_A_candidate_runtime_provenance.md
reports/benchmark/phase_24HV_A_candidate_runtime_provenance.json
```

Candidate:

```text
api_url = http://127.0.0.1:8044/v1
lane = phase24hv_full_candidate_validation
api_version = 2026-05-07-phase24hv-full-candidate-validation
DGX_MODEL = /models/merged_model_fabric_stage_20260321
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
guardrails = disabled
verification = disabled
```

Feature flags:

```text
ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true
ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true
ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=true
ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true
```

`ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true` was kept as a pre-existing family/domain gate dependency required to preserve prior Phase24HS behavior.

## Pre-Full Targeted Smoke

Output:

```text
reports/benchmark/phase_24HV_B_pre_full_targeted_smoke.md
```

Result:

```text
raw_score_proxy = 104.83 / 130
pass_proxy = 11 / 13
contract_invalid = 0
unsupported_confident_answer = 0
source_key_v2_collision = 0
binding_collision = 0
```

Gate result:

```text
PASS
```

The pre-full gate allowed full benchmark execution.

## Full Candidate Benchmark

Outputs:

```text
reports/benchmark/phase_24HV_C_full_candidate_summary.md
reports/benchmark/phase_24HV_C_green_lane_summary.md
reports/benchmark/phase_24HV_C_full_candidate_run_manifest.md
reports/benchmark/phase_24HV_C_full_candidate_run_manifest.json
```

Result:

```text
candidate_raw_score_proxy = 727.39 / 1000
candidate_pass_proxy = 74 / 100
base_trace_on_raw_score_proxy = 805.09 / 1000
base_trace_on_pass_proxy = 89 / 100
raw_delta = -77.70
pass_delta = -15
```

Hard counters:

```text
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = pass
```

Quality regressions:

```text
wrong_document = 18 vs base 3
hallucinated_identifier = 22 vs base 7
pass_to_fail = 19
fail_to_pass = 4
```

Minimum gate:

```text
FAIL
```

Preferred gate:

```text
FAIL
```

## Delta vs Current Trace-On Base

Outputs:

```text
reports/benchmark/phase_24HV_D_delta_vs_phase24U_base.md
reports/benchmark/phase_24HV_D_delta_vs_phase24U_base.csv
```

Summary:

```text
delta_class.unchanged = 54
delta_class.regressed = 31
delta_class.improved = 15
risk_class.new_wrong_document = 17
risk_class.safe_improvement = 14
risk_class.unknown = 15
risk_class.acceptable_neutral = 54
```

Interpretation:

```text
Target-row recoveries are real, but broad full-corpus degradation dominates.
```

## Integration Readiness Decision

Output:

```text
reports/benchmark/phase_24HV_E_integration_readiness_decision.md
```

Decision:

```text
Option C — Candidate regresses.
```

Result:

```text
No integration.
No cutover.
No productization.
No internal eval enablement.
Keep feature flags non-live/default-off.
Open regression audit.
```

## TEB-04 Raw Intake Status

Output:

```text
reports/benchmark/phase_24HV_F_teb04_raw_intake_status.md
```

Expected raw file:

```text
reports/benchmark/source_acquisition/phase_24R/raw/kdv_gut_2025_official_manual.pdf
status = missing
```

Available related official file:

```text
reports/benchmark/kdv_genteb_2026_official_gib.pdf
sha256 = bdea3737f421203d3814fce7c4b72c617dacd03878d4d8e655cacc9e19d0df68
```

No TEB-04 materialization was performed in Phase 24HV.

## Productization Decision

Productization remains closed.

## Internal Eval Decision

Internal eval remains closed.

## Fine-Tuning Decision

Fine-tuning remains closed. This phase evaluated retrieval/runtime feature flags only.

## Final Runtime State

Candidate `8044` was stopped after validation:

```text
candidate_gateway_stopped = true
status = STOPPED
```

Live `8000` final state:

```text
status = ok
service = hukuk-ai-api-gateway
lane = phase22f_s7_full_shadow
api_version = 2026-05-03-phase23R-E-benchmark-only-cutover
guardrails = disabled
retriever = milvus
verification = disabled
```

Live `8000` was not modified.

## Next Recommended Phase

Open Phase 24HW regression audit / feature isolation, not cutover.

Recommended focus:

```text
1. isolate whether secondary-family recall over-applies outside KANUN-08-like source-role queries
2. compare candidate env/runtime parity against Phase24U base trace-on beyond collection/model/embedding
3. inspect the 19 pass-to-fail rows, especially KANUN, CBY, KKY, UY, and TEB-03
4. preserve Phase24HU target-row recovery while preventing broad same-family/source-domain degradation
5. do not enable Phase24HU flags in live/productization until full gate recovers to at least 805.09/89 with no new wrong-document/hallucinated-identifier increase
```
