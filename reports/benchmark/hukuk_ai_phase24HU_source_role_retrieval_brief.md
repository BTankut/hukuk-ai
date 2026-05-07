# Hukuk-AI — Phase 24HU KANUN-08 Source-Role Retrieval and Secondary-Family Recall Brief

## Karar

Phase 24HT tamamlandı.

Sonuç:

```text
KANUN-08 family/source identity iyileşti.
Önce: TÜRK BORÇLAR KANUNU / TBK m.255
Şimdi: TÜKETİCİNİN KORUNMASI HAKKINDA KANUN / TKHK m.18
Score: 3.25 -> 3.93
Hâlâ FAIL.
```

Phase 24HT raporu açıkça şunu gösteriyor:

```text
Sorun artık same-family source identity değil.
Kalan sorun source-role retrieval, secondary-family recall ve answer-slot selection.
```

Kritik residual:

```text
pre_filter_family_set = ["kanun"] secondary YONETMELIK evidence path’i engelliyor.
Primary KANUN ve supporting YONETMELIK rolleri trace’te ayrı temsil edilmiyor.
Exception slot ilgisiz TBK/private-law span ile doluyor.
```

Sıradaki faz:

```text
Phase 24HU — KANUN-08 Source-Role Retrieval and Secondary-Family Recall
```

Bu faz live cutover değildir.  
Productization değildir.  
Internal eval değildir.  
Fine-tuning kapalıdır.  
Live `8000` değişmeyecek.

---

# 1. Kesin Kurallar

Phase 24HU boyunca:

- live `8000` değiştirilmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- base/live collection overwrite yok
- benchmark answer key kullanılmayacak
- QID-specific runtime branch yok
- large trace commit yok
- yalnız non-live candidate ve summary artifacts

Forbidden:

```text
hardcoded KANUN-08
hardcoded expected answer
hardcoded TKHK or specific yönetmelik title unless generally inferred from retrieved/source metadata
broad top-k increase
prompt hack
LLM fine-tuning
```

---

# 2. Current Evidence

## Primary source now improved

```text
selected_source = TÜKETİCİNİN KORUNMASI HAKKINDA KANUN / TKHK m.18
selector_reason = same_family_domain_identity_lock
source_identity_margin over TBK = 42.0305
```

## Remaining blocker

```text
Exception/supporting evidence missing or wrong.
secondary_types=YONETMELIK route is blocked by pre_filter_family_set=["kanun"].
Answer-slot exception evidence is filled with unrelated TBK supporting span.
```

---

# 3. Phase 24HU-A — Source-Role Retrieval Audit

## Amaç

KANUN-08 için primary law ve supporting regulation evidence paths nasıl kuruluyor, nerede kesiliyor belirlemek.

## Output

```text
reports/benchmark/phase_24HU_A_source_role_retrieval_audit.md
reports/benchmark/phase_24HU_A_source_role_retrieval_audit.csv
```

## Fields

```text
qid
query_text
primary_family_filter
secondary_types_detected
secondary_types_applied
pre_filter_family_set
primary_candidates
supporting_candidates
yonetmelik_candidates_present
yonetmelik_candidates_filtered
candidate_rank
candidate_source_family
candidate_title
candidate_article
candidate_role
candidate_selected
candidate_rejected_reason
slot_target
```

## Must answer

```text
secondary_types=YONETMELIK nerede üretiliyor?
pre_filter_family_set neden yalnız ["kanun"] kalıyor?
YONETMELIK candidates retrieval top-k'de var mı?
Varsa neden selector/evidence bundle'a girmiyor?
Yoksa family-filter mı, retrieval recall mı sorun?
Exception slot neden TBK/private-law span ile doluyor?
```

## Commit

```text
Audit Phase 24HU KANUN-08 source-role retrieval
```

Push required.

---

# 4. Phase 24HU-B — Secondary-Family Recall Design

## Amaç

Primary KANUN + supporting YONETMELIK rollerini QID-specific olmadan aynı evidence bundle’a sokacak tasarımı yapmak.

## Output

```text
reports/benchmark/phase_24HU_B_secondary_family_recall_design.md
```

## Design principles

```text
Primary family filter may remain KANUN.
Detected secondary_types may add supporting recall lanes, not replace primary source.
Supporting family candidates must be role-tagged as supporting_rule / exception_rule / implementation_detail.
Secondary family recall must require query/source-role signal.
Secondary candidates cannot overwrite primary source identity.
```

## Required rules

```text
If primary source family = KANUN
AND query/task needs implementation/exception/procedure detail
AND secondary_types includes YONETMELIK
THEN:
  run scoped supporting-family retrieval lane for YONETMELIK
  tag results as supporting/exception evidence
  do not rewrite primary claimed family
```

## Suggested feature flag

```text
ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true
```

## Trace fields to add

```text
secondary_family_recall_applied
secondary_family_recall_types
secondary_family_recall_candidates
secondary_family_recall_selected
secondary_family_recall_reason
primary_source_role
supporting_source_roles
exception_slot_source_key
exception_slot_role
```

## Commit

```text
Design Phase 24HU secondary-family recall
```

Push required.

---

# 5. Phase 24HU-C — Answer-Slot Exception Evidence Guard

