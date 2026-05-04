# Hukuk-AI — Phase 24P Targeted Materialization Brief

## Karar

Phase 24O targeted düzeyde bazı kazanımlar verdi ancak full shadow gate geçmedi.

Phase 24O sonucu:

- `KANUN-12` PASS oldu.
- `YON-04` PASS oldu.
- `TUZUK-04` eski tüzüğü active current-law gibi claim etmiyor.
- Guard rows temiz kaldı.
- Full shadow gate FAILED:
  - `raw_score_proxy = 805.09 < 816`
  - `pass_proxy = 89 < 91`
  - `wrong_family = 8`
  - `hallucinated_identifier = 7`

Bu nedenle Phase 24O candidate live’a alınmayacak.

Sıradaki teknik olarak anlamlı iş:

```text
Phase 24P — Targeted materialization for CBY-06 and TEB-04
```

Bu faz iki spesifik eksik materialization hattına odaklanır:

```text
CBY-06: 03.04.2026 / RG 33213 / Karar 11153 / m.11 ek fıkra
TEB-04: KDV Genel Uygulama Tebliği tevkifat/iade section spans
```

Productization kapalı.  
Internal eval kapalı.  
Fine-tuning kapalı.  
Live `8000` değişmeyecek.

---

## 1. Kesin Kurallar

Phase 24P boyunca:

- live `8000` değişmeyecek
- current benchmark-only live korunacak
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt değişmeyecek
- broad retrieval/top-k değişmeyecek
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- Phase 24O candidate live’a alınmayacak
- yalnız source acquisition / section materialization / shadow-only validation yapılacak

---

## 2. Phase 24P-A — CBY-06 Amendment Source Audit

## Amaç

03.04.2026 tarihli Karar 11153 / RG 33213 değişikliğinin resmi kaynağını ve m.11 ek fıkrasını doğrulamak.

## Output

```text
reports/benchmark/phase_24P_A_cby06_amendment_source_audit.md
reports/benchmark/phase_24P_A_cby06_amendment_source_audit.csv
```

## Fields

```text
qid
source_title
official_url
official_publication_date
official_gazette_no
decision_no
amended_regulation_title
amended_article
added_paragraph_text_available
raw_file_path
raw_file_sha256
parser_ready
article_boundary_notes
legal_confirmation
safe_for_materialization
blocking_reason
```

## Acceptance

```text
official source found
raw source captured
sha256 produced
m.11 added paragraph visible
parser_ready yes or deterministic extraction plan exists
```

## Commit

```text
Audit Phase 24P CBY-06 amendment source
```

---

## 3. Phase 24P-B — TEB-04 KDV Section Materialization Audit

## Amaç

KDV Genel Uygulama Tebliği içinde gerekli tevkifat/iade section span’larının materialize edilebilir olup olmadığını belirlemek.

## Output

```text
reports/benchmark/phase_24P_B_teb04_kdv_section_audit.md
reports/benchmark/phase_24P_B_teb04_kdv_section_audit.csv
```

## Fields

```text
qid
source_key
source_title
official_url
current_selected_span
required_section_candidate
required_section_title
section_text_available
table_or_appendix_involved
raw_file_path
raw_file_sha256
parser_ready
section_boundary_detectable
article_zero_problem
safe_for_section_materialization
blocking_reason
```

## Candidate required sections

Include if present:

```text
KDV Genel Uygulama Tebliği
I/C-2.1.3
tevkifat
iade
kısmi tevkifat
tam tevkifat
mahsuben iade
nakden iade
```

## Acceptance

```text
correct consolidated source confirmed
section text available
section boundary detectable or deterministic parser plan available
m.0-only surface can be replaced/supplemented
```

## Commit

```text
Audit Phase 24P TEB-04 KDV section materialization
```

---

## 4. Phase 24P-C — Targeted Shadow Materialization Plan

## Amaç

CBY-06 ve TEB-04 için safe shadow-only materialization planı hazırlamak.

## Output

```text
reports/benchmark/phase_24P_C_targeted_materialization_plan.md
reports/benchmark/phase_24P_C_targeted_materialization_plan.csv
```

