# Phase 2 — Candidate Expansion (2026-03-09)

## Durum
Phase 2 pending-review havuzu, repo içindeki gerçek artefaktlardan yeniden genişletildi.
Üretilen yeni paketin tamamı **pending-review** olarak etiketlidir; hiçbir kayıt otomatik olarak avukat onaylı kabul edilmez.

## Kullanılan kaynaklar (repo/artifacts)
1. `api-gateway/src/data_pipeline/fixtures/tbk_detail.html` (TBK tam HTML fixture, mevzuat metni)
2. `data/review_sheets/phase2_first_batch_20260308/reconciled_20260308/batch1_first100_reconciled_master.jsonl` (reconciled correction-pair kayıtları)

## Üretilen çıktı dosyaları
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/sft_train_pending_review.jsonl`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/sft_heldout_pending_review.jsonl`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/sft_all_pending_review.jsonl`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/candidate_metadata.jsonl`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/extraction_manifest.json`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/extraction_report.md`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/schema_validation.json`
- `scripts/expand_phase2_pending_candidates.py`

## Sayımlar (origin/source)
Toplam yeni aday (post-dedupe): **2643**
- `synthetic_pending_review_source_grounded_tbk_fixture`: **2604**
- `source_grounded_correction_pair_pending_revalidation`: **39**

Split:
- Train pending-review: **2383**
- Held-out pending-review: **260**

## Source-grounded vs synthetic-pending-review
- **Source-grounded:** 2643/2643 (tamamı gerçek proje/mevzuat kaynağına bağlı)
- **Synthetic-pending-review:** 2604/2643 (TBK madde metinlerinden şablonlu üretim)
- **Non-synthetic pending-review:** 39/2643 (reconciled correction-pair final cevaplarından türetilen, pending-revalidation kayıtları)

## Şema doğrulama
`scripts/validate_ft_data.py` ile SFT şema doğrulaması çalıştırıldı:
- train: PASS
- heldout: PASS
- all: PASS

Ayrıca paket içinde `schema_validation.json` üretildi.

## 1000 örnek blocker etkisi
- Mevcut approved baseline: **100**
- 1000 hedefi için açık: **900**
- Yeni pending aday eklemesi: **2643**

Yorum: Onay açığını doğrudan kapatmaz (çünkü pending), ancak review pipeline’a 900 açık üzerinde **~2.94x** hacimde gerçek kaynaklı aday enjekte ederek blocker’ı pratikte kaldıracak büyüklükte havuz sağlar.

## Commit
- Branch: `feat/phase2-candidate-expansion`
- Commit: `TBD`
