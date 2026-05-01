# Hukuk-AI — Phase 22M-H Legal Review Pending / Intake Readiness Brief

## Karar

Phase 22M-C tamamlandı ve Phase 22M-R sonucuna göre hâlâ şu karar geçerli:

```text
Await filled legal review CSV files.
No runtime work.
No productization.
No fine-tuning.
```

Repo’daki Phase 22M-C raporu, üç filled CSV dönmeden Phase 22F’nin kapalı kalacağını söylüyor:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
filled_phase_22M_official_source_acquisition_checklist.csv
```

Bu nedenle sıradaki görev runtime geliştirme değil, legal-review pending state’i ve Phase 22M-R2 intake hazırlığını repo’da netleştirmektir.

---

## 1. Mevcut Girdi Durumu

Avukatlara gönderilecek mevcut input CSV’ler:

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

Bu üç dosya gelmeden:

- Phase 22F açılmayacak.
- Shadow backfill yapılmayacak.
- Runtime/source patch yapılmayacak.
- Live collection update yapılmayacak.
- Productization açılmayacak.
- Fine-tuning açılmayacak.

---

## 2. Kesin Kurallar

Phase 22M-H boyunca:

- runtime code change yok
- source identity patch yok
- article/span selector patch yok
- answer synthesis patch yok
- answer slot patch yok
- retrieval / top-k / prompt değişikliği yok
- Milvus live collection update yok
- shadow collection build yok
- benchmark run yok
- productization yok
- fine-tuning yok
- QID-specific rule yok

Bu faz yalnızca dokümantasyon / intake-readiness fazıdır.

---

## 3. Phase 22M-H-A — Pending State Marker

## Amaç

Repo’da mevcut durumun açıkça görülebilmesi için pending marker raporu oluşturmak.

## Output

```text
reports/benchmark/phase_22M_H_legal_review_pending_state.md
```

## İçerik

Rapor şunları içermeli:

1. Phase 22M-C completed.
2. Awaiting filled legal review CSV files.
3. Phase 22F blocked.
4. Productization closed.
5. Fine-tuning closed.
6. Runtime work prohibited.
7. Expected input/output file list.
8. Next phase trigger condition.

## Commit

```text
Record Phase 22M legal review pending state
```

Push zorunlu.

---

## 4. Phase 22M-H-B — Filled CSV Schema Checklist

## Amaç

Avukatlardan dönecek filled CSV dosyalarının minimum şema beklentisini tek bir yerde belgelemek.

## Output

```text
reports/benchmark/phase_22M_H_filled_csv_schema_checklist.md
```

## P0 filled CSV required fields

```text
qid
legal_reviewer_decision
legal_reviewer_notes
confirmed_expected_source
confirmed_article_or_clause
official_source_url
effective_state_decision
current_law_relation
backfill_required
```

## P1 filled CSV required fields

```text
qid
legal_reviewer_decision
legal_reviewer_notes
expected_source_if_any
taxonomy_decision
runtime_relabel_allowed
backfill_required
```

## Official source acquisition filled CSV required fields

```text
source_title
official_url
downloaded
raw_file_path
sha256
parser_ready
article_boundaries_detectable
```

## Commit

```text
Document Phase 22M filled CSV schema checklist
```

Push zorunlu.

---

## 5. Phase 22M-H-C — Phase 22M-R2 Intake Checklist

## Amaç

Filled CSV’ler geldiğinde Phase 22M-R2’nin elle yeniden tasarlanmasına gerek kalmadan çalışabilmesi için intake checklist hazırlamak.

## Output

```text
reports/benchmark/phase_22M_H_R2_intake_checklist.md
```

## Checklist

Phase 22M-R2 açılmadan önce doğrulanacaklar:

```text
filled P0 CSV exists
filled P1 CSV exists
filled official source checklist exists
P0 decisions use allowed enum
P1 decisions use allowed enum
official URLs populated
SHA-256 hashes populated
parser readiness confirmed
article boundaries detectable
no private answer key included
no runtime config included in legal CSVs
```

## Phase 22M-R2 expected outputs

```text
reports/benchmark/phase_22M_R2_review_file_validation.md
reports/benchmark/phase_22M_R2_P0_decision_normalization.md
reports/benchmark/phase_22M_R2_P1_taxonomy_decision_normalization.md
reports/benchmark/phase_22M_R2_phase22F_readiness_decision.md
reports/benchmark/phase_22M_R2_legal_review_results_intake_report.md
```

## Commit

```text
Prepare Phase 22M-R2 intake checklist
```

Push zorunlu.

---

## 6. Phase 22M-H-D — No-Op Decision Report

## Amaç

Bu fazda neden runtime patch yapılmadığını ve neden bekleme durumunun doğru karar olduğunu kaydetmek.

## Output

```text
reports/benchmark/phase_22M_H_noop_decision.md
```

## İçerik

```text
No runtime work because legal sign-off is absent.
No shadow backfill because official source acquisition is incomplete.
No productization because P0 residuals are unresolved.
No fine-tuning because blockers are legal/corpus/source materialization issues.
```

## Commit

```text
Record Phase 22M-H no-op decision
```

Push zorunlu.

---

## 7. Final Report

## Output

```text
reports/benchmark/phase_22M_H_legal_review_pending_report.md
```

## İçerik

1. commit SHA listesi
2. pending state summary
3. expected filled CSV list
4. schema checklist summary
5. Phase 22M-R2 intake checklist summary
6. no-op decision
7. productization gate decision
8. fine-tuning gate decision
9. trigger condition for next phase

## Final decision

```text
Await filled legal review CSV files.
No runtime work.
No productization.
No fine-tuning.
```

---

## 8. Next Phase Trigger

Aşağıdaki dosyalar repo’ya eklendiğinde Phase 22M-R2 açılacak:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
filled_phase_22M_official_source_acquisition_checklist.csv
```

Eğer yalnız official source checklist döner ama legal decisions dönmezse:

```text
Continue legal review.
No Phase 22F.
```

Eğer legal decisions döner ama official sources/hash/parser readiness eksikse:

```text
Open Phase 22S Official Source Acquisition.
No Phase 22F yet.
```

Eğer legal decisions ve source readiness tamamlanırsa:

```text
Open Phase 22F P0 Shadow Backfill Implementation.
```

---

## Final Note

Bu fazın değeri hiçbir şeyi bozmamaktır.

Legal-review çıktıları yokken runtime davranışı değiştirmek, Phase 22’nin stabilite kazanımını riske atar.