## Plan fields

```text
qid
source_title
materialization_type
span_type
article_or_section
effective_state
relation_to_existing_source
expected_answer_slot
safe_to_implement
stop_rule
```

## Commit

```text
Plan Phase 24P targeted materialization
```

---

## 5. Phase 24P-D — Shadow-Only Materialization

Only run if C says safe.

## Target collection

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p
```

## Base collection

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

## Output

```text
reports/benchmark/phase_24P_D_shadow_materialization_report.md
reports/benchmark/phase_24P_D_shadow_runtime_provenance.json
```

## Requirements

```text
canonical_key_collision_count = 0
binding_key_collision_count = 0
entity_count >= 349403
vector_dimension = 1024
source catalog hash recorded
raw sha256 recorded
```

## Commit

```text
Materialize Phase 24P targeted shadow spans
```

If not safe:

```text
reports/benchmark/phase_24P_D_shadow_materialization_not_run.md
```

---

## 6. Phase 24P-E — Targeted Smoke

Only run if D succeeds.

## Target rows

```text
CBY-06
TEB-04
```

## Guard rows

```text
MULGA-01
MULGA-05
TEB-06
KANUN-12
YON-04
TUZUK-04
CBG-01
CBKAR-08
UY-01
```

## Acceptance

```text
CBY-06 improves or PASS
TEB-04 improves or PASS
MULGA-01 PASS
MULGA-05 PASS
TEB-06 PASS
contract_valid all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
TUZUK-04 not active-current-law claim
```

## Output

```text
reports/benchmark/phase_24P_E_targeted_smoke_report.md
```

## Commit

```text
Run Phase 24P targeted smoke
```

---

## 7. Phase 24P-F — Full Shadow Benchmark

Only run if targeted smoke passes.

## Minimum gate

```text
raw_score_proxy >= 816
pass_proxy >= 91
wrong_family <= 6
wrong_document <= 4
hallucinated_identifier <= 4
green_lane = PASS
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
```

## Preferred

```text
pass_proxy > 91
or TEB-04 no longer auto_fail
or CBY-06 PASS
```

## Output

```text
reports/benchmark/phase_24P_F_full_shadow_benchmark_summary.md
reports/benchmark/phase_24P_F_delta_vs_phase23RE.md
reports/benchmark/phase_24P_F_green_lane_summary.md
reports/benchmark/phase_24P_F_decision.md
```

## Commit

```text
Run Phase 24P full shadow benchmark
```

If not run:

```text
reports/benchmark/phase_24P_F_full_shadow_not_run.md
```

---

## 8. Phase 24P-G — Internal Eval Readiness Recheck

Always run after targeted/full decision.

## Output

```text
reports/benchmark/phase_24P_G_internal_eval_readiness_recheck.md
```

## Decision options

```text
internal_eval_ready
limited_legal_review_eval_only
not_ready_continue_residual_closure
```

Internal eval cannot open unless blockers are closed or explicitly accepted.

## Commit

```text
Recheck Phase 24P internal eval readiness
```

---

## 9. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24P_targeted_materialization_report.md
```

Must include:

1. commit SHA list
2. CBY-06 amendment source audit
3. TEB-04 KDV section audit
4. materialization plan
5. shadow materialization result or not-run reason
6. targeted smoke result
7. full shadow benchmark result or not-run reason
8. internal eval decision
9. productization decision
10. fine-tuning decision
11. final live 8000 state
12. remaining blockers

## Commit

```text
Report Phase 24P targeted materialization outcome
```

---

## 10. Stop Rules

Stop/revert if:

```text
live 8000 modified
base collection modified
QID-specific runtime branch introduced
MULGA-01 regresses
MULGA-05 regresses
TEB-06 regresses
contract invalid appears
unsupported confident appears
source_key_v2 collision appears
binding collision appears
TUZUK-04 active-current-law claim returns
```

---

## Final Note

Do not continue broad residual experimentation.

The only promising next technical work is precise materialization:
- CBY-06 amendment m.11
- TEB-04 KDV section spans

Everything else should stay review/blocker status.
