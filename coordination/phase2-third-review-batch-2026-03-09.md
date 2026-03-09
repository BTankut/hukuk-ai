# Phase 2 — Third Lawyer Review Batch (2026-03-09)

## Kapsam
İlk iki batch (`phase2_first_batch_20260308`, `phase2_second_batch_20260309`) candidate_id dışlaması sonrası kalan train pending-review havuzundan üçüncü (kalanların tamamı) avukat inceleme paketi üretildi.

- Toplam train havuzu: **276**
- Batch1: **100**
- Batch2: **100**
- Batch1+Batch2 dışlama sonrası kalan: **76**
- Bu batch'te üretilen kayıt: **76**
- Bu batch sonrası kalan havuz: **0**

## Çıktı Dosyaları

- `data/review_sheets/phase2_third_batch_20260309/batch3_remaining76_master.csv`
- `data/review_sheets/phase2_third_batch_20260309/batch3_remaining76_lawyerA.csv`
- `data/review_sheets/phase2_third_batch_20260309/batch3_remaining76_lawyerB.csv`
- `data/review_sheets/phase2_third_batch_20260309/batch3_remaining76_stats.json`
- `data/review_sheets/phase2_third_batch_20260309/README.md`

## Overlap Doğrulaması

`batch3_remaining76_master.csv` için candidate_id overlap kontrolleri:

- Batch3 vs Batch1 overlap: **0**
- Batch3 vs Batch2 overlap: **0**
- Batch1 vs Batch2 overlap: **0**

## Batch-3 Dağılımı (n=76)

### Difficulty
- easy: **14**
- medium: **39**
- hard: **23**

### Category
- tbk_genel: **36**
- tbk_haksiz_fiil: **10**
- tbk_kira: **8**
- out_of_scope: **6**
- tbk_hizmet: **5**
- tbk_vekaletname: **5**
- tbk_eser: **2**
- tbk_kefalet: **2**
- tbk_satis: **2**

## Git

- Branch: `feat/phase2-third-review-batch`
- Third batch commit: **9c86cc2**
- (Not: Bu branch'e ikinci batch commit'i de taşındı: **7ff5277**)
