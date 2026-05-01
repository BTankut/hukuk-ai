# Hukuk-AI — Phase 22D Residual Targeted Remediation Brief

## Karar

Phase 22 **stability açısından kabul edilmiştir**, fakat productization readiness hâlâ açılmamıştır.

Phase 22A, Phase 21F sonucunu birebir tekrar etti:

- `raw_score_proxy = 800.55`
- `pass_proxy = 89/100`
- `wrong_family = 6`
- `wrong_document = 5`
- `hallucinated_identifier = 5`
- `unsupported_confident_claim = 0`
- `contract_valid = 100/100`
- `source_key_v2_collision = 0`
- `binding_source_key_collision = 0`
- `green_lane = PASS`

Ancak Phase 22B residual audit hâlâ iki P0 blocker gösteriyor:

```text
MULGA-01
TEB-06
```

Bu yüzden sıradaki iş:

```text
Phase 22D — Residual Targeted Remediation
```

Productization kapalı.  
Fine-tuning kapalı.

---

# 1. Neden Phase 22D?

Phase 22A stability geçti. Bu iyi.

Ancak productization readiness için residual P0 blocker sayısı `0` olmalı veya bu blocker’lar açık biçimde manual legal review / corpus remediation backlog olarak kabul edilmelidir.

Mevcut audit:

| Priority | Count |
|---|---:|
| P0_blocks_productization | 2 |
| P1_high_value_next_iteration | 6 |
| P2_watchlist | 3 |
| P3_acceptable_residual | 0 |

Root cause dağılımı:

| Root cause | Count |
|---|---:|
| document_identity | 4 |
| family_boundary | 2 |
| source_identity | 2 |
| span_materialization | 3 |

Safe action dağılımı:

| Safe action | Count |
|---|---:|
| defer_needs_corpus | 2 |
| fix_now_generalizable | 6 |
| watch_only_pass_row | 3 |

Phase 22D’nin ilk hedefi P0 blocker’ları ele almaktır. P1 satırlar ikinci önceliktir.

---

# 2. Phase 22D Ana Hedefleri

## Primary objective

P0 blocker sayısını `2 -> 0` yapmak veya ikisini de açık ve kabul edilebilir corpus/manual-review backlog’a taşımak.

P0 rows:

```text
MULGA-01
TEB-06
```

## Secondary objective

P1 satırlardan düşük riskli ve genelleyici olanları düzeltmek.

P1 rows:

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

## Watchlist

P2 satırlar patch hedefi değildir; sadece izlenir.

```text
CBG-02
CBKAR-05
CBY-01
```

---

# 3. Kesin Kurallar

Phase 22D boyunca:

- no QID-specific branch
- no private answer key usage
- no fine-tuning
- no prompt broadening
- no retrieval top-k brute force
- no source-key v2 schema regression
- no binding collision
- no unsupported confident increase
- no productization gate opening
- no broad family-gate weakening
- no answer synthesis patch unless source/span is already correct and audit proves synthesis-only issue

Öncelikli modüller:

```text
api-gateway/src/rag/source_identity.py
api-gateway/src/rag/article_span_selection.py
```

Gerekirse:

```text
api-gateway/src/rag/runtime_trace.py
```

Kaçınılacak modüller:

```text
api-gateway/src/rag/answer_synthesis.py
api-gateway/src/rag/answer_slots.py
```

Bu faz source/document/span remediation fazıdır.

---

# 4. Phase 22D-A — P0 Corpus / Span Materialization Audit

## Amaç

`MULGA-01` ve `TEB-06` için gerçekten runtime fix mümkün mü, yoksa corpus/materialization backfill mi gerekiyor, bunu netleştirmek.

## Output

```text
reports/benchmark/phase_22D_P0_materialization_audit.md
reports/benchmark/phase_22D_P0_materialization_audit.csv
```

## Audit rows

```text
MULGA-01
TEB-06
```

## Her row için alanlar

```text
qid
family
score
pass_fail
selected_document
selected_span
selected_article
expected_document_if_available
expected_family
claimed_family
wrong_family
wrong_document
wrong_article
hallucinated_identifier
insufficient_canonical_span_evidence
missing_gold_document_signal
metadata_lookup_hit
metadata_candidates
dense_top_candidates
source_key_v2
binding_source_key
candidate_completeness_score
body_text_available
body_text_length
selected_document_has_non_title_span
corpus_materialization_required
title_only_degraded
source_text_available
expected_source_visible_in_corpus
expected_source_has_body_span
expected_source_has_article_span
root_cause
safe_action
```

