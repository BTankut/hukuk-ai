#!/usr/bin/env bash
# dgx-vllm-ensure-running.sh
# DGX Spark'ta Qwen3.5-35B-A3B-FP8 vLLM servisini kontrol eder,
# çalışmıyorsa container içinde arka planda başlatır.
#
# Kullanım:
#   bash scripts/dgx-vllm-ensure-running.sh [--wait]
#
# --wait  : Servis health check'i geçene kadar bekle (max 5 dakika)
# Çıkış:
#   0 = servis çalışıyor (veya başarıyla başlatıldı)
#   1 = başlatma/health check başarısız

set -euo pipefail

DGX_HOST="${DGX_HOST:-btankut@192.168.12.243}"
DGX_PORT="${DGX_PORT:-30000}"
DGX_CONTAINER="${DGX_CONTAINER:-vllm_head}"
WAIT_FOR_HEALTH=false
HEALTH_TIMEOUT=300  # saniye

# Model snapshot (container içi yol — sabit; yeni snapshot için güncelle)
MODEL_SNAPSHOT="/root/.cache/huggingface/hub/models--Qwen--Qwen3.5-35B-A3B-FP8/snapshots/0b2752837483aa34b3db6e83e151b150c0e00e49"
SERVED_MODEL="Qwen/Qwen3.5-35B-A3B-FP8"

VLLM_START_CMD="python3 -m vllm.entrypoints.openai.api_server \
  --model ${MODEL_SNAPSHOT} \
  --served-model-name ${SERVED_MODEL} \
  --host 0.0.0.0 \
  --port ${DGX_PORT} \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.85 \
  --dtype auto \
  > /tmp/vllm_serve.log 2>&1"

# RAG context'i genişletmek için: MAX_MODEL_LEN=131072
# VLLM_START_CMD="... --max-model-len 131072 ..."

for arg in "$@"; do
  case $arg in
    --wait) WAIT_FOR_HEALTH=true ;;
  esac
done

echo "[dgx-vllm] DGX host: ${DGX_HOST}"

# 1. vLLM sağlık kontrolü (M4 Max'ten)
check_health() {
  curl -sf --max-time 5 "http://192.168.12.243:${DGX_PORT}/v1/models" \
    -o /dev/null 2>/dev/null
  return $?
}

if check_health; then
  echo "[dgx-vllm] ✅ vLLM zaten çalışıyor (port ${DGX_PORT})"
  exit 0
fi

echo "[dgx-vllm] vLLM çalışmıyor. Container içinde başlatılıyor..."

# 2. Container ayakta mı?
CONTAINER_STATUS=$(ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=no "${DGX_HOST}" \
  "docker inspect ${DGX_CONTAINER} --format '{{.State.Status}}' 2>/dev/null || echo missing")

if [[ "${CONTAINER_STATUS}" != "running" ]]; then
  echo "[dgx-vllm] ❌ Container '${DGX_CONTAINER}' durumu: ${CONTAINER_STATUS}"
  echo "[dgx-vllm]    Container'ı başlatmak için: ssh ${DGX_HOST} 'docker start ${DGX_CONTAINER}'"
  exit 1
fi

# 3. vLLM'i container içinde arka planda başlat
ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=no "${DGX_HOST}" \
  "docker exec -d ${DGX_CONTAINER} bash -c '${VLLM_START_CMD}'"

echo "[dgx-vllm] vLLM başlatma komutu gönderildi (model yükleme ~4 dakika sürer)."

if [[ "${WAIT_FOR_HEALTH}" == "true" ]]; then
  echo "[dgx-vllm] Health check bekleniyor (max ${HEALTH_TIMEOUT}s)..."
  elapsed=0
  while ! check_health; do
    if [[ $elapsed -ge $HEALTH_TIMEOUT ]]; then
      echo "[dgx-vllm] ❌ Health check ${HEALTH_TIMEOUT}s içinde geçmedi."
      echo "[dgx-vllm]    Log için: ssh ${DGX_HOST} 'docker exec ${DGX_CONTAINER} tail -50 /tmp/vllm_serve.log'"
      exit 1
    fi
    sleep 15
    elapsed=$((elapsed + 15))
    echo "[dgx-vllm]   ... ${elapsed}s geçti, bekleniyor..."
  done
  echo "[dgx-vllm] ✅ vLLM sağlıklı (${elapsed}s sonra)."
else
  echo "[dgx-vllm]    Health check için: bash scripts/dgx-vllm-ensure-running.sh --wait"
  echo "[dgx-vllm]    Log için: ssh ${DGX_HOST} 'docker exec ${DGX_CONTAINER} tail -50 /tmp/vllm_serve.log'"
fi
