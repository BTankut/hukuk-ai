# Hukuk-AI — Phase 24HW Feature Isolation / Full-Candidate Regression Audit Brief

## Karar

Phase 24HV full-candidate validation tamamlandı.

Sonuç:

```text
pre-full targeted smoke = PASS
full candidate = FAIL
candidate_raw_score_proxy = 727.39 / 1000
candidate_pass_proxy = 74 / 100
base_trace_on_raw_score_proxy = 805.09 / 1000
base_trace_on_pass_proxy = 89 / 100
raw_delta = -77.70
pass_delta = -15
```

Hard counters temiz:

```text
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

Ama quality regression ağır:

```text
wrong_document = 18 vs base 3
hallucinated_identifier = 22 vs base 7
pass_to_fail = 19
fail_to_pass = 4
```

Decision:

```text
Option C — Candidate regresses.
No integration.
No cutover.
No productization.
No internal eval.
Feature flags remain non-live/default-off.
```

Sıradaki faz:

```text
Phase 24HW — Feature Isolation / Full-Candidate Regression Audit
```

Amaç:

```text
Phase24HU/HS/HT feature flag set içinde hangi parça full-corpus degradation üretiyor bulmak.
Target-row recovery korunurken broad wrong-document / hallucinated-identifier artışı engellenecek.
```

---

# 1. Kesin Kurallar

Phase 24HW boyunca:

- live `8000` değişmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- base/live collection overwrite yok
- benchmark answer key ile kod değişikliği yok
- QID-specific runtime branch yok
- large trace commit yok
- yalnız non-live feature isolation ve summary artifacts

Allowed:

```text
non-live feature-flag ablation
targeted smoke
full candidate benchmark if scoped gate passes
pass-to-fail row audit
feature interaction matrix
feature-scoped redesign
```

---

# 2. Candidate Feature Flags

Phase 24HV candidate used:

```text
ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true
ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true
ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true
ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=true
```

Known targeted benefits:

```text
TEB-04 recovered by HS active TEB temporal guard / family policy
TUZUK-05 recovered by HS ambiguous source stop-condition
YON-05 recovered by HS family/domain compatibility
KANUN-08 recovered by HT+HU source-role retrieval / secondary-family recall / exception guard
```

Known full regression:

```text
19 pass_to_fail rows
17 new_wrong_document rows
22 hallucinated_identifier rows
```

---

# 3. Phase 24HW-A — Pass-to-Fail Regression Audit

## Amaç

Full candidate’da bozulan 19 satırı sınıflamak.

## Output

```text
reports/benchmark/phase_24HW_A_pass_to_fail_regression_audit.md
reports/benchmark/phase_24HW_A_pass_to_fail_regression_audit.csv
```

## Fields

```text
qid
base_score
candidate_score
score_delta
base_selected_source
candidate_selected_source
base_claimed_family
candidate_claimed_family
base_claimed_identifier
candidate_claimed_identifier
base_failure_classes
candidate_failure_classes
new_wrong_document
new_hallucinated_identifier
candidate_feature_trace_fields
likely_regressing_feature
safe_next_action
```

## likely_regressing_feature enum

```text
HS_family_domain_gate
HT_same_family_domain_scoring
HU_secondary_family_recall
HU_exception_slot_guard
feature_interaction
runtime_provenance
scorer_trace_artifact
unknown
```

## Commit

```text
Audit Phase 24HW pass-to-fail regressions
```

Push required.

---

# 4. Phase 24HW-B — Feature Isolation Matrix Plan

## Amaç

Feature flag kombinasyonlarını non-live olarak sistemli test etmek.

## Output

```text
reports/benchmark/phase_24HW_B_feature_isolation_matrix_plan.md
reports/benchmark/phase_24HW_B_feature_isolation_matrix_plan.csv
```

## Required matrix

Minimum combinations:

```text
BASE = all flags off
HS_only = HS on
HT_only = HT on
HU_recall_only = HU secondary recall on
HU_guard_only = HU exception guard on
HS_HT = HS + HT
HS_HT_HU_recall = HS + HT + HU recall
HS_HT_HU_guard = HS + HT + HU guard
ALL = HS + HT + HU recall + HU guard
```

## For each combination record

```text
combination_name
feature_flags
expected_target_rows_recovered
expected_risk
run_targeted_smoke
run_full_if_targeted_passes
```

## Commit

```text
Plan Phase 24HW feature isolation matrix
```

Push required.

---

# 5. Phase 24HW-C — Targeted Feature Matrix Smoke

## Amaç

Her feature kombinasyonunun hedef satırları ve guardları nasıl etkilediğini ölçmek.

## Target rows

```text
TEB-04
TUZUK-05
YON-05
KANUN-08
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
reports/benchmark/phase_24HW_C_targeted_feature_matrix_smoke.md
reports/benchmark/phase_24HW_C_targeted_feature_matrix_smoke.csv
```

## For each combination

```text
raw_score_proxy
pass_proxy
TEB-04 score/pass
TUZUK-05 score/pass
YON-05 score/pass
KANUN-08 score/pass
guard_regression_count
contract_invalid
unsupported_confident
source_key_v2_collision
binding_collision
decision_for_full
```

## Acceptance for full run candidate

```text
targeted rows improved vs base
critical guards no regression
safety counters zero
contract_valid all
```

## Commit

```text
Run Phase 24HW targeted feature matrix smoke
```

Push required.

---

# 6. Phase 24HW-D — Full Benchmark on Best Safe Combination

Only run if Phase 24HW-C identifies a safe combination.

## Output

```text
reports/benchmark/phase_24HW_D_best_combination_full_summary.md
reports/benchmark/phase_24HW_D_delta_vs_phase24U_base.md
reports/benchmark/phase_24HW_D_green_lane_summary.md
```

## Minimum gate

```text
raw_score_proxy >= 805.09
pass_proxy >= 89
wrong_document <= 3 or no increase vs base
hallucinated_identifier <= 7 or no increase vs base
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