## Root cause enum

```text
expected_source_missing_from_corpus
expected_source_body_missing
expected_article_span_missing
source_visible_but_not_selected
selected_source_wrong_document
selected_source_correct_but_wrong_article
corpus_materialization_backfill_required
private_rubric_gold_unavailable
unknown
```

## Safe action enum

```text
runtime_fix_generalizable
corpus_backfill_required
manual_legal_review_required
defer_not_safe_to_fix
```

## Acceptance

- `MULGA-01` ve `TEB-06` için clear go/no-go kararı verilmeli.
- Eğer runtime fix mümkün değilse açık corpus backlog’a taşınmalı.
- Runtime davranış değişmeyecek.

## Commit

### Commit 1

```text
Audit P0 residual materialization blockers
```

Push zorunlu.

---

# 5. Phase 22D-B — P0 Runtime Remediation, Only If Safe

Bu adım yalnız Phase 22D-A audit `runtime_fix_generalizable` derse uygulanacak.

## 5.1 MULGA-01 possible remediation

Known issue:

```text
Family: MULGA
Selected document: SAYIŞTAY KANUNU
Selected span: 832 m.98/f.0
Failure: wrong_article + insufficient_canonical_span_evidence
Expected area: Yükseköğretim öğrenci disiplin yönetmeliği / mülga disciplinary regime
```

Possible generalized fixes:

- historical/repealed regulation title exactness boost
- body-bearing historical regulation candidate > unrelated law topical match
- suppress unreadable/title-only historical false positives
- article/span selector should prefer body-bearing historical regulation spans over law fallback when query title strongly names a regulation
- if expected body span missing, classify as corpus_materialization_backfill_required instead of over-answering

Allowed modules:

```text
source_identity.py
article_span_selection.py
runtime_trace.py
```

Hard rules:

- do not promote title-only evidence to confident answer
- do not use active/current law as substitute unless explicitly supporting
- preserve MULGA-02/03/04/05

## 5.2 TEB-06 possible remediation

Known issue:

```text
Family: TEBLIGLER
Selected document: Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ
Selected span: 23093 m.6/f.0
Failure: wrong_document + missing_gold_document_signal + hallucinated_identifier + insufficient_canonical_span_evidence
```

Possible generalized fixes:

- tebliğ identifier / source-title disambiguation for company formation / MERSİS / trade registry domain
- official source title canonicalization
- distinguish company-establishment tebliğ variants
- support `sıra no`, `seri no`, year and issuer identity in document rerank
- if expected gold source not visible, classify as corpus/materialization backlog

Allowed modules:

```text
source_identity.py
runtime_trace.py
```

Use `article_span_selection.py` only if selected document is correct but selected article/span is wrong.

## P0 Smoke

```text
MULGA-01
MULGA-02
MULGA-03
MULGA-04
MULGA-05
TEB-01
TEB-02
TEB-03
TEB-04
TEB-05
TEB-06
TEB-07
TEB-08
```

## Acceptance

Either:

```text
MULGA-01 PASS or moved to corpus_backfill_required with safer behavior
TEB-06 PASS or moved to corpus_backfill_required with safer behavior
```

And:

```text
MULGA >= 4/5
TEBLIGLER >= 7/8 preferred, >=6/8 minimum
unsupported_confident_answer = 0
contract_valid = all rows
source_key_v2_collision = 0
binding_collision = 0
```

## Commit

### Commit 2, only if safe runtime fix exists

```text
Remediate P0 residual source span blockers
```

Push zorunlu.

---

# 6. Phase 22D-C — P1 Generalizable Source/Document Remediation

Bu adım P0 audit/fix sonrası yapılmalı.

## P1 rows

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

## Amaç

Düşük riskli ve genelleyici source/document identity iyileştirmelerini yapmak.

## P1 row hints

### CBY-04

```text
root_cause = source_identity
selected = Devlet Arşivleri Başkanlığı Hakkında Cumhurbaşkanlığı Kararnamesi
```

Likely issue:

- CB_YONETMELIK vs CB_KARARNAME / CB authority source identity boundary
- document type mismatch

### KANUN-12

```text
root_cause = document_identity
selected = Araştırma Reaktörlerinin Güvenliği İçin Özel İlkeler Yönetmeliği
```

