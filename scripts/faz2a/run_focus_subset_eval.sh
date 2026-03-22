#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
EVAL_PY="${PROJECT_ROOT}/evaluation/eval_runner.py"
PYTHON="${PYTHON:-python3}"

MODE="all"
RUN=false
API_URL="${API_URL:-http://localhost:8004}"
MODEL_REF="${MODEL_REF:-gateway-api}"
CHECKPOINT_REF="${CHECKPOINT_REF:-gateway-live}"
GIT_COMMIT="${GIT_COMMIT:-$(git -C "${PROJECT_ROOT}" rev-parse --short HEAD)}"
OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/evaluation/reports}"
TIMEOUT="${TIMEOUT:-180}"
DELAY="${DELAY:-0.2}"
NO_VERIFICATION=false
ROLE="diagnostic"

usage() {
  cat <<'EOF'
Usage:
  run_focus_subset_eval.sh [mode] [options]

Modes:
  tmk-cross-law
  tbk-critical
  all

Default:
  plan mode (print resolved commands only)

Options:
  --run
  --api-url URL
  --model-ref REF
  --checkpoint-ref REF
  --output-dir DIR
  --timeout SEC
  --delay SEC
  --no-verification
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

format_cmd() {
  local arg
  for arg in "$@"; do
    printf '%q ' "$arg"
  done
  printf '\n'
}

resolve_case() {
  local mode="$1"
  case "$mode" in
    tmk-cross-law)
      CASE_LABEL="faz2a_tmk_cross_law"
      QUESTIONS_FILE="${PROJECT_ROOT}/configs/evaluation/test_questions_faz2a_tmk_cross_law_v3_30.json"
      ;;
    tbk-critical)
      CASE_LABEL="faz2a_tbk_critical"
      QUESTIONS_FILE="${PROJECT_ROOT}/configs/evaluation/test_questions_faz2a_tbk_critical_v3_61.json"
      ;;
    *)
      die "unknown mode: $mode"
      ;;
  esac
}

run_case() {
  local mode="$1"
  local stamp="$2"
  resolve_case "$mode"

  [[ -f "${QUESTIONS_FILE}" ]] || die "missing question set: ${QUESTIONS_FILE}"

  local output_file="${OUTPUT_DIR}/eval_${ROLE}_${CASE_LABEL}_${stamp}.json"
  local -a cmd=(
    "${PYTHON}"
    "${EVAL_PY}"
    "--questions" "${QUESTIONS_FILE}"
    "--api-url" "${API_URL}"
    "--timeout" "${TIMEOUT}"
    "--delay" "${DELAY}"
    "--eval-family" "v3-170"
    "--model-ref" "${MODEL_REF}"
    "--checkpoint-ref" "${CHECKPOINT_REF}"
    "--git-commit" "${GIT_COMMIT}"
    "--report-role" "${ROLE}"
    "--include-trace"
    "--output" "${output_file}"
  )

  if [[ "${NO_VERIFICATION}" == true ]]; then
    cmd+=("--no-verification")
  fi

  printf '== %s ==\n' "${CASE_LABEL}"
  printf 'questions: %s\n' "${QUESTIONS_FILE}"
  printf 'output:    %s\n' "${output_file}"
  printf 'command:   '
  format_cmd "${cmd[@]}"

  if [[ "${RUN}" == true ]]; then
    "${cmd[@]}"
  fi
  printf '\n'
}

if [[ $# -gt 0 && "${1:-}" != --* ]]; then
  MODE="$1"
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run)
      RUN=true
      ;;
    --api-url)
      API_URL="$2"
      shift
      ;;
    --model-ref)
      MODEL_REF="$2"
      shift
      ;;
    --checkpoint-ref)
      CHECKPOINT_REF="$2"
      shift
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift
      ;;
    --timeout)
      TIMEOUT="$2"
      shift
      ;;
    --delay)
      DELAY="$2"
      shift
      ;;
    --no-verification)
      NO_VERIFICATION=true
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
  shift
done

mkdir -p "${OUTPUT_DIR}"
STAMP="$(date +%Y%m%d_%H%M%S)"

case "${MODE}" in
  all)
    run_case "tmk-cross-law" "${STAMP}"
    run_case "tbk-critical" "${STAMP}"
    ;;
  tmk-cross-law|tbk-critical)
    run_case "${MODE}" "${STAMP}"
    ;;
  *)
    die "unknown mode: ${MODE}"
    ;;
esac
