# Hukuk-AI — Phase 24O Autonomous Residual Source-Identity / Selector Remediation Brief

## Master Planner Kararı

Phase 24N sonucuna göre avukat/source dönüşleri geçerli, raw/source materyalleri doğrulandı ve shadow backfill teknik olarak kuruldu. Ancak residual hedeflerde iyileşme üretmedi.

Kritik sonuç:

```text
Sorun artık raw source yokluğu değil.
Sorun source identity, selector/reranker, document-family boundary ve temporal/current-law claim policy tarafında.
```

Bu nedenle Phase 24O daha geniş ama hâlâ güvenli bir autonomous remediation programıdır.

Kod asistanı bu brief kapsamında daha geniş inisiyatif alabilir:

- audit yapabilir
- shadow-only runtime/code fix uygulayabilir
- selector/source identity logic tasarlayıp uygulayabilir
- targeted smoke / guard smoke / full shadow benchmark çalıştırabilir
- başarısız fix’i revert edebilir
- blocker’ları review packet’e düşürebilir
- final rapor üretebilir

Kapalı alanlar:

```text
live 8000 değişikliği
productization
public serving
internal eval açma
fine-tuning
model/prompt değişikliği
broad retrieval/top-k değişikliği
QID-specific runtime branch
benchmark answer key kullanımı
```

Live `8000` benchmark-only stabil kalacak.

---

# 0. Current State

## Live benchmark-only runtime

```text
API = http://127.0.0.1:8000/v1
lane = phase22f_s7_full_shadow
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
approval_scope = benchmark_only
status = healthy
```

## Current benchmark baseline

```text
raw_score_proxy = 816.86
pass_proxy = 91/100
wrong_family = 6
wrong_document = 4
hallucinated_identifier = 4
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

## Remaining residuals

```text
KANUN-12
KKY-03
YON-04
TUZUK-04
TUZUK-05
TEB-04
CBY-04
CBY-06
KKY-01
```

---

# 1. Global Safety Rules

Allowed without additional approval:

```text
shadow-only code changes
source identity / selector / reranker deterministic fixes
answer contract / family-surface deterministic fixes
evidence bundle / temporal policy deterministic fixes
targeted smoke
guard smoke
full shadow benchmark after gates pass
revert failed implementation
diagnostic reports
review packets
```

Forbidden without separate master approval:

```text
live 8000 cutover or config change
public serving
productization
internal_eval lane opening
fine-tuning
model change
prompt strategy change
broad retrieval/top-k increase
base/live collection overwrite
QID-specific runtime rule
benchmark answer key use
```

If a fix fails targeted gates, revert or isolate it. Do not keep failed behavior as active candidate.

---

# 2. Execution Strategy

Phase 24O should not stop at the first closed gate.

Use this decision pattern:

```text
If safe systemic fix exists:
  implement shadow-only
  run targeted smoke
  if passes, run guard smoke
  if passes, run full shadow benchmark
  if fails, revert or isolate and continue next workstream

If safe fix does not exist:
  create blocker/review packet
  continue next workstream

If blocker needs source/legal/scorer decision:
  document exact needed decision
  exclude from runtime patch
  continue next workstream
