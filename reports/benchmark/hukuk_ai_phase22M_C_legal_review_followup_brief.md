# Hukuk-AI — Phase 22M-C Legal Review Follow-Up Brief

## Karar

Phase 22M-R tamamlandı ancak Phase 22F açılamaz.

Seçili karar:

```text
Option C — Continue legal review
```

Neden:

- `filled_phase_22M_P0_manual_legal_review_packet.csv` repo içinde yok.
- `filled_phase_22M_P1_manual_taxonomy_review_packet.csv` repo içinde yok.
- `filled_phase_22M_official_source_acquisition_checklist.csv` repo içinde yok.
- P0 legal sign-off yok.
- P1 taxonomy sign-off yok.
- Official source URL / raw download / SHA-256 / parser readiness kanıtı yok.
- Phase 22F P0 shadow backfill kapalı.
- Productization kapalı.
- Fine-tuning kapalı.
- Runtime patch yok.

Phase 22M-C’nin amacı kod yazmak değil; legal-review ve official-source acquisition sürecini tamamlatacak takip paketini hazırlamaktır.

---

## 1. Girdi Durumu

Avukatlara gönderilmiş kaynak CSV’ler:

```text
reports/benchmark/phase_22M_P0_manual_legal_review_packet.csv
reports/benchmark/phase_22M_P1_manual_taxonomy_review_packet.csv
reports/benchmark/phase_22M_official_source_acquisition_checklist.csv
```

Beklenen dönüş dosyaları:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
filled_phase_22M_official_source_acquisition_checklist.csv
```

Bu üç filled dosya gelmeden:

- Phase 22F açılmayacak
- shadow backfill yapılmayacak
- runtime/source patch yapılmayacak
- live collection update yapılmayacak
- productization açılmayacak
- fine-tuning açılmayacak

---

## 2. Kesin Kurallar

Phase 22M-C boyunca:

- runtime code change yok
- source identity patch yok
- article/span selector patch yok
- answer synthesis patch yok
- answer slot patch yok
- Milvus live collection update yok
- shadow collection build yok
- QID-specific runtime rule yok
- benchmark answer key kullanılmayacak
- productization yok
- fine-tuning yok

---

## 3. Phase 22M-C-A — Legal Review Follow-Up Package

## Amaç

Avukatlara tekrar gönderilecek kısa ve kapalı uçlu takip paketini üretmek.

## Output

```text
reports/benchmark/phase_22M_C_legal_review_followup_packet.md
reports/benchmark/phase_22M_C_legal_review_followup_checklist.md
```

## İçerik

Paket şunları belirtmeli:

1. Doldurulması gereken 3 CSV dosyası
2. Eksik kalırsa Phase 22F’nin açılmayacağı
3. P0 rows:
   - `MULGA-01`
   - `TEB-06`
4. P1 rows:
   - `CBY-04`
   - `KANUN-12`
   - `KKY-01`
   - `KKY-03`
   - `TUZUK-05`
   - `YON-04`
5. Official source URL, raw download, SHA-256 ve parser readiness zorunluluğu
6. Runtime patch yapılmayacağı
7. Private benchmark answer key paylaşılmayacağı

## Commit

```text
Prepare Phase 22M-C legal review follow-up package
```

---

## 4. Phase 22M-C-B — P0 Reviewer Instructions

## Output

```text
reports/benchmark/phase_22M_C_P0_reviewer_instructions.md
```

## MULGA-01 için avukatın cevaplaması gerekenler

```text
1. Beklenen tarihsel kaynak 2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği mi?
2. Bu yönetmeliğin repeal instrument bilgisi nedir?
3. 2026 itibarıyla current-law basis 2547 sayılı Kanun m.54 mü?
4. Cevapta primary source ne olmalı?
5. Hangi madde/span materialize edilmeli?
6. 16532 source effective_state nasıl düzeltilmeli?
7. Sayıştay Kanunu m.98 bu benchmark item için hukuken ilgisiz mi?
```

## TEB-06 için avukatın cevaplaması gerekenler

```text
1. Beklenen primary source 23093 şirket kuruluş tebliği mi?
2. Yoksa başka bir Ticaret Sicili Tebliği mi bekleniyor?
3. 6102 TTK + Ticaret Sicili Yönetmeliği + tebliğ source chain gerekli mi?
4. Hangi madde veya madde aralığı doğrudan cevap kaynağıdır?
5. Official source URL nedir?
6. Body materialization gerekir mi?
7. Title-only/body=0 durumda runtime insufficient evidence mı vermeli?
```

## Commit

```text
Prepare Phase 22M-C P0 reviewer instructions
```

---

## 5. Phase 22M-C-C — P1 Taxonomy Reviewer Instructions

## Output

```text
reports/benchmark/phase_22M_C_P1_taxonomy_reviewer_instructions.md
```

## P1 rows

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

## Her row için doldurulacak alanlar

```text
qid
legal_reviewer_decision
legal_reviewer_notes
expected_source_if_any
taxonomy_decision
runtime_relabel_allowed
backfill_required
```

## Commit

```text
Prepare Phase 22M-C P1 taxonomy reviewer instructions
```

---

## 6. Phase 22M-C-D — Official Source Acquisition Instructions

## Output

```text
reports/benchmark/phase_22M_C_official_source_acquisition_instructions.md
```

## Her source için zorunlu alanlar

```text
source_title
official_url
source_type
publication_date
official_gazette_no
downloaded
raw_file_path
sha256
parser_ready
article_boundaries_detectable
notes
```

## Minimum source candidates

```text
2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği
2023 repeal instrument for that regulation
2547 sayılı Kanun m.54
23093 Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ
Candidate Ticaret Sicili Tebliği if legal review identifies it
6102 sayılı TTK relevant provisions if legal review requires source chain
```

## Commit

```text
Prepare Phase 22M-C official source acquisition instructions
```

---

## 7. Phase 22M-C-E — Handoff Summary

## Output

```text
reports/benchmark/phase_22M_C_legal_review_handoff_summary.md
```

## İçerik

1. Neden review gerekli?
2. Hangi CSV’ler doldurulacak?
3. P0 ve P1 rows listesi
4. Official source acquisition gereksinimleri
5. Eksik kalırsa Phase 22F’nin açılamayacağı
6. Runtime patch yapılmayacağı
7. Productization/fine-tuning kapalı olduğu

## Commit

```text
Prepare Phase 22M-C handoff summary
```

---

## 8. Final Report

## Output

```text
reports/benchmark/phase_22M_C_legal_review_followup_report.md
```

## İçerik

1. commit SHA listesi
2. hazırlanan follow-up dosyaları
3. avukatlara gönderilecek input CSV listesi
4. doldurulması gereken output CSV listesi
5. P0 legal decision summary
6. P1 taxonomy decision summary
7. official source acquisition summary
8. Phase 22F gate status
9. productization gate decision
10. fine-tuning gate decision

## Final decision

```text
Await filled legal review CSV files.
No runtime work.
No productization.
No fine-tuning.
```

---

## 9. Phase 22M-R2 Preview

Aşağıdaki dosyalar geldiğinde yeni intake yapılacak:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
filled_phase_22M_official_source_acquisition_checklist.csv
```

Sonra açılacak faz:

```text
Phase 22M-R2 — Legal Review Results Intake
```

Eğer uygun karar ve source readiness varsa:

```text
Phase 22F — P0 Shadow Backfill Implementation
```

---

## Final Note

Phase 22M-R eksikliği netleştirdi: filled legal-review dosyaları yok.

Phase 22M-C’nin görevi kod yazmak değil, review sürecini tamamlatacak follow-up paketini üretmektir.
