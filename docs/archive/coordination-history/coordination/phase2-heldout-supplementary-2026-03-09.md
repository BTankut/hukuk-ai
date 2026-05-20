# Phase 2 Held-out + Supplementary Recovery Report (2026-03-09)

## Durum
Second recovery/takeover tamamlandı. Worktree’de kalan gerçek değişiklikler toparlandı, doğrulandı, commit+push yapıldı.

## 1) Güncellenen/Oluşturulan Varlıklar (Exact Assets)

### Güncellenen
1. `data/finetune/eval/held_out_test.jsonl`
   - Önce: 1 satır scaffold placeholder
   - Sonra: **22 gerçek kayıt** (JSONL, SFT şeması)
   - SHA256: `16fcc4e557a9b55d5d820ac2a6317d8e3dcb8b52bc6d8d14b5c6162aad6bfdd5`

### Yeni
2. `data/finetune/sft/sft_training_batch1.jsonl`
   - **78 gerçek kayıt** (JSONL, SFT şeması)
   - SHA256: `8fd4cd59638aff97144af41208441d86fc4eb80991a1f9deee21bc5a2111cbaf`

3. `scripts/prepare_heldout_and_sft.py`
   - Reconciled master’dan held-out + train split üreten script
   - Seed: `42`, stratified split (`category+difficulty`), hedef oran `%20 held-out`
   - SHA256: `7a52332da5038bec1cd0c28f63efad1fdf8c2a025c870f5e9ee0f29366a89c90`

## 2) Held-out artık gerçek mi?
**Evet.**
- `held_out_test.jsonl` artık scaffold değil, gerçek veri içeriyor.
- **Kayıt sayısı: 22**
- Kaynak: `data/review_sheets/phase2_first_batch_20260308/reconciled_20260308/batch1_first100_reconciled_master.jsonl`
- Kaynak doğrulaması: held-out ve sft_training kayıtlarının tamamı reconciled source’tan türetilmiş (`not_from_source=0`).

## 3) Real vs Scaffold-only ayrımı

### Real (bu adımda netleşen)
- `data/finetune/eval/held_out_test.jsonl` (22)
- `data/finetune/sft/sft_training_batch1.jsonl` (78)
- (Önceden mevcut) `data/finetune/sft/phase2_first_batch1_training_candidate_20260308.jsonl` (100, scaffold içermiyor)

### Hâlâ scaffold-only
- `data/finetune/dpo/preference_pairs.jsonl`
- `data/finetune/sft/legal_qa.jsonl`
- `data/finetune/sft/petition_examples.jsonl`
- `data/finetune/sft/rag_corrected.jsonl`
- `data/finetune/sft/refusal_examples.jsonl`

## 4) Doğrulamalar
- JSON parse kontrolü:
  - held_out_test: 22/22 valid JSON
  - sft_training_batch1: 78/78 valid JSON
- Şema doğrulama:
  - `python scripts/validate_ft_data.py --file data/finetune/eval/held_out_test.jsonl --type sft` → PASSED
  - `python scripts/validate_ft_data.py --file data/finetune/sft/sft_training_batch1.jsonl --type sft` → PASSED
- Script çalıştırma çıktısı:
  - Total valid records: 100
  - Held-out set size: 22
  - SFT train set size: 78

## 5) İlk training run öncesi blocker’lar
1. **Held-out adet eşiği henüz sağlanmıyor:** quality gate dokümanında minimum 100 held-out bekleniyor; mevcut 22.
2. **Onaylı SFT hacmi yetersiz:** quality gate’te minimum 1000 onaylı SFT örneği hedefleniyor; bu adım sadece batch1’den 78 train örneği sağladı.
3. **Ana FT dosyalarının bir kısmı hâlâ scaffold:** legal_qa / petition_examples / rag_corrected / refusal_examples / dpo pairleri gerçek içerikle doldurulmadı.
4. **Lawyer approval gate kanıtı eksik:** ≥%80 avukat onay oranına dair güncel, bağlayıcı kayıt bu adımda üretilmedi.

## 6) Git çıktısı
- Branch: `feat/phase2-heldout-supplementary`
- Commit: `4d6d57bba6483fb5b7821bf672914ae01a3426fc`
- Push: `origin/feat/phase2-heldout-supplementary`’e başarıyla gönderildi
- PR URL (remote suggest):
  - `https://github.com/BTankut/hukuk-ai/pull/new/feat/phase2-heldout-supplementary`