```

---

# 3. Workstream A — Source Identity / Selector Residuals

## Target rows

```text
KANUN-12
KKY-03
YON-04
```

## Problem

Confirmed sources and spans exist, but selector still chooses wrong document/source.

## Required audit

Output:

```text
reports/benchmark/phase_24O_A_source_identity_selector_audit.md
reports/benchmark/phase_24O_A_source_identity_selector_audit.csv
```

Fields:

```text
qid
expected_source
current_selected_source
current_selected_family
candidate_pool_contains_expected
metadata_lookup_contains_expected
dense_topk_contains_expected
rerank_list_contains_expected
expected_candidate_rank
why_expected_not_selected
wrong_selected_reason
safe_selector_fix_available
proposed_fix_type
```

## Possible systemic fixes

### KANUN-12

```text
Primary KANUN source should outrank technical regulation if query/legal review identifies 5651 as primary law.
Supporting regulation may remain supporting evidence.
```

### KKY-03

```text
Confirmed source family is YONETMELIK.
Do not force KKY if legal review says YONETMELIK.
Prefer exact BDDK information systems regulation when query contains banking / information systems / electronic banking signals.
```

### YON-04

```text
Prefer KVKK deletion/destruction/anonymization regulation when query contains silme / yok etme / anonim / kişisel veri imha signals.
6698 m.7 may support but should not replace the regulation as primary procedural source.
```

## Implementation surface

Primary:

```text
api-gateway/src/rag/source_identity.py
api-gateway/src/rag/article_span_selection.py
api-gateway/src/rag/retrieval_orchestration.py
api-gateway/src/rag/runtime_trace.py
```

Avoid unless required:

```text
answer_synthesis.py
answer_slots.py
```

## Commit

```text
Audit and implement Phase 24O-A source identity selector fixes
```

---

# 4. Workstream B — TUZUK-04 Historical / Current-Law Temporal Guard

## Target row

```text
TUZUK-04
```

## Problem

Radyasyon Güvenliği Tüzüğü is historical/repealed and must not be claimed as standalone active current-law authority.

## Required audit

Output:

```text
reports/benchmark/phase_24O_B_tuzuk04_temporal_guard_audit.md
```

Must answer:

```text
Is selected source historical/repealed?
Is query current-law framed?
Is current-law supporting source present?
Is answer claiming old tüzük as active?
Can system safely answer with historical caveat + insufficient current-law evidence?
```

## Allowed fix

If audit supports:

```text
If source effective_state = repealed/historical
AND query has current-law/currentness intent
AND no confirmed current-law companion source is present
THEN answer must not claim active applicability.
It should produce qualified/insufficient-current-law answer with historical source caveat.
```

No QID-specific logic.

## Implementation surface

```text
answer_synthesis.py
answer_slots.py
evidence_bundle.py
runtime_trace.py
```

## Commit

```text
Implement Phase 24O-B repealed tüzük current-law guard
```

---

# 5. Workstream C — CBY-06 Amendment Span / Completeness

## Target row

```text
CBY-06
```

## Problem

Legal/scorer review says 03.04.2026 / RG 33213 / Karar 11153 amendment and m.11 added paragraph matter. Current answer is incomplete.

## Required audit

Output:

```text
reports/benchmark/phase_24O_C_cby06_amendment_span_audit.md
```

Check:

```text
Is amended m.11 source in corpus?
Is 2026 amendment source in catalog/Milvus?
Does selected evidence contain added paragraph?
Does answer miss fact slots?
Is corpus backfill required?
```

## Allowed paths

### If source/span exists

Implement deterministic article/span preference for amended m.11.

### If source/span missing

Do not fake. Create source acquisition/backfill packet:

```text
reports/benchmark/phase_24O_C_cby06_source_acquisition_packet.md
```

## Commit

```text
Audit Phase 24O-C CBY-06 amendment span completeness
```

If safe implementation:

```text
Implement Phase 24O-C CBY-06 amended span selection
```

---

# 6. Workstream D — CBY-04 / KKY-01 Taxonomy Compatibility

## Target rows

```text
CBY-04
KKY-01
```

## Problem

These are taxonomy/scorer compatibility issues.

## Rule

Do not implement runtime fix unless it is systemic and legally confirmed.

## Required audit

Output:

```text
reports/benchmark/phase_24O_D_taxonomy_compatibility_audit.md
```

Check:

```text
Can CBK supporting source remain supporting while primary CB_YONETMELIK is selected?
Can KKY benchmark bucket accept YONETMELIK legal family with issuer-based alias?
Would runtime relabel be legally misleading?
```

## Allowed fix

Only if systemic:

```text
supporting_source_family != primary_source_family should not overwrite primary claimed family
issuer-based alias may be recorded separately from legal source_family
```

Do not relabel a CB_KARARNAME as CB_YONETMELIK.

## Commit

```text
Audit Phase 24O-D taxonomy compatibility residuals
```

Optional implementation commit only if safe:

```text
Implement Phase 24O-D taxonomy compatibility guard
```

---

# 7. Workstream E — TEB-04 Scorer / Materialization Residual

## Target row

```text
TEB-04
```

## Problem

KDV Genel Uygulama Tebliği source identity improved but auto-fail persists. Likely scorer/rubric or section-level materialization issue.

## Required audit

Output:

```text
reports/benchmark/phase_24O_E_teb04_scorer_materialization_audit.md
```

Check:

```text
Does selected source = KDV Genel Uygulama Tebliği?
Does selected span include required section, not m.0 only?
Is I/C-2.1.3 or relevant tevkifat/iade section materialized?
Is auto_fail triggered because article/section is m.0?
Can section-level materialization fix this?
Or is scorer/rubric review required?
```

## Allowed paths

### If section materialization exists

Improve section/table/span selection for TEBLIGLER.

### If missing

Prepare section materialization plan.

### If scorer issue

Prepare scorer/rubric acceptance packet. No runtime patch.

## Commit

```text
Audit Phase 24O-E TEB-04 scorer materialization residual
```

Optional implementation if safe:

```text
Implement Phase 24O-E TEB section span selection
```

---

# 8. Workstream F — TUZUK-05 Stop-Loss

## Target row

```text
TUZUK-05
```

## Decision

TUZUK-05 remains:

```text
source_not_found
needs_more_review
benchmark_ambiguous
```

No runtime fix.  
No synthetic source.  
No shadow backfill.

## Output

```text
reports/benchmark/phase_24O_F_tuzuk05_stop_loss.md
```

Commit:

```text
Record Phase 24O-F TUZUK-05 stop-loss
```

---

# 9. Combined Targeted Smoke

After any safe implementation workstreams, run a targeted smoke.

## Targeted rows

```text
KANUN-12
KKY-03
YON-04
TUZUK-04
CBY-06
CBY-04
KKY-01
TEB-04
```

## Guard rows

```text
MULGA-01
MULGA-05
TEB-06
CBG-01
CBKAR-08
UY-01
YON-05
KANUN-03
```

## Acceptance

```text
contract_valid = all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
MULGA-01/MULGA-05/TEB-06 remain PASS
TUZUK-04 not claimed as active current law
at least 2 targeted residual rows improve OR document no-op
```

Output:

```text
reports/benchmark/phase_24O_targeted_smoke_report.md
```

Commit:

```text
Run Phase 24O targeted residual smoke
```

---

# 10. Full Shadow Benchmark

Only run if targeted smoke passes.

## Minimum gate

```text
raw_score_proxy >= 816
pass_proxy >= 91
wrong_family <= 6
wrong_document <= 4
hallucinated_identifier <= 4
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

