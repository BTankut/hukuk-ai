# Hukuk-AI — Phase 24V Commit-Level Regression Audit Brief

## Karar

Phase 24U tamamlandı.

Sonuç:

```text
BASE trace-on = 805.09 / 89
CBY trace-on = 807.27 / 90
source supplement ablation = 804.42 / 89
```

Karar:

```text
Option D — code regression not supplement-related
```

Source supplement drift tek başına Phase23R-E parity kaybını açıklamıyor. Sıradaki doğru faz:

```text
Phase 24V — Commit-Level Regression Audit
```

Bu faz implementation/revert fazı değildir. Önce Phase23R-E ile current HEAD arasındaki kod/runtime farkı izole edilecek.

Live `8000` değişmeyecek.  
Productization kapalı.  
Internal eval kapalı.  
Fine-tuning kapalı.

---

## 1. Kesin Kurallar

Phase 24V boyunca:

- live `8000` değiştirilmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- base/live collection overwrite yok
- large traces commitlenmeyecek
- yalnız commit-level diagnostic yapılacak

---

## 2. Regression Window

Good reference:

```text
Phase23R-E benchmark-only cutover commit/window
known good score = 816.86 / 91
```

Current:

```text
current HEAD after Phase24U
current trace-on BASE = 805.09 / 89
```

Known narrow candidates from prior phases:

```text
source_supplements.py drift not sufficient
include_trace normalized
collection binding not primary
scorer/runner hash unchanged in Phase24T
```

---

## 3. Phase 24V-A — Commit Range Inventory

## Amaç

Phase23R-E good state ile current HEAD arasındaki commitleri sınıflamak.

## Output

```text
reports/benchmark/phase_24V_A_commit_range_inventory.md
reports/benchmark/phase_24V_A_commit_range_inventory.csv
```

## Fields

```text
commit_sha
commit_subject
phase
files_changed
risk_area
runtime_code_changed
source_identity_changed
selector_changed
answer_contract_changed
source_supplement_changed
scorer_runner_changed
benchmark_artifact_only
candidate_for_ablation
notes
```

## risk_area enum

```text
source_identity
selector_reranker
answer_contract
evidence_bundle
source_supplement
scorer_runner
benchmark_artifact
docs_only
unknown
```

## Acceptance

- All commits from good Phase23R-E to current HEAD classified.
- Candidate code commits for ablation identified.
- Docs/report-only commits excluded.

## Commit

```text
Inventory Phase 24V regression commit range
```

Push required.

---

## 4. Phase 24V-B — High-Risk File Diff Audit

## Amaç

Regression potansiyeli yüksek dosyaları diff bazında incelemek.

## Output

```text
reports/benchmark/phase_24V_B_high_risk_file_diff_audit.md
reports/benchmark/phase_24V_B_high_risk_file_diff_audit.csv
```

## Focus files

At minimum:

```text
api-gateway/src/rag/source_identity.py
api-gateway/src/rag/article_span_selection.py
api-gateway/src/rag/retrieval_orchestration.py
api-gateway/src/rag/evidence_bundle.py
api-gateway/src/rag/answer_synthesis.py
api-gateway/src/rag/answer_slots.py
api-gateway/src/rag/source_supplements.py
scripts/benchmark/run_hukuk_ai_100.py
scripts/benchmark/score_hukuk_ai_100.py
```

## Fields

```text
file_path
changed_since_phase23RE
commits_touching
risk_level
behavior_changed
possible_score_impact
rows_likely_affected
ablation_possible
notes
```

## Commit

```text
Audit Phase 24V high-risk file diffs
```

Push required.

---

## 5. Phase 24V-C — Row-Level Drift Focus Audit

## Amaç

Phase23R-E 816.86/91 ile current trace-on 805.09/89 arasındaki kalan farkı row-level açıklamak.

## Output

```text
reports/benchmark/phase_24V_C_row_level_drift_focus.md
reports/benchmark/phase_24V_C_row_level_drift_focus.csv
```

## Focus rows

Include all rows with changed pass/fail or material score drop. At minimum:

```text
MULGA-04
KANUN-08
KANUN-02
YON-05
YON-08
```

## Fields

```text
qid
phase23RE_score
current_trace_on_score
delta
phase23RE_pass
current_pass
phase23RE_selected_source
current_selected_source
phase23RE_claimed_family
current_claimed_family
phase23RE_claimed_identifier
current_claimed_identifier
phase23RE_failure_classes
current_failure_classes
suspected_changed_component
candidate_commit
safe_ablation_test
```

## Commit

```text
Audit Phase 24V row-level drift focus
```

Push required.

---

## 6. Phase 24V-D — Non-Live Commit Ablation Plan

## Amaç

Riskli commitleri non-live ortamda ablate etmek için güvenli plan hazırlamak.

## Output

```text
reports/benchmark/phase_24V_D_commit_ablation_plan.md
```

## Plan must include

```text
candidate commits
candidate files
ablation method
non-live port
collection
include_trace=true
expected metrics
stop rules
```

## Allowed ablation types

```text
env flag disable
temporary revert in throwaway branch
cherry-pick inverse patch in local candidate
feature flag off
```

## Forbidden

```text
live 8000 changes
permanent revert without evidence
QID-specific patch
broad top-k/prompt changes
```

## Commit

```text
Plan Phase 24V non-live commit ablations
```

Push required.

---

## 7. Phase 24V-E — Non-Live Ablation Execution

Only run if Phase 24V-D identifies safe ablations.

## Runtime

Use non-live candidate ports only.

## Output

```text
reports/benchmark/phase_24V_E_commit_ablation_results.md
reports/benchmark/phase_24V_E_commit_ablation_results.csv
```

## For each ablation

Run either:

```text
focused rows first
then full 100 only if focused rows improve and safety clean
```

## Minimum acceptance for full run

```text
raw_score_proxy improves toward 816.86
pass_proxy improves toward 91
safety counters remain zero
contract_valid = 100/100
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

## Commit

```text
Run Phase 24V non-live commit ablations
```

Push required.

If no safe ablation:

```text
reports/benchmark/phase_24V_E_ablation_not_run.md
```

---

## 8. Phase 24V-F — Recovery Decision

## Output

```text
reports/benchmark/phase_24V_F_recovery_decision.md
```

## Decision options

### Option A — Specific regression commit found

```text
Open Phase24W controlled revert/fix brief.
```

### Option B — No single commit found, but component localized

```text
Open Phase24W component-level recovery design.
```

### Option C — Drift not actionable

```text
Freeze current benchmark-only baseline.
Do not chase further score recovery.
```

### Option D — Need manual scorer/source review

```text
Prepare human review packet.
No runtime changes.
```

## Commit

```text
Record Phase 24V recovery decision
```

Push required.

---

## 9. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24V_commit_regression_audit_report.md
```

Must include:

1. commit SHA list
2. commit range inventory
3. high-risk file diff audit
4. row-level drift focus
5. ablation plan
6. ablation results or not-run reason
7. recovery decision
8. productization decision
9. internal eval decision
10. fine-tuning decision
11. final live 8000 state
12. next recommended phase

## Commit

```text
Report Phase 24V commit regression audit outcome
```

Push required.

---

## 10. Stop Rules

Stop if:

```text
live 8000 would be modified
benchmark answer key would be needed
QID-specific patch required
large traces staged
safety counters non-zero in ablation
contract invalid appears
```

---

## Final Note

Do not patch yet.

Find the commit/component responsible for the remaining Phase23R-E parity gap first.
