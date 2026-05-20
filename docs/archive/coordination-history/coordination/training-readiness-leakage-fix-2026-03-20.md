# Training Readiness Leakage Fix

**Tarih:** 2026-03-20  
**Amaç:** `final_train.jsonl` içindeki held-out contamination'ı kaldırmak ve training gate'i tekrar çalışır hale getirmek.

## Bulgular

- `scripts/check_training_readiness.py` ilk çalıştırmada `final_train.jsonl` ile `held_out_test.jsonl` arasında **22** overlapping soru buldu.
- Sorun veri yokluğundan değil, build script karşılaştırma biçiminden kaynaklanıyordu.
- `scripts/build_training_dataset.py` held-out seti yüklerken tüm `input` metnini set'e alıyor, train tarafında ise yalnız `SORU:` sonrası parçayı kıyaslıyordu.
- Sonuç olarak contamination filtresi tanımlıydı ama gerçek veride etkin değildi.

## Uygulanan Düzeltme

1. `scripts/build_training_dataset.py` içine ortak question normalizer eklendi.
2. Held-out yükleme ve contamination filtresi aynı normalize edilmiş soru metni üzerinden çalışacak hale getirildi.
3. Script varsayılanı tek batch yerine repo içindeki **tüm** `reconciled_master.jsonl` dosyalarını kapsayacak şekilde güncellendi.
4. `data/finetune/sft/final_train.jsonl` script ile yeniden üretildi.

## Sonuç

### Önce
- `final_train.jsonl`: **1076** satır
- `held_out_test.jsonl`: **22** satır
- readiness gate: **FAIL**

### Sonra
- `final_train.jsonl`: **923** satır
- `held_out_test.jsonl`: **22** satır
- readiness gate: **PASS**

Komut:

```bash
python3 scripts/check_training_readiness.py \
  --mode preflight \
  --baseline-evidence-path evaluation/reports/eval_live_20260308_080601.json
```

## Sayısal Notlar

- Raw reconciled pool: **1076** lawyer-reviewed kayıt
- Exact duplicate removal: **26**
- Held-out contamination removal: **127** satır
- Temiz train output: **923** satır

Buradaki `127` sayısı yalnızca 22 unique held-out sorusunu değil, bu soruların batch'ler arası tekrarlarını da içerir.

## Kalan Risk

- Train set içinde **116** question-level duplicate hâlâ bulunuyor.
- Bu tekrarlar ayrı bir veri kalitesi işi olarak ele alınmalı; bu düzeltme onları otomatik olarak çözmez.
- Eval tarafında `95q` ve `170q` soru dosyaları çalışma ağacında hâlâ eksik.

## Sonraki Adım

Plana göre bir sonraki iş:

1. `configs/evaluation/test_questions_v2_95.json`
2. `configs/evaluation/test_questions_v3_170.json`

Bu iki set repo’ya geri alınmadan canonical eval matrix tamamlanmış sayılmayacak.
