# Phase2 P1 — Real Log/Artifact QA Extraction Report (2026-03-08)

## Durum
BAŞARILI (ilk gerçek aday havuz extraction tamamlandı; avukat onayı bekliyor)

## 1) İncelenen Faz 1 kaynakları
`evaluation/reports/` altındaki tüm JSON artefaktlar tarandı.

### Güvenli extraction kaynağı olarak kullanılanlar
Kriter: `mock_mode=false`, `error_count=0`, `per_question` alanı mevcut.

- `evaluation/reports/eval_live_20260308_042436.json`
- `evaluation/reports/eval_live_20260308_045101.json`
- `evaluation/reports/eval_live_20260308_080601.json`
- `evaluation/reports/eval_live_20260308_131021.json`
- `evaluation/reports/eval_live_20260308_edgecase_recovery_final.json`
- `evaluation/reports/eval_live_20260308_reindex.json`
- `evaluation/reports/eval_live_reranker_recovery_baseline_20260308.json`
- `evaluation/reports/eval_reranker_disabled_8010_20260308.json`

### Bilinçli olarak dışarıda bırakılanlar
- `evaluation/reports/eval_mock_20260307_221526.json` (mock)
- `evaluation/reports/eval_live_20260308_005802.json` (20/20 error)
- `evaluation/reports/eval_live_20260308_042925.json` (error_count=1)
- `evaluation/reports/reranker_ab_report.sample.json` (eval-per_question şemasında değil)

## 2) Tooling güncellemeleri
Güncellendi: `scripts/extract_qa_from_logs.py`

Yeni yetenekler:
- JSONL log + eval report (`per_question`) extraction desteği
- Mock/error’lı raporları otomatik eleme
- Exact QA dedupe (opsiyonel)
- Reproducible held-out split
- Otomatik çıktı paketleme:
  - `sft_train_pending_review.jsonl`
  - `sft_heldout_pending_review.jsonl`
  - `sft_all_pending_review.jsonl`
  - `candidate_metadata.jsonl`
  - `extraction_manifest.json`
  - `extraction_report.md`

Ek dokümantasyon güncellemesi:
- `docs/quality_gate_workflow.md` (raw/pending_review klasörü + manifest/rapor izlenebilirliği)

## 3) Üretilen ham aday veri (lawyer-approved DEĞİL)
Çıktı klasörü:
- `data/finetune/raw/pending_review/phase1_eval_reports_20260308/`

Sayılar (`extraction_manifest.json`):
- Raw aday (dedupe öncesi): **310**
- Exact duplicate kaldırılan: **6**
- Post-dedupe toplam: **304**
- Train pending-review: **276**
- Held-out pending-review: **28**

Kaynak bazlı katkı (post-dedupe):
- `eval_live_20260308_042436.json` → 20
- `eval_live_20260308_045101.json` → 20
- `eval_live_20260308_080601.json` → 50
- `eval_live_20260308_131021.json` → 50
- `eval_live_20260308_edgecase_recovery_final.json` → 44
- `eval_live_20260308_reindex.json` → 20
- `eval_live_reranker_recovery_baseline_20260308.json` → 50
- `eval_reranker_disabled_8010_20260308.json` → 50

## 4) Held-out split (açık ve reproducible)
Kural:
- `bucket = sha256(normalized_question) % 10`
- Held-out bucket: `[0]`
- Aynı normalize edilmiş soru daima aynı split’e düşer (leakage riskini azaltır)

## 5) Şema validasyonu
Aşağıdaki dosyalar `scripts/validate_ft_data.py --type sft` ile doğrulandı:
- `sft_train_pending_review.jsonl` ✅
- `sft_heldout_pending_review.jsonl` ✅
- `sft_all_pending_review.jsonl` ✅

## 6) Git
- Branch: `feat/phase2-ft-log-extract`
- Commit: `bd25c184274e63c6bf5ada03207b9847c69e574a`
- Push: `origin/feat/phase2-ft-log-extract` (tamam)

## 7) Lawyer review öncesi kalanlar
1. Avukat inceleme paketinin dağıtılması (2-3 danışman).
2. `candidate_metadata.jsonl` içindeki kalite sinyallerine göre önceliklendirme (özellikle `is_hallucination=true` kayıtlar).
3. Onay/düzeltme sonrası approved set’e terfi (hedef: ≥%80 onay, minimum 1000 yüksek kaliteli örnek).
4. Approved havuzdan nihai held-out set politikasının (>=100 soru) korunarak finalize edilmesi.

Not: Bu aşamadaki tüm kayıtlar açıkça **pending-review** statüsündedir; hiçbir kayıt lawyer-approved olarak işaretlenmemiştir.
