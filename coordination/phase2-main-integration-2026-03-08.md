# Phase 2 Main Integration Report — 2026-03-08

## Özet
Accepted Phase 2 işleri `main` üzerine başarıyla entegre edildi:

1. `feat/phase2-guardrails-safe-scope` @ `7585f0b`
   - Safe-scope guardrails default: Presidio/KVKK masking + input moderation
   - Riskli facts/output blocking varsayılan dışı bırakıldı
2. `feat/phase2-ft-data-prep` @ `b05175b703499c199ca88918ae77d809625427d8`
   - FT veri klasörleri, JSONL şemaları, extraction/validation scriptleri, quality gate dokümantasyonu

Ek olarak entegrasyon sonrası guardrails pipeline’da input moderation akışı düzeltildi:
- Moderation kontrolü masking sonrası false-negative üretmemesi için ham sorgu üzerinde çalışacak şekilde güncellendi.

## Reranker Kararı (değişmedi)
- `feat/phase2-reranker-activation` **merge edilmedi**.
- Reranker **default-off** durumda bırakıldı.

## Doğrulama
### Guardrails test subset
```bash
api-gateway/.venv/bin/pytest -q \
  api-gateway/tests/test_guardrails_config.py \
  api-gateway/tests/test_guardrails_pipeline_smoke.py \
  api-gateway/tests/test_guardrails_bench_smoke.py
```
Sonuç: **16 passed**

### FT data schema doğrulama
```bash
python3 scripts/validate_ft_data.py --file data/finetune/sft/legal_qa.jsonl --type sft
python3 scripts/validate_ft_data.py --file data/finetune/sft/petition_examples.jsonl --type sft
python3 scripts/validate_ft_data.py --file data/finetune/sft/rag_corrected.jsonl --type sft
python3 scripts/validate_ft_data.py --file data/finetune/sft/refusal_examples.jsonl --type sft
python3 scripts/validate_ft_data.py --file data/finetune/dpo/preference_pairs.jsonl --type dpo
python3 scripts/validate_ft_data.py --file data/finetune/eval/held_out_test.jsonl --type sft
```
Sonuç: **tüm dosyalar PASSED**

## Kalan Açık İşler
- Gerçek log extraction + avukat review + ≥%80 approval gate
- LoRA fine-tuning (dgxnode2)
- YİM veri genişlemesi
