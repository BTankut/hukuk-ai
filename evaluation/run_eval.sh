#!/usr/bin/env bash
# run_eval.sh — AI Hukuk Asistanı Faz 1 Evaluation Runner
#
# Kullanım:
#   ./evaluation/run_eval.sh                     # Mock mod (API gerektirmez)
#   ./evaluation/run_eval.sh --live              # Gerçek API (http://localhost:8000)
#   ./evaluation/run_eval.sh --live --url URL    # Özel API URL
#   ./evaluation/run_eval.sh --category tbk_kira # Tek kategori
#
# Çıktı:
#   evaluation/reports/eval_<mock|live>_<timestamp>.json

set -euo pipefail

# ── Yol ayarları ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
API_GATEWAY="$PROJECT_ROOT/api-gateway"
VENV="$API_GATEWAY/.venv"

# ── Argümanlar ────────────────────────────────────────────────────────────────
MOCK_MODE=true
API_URL="http://localhost:8000"
CATEGORY_ARG=""
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --live)
            MOCK_MODE=false
            shift
            ;;
        --url)
            API_URL="$2"
            shift 2
            ;;
        --category)
            CATEGORY_ARG="--category $2"
            shift 2
            ;;
        --no-verification)
            EXTRA_ARGS="$EXTRA_ARGS --no-verification"
            shift
            ;;
        --verbose|-v)
            EXTRA_ARGS="$EXTRA_ARGS --verbose"
            shift
            ;;
        *)
            echo "Bilinmeyen argüman: $1"
            echo "Kullanım: $0 [--live] [--url URL] [--category CAT] [--no-verification] [--verbose]"
            exit 1
            ;;
    esac
done

# ── Python interpreter seç ───────────────────────────────────────────────────
if [[ -f "$VENV/bin/python" ]]; then
    PYTHON="$VENV/bin/python"
    echo "▸ Python: $PYTHON (api-gateway venv)"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
    echo "▸ Python: $PYTHON (sistem)"
else
    echo "❌ Python bulunamadı!"
    exit 1
fi

# ── Mod bildirimi ─────────────────────────────────────────────────────────────
if $MOCK_MODE; then
    echo "▸ Mod: MOCK (API gerekmez)"
    MOCK_ARG="--mock"
else
    echo "▸ Mod: LIVE API → $API_URL"
    MOCK_ARG=""
fi

echo "▸ Proje kökü: $PROJECT_ROOT"
echo ""

# ── Değerlendirme başlat ──────────────────────────────────────────────────────
$PYTHON "$SCRIPT_DIR/eval_runner.py" \
    ${MOCK_ARG} \
    --api-url "$API_URL" \
    --questions "$PROJECT_ROOT/configs/evaluation/test_questions.json" \
    $CATEGORY_ARG \
    $EXTRA_ARGS

EXIT_CODE=$?

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ Değerlendirme tamamlandı — Tüm Faz 1 kriterleri GEÇTİ"
else
    echo "⚠️  Değerlendirme tamamlandı — Bazı Faz 1 kriterleri BAŞARISIZ"
fi

exit $EXIT_CODE
