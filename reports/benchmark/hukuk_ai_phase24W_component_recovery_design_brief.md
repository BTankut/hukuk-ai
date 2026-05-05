# Hukuk-AI — Phase 24W Controlled Component-Level Recovery Design and Evidence Brief

## Karar

Phase 24V tamamlandı.

Repo kararı:

```text
Option B — No single commit found, but component localized
Next phase: Phase24W controlled component-level recovery design
```

Phase 24V sonucu:

```text
Tek commit ablation ile kanıtlanmadı.
Ana bileşen source_identity.py / ddcadd2 çevresine lokalize edildi.
KANUN-08 ve YON-05 source-selection drift ile uyumlu.
KANUN-02, MULGA-04, YON-08 aynı kaynak seçiliyken düştüğü için ayrıca trace/failure-class audit istiyor.
Scored ablation answer-key stop-rule nedeniyle çalıştırılmadı.
Live 8000 değişmedi.
```

Bu nedenle Phase 24W iki ayrı hattı işleyecek:

1. `source_identity.py` / ddcadd2 çevresinde **component-level recovery design**.
2. Aynı kaynak seçildiği halde düşen satırlar için **trace/failure-class audit**.

Bu faz doğrudan live fix değildir.  
Önce non-live, trace-on, safety-clean kanıt üretilecek.

Productization kapalı.  
Internal eval kapalı.  
Fine-tuning kapalı.  
Live `8000` değişmeyecek.

---

# 1. Kesin Kurallar

Phase 24W boyunca:

- live `8000` değiştirilmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değiştirilmeyecek
- base/live collection overwrite edilmeyecek
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- scored full ablation answer-key gerektiriyorsa çalıştırılmayacak
- large traces commitlenmeyecek
- yalnız summary artifacts commitlenecek

Allowed:

```text
component-level design
non-live feature-flag candidate
non-live focused trace smoke
source identity diagnostics
selector diagnostics
answer contract/failure-class audit
safe local candidate branch
```

---

# 2. Current Evidence

## Known good

```text
Phase23R-E = 816.86 / 91
```

## Current trace-on base

```text
Phase24U BASE trace-on = 805.09 / 89
```

## Supplement ablation

```text
Phase24U source supplement ablation = 804.42 / 89
```

Conclusion:

```text
source_supplement drift alone does not restore Phase23R-E
component-level source_identity / selector behavior remains suspect
```

## Focus rows

Source-selection drift-like:

```text
KANUN-08
YON-05
```

Same-source but score/failure drift:

```text
KANUN-02
MULGA-04
YON-08
```

---

# 3. Phase 24W-A — Source Identity Component Design Audit

## Amaç

`source_identity.py` ve ddcadd2 sonrası source selection davranışını tasarım seviyesinde incelemek.

## Output

```text
reports/benchmark/phase_24W_A_source_identity_component_design_audit.md
reports/benchmark/phase_24W_A_source_identity_component_design_audit.csv
```

## Inputs

```text
api-gateway/src/rag/source_identity.py
api-gateway/src/rag/retrieval_orchestration.py
api-gateway/src/rag/article_span_selection.py
api-gateway/src/rag/source_supplements.py
Phase23R-E traces
Phase24U trace-on BASE traces
Phase24V row-level drift focus
```

## Fields

```text
component
function_or_rule
changed_since_phase23RE
commit_introduced
expected_behavior
current_behavior
risk_to_source_selection
rows_affected
feature_flag_possible
safe_recovery_design
```

## Must answer

```text
Which source_identity decisions changed after Phase23R-E?
Can behavior be gated without QID-specific logic?
Can source supplement logic be made support-only instead of primary-selection-affecting?
Can family/domain boosts be constrained to explicit query/source evidence?
```

## Commit

```text
Audit Phase 24W source identity component design
```

Push required.

---

# 4. Phase 24W-B — Focus Row Trace / Failure-Class Audit

## Amaç

Aynı kaynak seçildiği halde düşen satırlar ile source-selection drift satırlarını ayırmak.

## Rows

```text
KANUN-08
YON-05
KANUN-02
MULGA-04
YON-08
```

## Output

```text
reports/benchmark/phase_24W_B_focus_row_trace_failure_audit.md
reports/benchmark/phase_24W_B_focus_row_trace_failure_audit.csv
```

## Fields

```text
qid
phase23RE_score
phase24U_score
score_delta
same_selected_source
same_selected_span
same_claimed_family
same_claimed_identifier
phase23RE_failure_classes
phase24U_failure_classes
phase23RE_answer_mode
phase24U_answer_mode
phase23RE_evidence_roles
phase24U_evidence_roles
changed_trace_fields
likely_component
safe_recovery_action
```

## likely_component enum

```text
source_identity
article_span_selection
answer_contract_surface
answer_slot_completeness
scorer_proxy_only
trace_extraction
unknown
```

## Commit

```text
Audit Phase 24W focus row trace failure drift
```

Push required.

---

# 5. Phase 24W-C — Recovery Design

## Amaç

QID-specific olmayan, component-level recovery tasarımı üretmek.

