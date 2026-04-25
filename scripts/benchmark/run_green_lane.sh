#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${GREEN_LANE_OUT_DIR:-$ROOT_DIR/reports/benchmark/green_lane/$(date -u +%Y%m%dT%H%M%SZ)}"
RUN_DIR=""
CI_MODE="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ci)
      CI_MODE="true"
      shift
      ;;
    --run-dir)
      RUN_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -n "${BENCHMARK_PYTHON:-}" ]]; then
  PYTHON_BIN="$BENCHMARK_PYTHON"
elif [[ -x "$ROOT_DIR/api-gateway/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/api-gateway/.venv/bin/python"
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  echo "No project virtualenv Python found. Set BENCHMARK_PYTHON or create api-gateway/.venv." >&2
  exit 2
fi

case "$PYTHON_BIN" in
  *".venv"*|*"venv"*) ;;
  *)
    if [[ "${ALLOW_NON_VENV_PYTHON:-}" != "1" ]]; then
      echo "Refusing non-venv Python for benchmark green lane: $PYTHON_BIN" >&2
      exit 2
    fi
    ;;
esac

mkdir -p "$OUT_DIR"
echo "benchmark-green-lane python=$PYTHON_BIN"
echo "benchmark-green-lane out_dir=$OUT_DIR"

"$PYTHON_BIN" -m py_compile \
  "$ROOT_DIR/scripts/benchmark/run_hukuk_ai_100.py" \
  "$ROOT_DIR/scripts/benchmark/score_hukuk_ai_100.py" \
  "$ROOT_DIR/scripts/benchmark/check_private_guard.py" \
  "$ROOT_DIR/scripts/benchmark/validate_hukuk_ai_100_public_questions.py" \
  "$ROOT_DIR/scripts/benchmark/validate_hukuk_ai_100_run.py"

"$PYTHON_BIN" "$ROOT_DIR/scripts/benchmark/check_private_guard.py" \
  --json-out "$OUT_DIR/private_guard.json"

"$PYTHON_BIN" "$ROOT_DIR/scripts/benchmark/validate_hukuk_ai_100_public_questions.py" \
  --json-out "$OUT_DIR/public_questions.json"

if [[ -z "$RUN_DIR" && "$CI_MODE" != "true" ]]; then
  RUN_DIR="$(find "$ROOT_DIR/reports/benchmark/runs" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | tail -n 1 || true)"
fi

RUN_VALIDATION_STATUS="skipped"
if [[ -n "$RUN_DIR" ]]; then
  "$PYTHON_BIN" "$ROOT_DIR/scripts/benchmark/validate_hukuk_ai_100_run.py" \
    --run-dir "$RUN_DIR" \
    --require-provenance \
    --json-out "$OUT_DIR/run_validation.json" \
    --md-out "$OUT_DIR/run_validation.md"
  RUN_VALIDATION_STATUS="pass"
elif [[ "$CI_MODE" == "true" ]]; then
  printf '{"status":"skipped","reason":"ci mode without live benchmark artifact"}\n' > "$OUT_DIR/run_validation.json"
else
  echo "No benchmark run artifact found under reports/benchmark/runs; pass --run-dir." >&2
  exit 2
fi

cat > "$OUT_DIR/summary.json" <<EOF
{
  "status": "pass",
  "python": "$PYTHON_BIN",
  "ci_mode": $CI_MODE,
  "run_validation": "$RUN_VALIDATION_STATUS",
  "out_dir": "$OUT_DIR"
}
EOF

cat > "$OUT_DIR/summary.md" <<EOF
# Benchmark Green Lane

- status: pass
- python: \`$PYTHON_BIN\`
- ci_mode: \`$CI_MODE\`
- run_validation: \`$RUN_VALIDATION_STATUS\`
- out_dir: \`$OUT_DIR\`
EOF

echo "benchmark-green-lane status=pass"
