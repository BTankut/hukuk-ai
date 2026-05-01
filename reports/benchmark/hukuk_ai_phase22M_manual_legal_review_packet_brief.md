# Hukuk-AI — Phase 22M Manual Legal Review Packet Brief

## Karar

Phase 22E **tamamlandı** ve karar netleşti:

```text
Option B — P0 needs manual legal review first
```

Bu nedenle sıradaki faz:

```text
Phase 22M — Manual Legal Review Packet for P0/P1 Residuals
```

Phase 22M bir runtime remediation fazı değildir.

Amaç:
- P0 blocker’lar için hukukî kaynak zincirini kesinleştirmek
- corpus backfill için resmî kaynak ve madde/span beklentisini netleştirmek
- P1 residual taxonomy/document identity konularında hukukî sınırları belirlemek
- Phase 22F P0 shadow backfill için gerekli legal sign-off paketini üretmek

Productization kapalı.  
Fine-tuning kapalı.  
Runtime patch yok.

---

## 1. Mevcut Durum

Phase 22A stability geçti. Phase 22D stability’yi bozmadı. Phase 22E ise runtime patch yapılmadan corpus/legal truth seviyesine indi.

Phase 22E bulguları:

| QID | Finding | Decision |
|---|---|---|
| `MULGA-01` | `16532` body-bearing source görünür, fakat effective-state/current-law relation 2026 için eksik veya stale. Selected Sayıştay span title-only. | Manual legal review + corpus state/current-law bridge backfill gerekli. |
| `TEB-06` | `23093` source görünür, fakat article body spans title-only/body=0. Exact expected tebliğ identity hukukî teyit istiyor. | Official body materialization + legal review gerekli. |

Phase 22E-D P1 review sonucu:

| QID | Decision |
|---|---|
| `CBY-04` | CB_YONETMELIK vs CB_KARARNAME taxonomy review gerekli. Runtime relabel yok. |
| `KANUN-12` | Expected primary law belirlenmeden patch yok. |
| `KKY-01` | KKY/YONETMELIK taxonomy review gerekli. Runtime relabel yok. |
| `KKY-03` | Expected document belirlenmeden patch yok. |
| `TUZUK-05` | Corpus/span materialization veya manual review gerekli. |
| `YON-04` | Document identity patch öncesi manual review gerekli. |

---

# 2. Phase 22M Ana Hedefleri

## 2.1 P0 Legal Sign-Off

Aşağıdaki iki P0 row için hukukî kesinlik sağlanmalı:

```text
MULGA-01
TEB-06
```

Her biri için karar:

```text
confirmed_expected_source
confirmed_article_or_clause
confirmed_effective_state
confirmed_current_law_relation
confirmed_backfill_required
or
accepted_as_manual_residual
```

## 2.2 P1 Legal Taxonomy Sign-Off

Aşağıdaki P1 rows için taxonomy / expected source sınırı netleştirilmeli:

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

## 2.3 Phase 22F Readiness

Manual legal review sonucunda Phase 22F için şu karar verilmeli:

```text
Proceed to P0 shadow backfill
or
Do not backfill; accept residual legal/corpus backlog
or
Need more official source acquisition
```

---

# 3. Kesin Kurallar

Phase 22M boyunca:

- runtime code change yok
- source_identity patch yok
- article_span_selection patch yok
- answer_synthesis patch yok
- answer_slots patch yok
- live Milvus collection update yok
- private answer key commit yok
- fine-tuning yok
- productization yok
- QID-specific runtime rule yok

Yalnız rapor, hukukî inceleme paketi, kaynak listesi ve backfill readiness hazırlanacak.

---

# 4. Phase 22M-A — P0 Manual Legal Review Packet

## Amaç

`MULGA-01` ve `TEB-06` için hukuk uzmanına verilecek doğrulama paketini üretmek.

## Output

```text
reports/benchmark/phase_22M_P0_manual_legal_review_packet.md
reports/benchmark/phase_22M_P0_manual_legal_review_packet.csv
```

## Her P0 row için alanlar

