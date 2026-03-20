#!/usr/bin/env bash
set -euo pipefail

# Prepare a minimal Unsloth fine-tuning environment on dgxnode2.
# This script does not start training.

VENV_DIR="${1:-$HOME/.venvs/hukuk-ai-ft}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log() { echo "[INFO] $*"; }
warn() { echo "[WARN] $*"; }
err() { echo "[ERROR] $*"; }

log "Bootstrap basliyor"
log "Host: $(hostname)"
log "VENV_DIR=${VENV_DIR}"
log "PYTHON_BIN=${PYTHON_BIN}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  err "Python bulunamadi: ${PYTHON_BIN}"
  exit 1
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
  warn "nvidia-smi bulunamadi. Bu script DGX node icin tasarlandi."
else
  log "GPU:"
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | sed 's/^/  - /'
fi

if ! command -v uv >/dev/null 2>&1; then
  warn "uv bulunamadi, user-level kurulum deneniyor..."
  if command -v pip3 >/dev/null 2>&1; then
    pip3 install --user uv
    export PATH="$HOME/.local/bin:$PATH"
  else
    err "pip3 bulunamadi, uv otomatik kurulamadı"
    err "Manuel kurulum: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
  fi
fi

if ! command -v uv >/dev/null 2>&1; then
  err "uv kurulamadı"
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  log "Yeni venv olusturuluyor: ${VENV_DIR}"
  uv venv --python "${PYTHON_BIN}" "${VENV_DIR}"
else
  log "Mevcut venv kullanilacak: ${VENV_DIR}"
fi

# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

log "Paketler kuruluyor (cu130 + Unsloth/PEFT stack)"
uv pip install --upgrade pip wheel setuptools
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
uv pip install unsloth transformers trl peft datasets accelerate sentencepiece protobuf huggingface_hub bitsandbytes

python - <<'PY'
import importlib
import platform
import torch

mods = ["unsloth", "transformers", "trl", "peft", "datasets", "accelerate", "bitsandbytes"]
print("[INFO] Python:", platform.python_version())
print("[INFO] Torch:", torch.__version__)
print("[INFO] CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("[INFO] GPU:", torch.cuda.get_device_name(0))

for name in mods:
    module = importlib.import_module(name)
    print(f"[INFO] {name}: {getattr(module, '__version__', 'unknown')}")
PY

log "Bootstrap tamamlandi"
log "Sonraki adim: bash scripts/finetune/validate_dgxnode2_env.sh ${VENV_DIR}"
log "Ardindan: python3 scripts/finetune/check_finetune_config.py"
