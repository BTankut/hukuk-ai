# Hukuk-AI — Phase 24HV Controlled Full-Candidate Validation and Integration-Readiness Brief

## Karar

Phase 24HU başarıyla tamamlandı.

Repo kanıtı:

```text
KANUN-08: 3.93 FAIL -> 8.22 PASS
primary source remained: TÜKETİCİNİN KORUNMASI HAKKINDA KANUN / TKHK m.18
supporting YONETMELIK evidence entered selected support chain
contract_invalid = 0
unsupported_confident_answer = 0
source_key_v2_collision = 0
binding_collision = 0
guard-row score regression = 0
```

Phase 24HU recovery decision:

```text
Option A — KANUN-08 recovered safely for non-live focused scope.
Open controlled full-candidate validation / integration-readiness brief.
```

Bu nedenle sıradaki faz:

```text
Phase 24HV — Controlled Full-Candidate Validation and Integration Readiness
```

Bu faz live cutover değildir.  
Bu faz productization değildir.  
Bu faz internal eval açma fazı değildir.  
Fine-tuning kapalıdır.  
Live `8000` değişmeyecek.

---

## 1. Kesin Kurallar

Phase 24HV boyunca:

- live `8000` değiştirilmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- base/live collection overwrite yok
- benchmark answer key kullanılmayacak
- QID-specific runtime branch yok
- large trace commit yok
- yalnız non-live full candidate validation ve integration-readiness raporu

Allowed:

```text
non-live candidate runtime
full 100 benchmark
green-lane validation
delta vs current trace-on base
targeted post-full smoke
integration-readiness decision
```

---

## 2. Candidate Under Test

Use Phase 24HU feature set:

```text
ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true
ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true
ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=true
```

Candidate must preserve:

```text
primary KANUN identity for KANUN-08
supporting YONETMELIK evidence role
TEB-04 active TEBLIGLER temporal guard
TUZUK-05 ambiguous-source stop condition
YON-05 family/domain compatibility recovery
MULGA/TEB guard rows
```

Current live baseline:

```text
API = http://127.0.0.1:8000/v1
lane = phase22f_s7_full_shadow
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

Candidate runtime:

```text
non-live only
suggested API = http://127.0.0.1:8044/v1
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
include_trace = true
```

---

## 3. Phase 24HV-A — Candidate Runtime Provenance

## Amaç

Non-live candidate runtime’ın Phase 24HU feature set’iyle doğru kalktığını doğrulamak.

## Output

```text
reports/benchmark/phase_24HV_A_candidate_runtime_provenance.md
reports/benchmark/phase_24HV_A_candidate_runtime_provenance.json
```

## Must include

```text
api_url
pid
git_sha
lane
api_version
model
DGX_MODEL
collection
entity_count
embedding_backend
embedding_model
guardrails
verification
feature_flags
include_trace_support
source_catalog_hash
source_supplement_hash
```

## Acceptance

```text
candidate health OK
/v1/models OK
collection = base p0_backfill
entity_count = 349403
feature flags enabled
live 8000 untouched
```

## Commit

```text
Verify Phase 24HV candidate runtime provenance
```

Push required.

---

## 4. Phase 24HV-B — Pre-Full Targeted Guard Smoke

## Amaç

Full 100 benchmark öncesi kritik recovery ve guard satırlarını doğrulamak.

## Target rows

```text
KANUN-08
TEB-04
TUZUK-05
YON-05
```

## Guard rows

```text
MULGA-01
MULGA-05
TEB-06
CBY-06
KANUN-12
YON-04
TUZUK-04
CBG-01
CBKAR-08
```

## Output

```text
reports/benchmark/phase_24HV_B_pre_full_targeted_smoke.md
```

## Acceptance

```text
contract_valid all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0

