# Hukuk-AI — Phase 24X Source Identity Candidate-Selection Recovery Continuation Brief

## Karar

Phase 24W tamamlandı.

Repo kararı:

```text
Option B — prototype safe but insufficient
```

Phase24W prototipi güvenliydi fakat `KANUN-08` ve `YON-05` source-selection drift satırlarını düzeltmedi.

Sonuç:

```text
Sorun yalnızca _chunk_matches_selected_source_key içindeki title metadata eşleşmesi değil.
Sıradaki teknik hat:
  metadata-first candidate selection
  source identity rerank trace
  family/domain compatibility
```

Ayrıca aynı kaynak seçildiği halde skor/failure-class düşen satırlar ayrı hat olarak ele alınmalı:

```text
KANUN-02
MULGA-04
YON-08
```

Bu nedenle Phase 24X iki ana workstream içerir:

1. `KANUN-08`, `YON-05` için source identity candidate-selection recovery.
2. `KANUN-02`, `MULGA-04`, `YON-08` için answer contract / trace extraction / slot completeness audit.

Bu faz live fix değildir.  
Önce trace-only ve non-live diagnostic yapılacak.  
Güvenli systemic fix bulunursa feature-flagged non-live prototype denenebilir.

Productization kapalı.  
Internal eval kapalı.  
Fine-tuning kapalı.  
Live `8000` değişmeyecek.

---

# 1. Kesin Kurallar

Phase 24X boyunca:

- live `8000` değiştirilmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- base/live collection overwrite yok
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- large trace files commitlenmeyecek
- full benchmark yalnız focused smoke geçerse ve measurement-only scorer izni varsa
- başarısız prototype kalıcı bırakılmayacak

Allowed:

```text
trace diagnostics
candidate/rerank audit
family/domain compatibility design
feature-flagged non-live prototype
focused non-live smoke
reporting
```

---

# 2. Current Evidence

## Live runtime

```text
lane = phase22f_s7_full_shadow
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
model = hukuk-ai-poc
live_modified_by_phase24W = false
```

## Phase24W result

```text
prototype = safe but insufficient
primary source-selection rows improved = 0/2
KANUN-08 remained wrong selected source
YON-05 remained wrong selected source
```

## Row split

Source-selection drift:

```text
KANUN-08
YON-05
```

Same-source / answer-contract or slot drift:

```text
KANUN-02
MULGA-04
YON-08
```

---

# 3. Workstream A — Metadata-First Candidate Selection Audit

## Amaç

`KANUN-08` ve `YON-05` için expected source neden candidate/metadata/rerank aşamasında seçilmiyor, bunu trace-level belirlemek.

## Output

```text
reports/benchmark/phase_24X_A_metadata_first_candidate_selection_audit.md
reports/benchmark/phase_24X_A_metadata_first_candidate_selection_audit.csv
```

## Rows

```text
KANUN-08
YON-05
```

## Fields

```text
qid
query_text
phase23RE_selected_source
current_selected_source
expected_source_if_known
metadata_lookup_candidates
metadata_lookup_expected_present
dense_topk_expected_present
dense_topk_expected_rank
rerank_list_expected_present
rerank_expected_rank
source_identity_top_scores
selected_source_reason
wrong_source_reason
family_domain_compatibility_violation
safe_recovery_candidate
```

## Must answer

```text
Expected source metadata lookup'a giriyor mu?
Dense top-k'de var mı?
Rerank listesinde var mı?
Selected wrong source hangi sinyal yüzünden kazanıyor?
Family/domain compatibility gate olsaydı yanlış kaynak elenir miydi?
```

## Commit

```text
Audit Phase 24X metadata-first candidate selection
```

Push required.

---

# 4. Workstream B — Source Identity Rerank Trace Audit

## Amaç

Source identity score/rerank path’inde hangi sinyalin yanlış source’u öne aldığını belirlemek.

## Output

```text
reports/benchmark/phase_24X_B_source_identity_rerank_trace_audit.md
reports/benchmark/phase_24X_B_source_identity_rerank_trace_audit.csv
```

## Fields

```text
qid
candidate_source_key
candidate_title
candidate_family
candidate_identifier
candidate_score_lexical
candidate_score_dense
candidate_score_metadata
candidate_score_family
candidate_score_domain
candidate_score_final
candidate_selected
candidate_should_be_filtered
filter_reason
rerank_reason
```

## Commit

```text
Audit Phase 24X source identity rerank trace
```

Push required.

---

# 5. Workstream C — Family / Domain Compatibility Design

## Amaç

Yanlış source promotion'ı QID-specific olmadan engelleyecek systemic family/domain compatibility gate tasarlamak.

## Output

```text
reports/benchmark/phase_24X_C_family_domain_compatibility_design.md
```

## Design principles

```text
Query legal family/domain signals must constrain source promotion.
Supporting source cannot overwrite primary source identity.
Cross-family promotion requires explicit legal relation metadata.
Identifier/title lexical similarity alone cannot override incompatible family/domain.
Issuer/domain alias may be separate from legal source_family.
```

## Required examples

Use at least:

```text
KANUN-08
YON-05
CBY-04
KKY-01
TEB-04
```

## Design output

