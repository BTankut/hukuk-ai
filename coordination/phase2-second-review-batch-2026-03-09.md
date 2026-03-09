# Phase 2 — Second Lawyer Review Batch (2026-03-09)

## Kapsam
`phase1_eval_reports_20260308` train pending-review havuzundan, ilk batch'te kullanılan kayıtlar hariç tutularak ikinci avukat inceleme paketi hazırlandı.

- Toplam train havuzu: **276**
- İlk batch'te kullanılan candidate sayısı: **100**
- Dışlama sonrası kalan havuz: **176**
- Bu çalışmada üretilen ikinci batch: **100**
- Bu batch sonrası tahmini kalan havuz: **76**

## Çıktı Dosyaları

- `data/review_sheets/phase2_second_batch_20260309/batch2_second100_master.csv`
- `data/review_sheets/phase2_second_batch_20260309/batch2_second100_lawyerA.csv`
- `data/review_sheets/phase2_second_batch_20260309/batch2_second100_lawyerB.csv`
- `data/review_sheets/phase2_second_batch_20260309/batch2_second100_stats.json`
- `data/review_sheets/phase2_second_batch_20260309/README.md`

## Seçim ve Doğrulama Notları

- İlk batch dışlaması `batch1_first100_master.csv` içindeki `candidate_id` alanı üzerinden yapıldı.
- `batch2_second100_master.csv` ile ilk batch arasında candidate overlap: **0**
- Seçim modu: `balanced` (difficulty/category oranını koruyacak şekilde)

## Batch-2 Dağılımı (n=100)

### Difficulty
- easy: **19**
- medium: **50**
- hard: **31**

### Category
- tbk_genel: **46**
- tbk_haksiz_fiil: **11**
- tbk_kira: **8**
- out_of_scope: **5**
- tbk_hizmet: **5**
- tbk_vekaletname: **5**
- tbk_eser: **4**
- tbk_kefalet: **4**
- tbk_satis: **4**
- tmk_genel: **4**
- tmk_aile: **2**
- tmk_esya: **2**

## Git

- Branch: `feat/phase2-second-review-batch`
- Commit: **b6b020e**