## Output

```text
reports/benchmark/phase_24W_C_component_recovery_design.md
```

## Candidate designs

### Design 1 — Source identity support-only supplement gating

```text
Dynamic/source supplement candidates may support evidence bundle but must not override primary source identity unless:
- query explicitly matches source title/identifier/domain, and
- selected source family/domain is compatible, and
- source is present in candidate pool with adequate lexical/metadata support.
```

### Design 2 — Primary source preservation guard

```text
If original source_identity selection is high-confidence and source_key_v2/binding_key stable, later supplements must not rewrite primary family/identifier.
```

### Design 3 — Family/domain compatibility gate

```text
Boosts or aliases may only apply within compatible legal family/domain boundaries.
No CB_KARARNAME -> CB_YONETMELIK relabel.
No YONETMELIK -> KKY relabel unless alias field, not legal family, is used.
```

### Design 4 — Answer contract preservation for same-source rows

```text
When selected source/span is unchanged, answer contract surface should not degrade family/identifier/failure classes.
```

## Design must include

```text
feature flag name
default off/on decision
non-live test plan
focused smoke rows
rollback plan
no-QID-specific proof
```

## Commit

```text
Design Phase 24W component-level recovery
```

Push required.

---

# 6. Phase 24W-D — Non-Live Prototype, Only If Safe

Only run if Phase 24W-C identifies a safe systemic design.

## Rules

```text
non-live candidate only
feature-flagged
no live 8000 change
no base collection change
no prompt/model/top-k change
```

## Suggested flag

```text
ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY=true
```

## Output

```text
reports/benchmark/phase_24W_D_non_live_prototype_report.md
```

## Commit

```text
Prototype Phase 24W source identity recovery under feature flag
```

If not safe:

```text
reports/benchmark/phase_24W_D_prototype_not_run.md
```

Commit:

```text
Record Phase 24W prototype not run
```

---

# 7. Phase 24W-E — Focused Non-Live Smoke

Only run if D prototype exists.

## Runtime

Use non-live port.

## Rows

```text
KANUN-08
YON-05
KANUN-02
MULGA-04
YON-08
MULGA-01
MULGA-05
TEB-06
CBY-06
KANUN-12
YON-04
```

## Acceptance

```text
safety counters zero
contract_valid all
source_key_v2_collision = 0
binding_collision = 0
no regression in MULGA-01/MULGA-05/TEB-06
at least 2 focus rows improve OR component is not sufficient
```

## Output

```text
reports/benchmark/phase_24W_E_focused_non_live_smoke.md
```

## Commit

```text
Run Phase 24W focused non-live smoke
```

---

# 8. Phase 24W-F — Trace-On Full Candidate Benchmark, If Focused Smoke Passes

Only run if E passes.

## Minimum comparison

Compare against current trace-on BASE:

```text
current trace-on BASE = 805.09 / 89
```

## Target

```text
raw_score_proxy > 805.09
pass_proxy >= 89
safety counters zero
green_lane = PASS
wrong_document <= current
hallucinated_identifier <= current
```

## Output

```text
reports/benchmark/phase_24W_F_trace_on_full_candidate_summary.md
reports/benchmark/phase_24W_F_delta_vs_phase24U_base.md
reports/benchmark/phase_24W_F_green_lane_summary.md
```

## Commit

```text
Run Phase 24W trace-on full candidate benchmark
```

If not run:

```text
reports/benchmark/phase_24W_F_full_candidate_not_run.md
```

---

# 9. Phase 24W-G — Recovery Decision

## Output

```text
reports/benchmark/phase_24W_G_recovery_decision.md
```

## Decision options

### Option A — Component recovery improves and is safe

```text
Open Phase24X controlled recovery integration brief.
No live cutover yet.
```

### Option B — Prototype safe but insufficient

```text
Keep as diagnostic.
Continue targeted component analysis.
```

### Option C — No safe prototype

```text
Freeze runtime recovery line.
Return to external residual/legal/scorer closure.
```

### Option D — Same-source rows are scorer/contract-only

```text
Open answer contract / scorer proxy audit.
No source_identity fix.
```

## Commit

```text
Record Phase 24W recovery decision
```

Push required.

---

# 10. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24W_component_recovery_report.md
```

Must include:

1. commit SHA list
2. source identity design audit
3. focus row trace/failure audit
4. recovery design
5. prototype run/not-run
6. focused smoke result
7. full candidate result if run
8. recovery decision
9. productization decision
10. internal eval decision
11. fine-tuning decision
12. final live 8000 state
13. next recommended phase

## Commit

```text
Report Phase 24W component recovery outcome
```

Push required.

---

# 11. Stop Rules

Stop/revert prototype if:

```text
live 8000 would be modified
QID-specific logic required
benchmark answer key required
safety counters non-zero
contract invalid appears
source_key_v2 or binding collision appears
MULGA-01/MULGA-05/TEB-06 regress
large traces staged
```

---

## Final Note

Phase24V localized the remaining drift but did not prove one commit.

Phase24W may prototype only feature-flagged, non-live, component-level recovery. No live change.
