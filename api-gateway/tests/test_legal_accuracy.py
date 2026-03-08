from __future__ import annotations

import json
import os
from pathlib import Path


CITATION_RATE_MIN = 0.90
CORRECT_SOURCE_RATE_MIN = 0.70
HALLUCINATION_RATE_MAX = 0.10
REFUSAL_RATE_MIN = 0.80
CATEGORY_ACCURACY_MIN = 0.60
MIN_QUESTION_COUNT = 50


def _load_eval_report() -> dict:
    default_path = Path(__file__).parent / "fixtures" / "legal_eval_report.sample.json"
    report_path = Path(os.getenv("LEGAL_EVAL_REPORT", str(default_path)))
    return json.loads(report_path.read_text(encoding="utf-8"))


class TestLegalAccuracy:
    """Faz 1 kalite gate'leri: contract değişmeden korunur."""

    def test_source_citation_rate(self):
        report = _load_eval_report()
        assert report["total_questions"] >= MIN_QUESTION_COUNT
        assert report["source_citation_rate"] >= CITATION_RATE_MIN

    def test_correct_source_rate(self):
        report = _load_eval_report()
        assert report["correct_source_rate"] >= CORRECT_SOURCE_RATE_MIN

    def test_hallucination_rate(self):
        report = _load_eval_report()
        assert report["hallucination_rate"] <= HALLUCINATION_RATE_MAX

    def test_refusal_on_unknown(self):
        report = _load_eval_report()
        assert report["refusal_on_unknown_rate"] >= REFUSAL_RATE_MIN

    def test_per_category_accuracy(self):
        report = _load_eval_report()
        per_category = report["per_category_accuracy"]
        assert per_category, "Kategori bazlı doğruluk metrikleri boş olamaz."
        for category_name, accuracy in per_category.items():
            assert accuracy >= CATEGORY_ACCURACY_MIN, (
                f"{category_name} doğruluğu eşik altında: "
                f"{accuracy:.2%} < {CATEGORY_ACCURACY_MIN:.2%}"
            )
