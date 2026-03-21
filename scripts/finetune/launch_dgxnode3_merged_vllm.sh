#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE_HOST="${REMOTE_HOST:-btankut@dgxnode3}"
REMOTE_REPO="${REMOTE_REPO:-/home/btankut/hukuk-ai-git}"
EXTERNAL_REPO="${EXTERNAL_REPO:-/home/btankut/dgx-spark-unsloth-qwen3.5-training}"
IMAGE="${IMAGE:-vllm/vllm-openai:cu130-nightly}"
JOB_NAME="${JOB_NAME:-hukuk_ai_active_807_merged_vllm}"
REMOTE_LOG_DIR="${EXTERNAL_REPO}/runtime_logs"
CONTAINER_NAME="${CONTAINER_NAME:-qwen35_ft_active_807}"
PORT="${PORT:-30003}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-hukuk-ai-sft-qwen35-807-merged}"
MERGED_MODEL_PATH="${MERGED_MODEL_PATH:-${EXTERNAL_REPO}/outputs/hukuk_ai_active_807_run/merged_model}"
HF_CACHE_PATH="${HF_CACHE_PATH:-/home/btankut/.cache/huggingface}"

echo "[INFO] remote_host=${REMOTE_HOST}"
echo "[INFO] merged_model_path=${MERGED_MODEL_PATH}"
echo "[INFO] container_name=${CONTAINER_NAME}"
echo "[INFO] port=${PORT}"
echo "[INFO] served_model_name=${SERVED_MODEL_NAME}"

echo "[STEP] Sync repo to node3"
rsync -az --delete --exclude '.git' --exclude '__pycache__' "${REPO_ROOT}/" "${REMOTE_HOST}:${REMOTE_REPO}/"

echo "[STEP] Launch detached merged vLLM runtime on node3"
ssh "${REMOTE_HOST}" "\
  test -d ${MERGED_MODEL_PATH} && \
  mkdir -p ${REMOTE_LOG_DIR} && \
  python3 ${REMOTE_REPO}/scripts/finetune/detach_logged_job.py \
    --workdir ${REMOTE_REPO} \
    --log-path ${REMOTE_LOG_DIR}/${JOB_NAME}.log \
    --pid-path ${REMOTE_LOG_DIR}/${JOB_NAME}.pid \
    -- /bin/bash -lc 'docker rm -f ${CONTAINER_NAME} >/dev/null 2>&1 || true && \
      docker run --name ${CONTAINER_NAME} -d \
        --gpus all \
        --ipc host \
        --shm-size 64gb \
        -p ${PORT}:${PORT} \
        -v ${MERGED_MODEL_PATH}:/model \
        -v ${HF_CACHE_PATH}:/root/.cache/huggingface \
        ${IMAGE} \
        /model \
        --served-model-name ${SERVED_MODEL_NAME} \
        --port ${PORT} \
        --host 0.0.0.0 \
        --gpu-memory-utilization 0.80 \
        --enforce-eager \
        --reasoning-parser qwen3 \
        --enable-auto-tool-choice \
        --tool-call-parser qwen3_coder \
        --enable-prefix-caching \
        --language-model-only'"

echo "[INFO] remote_log=${REMOTE_LOG_DIR}/${JOB_NAME}.log"
echo "[INFO] remote_pid=${REMOTE_LOG_DIR}/${JOB_NAME}.pid"
