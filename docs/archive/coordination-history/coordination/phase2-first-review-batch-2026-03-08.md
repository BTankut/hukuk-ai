# Phase 2 — First 100-item Lawyer Review Batch (2026-03-08)

## Kapsam
İlk avukat inceleme paketi, `phase1_eval_reports_20260308` pending-review havuzundan **100 kayıt** olarak hazırlandı.

- Kaynak havuz (train_pending_review): **276 kayıt**
- Paket boyutu: **100 kayıt**
- Amaç: Avukatların hemen başlayabileceği, triage metadata'sı (özellikle difficulty/category) içeren pratik CSV seti.

## Çıktı Dosyaları

Repo/worktree içinde üretilen dosyalar:

- `data/review_sheets/phase2_first_batch_20260308/batch1_first100_master.csv`
- `data/review_sheets/phase2_first_batch_20260308/batch1_first100_lawyerA.csv`
- `data/review_sheets/phase2_first_batch_20260308/batch1_first100_lawyerB.csv`
- `data/review_sheets/phase2_first_batch_20260308/batch1_first100_stats.json`
- `data/review_sheets/phase2_first_batch_20260308/README.md`

## Dağılım Özeti (Batch = 100)

### Difficulty
- easy: **18**
- medium: **51**
- hard: **31**

### Category
- tbk_genel: **46**
- tbk_haksiz_fiil: **10**
- tbk_kira: **8**
- tbk_hizmet: **6**
- tbk_vekaletname: **6**
- out_of_scope: **4**
- tbk_eser: **4**
- tbk_kefalet: **4**
- tbk_satis: **4**
- tmk_genel: **4**
- tmk_aile: **2**
- tmk_esya: **2**

### Ek segment bilgileri
- Unique question_id: **46**
- Soru başına örnek sayısı: **2–3** (38 soru için 2 adet, 8 soru için 3 adet)
- Source file dağılımı:
  - `eval_live_20260308_131021.json`: 46
  - `eval_live_reranker_recovery_baseline_20260308.json`: 46
  - `eval_reranker_disabled_8010_20260308.json`: 8

## Yapılan İyileştirmeler

1. `scripts/prepare_review_sheets.py` geliştirildi:
   - metadata enrichment (`candidate_metadata.jsonl`) desteği,
   - `difficulty`/`category`/`question_id`/`source_file` gibi triage sütunları,
   - `--limit` + `--selection balanced` ile ilk 100 paket üretimi,
   - özet istatistik JSON çıktısı (`--stats-output`).

2. `data/review_sheets/template_review.csv` yeni sütun seti ile güncellendi.
3. `docs/review_guidelines.md` sütun dokümantasyonu triage metadata'yı kapsayacak şekilde güncellendi.

## Avukatlara İlk Gönderilecek Dosya

Öncelik sırası:
1. `batch1_first100_lawyerA.csv`
2. `batch1_first100_lawyerB.csv`

`batch1_first100_master.csv` referans/arsiv dosyası olarak saklanmalı.

## Commit

- Branch: `feat/phase2-first-review-batch`
- Commit: **ab99f0d**
