# Hukuk-AI — Phase 24HS Systemic Remediation After Option C Targeted Smoke Failure

## Karar

Phase 24HR Option C targeted smoke çalıştırıldı.

Sonuç:

```text
technical_status = PASS
quality_gate_status = FAIL
raw_score_proxy = 10.45 / 40
pass_proxy = 0 / 4
answer_contract_invalid = 0
unsupported_confident_answer = 0
source_key_v2_collision = 0
binding_collision = 0
live_8000_modified = false
```

Target rows:

```text
TEB-04
TUZUK-05
KANUN-08
YON-05
```

Hepsi quality gate açısından FAIL.

Bu nedenle:

```text
Option D full trace-on candidate benchmark çalıştırılmayacak.
Productization kapalı.
Internal eval kapalı.
Fine-tuning kapalı.
Live 8000 değişmeyecek.
```

Sıradaki faz:

```text
Phase 24HS — Systemic Remediation After Option C Failure
```

Bu fazın amacı, Option C’de görülen dört failure pattern için QID-specific olmayan sistemik düzeltme tasarlamak ve non-live targeted smoke ile doğrulamaktır.

---

# 1. Kesin Kurallar

Phase 24HS boyunca:

- live `8000` değişmeyecek
- Option D full benchmark yok
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- base/live collection overwrite yok
- benchmark answer key kullanılmayacak
- QID-specific runtime branch yok
- large trace commit yok
- yalnız non-live candidate ve summary artifacts

---

# 2. Option C Failure Summary

## TEB-04

```text
selected source = KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ
source_key = 19631
failure = active KDV GUT treated as MULGA/repealed
auto_fail_triggered
wrong_family
hallucinated_identifier
missing_required_content_signal
```

Interpretation:

```text
Source selection is close/correct, but temporal/source-family policy is wrong.
Active TEBLIGLER source must not be rewritten as MULGA/repealed.
```

---

## TUZUK-05

```text
selected source = GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK
failure = concrete irrelevant tüzük selected as primary
expected behavior = human-reviewed general hierarchy handling / stop-loss
```

Interpretation:

```text
Stop-condition failed.
When exact source is benchmark_ambiguous / needs_more_review, system must not choose a concrete unrelated tüzük as primary.
```

---

## KANUN-08

```text
selected source = ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN TÜKETİCİ HAKLARI YÖNETMELİĞİ
failure = wrong family / wrong document
```

Interpretation:

```text
Source identity / family-domain compatibility failure.
A regulation source is outranking expected law/source family.
```

---

## YON-05

```text
selected source = İMAR KANUNU
failure = wrong_family / hallucinated_identifier / partial grounding
```

Interpretation:

```text
Family/domain compatibility failure in the opposite direction.
KANUN source is overwriting expected YONETMELIK/procedural source.
```

---

# 3. Workstream A — TEB Active Source Temporal Guard

## Amaç

Active TEBLIGLER source’un MULGA/repealed claim surface’e yanlış kaymasını engellemek.

## Output

```text
reports/benchmark/phase_24HS_A_teb_active_temporal_guard_audit.md
```

## Audit questions

```text
Why did source 19631 get claimed as MULGA/repealed?
Which temporal policy produced repealed surface?
Was source effective_state active/amended?
Was relation_chain_expansion_applied incorrectly?
Was historical_claim_surface_allowed incorrectly true?
Was claim_family_rewrite_allowed incorrectly true?
```

## Required systemic rule

```text
If selected source family = TEBLIGLER
AND effective_state is active/amended/unknown_non_repealed
AND no explicit repeal relation exists
THEN:
  claim_family must remain TEBLIGLER
  source must not be claimed MULGA/repealed
  temporal historical surface must be disabled
```

## Allowed implementation surface

```text
answer_synthesis.py
answer_slots.py
evidence_bundle.py
runtime_trace.py
```

Avoid changing retrieval unless audit proves necessary.

## Commit

```text
Audit and guard Phase 24HS active TEB temporal policy
```

---

# 4. Workstream B — TUZUK-05 Ambiguous Source Stop Condition

## Amaç

`TUZUK-05` gibi exact source identity unresolved olan rows için concrete irrelevant tüzük seçimini engellemek.

## Output

```text
reports/benchmark/phase_24HS_B_tuzuk05_ambiguous_source_stop_condition.md
```

## Required systemic rule

```text
If source identity is marked:
  benchmark_ambiguous
  exact_source_not_identified
  needs_more_review
  source_not_found

AND query asks abstract hierarchy/conflict principle
AND no confirmed concrete tüzük source exists

THEN:
  do not select arbitrary concrete tüzük as primary
  answer must use general hierarchy/source-policy handling if available
  or produce insufficient_source_identity answer
  manual_review_required = true
```

## Forbidden

```text
No hardcoded TUZUK-05 branch.
No synthetic source.
No arbitrary tüzük fallback.
```