## Preferred

```text
raw_score_proxy > 805.09
pass_proxy > 89
at least two target rows recovered
no new broad wrong_document class
```

## Commit

```text
Run Phase 24HW best-combination full benchmark
```

Push required.

If not run:

```text
reports/benchmark/phase_24HW_D_full_not_run.md
```

---

# 7. Phase 24HW-E — Feature Redesign Decision

## Output

```text
reports/benchmark/phase_24HW_E_feature_redesign_decision.md
```

## Decision options

### Option A — Safe feature subset found

```text
Open Phase24HX controlled integration for safe subset.
No live cutover yet.
```

### Option B — Target recovery requires broad regression

```text
Keep features diagnostic-only.
Do not integrate.
```

### Option C — Specific feature over-applies

```text
Open scoped redesign for that feature.
```

### Option D — No safe runtime path

```text
Return to product policy / residual acceptance.
No further runtime recovery.
```

## Commit

```text
Record Phase 24HW feature redesign decision
```

Push required.

---

# 8. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24HW_feature_isolation_report.md
```

Must include:

1. commit SHA list
2. pass-to-fail audit
3. feature isolation matrix
4. targeted matrix smoke
5. best-combination full benchmark result or not-run reason
6. feature redesign decision
7. productization decision
8. internal eval decision
9. fine-tuning decision
10. final live 8000 state
11. next recommended phase

## Commit

```text
Report Phase 24HW feature isolation outcome
```

Push required.

---

# 9. Stop Rules

Stop/revert candidate if:

```text
live 8000 would be modified
contract invalid appears
unsupported confident appears
source_key_v2 or binding collision appears
MULGA-01/MULGA-05/TEB-06 regress
large traces staged
QID-specific logic required
benchmark answer key required for code changes
```

---

## Final Note

Phase24HV proved that the combined feature set over-applies globally.

Phase24HW must isolate the smallest safe feature subset before any integration or cutover is discussed.
