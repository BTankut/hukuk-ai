# DGXNode3 Qwen Full Run Launch

Date: 2026-03-21
Scope: launch the first full detached Qwen3.5 run on the user-provided proven node3 training path using the active frozen package
Decision: full node3 training is now in progress; the immediate follow-up is monitoring and post-train evidence preparation, not another training-target decision

## Launch Chain

The run was launched through the repo-native wrapper:

- `scripts/finetune/launch_dgxnode3_qwen_external.sh full`

That wrapper performed:

1. repo sync to `dgxnode3`
2. frozen package gate
3. ShareGPT export
4. dataset copy into the proven external Qwen repo
5. detached full run launch

## Verified Pre-Launch State

Before launch, the wrapper re-confirmed:

- `READY_FOR_TRAINING_GATE`
- ShareGPT export `807/807`
- no skipped rows

## Detached Run Details

Remote host:

- `dgxnode3`

Remote log:

- `/home/btankut/dgx-spark-unsloth-qwen3.5-training/runtime_logs/hukuk_ai_active_807_run.log`

Remote pid file:

- `/home/btankut/dgx-spark-unsloth-qwen3.5-training/runtime_logs/hukuk_ai_active_807_run.pid`

Detached wrapper returned:

- pid: `869015`

External trainer workdir:

- `/home/btankut/dgx-spark-unsloth-qwen3.5-training`

Training command inside the proven external repo:

- `./run_train.sh --dataset /workspace/data/hukuk_ai_active_807_sharegpt.jsonl --num_train_epochs 3 --batch_size 1 --output_dir /workspace/outputs/hukuk_ai_active_807_run`

## Initial Health Check

Initial post-launch probe confirmed:

- launcher bash process alive
- Docker container alive
- container image: `dgx-spark-qwen3.5:latest`
- runtime log emitting Unsloth / PyTorch startup lines

Observed container sample:

- container id: `5af4f7d6709a`
- status: `Up 35 seconds`

At this checkpoint the run had clearly started and was not stuck before container boot.

## Next Step

1. monitor the detached full run to completion
2. capture final adapter/output path
3. prepare post-train diagnostic or promotion-evidence chain depending on the resulting artifact
