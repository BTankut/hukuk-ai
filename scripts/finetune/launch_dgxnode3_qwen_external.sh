#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-smoke}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE_HOST="${REMOTE_HOST:-btankut@dgxnode3}"
REMOTE_REPO="${REMOTE_REPO:-/home/btankut/hukuk-ai-git}"
EXTERNAL_REPO="${EXTERNAL_REPO:-/home/btankut/dgx-spark-unsloth-qwen3.5-training}"
REMOTE_EXPORT_PATH="${REMOTE_REPO}/data/finetune/sft/final_train_sharegpt.jsonl"
DATASET_TARGET_NAME="${DATASET_TARGET_NAME:-hukuk_ai_active_807_sharegpt.jsonl}"
REMOTE_DATASET_PATH="${EXTERNAL_REPO}/data/${DATASET_TARGET_NAME}"
REMOTE_LOG_DIR="${EXTERNAL_REPO}/runtime_logs"

case "${MODE}" in
  smoke)
    JOB_NAME="hukuk_ai_active_807_smoke"
    RUN_ARGS=(
      --dataset "/workspace/data/${DATASET_TARGET_NAME}"
      --max_steps 1
      --batch_size 1
      --output_dir /workspace/outputs/hukuk_ai_active_807_smoke
    )
    ;;
  full)
    JOB_NAME="hukuk_ai_active_807_run"
    RUN_ARGS=(
      --dataset "/workspace/data/${DATASET_TARGET_NAME}"
      --num_train_epochs 3
      --batch_size 1
      --output_dir /workspace/outputs/hukuk_ai_active_807_run
    )
    ;;
  *)
    echo "[FAIL] Unsupported mode: ${MODE}" >&2
    echo "Usage: $0 [smoke|full]" >&2
    exit 1
    ;;
esac

printf -v RUN_ARGS_S "%q " "${RUN_ARGS[@]}"
RUN_ARGS_S="${RUN_ARGS_S% }"

echo "[INFO] mode=${MODE}"
echo "[INFO] remote_host=${REMOTE_HOST}"
echo "[INFO] remote_repo=${REMOTE_REPO}"
echo "[INFO] external_repo=${EXTERNAL_REPO}"

echo "[STEP] Sync repo to node3"
rsync -az --delete --exclude '.git' --exclude '__pycache__' "${REPO_ROOT}/" "${REMOTE_HOST}:${REMOTE_REPO}/"

echo "[STEP] Run frozen package gate on node3"
ssh "${REMOTE_HOST}" "cd ${REMOTE_REPO} && python3 scripts/finetune/check_finetune_config.py --config configs/finetune/unsloth_sft_qwen35_35b_a3b.json"

echo "[STEP] Export ShareGPT compatibility dataset on node3"
ssh "${REMOTE_HOST}" "cd ${REMOTE_REPO} && python3 scripts/finetune/export_sharegpt_dataset.py --output ${REMOTE_EXPORT_PATH}"

echo "[STEP] Copy exported dataset into proven external Qwen repo"
ssh "${REMOTE_HOST}" "cp ${REMOTE_EXPORT_PATH} ${REMOTE_DATASET_PATH}"

echo "[STEP] Launch detached ${MODE} run on node3"
ssh "${REMOTE_HOST}" "\
  mkdir -p ${REMOTE_LOG_DIR} && \
  python3 ${REMOTE_REPO}/scripts/finetune/detach_logged_job.py \
    --workdir ${EXTERNAL_REPO} \
    --log-path ${REMOTE_LOG_DIR}/${JOB_NAME}.log \
    --pid-path ${REMOTE_LOG_DIR}/${JOB_NAME}.pid \
    -- /bin/bash -lc 'cd ${EXTERNAL_REPO} && ./run_train.sh ${RUN_ARGS_S}'"

echo "[INFO] remote_log=${REMOTE_LOG_DIR}/${JOB_NAME}.log"
echo "[INFO] remote_pid=${REMOTE_LOG_DIR}/${JOB_NAME}.pid"
