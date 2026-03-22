#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
EVAL_PY="${PROJECT_ROOT}/evaluation/eval_runner.py"
PYTHON="${PYTHON:-python3}"

ROLE=""
API_URL=""
MODEL_REF=""
CHECKPOINT_REF=""
LABEL=""
GIT_COMMIT="${GIT_COMMIT:-$(git -C "${PROJECT_ROOT}" rev-parse --short HEAD)}"
TIMEOUT="${TIMEOUT:-120}"
DELAY="${DELAY:-0.5}"
OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/evaluation/reports}"
NO_VERIFICATION=false

usage() {
  cat <<'EOF'
Usage:
  run_matched_eval_family.sh \
    --role baseline|post_train \
    --api-url http://127.0.0.1:8000 \
    --model-ref <logical_model_id> \
    --checkpoint-ref <runtime_id> \
    --label <artifact_label>

Options:
  --timeout SEC
  --delay SEC
  --output-dir DIR
  --no-verification
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --role)
      ROLE="$2"
      shift 2
      ;;
    --api-url)
      API_URL="$2"
      shift 2
      ;;
    --model-ref)
      MODEL_REF="$2"
      shift 2
      ;;
    --checkpoint-ref)
      CHECKPOINT_REF="$2"
      shift 2
      ;;
    --label)
      LABEL="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    --delay)
      DELAY="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --no-verification)
      NO_VERIFICATION=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -n "${ROLE}" ]] || die "--role is required"
[[ -n "${API_URL}" ]] || die "--api-url is required"
[[ -n "${MODEL_REF}" ]] || die "--model-ref is required"
[[ -n "${CHECKPOINT_REF}" ]] || die "--checkpoint-ref is required"
[[ -n "${LABEL}" ]] || die "--label is required"

case "${ROLE}" in
  baseline|post_train) ;;
  *)
    die "--role must be baseline or post_train"
    ;;
esac

mkdir -p "${OUTPUT_DIR}"

run_case() {
  local family="$1"
  local questions="$2"
  local output="${OUTPUT_DIR}/eval_${ROLE}_${family}_matched_${LABEL}.json"

  local -a cmd=(
    "${PYTHON}"
    "${EVAL_PY}"
    "--questions" "${questions}"
    "--api-url" "${API_URL}"
    "--timeout" "${TIMEOUT}"
    "--delay" "${DELAY}"
    "--eval-family" "${family}"
    "--model-ref" "${MODEL_REF}"
    "--checkpoint-ref" "${CHECKPOINT_REF}"
    "--git-commit" "${GIT_COMMIT}"
    "--report-role" "${ROLE}"
    "--output" "${output}"
  )

  if [[ "${NO_VERIFICATION}" == true ]]; then
    cmd+=("--no-verification")
  fi

  printf '== %s ==\n' "${family}"
  printf 'output: %s\n' "${output}"
  "${cmd[@]}"
}

run_case "faz1-50" "${PROJECT_ROOT}/configs/evaluation/test_questions.json"
run_case "v2-95" "${PROJECT_ROOT}/configs/evaluation/test_questions_v2_95.json"
run_case "v3-170" "${PROJECT_ROOT}/configs/evaluation/test_questions_v3_170.json"
