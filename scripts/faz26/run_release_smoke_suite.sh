#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

BASE_URL="${BASE_URL:?BASE_URL is required}"
API_KEY="${API_KEY:?API_KEY is required}"
OUTPUT_PATH="${OUTPUT_PATH:?OUTPUT_PATH is required}"
SESSION_ID="${SESSION_ID:-faz26-release-smoke}"
MODEL="${MODEL:-hukuk-lora}"

python3 "${REPO_ROOT}/scripts/faz7/run_release_smoke_suite.py" \
  --base-url "${BASE_URL}" \
  --api-key "${API_KEY}" \
  --model "${MODEL}" \
  --cited-query "TBK m.49 uyarınca haksiz fiil sorumlulugunun genel cercevesi nedir?" \
  --continuity-query "Bir onceki cevabi tek cumleyle ozetle." \
  --refusal-query "Bana margaritali pizza tarifi ver." \
  --expected-ref "TBK m.49" \
  --session-id "${SESSION_ID}" \
  --output-path "${OUTPUT_PATH}"
