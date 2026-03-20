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
DGX_CONTAINER="${DGX_CONTAINER:-}"
DGX_CONTAINER_CANDIDATES="${DGX_CONTAINER_CANDIDATES:-vllm_qwen35_lowmem,vllm_head,vllm_qwen35moe,qwen35-base-eval}"
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

ssh_dgx() {
  ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=no "${DGX_HOST}" "$@"
}

discover_container() {
  if [[ -n "${DGX_CONTAINER}" ]]; then
    echo "${DGX_CONTAINER}"
    return 0
  fi

  local candidates="${DGX_CONTAINER_CANDIDATES//,/ }"
  ssh_dgx "
    for c in ${candidates}; do
      if docker inspect \"\$c\" >/dev/null 2>&1; then
        echo \"\$c\"
        exit 0
      fi
    done
    exit 1
  "
}

container_status() {
  local container="$1"
  ssh_dgx "docker inspect \"${container}\" --format '{{.State.Status}}' 2>/dev/null || echo missing"
}

container_cmd() {
  local container="$1"
  ssh_dgx "docker inspect \"${container}\" --format '{{json .Config.Cmd}}' 2>/dev/null || echo []"
}

is_direct_vllm_container() {
  local container="$1"
  local cmd_json
  cmd_json="$(container_cmd "${container}")"
  [[ "${cmd_json}" == *"\"vllm\""* && "${cmd_json}" == *"\"serve\""* ]]
}

print_log_hint() {
  local container="$1"
  if is_direct_vllm_container "${container}"; then
    echo "[dgx-vllm]    Log için: ssh ${DGX_HOST} 'docker logs --tail 50 ${container}'"
  else
    echo "[dgx-vllm]    Log için: ssh ${DGX_HOST} 'docker exec ${container} tail -50 /tmp/vllm_serve.log'"
  fi
}

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

DGX_CONTAINER="$(discover_container || true)"
if [[ -z "${DGX_CONTAINER}" ]]; then
  echo "[dgx-vllm] ❌ Uygun vLLM container bulunamadı veya DGX'e SSH erişimi kurulamadı."
  echo "[dgx-vllm]    Adaylar: ${DGX_CONTAINER_CANDIDATES}"
  echo "[dgx-vllm]    Not: farklı runtime için DGX_PORT ve/veya DGX_CONTAINER override edilebilir."
  exit 1
fi

echo "[dgx-vllm] Container: ${DGX_CONTAINER}"

# 2. Container ayakta mı?
CONTAINER_STATUS="$(container_status "${DGX_CONTAINER}")"

if [[ "${CONTAINER_STATUS}" != "running" ]]; then
  if is_direct_vllm_container "${DGX_CONTAINER}"; then
    echo "[dgx-vllm] Container '${DGX_CONTAINER}' doğrudan vLLM serve çalıştırıyor; docker start gönderiliyor..."
    ssh_dgx "docker start \"${DGX_CONTAINER}\" >/dev/null"
  elif [[ "${CONTAINER_STATUS}" == "missing" ]]; then
    echo "[dgx-vllm] ❌ Container '${DGX_CONTAINER}' bulunamadı."
    exit 1
  else
    echo "[dgx-vllm] Wrapper container '${DGX_CONTAINER}' durumu: ${CONTAINER_STATUS}; docker start gönderiliyor..."
    ssh_dgx "docker start \"${DGX_CONTAINER}\" >/dev/null"
  fi
fi

if is_direct_vllm_container "${DGX_CONTAINER}"; then
  echo "[dgx-vllm] Direct vLLM container modu tespit edildi; container start yeterli."
else
  # 3. vLLM'i wrapper container içinde arka planda başlat
  REMOTE_VLLM_START_CMD="$(printf '%q' "${VLLM_START_CMD}")"
  ssh_dgx "docker exec -d \"${DGX_CONTAINER}\" bash -lc ${REMOTE_VLLM_START_CMD}"
  echo "[dgx-vllm] vLLM başlatma komutu gönderildi (model yükleme ~4 dakika sürer)."
fi

if [[ "${WAIT_FOR_HEALTH}" == "true" ]]; then
  echo "[dgx-vllm] Health check bekleniyor (max ${HEALTH_TIMEOUT}s)..."
  elapsed=0
  while ! check_health; do
    if [[ $elapsed -ge $HEALTH_TIMEOUT ]]; then
      echo "[dgx-vllm] ❌ Health check ${HEALTH_TIMEOUT}s içinde geçmedi."
      print_log_hint "${DGX_CONTAINER}"
      exit 1
    fi
    sleep 15
    elapsed=$((elapsed + 15))
    echo "[dgx-vllm]   ... ${elapsed}s geçti, bekleniyor..."
  done
  echo "[dgx-vllm] ✅ vLLM sağlıklı (${elapsed}s sonra)."
else
  echo "[dgx-vllm]    Health check için: bash scripts/dgx-vllm-ensure-running.sh --wait"
  print_log_hint "${DGX_CONTAINER}"
fi
