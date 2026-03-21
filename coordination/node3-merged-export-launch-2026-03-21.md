# Node3 Merged Export Launch

Date: 2026-03-21
Scope: start the official `merged_16bit` export for the current node3 post-train candidate so the adapter can move onto a faster production-style inference path
Decision: the current promotion-eligible adapter is now being exported as a merged 16-bit checkpoint using the Unsloth official `save_pretrained_merged(..., save_method="merged_16bit")` path

## Source Candidate

- host: `dgxnode3`
- base model: `unsloth/Qwen3.5-35B-A3B`
- adapter path: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/lora_adapter`
- target merged path: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/merged_model`

## Repo-Native Tooling Added

- merge helper: `scripts/finetune/merge_unsloth_adapter.py`
- detached launcher: `scripts/finetune/launch_dgxnode3_qwen_external_merge.sh`

The helper loads the base model in 16-bit, attaches the LoRA adapter, clears stale quantization flags, and writes the merged checkpoint through:

```python
model.save_pretrained_merged(output_dir, tokenizer, save_method="merged_16bit")
```

## Launch Result

The detached export was launched on node3 with:

- remote pid file: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/runtime_logs/hukuk_ai_active_807_merge.pid`
- remote log file: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/runtime_logs/hukuk_ai_active_807_merge.log`

The first log lines confirmed the container booted and entered the Unsloth merge path.

## Follow-Up

1. confirm merged artefact completion on node3
2. bind a faster serving runtime to the merged checkpoint
3. re-measure latency before making any stronger live-parity claim
