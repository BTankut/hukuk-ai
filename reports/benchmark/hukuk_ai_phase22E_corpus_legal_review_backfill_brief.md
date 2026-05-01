# Hukuk-AI — Phase 22E Corpus / Legal Review and Backfill Readiness Brief

## Karar

Phase 22D tamamlandı; stability korunmuş ancak productization readiness hâlâ açılmamıştır.

Phase 22D full benchmark, Phase 22A ile aynı kaldı:

- `raw_score_proxy = 800.55`
- `pass_proxy = 89/100`
- `wrong_family = 6`
- `wrong_document = 5`
- `hallucinated_identifier = 5`
- `unsupported_confident_answer = 0`
- `answer_contract_invalid = 0`
- `source_key_v2_collision = 0`
- `binding_source_key_collision = 0`
- `green_lane = PASS`

Ancak hedef metrikler iyileşmedi:

- `wrong_family <= 5` hedefi geçmedi
- `wrong_document <= 4` hedefi geçmedi
- `hallucinated_identifier <= 4` hedefi geçmedi
- `MULGA-01` hâlâ unresolved
- `TEB-06` corpus materialization / backfill gerektiriyor

Bu nedenle sıradaki iş runtime heuristic patch değildir.

Sıradaki faz:

```text
Phase 22E — Corpus / Legal Review and Backfill Readiness
```

Productization kapalı.  
Fine-tuning kapalı.

---

## 1. Phase 22D’den Çıkan Net Sonuç

Phase 22D güvenlik ve stabilite açısından başarılıdır:

- safety gate temiz
- benchmark stabil
- green lane pass
- collision yok
- unsupported confident yok

Fakat Phase 22D residual remediation hedefini gerçekleştirmedi:

- P0 blocker sayısı düşmedi
- `MULGA-01` için denenen runtime bridge mixed source identity contract üretti ve revert edildi
- `TEB-06` için runtime fix yapılmadı; title-only/body-missing tebliğ evidence ile confident answer üretmek güvenli değil
- P1 rows runtime patch için güvenli bulunmadı

Bu yüzden Phase 22E artık kod davranışı değil, **corpus truth / legal taxonomy / backfill readiness** fazıdır.

---

## 2. Phase 22E Ana Hedefleri

### Primary objective

P0 blocker’lar için legal/corpus truth kesinleştirilecek:

```text
MULGA-01
TEB-06
```

### Secondary objective

P1 residuals için legal taxonomy ve safe-action kararı netleşecek:

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

### Not hedef

Bu fazda doğrudan score artırma hedefi yoktur.

Hedef:

- P0 gerçekten fix edilebilir mi?
- Corpus backfill gerekli mi?
- Manual legal review gerekli mi?
- Productization readiness önünde blokaj mı?
- Hangi residual risk kabul edilebilir, hangisi edilemez?

---

## 3. Kesin Kurallar

Phase 22E boyunca:

- no QID-specific branch
- no private answer key usage
- no fine-tuning
- no answer synthesis patch
- no broad retrieval/top-k tuning
- no prompt broadening
- no source-key schema change
- no runtime family relabeling
- no title-only evidence promotion
- no productization opening

Öncelikli çalışma yüzeyi:

```text
reports / audits / corpus truth packets / backfill plan
```

Runtime code değişikliği yalnız açıkça ayrı onaylanmış shadow backfill için yapılabilir.

---

## 4. Phase 22E-A — P0 Legal / Corpus Truth Packet

## Amaç

`MULGA-01` ve `TEB-06` için beklenen hukuki kaynak, corpus görünürlüğü, body-span durumu ve materialization ihtiyacını kesinleştirmek.

## Output

```text
reports/benchmark/phase_22E_P0_legal_corpus_truth_packet.md
reports/benchmark/phase_22E_P0_legal_corpus_truth_packet.csv
```

## Rows

```text
MULGA-01
TEB-06
```

## Her row için zorunlu alanlar