KANUN-08 PASS or >= 8.0
TEB-04 PASS
TUZUK-05 PASS or expected stop-condition response
YON-05 PASS
MULGA-01/MULGA-05/TEB-06 no regression
TUZUK-04 not active-current-law claim
```

## Commit

```text
Run Phase 24HV pre-full targeted smoke
```

Push required.

## Stop rule

If this smoke fails, do not run full benchmark. Produce not-run report and final report.

---

## 5. Phase 24HV-C — Full Candidate Benchmark

Only run if Phase 24HV-B passes.

## Runtime

```text
api_url = http://127.0.0.1:8044/v1
include_trace = true
```

## Output

```text
reports/benchmark/phase_24HV_C_full_candidate_summary.md
reports/benchmark/phase_24HV_C_green_lane_summary.md
reports/benchmark/phase_24HV_C_full_candidate_run_manifest.md
```

## Minimum gate

Compare against current trace-on BASE:

```text
BASE trace-on = 805.09 / 89
```

Candidate must satisfy:

```text
raw_score_proxy >= 805.09
pass_proxy >= 89
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
wrong_document <= current trace-on base
hallucinated_identifier <= current trace-on base
```

## Preferred gate

```text
raw_score_proxy >= 816
pass_proxy >= 91
KANUN-08 PASS
TEB-04 PASS
TUZUK-05 PASS or accepted stop-condition
YON-05 PASS
```

## Commit

```text
Run Phase 24HV full candidate benchmark
```

Push required.

---

## 6. Phase 24HV-D — Delta Analysis vs Current Trace-On Base

## Amaç

Candidate’ın current trace-on BASE’e göre hangi satırları değiştirdiğini netleştirmek.

## Output

```text
reports/benchmark/phase_24HV_D_delta_vs_phase24U_base.md
reports/benchmark/phase_24HV_D_delta_vs_phase24U_base.csv
```

## Fields

```text
qid
base_score
candidate_score
score_delta
base_pass
candidate_pass
pass_to_fail
fail_to_pass
base_failure_classes
candidate_failure_classes
base_selected_source
candidate_selected_source
base_claimed_family
candidate_claimed_family
base_claimed_identifier
candidate_claimed_identifier
delta_class
risk_class
```

## delta_class enum

```text
improved
regressed
unchanged
mixed
```

## risk_class enum

```text
safe_improvement
acceptable_neutral
target_regression
guard_regression
new_wrong_document
new_hallucinated_identifier
unknown
```

## Commit

```text
Analyze Phase 24HV candidate delta
```

Push required.

---

## 7. Phase 24HV-E — Integration Readiness Decision

## Output

```text
reports/benchmark/phase_24HV_E_integration_readiness_decision.md
```

## Decision options

### Option A — Candidate full validation passes

```text
Open Phase 24HW controlled benchmark-only integration/cutover brief.
No automatic cutover.
Productization still closed.
Internal eval still closed unless separately approved.
```

### Option B — Candidate improves but misses full gate

```text
Keep diagnostic candidate.
Continue targeted recovery.
No cutover.
```

### Option C — Candidate regresses

```text
Disable feature flags by default.
Do not integrate.
Open regression audit.
```

### Option D — Validation inconclusive

```text
Rerun once with same provenance.
No cutover.
```

## Commit

```text
Record Phase 24HV integration readiness decision
```

Push required.

---

## 8. Phase 24HV-F — TEB-04 Raw Intake Status Check

Do not materialize TEB-04 here, but preserve blocker visibility.

## Expected raw file

```text
reports/benchmark/source_acquisition/phase_24R/raw/kdv_gut_2025_official_manual.pdf
```

## Output

```text
reports/benchmark/phase_24HV_F_teb04_raw_intake_status.md
```

## Commit

```text
Check Phase 24HV TEB-04 raw intake status
```

Push required.

---

## 9. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24HV_full_candidate_validation_report.md
```

Must include:

1. commit SHA list
2. candidate runtime provenance
3. pre-full targeted smoke
4. full candidate benchmark result or not-run reason
5. delta vs current trace-on base
6. integration readiness decision
7. TEB-04 raw intake status
8. productization decision
9. internal eval decision
10. fine-tuning decision
11. final live 8000 state
12. next recommended phase

## Commit

```text
Report Phase 24HV full candidate validation outcome
```

Push required.

---

## 10. Stop Rules

Stop/revert candidate if:

```text
live 8000 would be modified
targeted smoke fails
contract invalid appears
unsupported confident appears
source_key_v2 or binding collision appears
MULGA-01/MULGA-05/TEB-06 regress
TEB-04/TUZUK-05/YON-05 regress
KANUN-08 primary identity regresses away from TKHK
large traces staged
benchmark answer key needed for code changes
```

---

## Final Note

Phase 24HU recovered the focused KANUN-08 path.

Phase 24HV must prove whether that focused recovery is safe at full-candidate scope before any integration/cutover brief is opened.