## Amaç

Exception slot’un ilgisiz same-family/private-law span ile dolmasını engellemek.

## Output

```text
reports/benchmark/phase_24HU_C_exception_slot_guard_design.md
```

## Required systemic rule

```text
Exception/procedure slot must be filled by evidence whose role/domain matches the requested legal task.
A same-family KANUN span cannot fill exception slot solely because it is semantically similar.
If supporting YONETMELIK evidence exists with stronger domain match, prefer it for exception/procedure slot.
If no suitable supporting evidence exists, mark slot missing instead of filling with unrelated law.
```

## Implementation surface

Likely:

```text
api-gateway/src/rag/evidence_bundle.py
api-gateway/src/rag/answer_slots.py
api-gateway/src/rag/article_span_selection.py
api-gateway/src/rag/runtime_trace.py
```

Avoid unless necessary:

```text
answer_synthesis.py
```

## Commit

```text
Design Phase 24HU exception slot evidence guard
```

Push required.

---

# 6. Phase 24HU-D — Feature-Flagged Non-Live Prototype

Only run if B/C design is systemic and safe.

## Runtime

Non-live candidate only, for example:

```text
http://127.0.0.1:8043/v1
```

## Feature flags

```text
ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true
ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true
ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=true
```

## Output

```text
reports/benchmark/phase_24HU_D_non_live_prototype_report.md
```

## Tests

Add focused tests:

```text
secondary_family_recall_does_not_rewrite_primary_family
supporting_yonetmelik_can_fill_exception_slot_for_kanun_primary
unrelated_same_family_law_does_not_fill_exception_slot
no_qid_specific_phase24hu_logic
critical_guard_rows_do_not_regress
```

## Commit

```text
Prototype Phase 24HU secondary-family recall and exception guard
```

If unsafe:

```text
reports/benchmark/phase_24HU_D_prototype_not_run.md
```

Commit:

```text
Record Phase 24HU prototype not run
```

---

# 7. Phase 24HU-E — Focused Non-Live Smoke

Only run if D prototype exists.

## Target rows

```text
KANUN-08
```

## Guard rows

```text
TEB-04
TUZUK-05
YON-05
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

## Acceptance

```text
contract_valid all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0

KANUN-08 score improves materially or PASS
KANUN-08 primary source remains TKHK / KANUN
KANUN-08 exception/supporting slot is not filled by unrelated TBK/private-law span
supporting YONETMELIK evidence appears if available
TEB-04 remains PASS
TUZUK-05 remains PASS / no arbitrary concrete tüzük
YON-05 remains PASS
MULGA-01/MULGA-05/TEB-06 no regression
TUZUK-04 not active-current-law claim
```

## Output

```text
reports/benchmark/phase_24HU_E_focused_non_live_smoke_report.md
```

## Commit

```text
Run Phase 24HU focused non-live smoke
```

---

# 8. Optional Full Candidate Benchmark

Only run if focused smoke passes and KANUN-08 improves materially.

## Minimum comparison

Compare to current trace-on BASE:

```text
BASE trace-on = 805.09 / 89
```

Candidate must satisfy:

```text
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
raw_score_proxy >= current trace-on base
pass_proxy >= current trace-on base
wrong_document <= current trace-on base
hallucinated_identifier <= current trace-on base
```

## Output

```text
reports/benchmark/phase_24HU_F_full_candidate_summary.md
reports/benchmark/phase_24HU_F_delta_vs_phase24U_base.md
reports/benchmark/phase_24HU_F_green_lane_summary.md
```

## Commit

```text
Run Phase 24HU full candidate benchmark
```

If not run:

```text
reports/benchmark/phase_24HU_F_full_candidate_not_run.md
```

---

# 9. Phase 24HU-G — Recovery Decision

## Output

```text
reports/benchmark/phase_24HU_G_recovery_decision.md
```

## Decision options

### Option A — KANUN-08 recovered safely

```text
Open controlled full-candidate validation / integration brief.
No live cutover yet.
```

### Option B — Supporting recall improves but full insufficient

```text
Keep diagnostic candidate.
Continue answer-slot/evidence-role recovery.
```

### Option C — Secondary recall not sufficient

```text
Open document-level retrieval/corpus source review for KANUN-08.
No runtime integration.
```

### Option D — Needs scorer/rubric review

```text
No runtime change.
Prepare scorer/legal review packet.
```

## Commit

```text
Record Phase 24HU recovery decision
```

---

# 10. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24HU_source_role_retrieval_report.md
```

Must include:

1. commit SHA list
2. source-role retrieval audit
3. secondary-family recall design
4. exception-slot guard design
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
Report Phase 24HU source-role retrieval outcome
```

---

# 11. Stop Rules

Stop/revert prototype if:

```text
live 8000 would be modified
QID-specific logic required
benchmark answer key required
contract invalid appears
unsupported confident appears
source_key_v2 or binding collision appears
TEB-04/TUZUK-05/YON-05 regress
MULGA-01/MULGA-05/TEB-06 regress
primary KANUN identity for KANUN-08 regresses away from TKHK
large traces staged
```

---

## Final Note

Phase24HT fixed primary KANUN identity.

Phase24HU should recover the supporting/exception evidence path without rewriting primary source identity.
