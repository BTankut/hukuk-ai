# Historical Finetuning Sonuc Kilitleme Envanteri 2026-04-19

## Official Inventory

| artifact_name | artifact_type | date | lane_name | model_id_or_checkpoint_ref | eval_pack_name | citation_rate | source_correct_rate | hallucination_rate | refusal_accuracy | avg_latency_ms | is_frozen_source_of_record |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `evaluation/reports/eval_live_20260308_080601.json` | `baseline_eval_report` | `2026-03-08` | `baseline_lane` | `base-acceptance-runtime-20260308 / Qwen/Qwen3.5-35B-A3B-FP8` | `live-50` | `0.88` | `0.7707` | `0.08` | `0.90` | `9357.4` | `true` |
| `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_stable_20260321.json` | `post_train_eval_report` | `2026-03-21` | `dgx1_merged_lane` | `dgx1_merged_8004_stable / hukuk_ai_sft_qwen35_807` | `faz1-50` | `0.7647` | `0.6843` | `0.0` | `1.0` | `15593.2` | `false` |
| `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_docker_refresh_20260322.json` | `post_train_eval_report` | `2026-03-22` | `dgx1_merged_lane` | `dgx1_merged_8004_docker_refresh / hukuk_ai_sft_qwen35_807` | `faz1-50` | `0.78` | `0.682` | `0.02` | `0.98` | `16696.2` | `false` |
| `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_refusal_fix_20260322.json` | `post_train_eval_report` | `2026-03-22` | `dgx1_merged_lane` | `dgx1_merged_8005_refusal_fix / hukuk_ai_sft_qwen35_807` | `faz1-50` | `0.7959` | `0.6857` | `0.0612` | `1.0` | `16267.5` | `false` |
| `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_tbk044_fix_20260322.json` | `post_train_eval_report` | `2026-03-22` | `dgx1_merged_lane` | `dgx1_merged_8006_tbk044_fix / hukuk_ai_sft_qwen35_807` | `faz1-50` | `0.7917` | `0.7069` | `0.0208` | `0.9792` | `15427.8` | `false` |
| `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_precision_fix_20260322.json` | `post_train_eval_report` | `2026-03-22` | `dgx1_merged_lane` | `dgx1_merged_8009_precision_fix / hukuk_ai_sft_qwen35_807` | `faz1-50` | `0.86` | `0.82` | `0.02` | `1.0` | `10172.4` | `true` |
| `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json` | `post_train_eval_report` | `2026-03-22` | `dgx1_merged_lane` | `dgx1_merged_8010_post_promotion_cleanup / hukuk_ai_sft_qwen35_807` | `faz1-50` | `0.88` | `0.86` | `0.0` | `1.0` | `9116.5` | `true` |

## Source-Of-Record Meaning

- historical baseline source-of-record = `evaluation/reports/evidence_baseline_faz1_50_20260308.json`
- historical merged source-of-record = `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json`
- historical fine-tuning advantage frozen in repo = `true`
- frozen historical merged advantage present = `true`