## Commit

```text
Implement Phase 24HS ambiguous tüzük stop condition
```

---

# 5. Workstream C — Family / Domain Compatibility Gate for KANUN-08 and YON-05

## Amaç

Source family mismatch yönündeki yanlış document selection’ları sistemik şekilde azaltmak.

## Output

```text
reports/benchmark/phase_24HS_C_family_domain_compatibility_audit.md
reports/benchmark/phase_24HS_C_family_domain_compatibility_audit.csv
```

## Rows

```text
KANUN-08
YON-05
```

## Audit fields

```text
qid
query_family_signal
query_domain_signal
selected_source_family
selected_source_title
expected_family_if_known
candidate_pool_expected_present
wrong_source_rank
why_wrong_source_won
family_domain_gate_would_filter
safe_systemic_rule
```

## Required systemic rule

```text
Primary source family must be compatible with query legal family/domain signals.
Supporting source may appear in evidence, but cannot overwrite primary selected source.
KANUN cannot overwrite YONETMELIK primary unless query explicitly asks statutory basis.
YONETMELIK cannot overwrite KANUN primary unless query asks implementation/procedure/regulation.
Cross-family promotion requires explicit relation metadata.
```

## Suggested feature flag

```text
ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true
```

## Commit

```text
Audit and implement Phase 24HS family domain compatibility gate
```

---

# 6. Workstream D — Focused Non-Live Candidate Smoke

Only run after A/B/C implementation or after design-only decision if implementation is not safe.

## Runtime

Use non-live candidate, for example:

```text
http://127.0.0.1:8041/v1
```

## Target QIDs

```text
TEB-04
TUZUK-05
KANUN-08
YON-05
```

## Guard QIDs

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

## Acceptance

```text
contract_valid all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0

TEB-04 must not claim MULGA/repealed if source 19631 selected
TUZUK-05 must not select unrelated concrete tüzük as primary
KANUN-08 or YON-05 at least one source identity improves
MULGA-01/MULGA-05/TEB-06 no regression
TUZUK-04 not active-current-law claim
```

## Output

```text
reports/benchmark/phase_24HS_D_focused_non_live_smoke_report.md
```

## Commit

```text
Run Phase 24HS focused non-live smoke
```

---

# 7. Optional Full Candidate Benchmark

Only run if focused smoke passes.

## Minimum

Compare against current trace-on BASE:

```text
BASE trace-on = 805.09 / 89
```

Candidate must satisfy:

```text
raw_score_proxy >= 805.09
pass_proxy >= 89
wrong_document <= current
hallucinated_identifier <= current
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

## Output

```text
reports/benchmark/phase_24HS_full_candidate_summary.md
reports/benchmark/phase_24HS_delta_vs_phase24U_base.md
reports/benchmark/phase_24HS_green_lane_summary.md
```

## Commit

```text
Run Phase 24HS full candidate benchmark
```

If not run:

```text
reports/benchmark/phase_24HS_full_candidate_not_run.md
```

---

# 8. Decision Report

## Output

```text
reports/benchmark/phase_24HS_recovery_decision.md
```

## Options

### Option A — Candidate improves safely

```text
Open controlled integration brief.
No live cutover yet.
```

### Option B — Focused smoke improves but full insufficient

```text
Keep as diagnostic candidate.
Continue component recovery.
```

### Option C — No systemic fix found

```text
Stop runtime recovery line.
Return to product policy/residual acceptance.
```

### Option D — Needs scorer/rubric policy

```text
Prepare scorer/rubric packet.
No runtime change.
```

## Commit

```text
Record Phase 24HS recovery decision
```

---

# 9. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24HS_option_C_failure_remediation_report.md
```

Must include:

1. commit SHA list
2. TEB active temporal guard result
3. TUZUK ambiguous source stop-condition result
4. family/domain compatibility result
5. focused smoke result
6. full benchmark result or not-run reason
7. recovery decision
8. productization decision
9. internal eval decision
10. fine-tuning decision
11. final live 8000 state
12. next recommended phase

## Commit

```text
Report Phase 24HS Option C failure remediation outcome
```

---

# 10. Stop Rules

Stop/revert candidate if:

```text
live 8000 would be modified
QID-specific runtime branch introduced
benchmark answer key required
contract invalid appears
unsupported confident appears
source_key_v2 collision appears
binding collision appears
MULGA-01/MULGA-05/TEB-06 regress
TEB-04 still claims active source as MULGA/repealed after fix
TUZUK-05 still selects unrelated concrete tüzük after fix
large traces staged
```

---

## Final Note

Option C did not fail technically; it failed quality.

The next recovery must fix:
1. active TEB temporal misclassification,
2. ambiguous tüzük stop-condition,
3. family/domain source identity compatibility.

Do not run Option D until a new focused smoke passes.
