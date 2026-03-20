#!/usr/bin/env bash
set -euo pipefail

# Preflight checks for dgxnode2 before any LoRA run.

VENV_DIR="${1:-$HOME/.venvs/hukuk-ai-ft}"
FAIL=0

check_cmd() {
  local cmd="$1"
  local label="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[PASS] ${label}: $(command -v "$cmd")"
  else
    echo "[FAIL] ${label}: command not found (${cmd})"
    FAIL=1
  fi
}

echo "[INFO] Host: $(hostname)"
echo "[INFO] Kernel: $(uname -srmo)"

gpu_info="$(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null || true)"
if [[ -n "$gpu_info" ]]; then
  echo "[PASS] GPU:"
  echo "$gpu_info" | sed 's/^/  - /'
else
  echo "[FAIL] GPU bilgisi okunamadi (nvidia-smi)"
  FAIL=1
fi

check_cmd python3 "Python"
check_cmd git "Git"
check_cmd nvidia-smi "NVIDIA-SMI"

if [[ -d "$VENV_DIR" ]]; then
  echo "[PASS] Venv exists: $VENV_DIR"
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
else
  echo "[FAIL] Venv not found: $VENV_DIR"
  FAIL=1
fi

python3 - <<'PY' || FAIL=1
import importlib

modules = ["torch", "transformers", "datasets", "trl", "peft", "unsloth", "huggingface_hub"]
ok = True
for name in modules:
    try:
        module = importlib.import_module(name)
        print(f"[PASS] {name}: {getattr(module, '__version__', 'unknown')}")
    except Exception as exc:
        ok = False
        print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")

if not ok:
    raise SystemExit(1)
PY

python3 - <<'PY' || FAIL=1
import torch

print(f"[INFO] torch.cuda.is_available={torch.cuda.is_available()}")
if not torch.cuda.is_available():
    raise SystemExit("CUDA unavailable")
print(f"[INFO] torch.cuda.device_count={torch.cuda.device_count()}")
print(f"[INFO] torch.cuda.get_device_name(0)={torch.cuda.get_device_name(0)}")
PY

if command -v huggingface-cli >/dev/null 2>&1; then
  if huggingface-cli whoami >/dev/null 2>&1; then
    echo "[PASS] Hugging Face auth: OK"
  else
    echo "[WARN] Hugging Face auth not configured (huggingface-cli whoami failed)"
  fi
else
  echo "[WARN] huggingface-cli not found; token kontrolu atlandi"
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "[RESULT] PRE-FLIGHT FAILED"
  exit 1
fi

echo "[RESULT] PRE-FLIGHT PASSED"