Likely issue:

- law question hijacked by technical regulation
- KANUN primary source vs supporting regulation boundary

### KKY-01 / KKY-03

Likely issue:

- KKY family vs YONETMELIK / KANUN / technical regulation boundary
- institutional regulation/document identity

### TUZUK-05

Likely issue:

- tüzük document identity / legacy materialization
- selected m.0 / wrong document

### YON-04

Known residual:

```text
selected = Nükleer Güç Santrallerinin Güvenliği İçin Özel İlkeler Yönetmeliği
expected area = personal data deletion / anonymization regulation
```

Likely issue:

- domain expansion not enough
- selected document retention/source-lock arbitration problem
- metadata sees expected title but final source retention chooses wrong document

## Allowed modules

```text
source_identity.py
runtime_trace.py
```

Use `article_span_selection.py` only if audit proves source correct but span wrong.

## Smoke set

```text
CBY-01
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

Regression guards:

```text
CB_GENELGE all 4
CB_KARAR all 8
MULGA all 5
TEBLIGLER all 8
YONETMELIK all 10
UY-07 UY-08
KANUN-03 KANUN-04 KANUN-19
```

## Acceptance

- at least 2 P1 rows recovered or clearly classified as not safe
- no hard safety regression
- family guards preserved

## Commit

### Commit 3

```text
Remediate P1 residual source document blockers
```

Push zorunlu.

---

# 7. Phase 22D-D — Full Benchmark Gate

After P0/P1 work, run full benchmark.

## Target metrics

Phase 22A baseline:

```text
raw_score_proxy = 800.55
pass_proxy = 89/100
wrong_family = 6
wrong_document = 5
hallucinated_identifier = 5
```

Phase 22D targets:

| Metric | Target |
|---|---:|
| raw_score_proxy | `>= 805` preferred, `>= 800` minimum |
| pass_proxy | `>= 90` preferred, `>= 89` minimum |
| wrong_family | `<= 5` |
| wrong_document | `<= 4` |
| hallucinated_identifier | `<= 4` |
| unsupported_confident_claim | `<= 2` |
| contract_valid | `100/100` |
| green_lane | `PASS` |
| source_key_v2_collision | `0` |
| binding_source_key_collision | `0` |
| P0 blockers | `0` or formally accepted corpus backlog |

## Hard gates

```text
unsupported_confident_answer = 0
contract_valid = 100/100
green_lane = PASS
source_key_v2_collision = 0
binding_collision = 0
CB_GENELGE = 4/4
UY >= 9/10
MULGA >= 4/5
TEBLIGLER >= 6/8
YONETMELIK >= 7/10
CB_KARAR >= 7/8
```

## Commit

### Commit 4

```text
Run Phase 22D residual remediation full benchmark
```

Push zorunlu.

---

# 8. Phase 22D Decision

## Option A — P0 resolved and full gate stable

```text
Open Phase 23 Productization Readiness Audit
Fine-tuning remains closed
```

## Option B — P0 not runtime-fixable but accepted as corpus backlog

```text
Open Phase 23 Productization Readiness Audit with explicit corpus backlog risk
Fine-tuning remains closed
```

## Option C — P0/P1 fixes regress safety

```text
Rollback offending changes
Open Phase 22R regression investigation
```

## Option D — P0 remains unresolved and not accepted

```text
Continue Phase 22D residual remediation or manual legal/corpus review
No productization
No fine-tuning
```

---

# 9. Productization / Fine-Tuning

Productization remains closed during Phase 22D.

Fine-tuning remains closed.

Do not open fine-tuning while residual failures are source/span/corpus issues.

---

# 10. Required Final Report

Produce:

```text
reports/benchmark/phase_22D_residual_targeted_remediation_report.md
```

Report content:

1. commit SHA list
2. P0 audit
3. P0 runtime fix or corpus backlog decision
4. P1 remediation result
5. full benchmark delta vs Phase 22A
6. residual backlog after remediation
7. safety gate table
8. productization readiness recommendation
9. fine-tuning gate decision
10. remaining risks

---

## Final Note

Phase 22A proved stability.  
Phase 22B proved residual risk remains.

Phase 22D should be narrow, evidence-driven, and primarily focused on P0 blockers.  
Do not chase every residual row. Do not use QID-specific patches. Do not tune answer text for source/span failures.

