# Hukuk-AI — Phase 24N Completed Review Intake and Safe Shadow Remediation Brief

## Karar

Phase 24 için beklenen iki uzman dönüş dosyası artık mevcut ve kullanılabilir:

```text
01_filled_phase_24H_legal_scorer_review_return.csv
02_filled_phase_24I_official_source_acquisition_checklist.csv
```

Aynı içerikte `__completed` kopyaları da verilmiş.

Bu dosyalar kod asistanı tarafından repo’ya işlenecek, validate edilecek ve Phase 24 residual closure süreci tekrar açılacaktır.

Önemli karar:

```text
Ek hukukçu dönüşü beklenmeyecek.
TUZUK-05 açık residual olarak kalacak.
TUZUK-05 için synthetic source/backfill yapılmayacak.
```

Productization kapalı.  
Internal eval kapalı.  
Fine-tuning kapalı.  
Live `8000` değiştirilmemeli.

---

# 1. Girdi Dosyaları

Kullanıcıdan alınan ve repo’ya işlenecek dosyalar:

```text
01_filled_phase_24H_legal_scorer_review_return.csv
01_filled_phase_24H_legal_scorer_review_return__completed.csv
02_filled_phase_24I_official_source_acquisition_checklist.csv
02_filled_phase_24I_official_source_acquisition_checklist__completed.csv
```

Repo hedef yolları:

```text
reports/benchmark/legal_review_returns/filled_phase_24H_legal_scorer_review_return.csv
reports/benchmark/legal_review_returns/filled_phase_24I_official_source_acquisition_checklist.csv
```

`__completed` kopyaları ayrıca arşiv olarak saklanabilir:

```text
reports/benchmark/legal_review_returns/filled_phase_24H_legal_scorer_review_return__completed.csv
reports/benchmark/legal_review_returns/filled_phase_24I_official_source_acquisition_checklist__completed.csv
```

---

# 2. Beklenen İçerik Kararları

## 2.1 Legal / Scorer Review

Review rows:

```text
CBY-04
CBY-06
KKY-01
TEB-04
TUZUK-04
```

Beklenen ana kararlar:

```text
CBY-04  -> legal_taxonomy_confirmed
CBY-06  -> runtime_fix_allowed
KKY-01  -> legal_taxonomy_confirmed
TEB-04  -> scorer_rubric_mismatch
TUZUK-04 -> runtime_fix_allowed / legal current-law limitation
```

Önemli yorumlar:

- CBY-04: primary source CB yönetmelik olmalı; CBK 11 supporting.
- CBY-06: 03.04.2026 / 33213 RG / Karar 11153 değişikliği ve m.11 ek fıkra scorer beklentisine girmeli.
- KKY-01: hukukî source family `YONETMELIK`; KKY benchmark alias/bucket olabilir.
- TEB-04: KDV Genel Uygulama Tebliği primary source; auto-fail scorer/materialization mismatch olabilir.
- TUZUK-04: Radyasyon Güvenliği Tüzüğü historical/repealed; current-law answer’da tek başına yeterli değil.

## 2.2 Official Source Acquisition

Source rows:

```text
KANUN-12
KKY-03
TUZUK-04
TUZUK-05
YON-04
```

Beklenen kararlar:

```text
KANUN-12 -> confirmed, parser_ready=yes
KKY-03   -> confirmed, parser_ready=yes, source_family=YONETMELIK
TUZUK-04 -> confirmed, parser_ready=yes, effective_state=repealed, historical-only
YON-04   -> confirmed, parser_ready=yes
TUZUK-05 -> needs_more_review / benchmark_ambiguous / not_found
```

Önemli:

```text
TUZUK-05 remediation dışında kalacak.
TUZUK-05 için source uydurulmayacak.
TUZUK-05 internal_eval/productization blocker olarak kalacak.
```

---

# 3. Kesin Kurallar

Bu faz boyunca:

- live `8000` değişmeyecek
- base/live collection değişmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- prompt/model/top-k değişmeyecek
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- TUZUK-05 için synthetic backfill yok
- yalnız confirmed rows için shadow-only remediation yapılabilir

---

# 4. Phase 24N-A — Intake and Validation

## Amaç

Yeni filled CSV dosyalarını repo’ya işlemek ve doğrulamak.

## Output

```text
reports/benchmark/phase_24N_review_return_intake.md
reports/benchmark/phase_24N_review_return_validation.csv
```

## Kontroller

Legal/scorer file:

```text
required columns present
5/5 expected rows present
primary_decision_enum valid
runtime_fix_allowed_if_systemic values valid
manual acceptance fields present
```

Source acquisition file:

```text
required columns present
5/5 expected rows present
KANUN-12 confirmed
KKY-03 confirmed
TUZUK-04 confirmed historical/repealed
YON-04 confirmed
TUZUK-05 needs_more_review/not_found
raw_file_path populated for confirmed rows
raw_file_sha256 populated for confirmed rows
parser_ready_yes_no=yes for confirmed rows
```

## Acceptance

- Filled files committed.
- Validation report clean except explicit TUZUK-05 residual.
- No runtime change.

## Commit

```text
Intake Phase 24N completed review returns
```

Push required.

---

# 5. Phase 24N-B — Closure Decision Normalization

## Amaç

Filled CSV kararlarını sistemin okuyacağı normalized closure tablosuna çevirmek.

## Output

```text
reports/benchmark/phase_24N_closure_decision_normalization.md
reports/benchmark/phase_24N_closure_decision_normalization.csv
```

