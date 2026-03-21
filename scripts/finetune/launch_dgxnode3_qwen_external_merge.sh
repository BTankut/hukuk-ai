#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE_HOST="${REMOTE_HOST:-btankut@dgxnode3}"
REMOTE_REPO="${REMOTE_REPO:-/home/btankut/hukuk-ai-git}"
EXTERNAL_REPO="${EXTERNAL_REPO:-/home/btankut/dgx-spark-unsloth-qwen3.5-training}"
IMAGE="${IMAGE:-dgx-spark-qwen3.5:latest}"
JOB_NAME="${JOB_NAME:-hukuk_ai_active_807_merge}"
REMOTE_LOG_DIR="${EXTERNAL_REPO}/runtime_logs"
REMOTE_OUTPUT_DIR="${REMOTE_OUTPUT_DIR:-${EXTERNAL_REPO}/outputs/hukuk_ai_active_807_run/merged_model}"
REMOTE_ADAPTER_PATH="${REMOTE_ADAPTER_PATH:-${EXTERNAL_REPO}/outputs/hukuk_ai_active_807_run/lora_adapter}"

echo "[INFO] remote_host=${REMOTE_HOST}"
echo "[INFO] remote_repo=${REMOTE_REPO}"
echo "[INFO] external_repo=${EXTERNAL_REPO}"
echo "[INFO] adapter_path=${REMOTE_ADAPTER_PATH}"
echo "[INFO] output_dir=${REMOTE_OUTPUT_DIR}"

echo "[STEP] Sync repo to node3"
rsync -az --delete --exclude '.git' --exclude '__pycache__' "${REPO_ROOT}/" "${REMOTE_HOST}:${REMOTE_REPO}/"

echo "[STEP] Launch detached merge job on node3"
ssh "${REMOTE_HOST}" "\
  mkdir -p ${REMOTE_LOG_DIR} && \
  python3 ${REMOTE_REPO}/scripts/finetune/detach_logged_job.py \
    --workdir ${REMOTE_REPO} \
    --log-path ${REMOTE_LOG_DIR}/${JOB_NAME}.log \
    --pid-path ${REMOTE_LOG_DIR}/${JOB_NAME}.pid \
    -- /bin/bash -lc 'if [ -w /proc/sys/vm/drop_caches ]; then sync && echo 3 > /proc/sys/vm/drop_caches; fi && \
      docker run --rm \
        --gpus all \
        --network host \
        --ipc=host \
        --ulimit memlock=-1 \
        --ulimit stack=67108864 \
        --shm-size=1g \
        -v ${REMOTE_REPO}:/workspace/repo \
        -v ${EXTERNAL_REPO}/outputs:/workspace/outputs \
        -v ${EXTERNAL_REPO}/model:/workspace/model \
        -e HF_HOME=/workspace/model \
        -e HF_HUB_ENABLE_HF_TRANSFER=1 \
        -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
        ${IMAGE} \
        python /workspace/repo/scripts/finetune/merge_unsloth_adapter.py \
          --adapter-path /workspace/outputs/hukuk_ai_active_807_run/lora_adapter \
          --output-dir /workspace/outputs/hukuk_ai_active_807_run/merged_model'"

echo "[INFO] remote_log=${REMOTE_LOG_DIR}/${JOB_NAME}.log"
echo "[INFO] remote_pid=${REMOTE_LOG_DIR}/${JOB_NAME}.pid"