```text
qid
benchmark_family
current_score
current_selected_source
current_selected_span
current_failure_classes
candidate_expected_source
candidate_expected_article_or_clause
candidate_current_law_source
candidate_transition_or_repeal_source
official_source_candidates
official_source_urls
corpus_catalog_record
milvus_visibility
body_span_availability
known_legal_uncertainty
question_for_legal_reviewer
required_legal_decision
backfill_implication
```

---

## 4.1 MULGA-01 Legal Review Questions

Hukukî olarak cevaplanması gerekenler:

```text
1. Benchmark sorusunda beklenen tarihsel kaynak tam olarak hangisidir?
2. 2012 tarihli Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği bu soru için doğru tarihsel kaynak mı?
3. Bu yönetmeliğin yürürlükten kaldırılma kaynağı ve tarihi nedir?
4. 2026 referans tarihinde geçerli current-law basis 2547 sayılı Kanun m.54 müdür?
5. Cevapta tarihsel yönetmelik mi, yürürlükten kaldırma aracı mı, yoksa 2547 m.54 mü primary source olmalıdır?
6. Corpus içinde `16532` source’un effective_state değeri nasıl işaretlenmelidir?
7. Hangi article/span materialize edilmelidir?
8. Runtime’ın Sayıştay Kanunu m.98 seçimi hukukî olarak tamamen yanlış mı, yoksa destekleyici tarihsel bağlam mı?
```

Beklenen legal review output:

```text
mulga01_expected_primary_source
mulga01_expected_historical_source
mulga01_expected_current_source
mulga01_repeal_instrument
mulga01_expected_article_or_clause
mulga01_effective_state_correction
mulga01_backfill_required
mulga01_safe_runtime_behavior
```

---

## 4.2 TEB-06 Legal Review Questions

Hukukî olarak cevaplanması gerekenler:

```text
1. Benchmark sorusunda beklenen primary source tam olarak hangi tebliğdir?
2. 2016 tarihli `Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ` (`23093`) doğru primary source mudur?
3. Yoksa beklenen kaynak ayrı bir `Ticaret Sicili Tebliği` midir?
4. Yoksa doğru kaynak zinciri `6102 sayılı Türk Ticaret Kanunu` + Ticaret Sicili Yönetmeliği + şirket kuruluş tebliği midir?
5. Hangi madde veya span cevap için gerekir?
6. `23093 m.6` gerçekten ilgili hüküm mü?
7. Corpus backfill için hangi resmî metin esas alınmalıdır?
8. Title-only/body=0 durumda runtime ne yapmalıdır: insufficient evidence mı, source identity correction mı?
```

Beklenen legal review output:

```text
teb06_expected_primary_source
teb06_expected_supporting_sources
teb06_expected_article_or_clause
teb06_official_source_url
teb06_body_materialization_required
teb06_source_catalog_update_required
teb06_safe_runtime_behavior
```

---

# 5. Phase 22M-B — P1 Manual Taxonomy Review Packet

## Amaç

P1 rows için family/document taxonomy kararlarını hukukî olarak netleştirmek.

## Output

```text
reports/benchmark/phase_22M_P1_manual_taxonomy_review_packet.md
reports/benchmark/phase_22M_P1_manual_taxonomy_review_packet.csv
```

## Rows

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

## Her row için alanlar

```text
qid
current_selected_source
current_family
expected_family_if_known
current_failure
taxonomy_issue
legal_question
possible_expected_source_candidates
runtime_relabel_risk
source_identity_fix_risk
corpus_backfill_risk
required_legal_decision
```

---

## 5.1 CBY-04

Review questions:

```text
1. Bu soru CB_YONETMELIK mi, CB_KARARNAME mi bekliyor?
2. Seçilen Cumhurbaşkanlığı Kararnamesi hukukî olarak doğru primary source olabilir mi?
3. Eğer benchmark CB_YONETMELIK bekliyorsa, beklenen source title nedir?
4. Runtime’da CB_KARARNAME source’u CB_YONETMELIK olarak relabel etmek hukuken yanlış mı?
```

Expected decision:

```text
do_not_relabel
or
expected_cb_yonetmelik_source_identified
```

## 5.2 KANUN-12

