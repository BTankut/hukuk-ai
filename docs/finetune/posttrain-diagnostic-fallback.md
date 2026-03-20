# Post-Train Diagnostic Fallback

Bu yol, vLLM serving zinciri bloklandığında merged checkpoint'i doğrudan `transformers` ile ölçmek içindir.

Bu bir **diagnostic fallback**'tır.

Şu an resmi accepted baseline:
- `runner=eval_runner`

Bu fallback ise:
- `runner=eval_transformers_direct`

Bu yüzden üretilen artefact promotion için baseline ile doğrudan karşılaştırılamaz. Ama:
- checkpoint gerçekten yükleniyor mu
- cevap üretiyor mu
- Faz 1 family üzerinde kaba kalite sinyali nasıl

sorularını yanıtlamak için kullanılabilir.

## Plan Komutu

```bash
python3 scripts/finetune/plan_posttrain_diagnostic_eval.py \
  --config configs/finetune/unsloth_sft_qwen35_35b_a3b.json \
  --checkpoint-ref hukuk-ai-sft-v3 \
  --model-path /path/to/merged-checkpoint \
  --model hukuk-ai-sft-v3 \
  --git-commit $(git rev-parse --short HEAD)
```

## Doğrudan Eval

```bash
python3 evaluation/eval_transformers_direct.py \
  --model-path /path/to/merged-checkpoint \
  --model hukuk-ai-sft-v3 \
  --questions configs/evaluation/test_questions.json \
  --output evaluation/reports/eval_diagnostic_post_train_faz1-50_hukuk_ai_sft_v3_YYYYMMDD.json \
  --eval-family faz1-50 \
  --checkpoint-ref hukuk-ai-sft-v3 \
  --git-commit $(git rev-parse --short HEAD) \
  --report-role diagnostic_post_train \
  --trust-remote-code
```

## Kural

- expected sources prompt'a verilmez
- shared `metrics.py` kullanılır
- shared report schema kullanılır
- manifest üretilebilir
- promotion için ayrıca matched runner baseline gerekir
