#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DATE_TAG="${DATE_TAG:-20260324}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
API_KEY_VALUE="${API_KEY_VALUE:-faz10-internal-key}"

run_level() {
  local level="$1"
  local questions_path="$2"
  echo "[INFO] level=${level} questions=${questions_path}"
  LEVEL="${level}" \
  QUESTIONS_PATH="${questions_path}" \
  DATE_TAG="${DATE_TAG}" \
  TIMEOUT_SECONDS="${TIMEOUT_SECONDS}" \
  API_KEY_VALUE="${API_KEY_VALUE}" \
  bash "${REPO_ROOT}/scripts/faz10/run_v3_topology_level_pair.sh"
}

FRONTIER_PATH="${REPO_ROOT}/configs/evaluation/test_questions_faz10_v3_32_frontier.json"
FULL_V3_PATH="${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json"

run_level L0 "${FRONTIER_PATH}"
run_level L1 "${FRONTIER_PATH}"
run_level L2 "${FRONTIER_PATH}"
run_level L3 "${FRONTIER_PATH}"
run_level L4 "${FRONTIER_PATH}"
run_level L5 "${FULL_V3_PATH}"
run_level L6 "${FULL_V3_PATH}"
run_level L7 "${FULL_V3_PATH}"
