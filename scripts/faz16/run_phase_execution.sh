#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DATE_TAG="${DATE_TAG:-20260325}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.5}"
API_KEY_VALUE="${API_KEY_VALUE:-faz16-internal-key}"

run_control_family() {
  local family="$1"
  EVAL_FAMILY="${family}" \
  DATE_TAG="${DATE_TAG}" \
  TIMEOUT_SECONDS="${TIMEOUT_SECONDS}" \
  DELAY_SECONDS="${DELAY_SECONDS}" \
  API_KEY_VALUE="${API_KEY_VALUE}" \
  bash "${REPO_ROOT}/scripts/faz16/run_control_pair_current_authority.sh"
}

run_static_builders() {
  python3 "${REPO_ROOT}/scripts/faz16/build_breach_sentinel_16.py" \
    --first-divergence-table "${REPO_ROOT}/coordination/faz15-breach-first-divergence-table-2026-03-25.json" \
    --output-json "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-${DATE_TAG}.json" \
    --output-md "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-${DATE_TAG}.md" \
    --subset-output-faz1 "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-faz1-50-${DATE_TAG}.json" \
    --subset-output-v2 "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-v2-95-${DATE_TAG}.json" \
    --subset-output-v3 "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-v3-170-${DATE_TAG}.json"

  python3 "${REPO_ROOT}/scripts/faz14/build_v3_frontier_subset.py" \
    --questions "${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json" \
    --question-id TBK-051 \
    --question-id TBK-054 \
    --question-id TBK-055 \
    --question-id TBK-057 \
    --question-id TBK-058 \
    --question-id TBK-061 \
    --output "${REPO_ROOT}/coordination/faz16-targeted-6-v3-170-${DATE_TAG}.json"

  python3 "${REPO_ROOT}/scripts/faz16/build_rc_m_manifest.py" \
    --rc-j-manifest "${REPO_ROOT}/coordination/faz9-rc-j-manifest-2026-03-24.json" \
    --git-commit "$(git -C "${REPO_ROOT}" rev-parse HEAD)" \
    --manifest-output-json "${REPO_ROOT}/coordination/faz16-rc-m-manifest-${DATE_TAG}.json" \
    --diff-contract-output-md "${REPO_ROOT}/coordination/faz16-rc-j-to-rc-m-diff-surface-contract-${DATE_TAG}.md" \
    --build-proof-output-md "${REPO_ROOT}/coordination/faz16-rc-m-build-proof-${DATE_TAG}.md"
}

run_rc_m_lane() {
  local eval_family="$1"
  local questions_path="$2"
  local output_path="$3"
  local checkpoint_ref="$4"
  local run_label="$5"
  local gateway_port="$6"
  local tunnel_port="$7"

  RC_KIND=rc_m \
  EVAL_FAMILY="${eval_family}" \
  QUESTIONS_PATH="${questions_path}" \
  OUTPUT_PATH="${output_path}" \
  CHECKPOINT_REF="${checkpoint_ref}" \
  RUN_LABEL="${run_label}" \
  GATEWAY_PORT="${gateway_port}" \
  LOCAL_TUNNEL_PORT="${tunnel_port}" \
  TIMEOUT_SECONDS="${TIMEOUT_SECONDS}" \
  DELAY_SECONDS="${DELAY_SECONDS}" \
  API_KEY_VALUE="${API_KEY_VALUE}" \
  bash "${REPO_ROOT}/scripts/faz16/run_build_surface_lane.sh"
}

run_static_builders

for family in faz1-50 v2-95 v3-170; do
  run_control_family "${family}"
done

run_static_builders

run_rc_m_lane \
  v3-170 \
  "${REPO_ROOT}/coordination/faz16-targeted-6-v3-170-${DATE_TAG}.json" \
  "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_m_v3_170_targeted_${DATE_TAG}.json" \
  "rc-m-targeted-v3-170-${DATE_TAG}" \
  "faz16_rc_m_targeted" \
  8148 \
  30158

run_rc_m_lane \
  faz1-50 \
  "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-faz1-50-${DATE_TAG}.json" \
  "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_m_faz1_50_breach_sentinel_${DATE_TAG}.json" \
  "rc-m-breach-sentinel-faz1-50-${DATE_TAG}" \
  "faz16_rc_m_breach_sentinel_faz1_50" \
  8149 \
  30159

run_rc_m_lane \
  v2-95 \
  "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-v2-95-${DATE_TAG}.json" \
  "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_m_v2_95_breach_sentinel_${DATE_TAG}.json" \
  "rc-m-breach-sentinel-v2-95-${DATE_TAG}" \
  "faz16_rc_m_breach_sentinel_v2_95" \
  8150 \
  30160

run_rc_m_lane \
  v3-170 \
  "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-v3-170-${DATE_TAG}.json" \
  "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_m_v3_170_breach_sentinel_${DATE_TAG}.json" \
  "rc-m-breach-sentinel-v3-170-${DATE_TAG}" \
  "faz16_rc_m_breach_sentinel_v3_170" \
  8241 \
  30241

run_rc_m_lane \
  faz1-50 \
  "${REPO_ROOT}/configs/evaluation/test_questions.json" \
  "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_m_faz1_50_full_family_${DATE_TAG}.json" \
  "rc-m-full-family-faz1-50-${DATE_TAG}" \
  "faz16_rc_m_full_faz1_50" \
  8242 \
  30242

run_rc_m_lane \
  v2-95 \
  "${REPO_ROOT}/configs/evaluation/test_questions_v2_95.json" \
  "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_m_v2_95_full_family_${DATE_TAG}.json" \
  "rc-m-full-family-v2-95-${DATE_TAG}" \
  "faz16_rc_m_full_v2_95" \
  8243 \
  30243

run_rc_m_lane \
  v3-170 \
  "${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json" \
  "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_m_v3_170_full_family_${DATE_TAG}.json" \
  "rc-m-full-family-v3-170-${DATE_TAG}" \
  "faz16_rc_m_full_v3_170" \
  8244 \
  30244

DATE_TAG="${DATE_TAG}" \
PYTHON_BIN=python3 \
bash "${REPO_ROOT}/scripts/faz16/build_phase_package.sh"