```text
compatibility_gate_rules
allowed_cross_family_relations
blocked_cross_family_relations
supporting_source_policy
primary_source_preservation_policy
trace_fields_to_add
feature_flag_name
```

## Suggested flag

```text
ENABLE_PHASE24X_FAMILY_DOMAIN_COMPATIBILITY_GATE=true
```

## Commit

```text
Design Phase 24X family domain compatibility gate
```

Push required.

---

# 6. Workstream D — Feature-Flagged Non-Live Prototype

Only run if Workstream C produces a safe systemic design.

## Rules

```text
non-live only
feature flag default false
no live 8000 change
no prompt/model/top-k change
no QID-specific strings
```

## Implementation surface

Likely:

```text
api-gateway/src/rag/source_identity.py
api-gateway/src/rag/retrieval_orchestration.py
api-gateway/src/rag/runtime_trace.py
```

Avoid unless necessary:

```text
answer_synthesis.py
answer_slots.py
```

## Output

```text
reports/benchmark/phase_24X_D_non_live_prototype_report.md
```

## Commit

```text
Prototype Phase 24X family domain compatibility gate
```

If unsafe:

```text
reports/benchmark/phase_24X_D_prototype_not_run.md
```

Commit:

```text
Record Phase 24X prototype not run
```

---

# 7. Workstream E — Focused Non-Live Smoke

Only run if D prototype exists.

## Runtime

Use non-live candidate port.

## Rows

Source-selection target:

```text
KANUN-08
YON-05
```

Same-source audit rows:

```text
KANUN-02
MULGA-04
YON-08
```

Guards:

```text
MULGA-01
MULGA-05
TEB-06
CBY-06
KANUN-12
YON-04
CBG-01
CBKAR-08
```

## Acceptance

```text
contract_valid all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
MULGA-01/MULGA-05/TEB-06 no regression
at least one of KANUN-08/YON-05 improves OR prove source identity not sufficient
```

## Output

```text
reports/benchmark/phase_24X_E_focused_non_live_smoke.md
```

## Commit

```text
Run Phase 24X focused non-live smoke
```

---

# 8. Workstream F — Same-Source Answer Contract / Slot Drift Audit

## Amaç

`KANUN-02`, `MULGA-04`, `YON-08` aynı source seçimine rağmen neden düştü, source_identity dışı nedenleri ayırmak.

## Output

```text
reports/benchmark/phase_24X_F_same_source_answer_contract_audit.md
reports/benchmark/phase_24X_F_same_source_answer_contract_audit.csv
```

## Fields

```text
qid
phase23RE_score
current_score
same_selected_source
same_selected_span
same_claimed_family
same_claimed_identifier
phase23RE_answer_mode
current_answer_mode
phase23RE_slots
current_slots
missing_required_content_signal_changed
partial_grounding_changed
claim_surface_changed
confidence_changed
likely_component
safe_next_action
```

## likely_component enum

```text
answer_contract_surface
answer_slot_completeness
evidence_bundle_role_assignment
claim_verifier
scorer_proxy_only
unknown
```

## Commit

```text
Audit Phase 24X same-source answer contract drift
```

Push required.

---

# 9. Optional Full Candidate Benchmark

Only run if focused smoke passes and prototype improves at least one primary source-selection row.

## Target

Compare to current trace-on BASE:

```text
BASE trace-on = 805.09 / 89
```

## Acceptance

```text
raw_score_proxy > 805.09
pass_proxy >= 89
wrong_document <= current
hallucinated_identifier <= current
safety counters zero
green_lane = PASS
```

## Output

```text
reports/benchmark/phase_24X_full_candidate_summary.md
reports/benchmark/phase_24X_delta_vs_phase24U_base.md
reports/benchmark/phase_24X_green_lane_summary.md
```

## Commit

```text
Run Phase 24X full candidate benchmark
```

If not run:

```text
reports/benchmark/phase_24X_full_candidate_not_run.md
```

---

# 10. Decision Report

## Output

```text
reports/benchmark/phase_24X_recovery_decision.md
```

## Options

### Option A — Compatibility gate helps

```text
Open Phase24Y controlled integration brief.
```

### Option B — Source identity not sufficient

```text
Open answer contract / evidence role recovery phase.
```

### Option C — No safe systemic fix

```text
Freeze runtime recovery line.
Continue only external residual closure.
```

### Option D — Need scorer/rubric review

```text
Prepare scorer/rubric packet.
No runtime change.
```

## Commit

```text
Record Phase 24X recovery decision
```

Push required.

---

# 11. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24X_source_identity_recovery_report.md
```

Must include:

1. commit SHA list
2. metadata-first candidate selection audit
3. source identity rerank trace audit
4. family/domain compatibility design
5. prototype run/not-run
6. focused smoke result
7. same-source answer contract audit
8. full candidate result if run
9. recovery decision
10. productization decision
11. internal eval decision
12. fine-tuning decision
13. final live 8000 state
14. next recommended phase

## Commit

```text
Report Phase 24X source identity recovery outcome
```

Push required.

---

# 12. Stop Rules

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

Phase24W proved the first narrow prototype was safe but insufficient.

Phase24X should inspect the earlier source identity pipeline:
metadata candidate selection, rerank scoring, and family/domain compatibility.