## Fields

```text
qid
legal_review_status
source_acquisition_status
runtime_fix_allowed
shadow_backfill_allowed
scorer_rubric_review_required
corpus_backfill_required
internal_eval_status
productization_status
normalized_next_action
```

## Expected decisions

```text
CBY-04: legal taxonomy confirmed, source identity design possible, productization blocked
CBY-06: runtime/corpus update possible, productization blocked
KKY-01: taxonomy confirmed, scorer compatibility issue, productization blocked
TEB-04: scorer/materialization review required, internal_eval blocked unless manually accepted
TUZUK-04: historical/current-law handling required, productization blocked
KANUN-12: source confirmed, shadow backfill allowed
KKY-03: source confirmed, shadow backfill allowed as YONETMELIK
YON-04: source confirmed, shadow backfill allowed
TUZUK-05: unresolved, no backfill, blocks internal_eval/productization
```

## Commit

```text
Normalize Phase 24N residual closure decisions
```

Push required.

---

# 6. Phase 24N-C — Shadow Remediation Plan

## Amaç

Confirmed rows için shadow-only remediation planı hazırlamak.

## Rows eligible for shadow remediation

```text
KANUN-12
KKY-03
YON-04
```

## Conditional / limited row

```text
TUZUK-04
```

`TUZUK-04` yalnız historical/repealed handling için kullanılabilir; current-law authority olarak kullanılmayacak.

## Excluded

```text
TUZUK-05
```

## Output

```text
reports/benchmark/phase_24N_shadow_remediation_plan.md
reports/benchmark/phase_24N_shadow_remediation_plan.csv
```

## Plan must define

```text
source spans to materialize
family identity to preserve
supporting-source relations
effective_state constraints
expected impact per QID
guard rows
stop rules
target shadow collection name
```

## Target shadow collection

Use a new collection, not previous broken Phase24J target unless reused intentionally after normalized-provenance analysis:

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24n
```

## Commit

```text
Plan Phase 24N shadow remediation
```

Push required.

---

# 7. Phase 24N-D — Shadow-Only Implementation, If Safe

Only run if Phase 24N-C marks at least one row safe.

## Rules

```text
shadow-only
no live 8000 change
no base collection overwrite
no broad retrieval/top-k change
no QID-specific branch
```

## Output

```text
reports/benchmark/phase_24N_shadow_remediation_report.md
reports/benchmark/phase_24N_shadow_runtime_provenance.json
```

## Commit

```text
Implement Phase 24N shadow residual remediation
```

Push required.

If implementation is not safe:

```text
reports/benchmark/phase_24N_shadow_remediation_not_run.md
```

Commit:

```text
Record Phase 24N shadow remediation not run
```

---

# 8. Phase 24N-E — Targeted Smoke

Only run if Phase 24N-D ran.

## Target QIDs

```text
KANUN-12
KKY-03
YON-04
TUZUK-04
```

## Guard QIDs

```text
MULGA-01
MULGA-05
TEB-04
TEB-06
CBG-01
CBKAR-08
UY-01
YON-05
```

## Acceptance

```text
answered = all
contract_valid = all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
no regression in MULGA-01/MULGA-05/TEB-06
TUZUK-04 not claimed as active current law
at least one targeted row improves OR document no-op
```

## Output

```text
reports/benchmark/phase_24N_targeted_shadow_smoke_report.md
```

## Commit

```text
Run Phase 24N targeted shadow smoke
```

Push required.

---

# 9. Phase 24N-F — Full Shadow Benchmark, If Targeted Passes

Only run if targeted smoke passes and at least one targeted row improves.

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

## Output

```text
reports/benchmark/phase_24N_full_shadow_benchmark_summary.md
reports/benchmark/phase_24N_delta_vs_phase23RE.md
reports/benchmark/phase_24N_green_lane_summary.md
```

## Commit

```text
Run Phase 24N full shadow benchmark
```

Push required.

If not run:

```text
reports/benchmark/phase_24N_full_shadow_not_run.md
```

---

# 10. Phase 24N-G — Internal Eval Readiness Recheck

Always run after N-D/E/F decision.

## Output

```text
reports/benchmark/phase_24N_internal_eval_readiness_recheck.md
```

## Checks

```text
KANUN-12 closure status
KKY-03 closure status
TEB-04 closure status
TUZUK-05 closure status
YON-04 closure status
legal/scorer status
source acquisition status
shadow remediation result
serving policy readiness
residual blockers
```

## Decision options

```text
internal_eval_ready
limited_legal_review_eval_only
not_ready_continue_residual_closure
```

## Commit

```text
Recheck Phase 24N internal eval readiness
```

Push required.

---

# 11. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24N_completed_review_intake_report.md
```

Must include:

1. commit SHA list
2. intake validation
3. normalized decisions
4. shadow remediation plan
5. shadow remediation run/not-run
6. targeted smoke result
7. full shadow benchmark result/not-run
8. internal eval readiness decision
9. productization decision
10. fine-tuning decision
11. final live 8000 state
12. remaining blockers

## Commit

```text
Report Phase 24N completed review intake outcome
```

Push required.

---

## Final Decision

Bu dosyalar artık teknik intake için yeterlidir.

Ek hukukçu dönüşü şimdilik istenmeyecek.

TUZUK-05 açık ve excluded kalacak.

Confirmed rows için shadow-only remediation denenebilir; live 8000 etkilenmeyecek.
