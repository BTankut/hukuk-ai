#!/usr/bin/env bash
# run_eval_matrix.sh — canonical baseline / eval matrix helper
#
# Default behavior is plan mode: print the resolved commands and validate the
# required files. Use --run to execute the matrix.
#
# Modes:
#   faz1-50   -> 50-question acceptance baseline
#   phase3-95 -> 95-question hardening baseline
#   faz2-170  -> 170-question stress / training-readiness baseline
#   all       -> run or print all three in order
#
# Examples:
#   ./scripts/run_eval_matrix.sh
#   ./scripts/run_eval_matrix.sh faz1-50 --run --live
#   ./scripts/run_eval_matrix.sh all --run --mock

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EVAL_PY="$PROJECT_ROOT/evaluation/eval_runner.py"
PYTHON="${PYTHON:-python3}"

MODE="faz1-50"
RUN=false
MOCK_MODE=true
API_URL="http://localhost:8000"
OUTPUT_DIR="$PROJECT_ROOT/evaluation/reports"
VERBOSE=false
NO_VERIFICATION=false
DELAY="0.5"
TIMEOUT="60.0"

usage() {
    cat <<'EOF'
Usage:
  run_eval_matrix.sh [mode] [options]

Default:
  plan mode (no execution) with file validation

Modes:
  faz1-50   50-question acceptance baseline
  phase3-95 95-question hardening baseline
  faz2-170 170-question stress / training-readiness baseline
  all       all three modes in order

Options:
  --run              execute the resolved commands
  --mock             use mock evaluation mode (default)
  --live             use live API mode
  --url URL          API base URL for live mode
  --output-dir DIR    directory for generated reports
  --delay SEC        delay between live requests (default: 0.5)
  --timeout SEC      HTTP timeout in seconds (default: 60.0)
  --no-verification  disable verification engine in eval_runner
  --verbose, -v      enable verbose logging
  --help, -h         show this help
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
        faz1-50)
            CASE_LABEL="faz1-50"
            QUESTIONS_FILE="$PROJECT_ROOT/configs/evaluation/test_questions.json"
            ;;
        phase3-95)
            CASE_LABEL="phase3-95"
            QUESTIONS_FILE="$PROJECT_ROOT/configs/evaluation/test_questions_v2_95.json"
            ;;
        faz2-170)
            CASE_LABEL="faz2-170"
            QUESTIONS_FILE="$PROJECT_ROOT/configs/evaluation/test_questions_v3_170.json"
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

    local output_file="$OUTPUT_DIR/eval_matrix_${CASE_LABEL}_${stamp}.json"
    local -a cmd=(
        "$PYTHON"
        "$EVAL_PY"
        "--questions" "$QUESTIONS_FILE"
        "--output" "$output_file"
        "--api-url" "$API_URL"
        "--delay" "$DELAY"
        "--timeout" "$TIMEOUT"
    )

    if [[ "$MOCK_MODE" == true ]]; then
        cmd+=("--mock")
    fi
    if [[ "$VERBOSE" == true ]]; then
        cmd+=("--verbose")
    fi
    if [[ "$NO_VERIFICATION" == true ]]; then
        cmd+=("--no-verification")
    fi

    printf '== %s ==\n' "$CASE_LABEL"
    printf 'questions: %s\n' "$QUESTIONS_FILE"
    printf 'output:    %s\n' "$output_file"
    printf 'command:   '
    format_cmd "${cmd[@]}"

    if [[ ! -f "$QUESTIONS_FILE" ]]; then
        die "missing question-set file for '$CASE_LABEL': $QUESTIONS_FILE"
    fi

    if [[ "$RUN" == true ]]; then
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
        --mock)
            MOCK_MODE=true
            ;;
        --live)
            MOCK_MODE=false
            ;;
        --url)
            [[ $# -ge 2 ]] || die "--url requires a value"
            API_URL="$2"
            shift
            ;;
        --output-dir)
            [[ $# -ge 2 ]] || die "--output-dir requires a value"
            OUTPUT_DIR="$2"
            shift
            ;;
        --delay)
            [[ $# -ge 2 ]] || die "--delay requires a value"
            DELAY="$2"
            shift
            ;;
        --timeout)
            [[ $# -ge 2 ]] || die "--timeout requires a value"
            TIMEOUT="$2"
            shift
            ;;
        --no-verification)
            NO_VERIFICATION=true
            ;;
        --verbose|-v)
            VERBOSE=true
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

command -v "$PYTHON" >/dev/null 2>&1 || die "python interpreter not found: $PYTHON"
[[ -f "$EVAL_PY" ]] || die "missing eval runner: $EVAL_PY"
mkdir -p "$OUTPUT_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"

case "$MODE" in
    all)
        run_case "faz1-50" "$STAMP"
        run_case "phase3-95" "$STAMP"
        run_case "faz2-170" "$STAMP"
        ;;
    faz1-50|phase3-95|faz2-170)
        run_case "$MODE" "$STAMP"
        ;;
    *)
        die "unknown mode: $MODE"
        ;;
esac
