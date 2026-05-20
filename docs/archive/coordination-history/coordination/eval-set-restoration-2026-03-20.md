# Eval Set Restoration

**Tarih:** 2026-03-20  
**Amaç:** Canonical eval matrix'i tekrar tamamlamak için eksik 95q ve 170q soru setlerini repo'ya geri almak.

## Bulgular

- `scripts/run_eval_matrix.sh all` başlangıçta yalnız `faz1-50` setini çözebiliyor, `phase3-95` adımında duruyordu.
- Eksik dosyalar:
  - `configs/evaluation/test_questions_v2_95.json`
  - `configs/evaluation/test_questions_v3_170.json`
- Git geçmişi incelendiğinde ilgili tarihsel kaynaklar bulundu:
  - `6c157e3` → `configs/evaluation/test_questions_v2.json`
  - `429c650` → `configs/evaluation/test_questions_v3.json`

## Uygulanan Düzeltme

1. Tarihsel `v2` ve `v3` setleri git geçmişinden geri alındı.
2. Mevcut tooling ile uyumlu olması için bunlar wrapper metadata ile şu adlara yazıldı:
   - `configs/evaluation/test_questions_v2_95.json`
   - `configs/evaluation/test_questions_v3_170.json`
3. `evaluation/eval_runner.py` hem wrapped dict hem plain-array soru setlerini okuyabilecek şekilde genişletildi.

## Doğrulama

Komutlar:

```bash
python3 -m py_compile evaluation/eval_runner.py
bash -n scripts/run_eval_matrix.sh
./scripts/run_eval_matrix.sh all
```

Sonuç:

- `test_questions_v2_95.json` → **95** soru
- `test_questions_v3_170.json` → **170** soru
- `run_eval_matrix.sh all` artık üç canonical set için de komutları eksiksiz çözüyor

## Sonraki Adım

Plana göre sıradaki iş:

1. Reranker A/B baseline
2. Threshold sweep
3. Sonuçlara göre `enable / keep-off / rework` kararı