Preferred:

```text
pass_proxy > 91
or wrong_family < 6
or wrong_document < 4
or hallucinated_identifier < 4
```

Output:

```text
reports/benchmark/phase_24O_full_shadow_benchmark_summary.md
reports/benchmark/phase_24O_delta_vs_phase23RE.md
reports/benchmark/phase_24O_green_lane_summary.md
```

Commit:

```text
Run Phase 24O full shadow benchmark
```

If not run:

```text
reports/benchmark/phase_24O_full_shadow_not_run.md
```

---

# 11. Internal Eval Readiness Recheck

Always run after targeted/full decision.

Output:

```text
reports/benchmark/phase_24O_internal_eval_readiness_recheck.md
```

Decision options:

```text
internal_eval_ready
limited_legal_review_eval_only
not_ready_continue_residual_closure
```

Do not open internal eval unless explicitly ready.

Commit:

```text
Recheck Phase 24O internal eval readiness
```

---

# 12. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24O_autonomous_residual_remediation_report.md
```

Must include:

1. commit SHA list
2. workstream A result
3. workstream B result
4. workstream C result
5. workstream D result
6. workstream E result
7. workstream F result
8. targeted smoke result
9. full shadow benchmark result or not-run reason
10. internal eval decision
11. productization decision
12. fine-tuning decision
13. final live 8000 state
14. next human decision if any

Commit:

```text
Report Phase 24O autonomous residual remediation outcome
```

---

# 13. Stop Rules

Stop/revert implementation branch if:

```text
MULGA-01 regresses
MULGA-05 regresses
TEB-06 regresses
contract invalid appears
unsupported confident appears
source_key_v2 collision appears
binding collision appears
TUZUK-04 is claimed active current law
live 8000 modified
base collection modified
QID-specific branch introduced
```

---

## Final Note

This is a broader autonomous task set.

It should make progress without repeatedly returning to the master planner, but only within shadow/runtime-safe boundaries.

If a workstream cannot be fixed safely, document it and continue the next workstream.