```text
qid
family
current_score
current_selected_document
current_selected_span
current_failure_classes
expected_source_title
expected_source_family
expected_identifier
expected_official_source_url_if_known
expected_publication_date
expected_official_gazette_no
expected_effective_state
expected_article_or_clause
expected_body_text_available
expected_body_span_in_current_corpus
expected_source_visible_in_milvus
expected_source_visible_in_source_catalog
expected_source_has_non_title_body_span
current_selected_source_has_body_span
current_selected_source_is_title_only
materialization_gap
legal_review_needed
corpus_backfill_needed
safe_runtime_fix_possible
recommended_next_action
```

---

## 5. Row-Specific Questions

## 5.1 MULGA-01

Cevaplanacak sorular:

```text
Beklenen kaynak gerçekten Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği mi?
Bu kaynak corpus içinde hangi family/state ile temsil ediliyor?
Mülga kaynak body-bearing article span olarak var mı?
Beklenen madde/span corpus içinde görünür mü?
Neden Sayıştay Kanunu m.98 seçiliyor?
Runtime selector bridge neden mixed source identity contract üretti?
Bu sorun source_identity mi, article_span_selection mı, corpus/materialization mı?
```

Karar seçenekleri:

```text
runtime_fix_possible
corpus_backfill_required
manual_legal_review_required
not_safe_to_fix_without_private_rubric
```

## 5.2 TEB-06

Cevaplanacak sorular:

```text
Beklenen gold document hangi tebliğ?
Şu an seçilen 23093 source doğru domain mi yoksa wrong document mı?
Seçilen tebliğ title-only/body-missing mi?
Beklenen tebliğ source catalog/Milvus içinde var mı?
Body-bearing spans var mı?
Official source acquisition gerekiyor mu?
Corpus backfill ile çözülür mü?
```

Karar seçenekleri:

```text
corpus_backfill_required
manual_legal_review_required
private_rubric_gold_unavailable
not_safe_to_fix_without_corpus
```

## Acceptance

- `MULGA-01` ve `TEB-06` için clear go/no-go kararı verilmeli.
- Runtime behavior değişmeyecek.
- Eğer corpus backfill gerekiyorsa source/materialization planına taşınmalı.

## Commit

```text
Create Phase 22E P0 legal corpus truth packet
```

Push zorunlu.

---

## 6. Phase 22E-B — Corpus Backfill Plan

Bu adım yalnız Phase 22E-A sonucunda `corpus_backfill_required` çıkan satırlar için yapılacak.

## Output

```text
reports/benchmark/phase_22E_corpus_backfill_plan.md
reports/benchmark/phase_22E_corpus_backfill_plan.csv
```

## Her backfill item için

```text
qid
source_title
source_family
source_identifier
official_source_url
raw_source_available
raw_source_format
needs_download
needs_text_extraction
needs_parser_update
needs_article_span_materialization
needs_source_catalog_update
needs_milvus_reindex
target_collection
validation_qids
rollback_plan
```

## Backfill kuralları

- Private answer key commit edilmeyecek.
- Official/public source kullanılacak.
- Raw source hash kaydedilecek.
- Body text extraction deterministic olacak.
- New spans canonical key v2 ile materialize edilecek.
- Shadow index kullanılmadan live collection overwrite edilmeyecek.
- Reindex sonrası önce targeted smoke, sonra full benchmark.

## Commit

```text
Plan P0 corpus backfill and materialization
```

Push zorunlu.

---

## 7. Phase 22E-C — Optional Shadow Backfill

Bu adım sadece resmi kaynak ve güvenli parser yolu hazırsa yapılacak.

## Amaç

Backfill’i live collection’a doğrudan basmadan shadow index üzerinde doğrulamak.

## Target collection

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

## Yapılacaklar

- source text ingest
- body extraction
- article/span materialization
- canonical source key v2 generation
- Milvus shadow reindex
- source catalog / supplement hash update
- runtime provenance update

## Targeted smoke

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

