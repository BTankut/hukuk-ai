# DGXNode2 LoRA Bootstrap Runbook

Bu runbook dgxnode2 üzerinde resmi fine-tune zincirini ayağa kaldırmak içindir. Ortam kurulumunu, aktif package gate'ini ve eğitim öncesi promotion hazırlığını kapsar.

## Resmi Giriş Noktaları

- `scripts/finetune/bootstrap_dgxnode2_unsloth.sh`
- `scripts/finetune/validate_dgxnode2_env.sh`
- `scripts/finetune/check_finetune_config.py`
- `scripts/finetune/train_qwen35_textonly_peft.py`
- `configs/finetune/unsloth_sft_qwen35_35b_a3b.json`
- `configs/training/sft_config.yaml`
- `configs/training/sft_llamafactory.yaml`

## 1) Repo ve branch

```bash
ssh btankut@dgxnode2
cd ~/hukuk-ai
git fetch origin
git checkout main
git pull --ff-only
```

## 2) Environment bootstrap

```bash
bash scripts/finetune/bootstrap_dgxnode2_unsloth.sh ~/.venvs/hukuk-ai-ft
```

Beklenen sonuç: Python, Torch, CUDA ve Unsloth stack versiyonları listelenir; script `[INFO] Bootstrap tamamlandı` ile biter.

## 3) Node preflight

```bash
bash scripts/finetune/validate_dgxnode2_env.sh ~/.venvs/hukuk-ai-ft
```

Beklenen sonuç: `[RESULT] PRE-FLIGHT PASSED`

## 4) Aktif package gate

```bash
source ~/.venvs/hukuk-ai-ft/bin/activate
python3 scripts/finetune/check_finetune_config.py \
  --config configs/finetune/unsloth_sft_qwen35_35b_a3b.json
```

Beklenen sonuç:
- Geçerse: `[RESULT] READY_FOR_TRAINING_GATE`
- Geçmezse: train SHA, row count, held-out row count veya readiness gate sebebiyle fail verir.

Bu adım, aşağıdaki resmi preflight zincirini içerir:

```bash
python3 scripts/check_training_readiness.py \
  --mode preflight \
  --expected-eval-family faz1-50 \
  --max-question-duplicate-excess 0 \
  --baseline-evidence-path evaluation/reports/evidence_baseline_faz1_50_20260308.json \
  --workflow-file scripts/build_training_dataset.py \
  --workflow-file configs/finetune/unsloth_sft_qwen35_35b_a3b.json
```

## 5) Training config seçimi

Primary yol:

- `configs/training/sft_config.yaml`

Fallback yol:

- `configs/training/sft_llamafactory.yaml`

Fallback yalnız Unsloth stack'i dgxnode2 üzerinde bozulursa kullanılmalı; active dataset ve promotion standardı değişmez.

Text-only smoke / training entrypoint:

- `python3 scripts/finetune/train_qwen35_textonly_peft.py --config configs/finetune/unsloth_sft_qwen35_35b_a3b.json --dry-run`

## 6) Eğitim sonrası zorunlu zincir

Training tamamlandığında promotion için en az şu adımlar gerekir:

1. Aynı eval family ile raw post-train report üret.
2. `scripts/build_eval_evidence_manifest.py` ile `role=post_train` manifest üret.
3. `scripts/check_training_readiness.py --mode promotion` ile baseline vs post-train manifest kontratını doğrula.

Alternatif olarak komut planını hazır üretmek için:

```bash
python3 scripts/finetune/plan_posttrain_eval.py \
  --checkpoint-ref hukuk-ai-sft-v3 \
  --api-url http://192.168.12.236:8080 \
  --model hukuk-ai-sft-v3 \
  --git-commit $(git rev-parse --short HEAD)
```

Bu repo'da baseline referansı:

- `evaluation/reports/evidence_baseline_faz1_50_20260308.json`

## 7) Serving bloklanırsa diagnostic fallback

`qwen3_5_moe` serving path bloke ise merged checkpoint için şu diagnostic plan kullanılabilir:

```bash
python3 scripts/finetune/plan_posttrain_diagnostic_eval.py \
  --config configs/finetune/unsloth_sft_qwen35_35b_a3b.json \
  --checkpoint-ref hukuk-ai-sft-v3 \
  --model-path /path/to/merged-checkpoint \
  --model hukuk-ai-sft-v3 \
  --git-commit $(git rev-parse --short HEAD)
```

Bu yol promotion shortcut değildir; yalnız runtime recovery / diagnostic içindir.

## Notlar

- Tarihsel `outputs/hukuk-ai-lora-v2` run'ı audit için korunur ama promotion için kullanılamaz.
- Yeni run ancak aktif 807 satırlık canonical package ile ve yeni post-train evidence ile karşılaştırılabilir.
- Bu runbook eğitim komutunu kasıtlı olarak sabitlemez; dgxnode2 ortamında seçilen framework'e göre komut değişebilir. Sabit olan şey gate ve evidence contract'tır.