Review questions:

```text
1. Soru hangi kanunu primary source olarak bekliyor?
2. Seçilen araştırma reaktörü yönetmeliği sadece supporting source mu?
3. Beklenen kanun corpus içinde var mı?
4. KANUN-over-regulation promotion güvenli mi?
```

## 5.3 KKY-01 / KKY-03

Review questions:

```text
1. İlgili belge KKY mi, generic YONETMELIK mi?
2. Kurum/kurul düzenlemesi family taxonomy açısından hangi kategoriye girmeli?
3. Runtime family relabel güvenli mi?
4. Beklenen source identity nedir?
```

## 5.4 TUZUK-05

Review questions:

```text
1. Doğru tüzük source hangisi?
2. Seçilen article-zero span yeterli mi?
3. Corpus article/span materialization eksik mi?
4. Backfill gerekir mi?
```

## 5.5 YON-04

Review questions:

```text
1. Beklenen document kişisel veri silme/yok etme/anonimleştirme yönetmeliği mi?
2. Neden nuclear safety regulation seçiliyor?
3. Expected source title ve identifier nedir?
4. Metadata expected source’u görüyor mu?
5. Source retention fix güvenli mi yoksa corpus/legal mapping mi gerekiyor?
```

---

# 6. Phase 22M-C — Official Source Acquisition Checklist

## Amaç

Phase 22F shadow backfill’e geçmeden önce official source paketlerinin hazır olup olmadığını denetlemek.

## Output

```text
reports/benchmark/phase_22M_official_source_acquisition_checklist.md
reports/benchmark/phase_22M_official_source_acquisition_checklist.csv
```

## Her source için

```text
source_title
source_family
official_url
source_type
publication_date
official_gazette_no
raw_text_available
raw_pdf_available
html_available
downloaded
sha256
parser_ready
article_boundaries_detectable
known_encoding_or_ocr_issue
license_or_usage_note
```

## Required candidates

Minimum:

```text
2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği
2023 repeal instrument for that regulation
2547 sayılı Kanun m.54 current basis
23093 Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ
candidate Ticaret Sicili Tebliği if legal review identifies it
6102 sayılı TTK relevant provisions if legal review requires source chain
```

---

# 7. Phase 22M-D — Decision Report

## Output

```text
reports/benchmark/phase_22M_manual_legal_review_decision.md
```

## Decision options

### Option A — Legal sign-off complete, backfill ready

```text
Open Phase 22F P0 Shadow Backfill Implementation
```

### Option B — Legal sign-off incomplete

```text
Continue manual legal review
No runtime patch
No productization
No fine-tuning
```

### Option C — P0 accepted as explicit backlog

```text
Open Phase 23 Productization Readiness Audit with accepted P0 backlog
Only if legal owner signs off
```

### Option D — P0 legally invalidates benchmark item

```text
Open benchmark rubric review
Do not train or patch runtime for invalid item
```

---

# 8. Phase 22F Preview

Phase 22F açılacaksa sadece legal sign-off ve official source acquisition sonrası açılmalı.

Phase 22F scope:

```text
P0 shadow backfill implementation
no live collection overwrite
shadow collection only
targeted smoke
then full benchmark
then cutover decision
```

Target shadow collection:

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

---

# 9. Productization / Fine-Tuning

Productization remains closed.

Fine-tuning remains closed.

Do not open either until:

```text
manual legal review completed
P0 status resolved or formally accepted
official source acquisition documented
shadow backfill validated if needed
two stable full benchmark runs remain clean
benchmark contamination controls documented
```

---

# 10. Required Final Report

Produce:

```text
reports/benchmark/phase_22M_manual_legal_review_packet_report.md
```

Report content:

1. commit SHA list
2. P0 legal review packet
3. P1 taxonomy review packet
4. official source acquisition checklist
5. legal review decision
6. next phase recommendation
7. productization gate decision
8. fine-tuning gate decision

---

## Final Note

Do not attempt another runtime heuristic patch for `MULGA-01` or `TEB-06` before legal review.

Phase 22M’s output should be a legal/corpus decision package, not executable remediation.