```text
MULGA >= 4/5
TEBLIGLER >= 7/8 preferred, >=6/8 minimum
unsupported_confident_answer = 0
contract_valid = all rows
source_key_v2_collision = 0
binding_collision = 0
```

If P0 rows do not improve but corpus truth is correct, classify as manual/legal review or scorer proxy mismatch.

## Commit

```text
Validate P0 corpus backfill on shadow collection
```

Push zorunlu.

---

## 8. Phase 22E-D — P1 Legal Taxonomy Review

## Amaç

P1 rows için runtime relabeling yapmadan önce family/document taxonomy kararlarını netleştirmek.

P1 rows:

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

## Output

```text
reports/benchmark/phase_22E_P1_legal_taxonomy_review.md
reports/benchmark/phase_22E_P1_legal_taxonomy_review.csv
```

## Her row için

```text
qid
current_selected_document
current_family
expected_family
expected_document_if_available
legal_taxonomy_issue
is_runtime_family_relabel_safe
is_document_identity_fix_safe
needs_manual_legal_review
needs_corpus_backfill
safe_action
priority
```

## Özel kararlar

### CBY-04

- CB_YONETMELIK vs CB_KARARNAME ayrımı manuel hukuki taxonomy gerektiriyor.
- Runtime relabeling yapılmayacak.

### KKY-01 / KKY-03

- KKY vs YONETMELIK sınırı zayıflatılmayacak.
- Generic yönetmelik belgesini KKY diye relabel etmek yasak.

### YON-04

- Metadata expected title görüyor ama source retention wrong-domain seçiyor.
- Geniş title/domain bias eklenmeden önce manual review gerekir.

### TUZUK-05

- Article-zero / tüzük materialization durumu incelenmeli.
- Answer synthesis patch yapılmayacak.

## Commit

```text
Review P1 legal taxonomy residuals
```

Push zorunlu.

---

## 9. Phase 22E-E — Decision Report

## Output

```text
reports/benchmark/phase_22E_corpus_legal_review_decision.md
```

## Karar seçenekleri

### Option A — P0 corpus backfill ready

```text
Open Phase 22F P0 shadow backfill implementation
No productization
No fine-tuning
```

### Option B — P0 needs manual legal review first

```text
Open Phase 22M manual legal review packet
No runtime patching
No productization
No fine-tuning
```

### Option C — P0 accepted as explicit corpus backlog

```text
Open Phase 23 Productization Readiness Audit with known P0 corpus backlog
Only if legally accepted and risk is documented
Fine-tuning still closed
```

### Option D — P0 still unresolved and not acceptable

```text
Continue corpus/legal investigation
No productization
No fine-tuning
```

---

## 10. Productization Gate

Productization remains closed during Phase 22E.

Productization can be discussed only if:

```text
Phase 22A stability accepted
P0 blockers resolved OR formally accepted by manual legal review
runtime serving config separated from benchmark config
residual risk register created
green lane stable
contract_valid = 100/100
unsupported_confident_claim <= 2
```

---

## 11. Fine-Tuning Gate

Fine-tuning remains closed.

Reason:

- Remaining blockers are corpus/source/span/legal-taxonomy issues.
- Fine-tuning will not fix missing body spans or wrong legal taxonomy.
- Private benchmark contamination risk remains.

Do not open fine-tuning in Phase 22E.

---

## 12. Required Final Report

Produce:

```text
reports/benchmark/phase_22E_corpus_legal_review_report.md
```

Report content:

1. commit SHA list
2. P0 legal/corpus truth packet
3. P0 corpus backfill plan
4. optional shadow backfill result
5. P1 legal taxonomy review
6. productization gate decision
7. fine-tuning gate decision
8. recommended next phase

---

## Final Note

Phase 22D correctly avoided unsafe runtime patches.  
Phase 22E must not repeat runtime heuristic attempts.

The correct work now is to establish legal/corpus truth for P0 blockers, prepare safe corpus backfill if possible, and classify remaining taxonomy risks before any productization-readiness discussion.
