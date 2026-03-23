from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "faz4"))

from build_citation_family_failure_pack import classify_failure  # noqa: E402


def test_classify_failure_prefers_residual_false_refusal_for_answer_questions():
    assert (
        classify_failure(
            expected_mode="answer",
            expected_primary_source_id="TBK m.49",
            rc_final_mode="refusal",
            rc_primary_source_id=None,
            supported_source_ids=["TBK m.49"],
        )
        == "residual_false_refusal"
    )


def test_classify_failure_marks_wrong_primary_before_citation_under_emission():
    assert (
        classify_failure(
            expected_mode="answer",
            expected_primary_source_id="TBK m.49",
            rc_final_mode="answer",
            rc_primary_source_id="TBK m.50",
            supported_source_ids=["TBK m.49", "TBK m.50"],
        )
        == "wrong_primary_source_with_supported_answer"
    )


def test_classify_failure_falls_back_to_citation_under_emission():
    assert (
        classify_failure(
            expected_mode="answer",
            expected_primary_source_id="TBK m.49",
            rc_final_mode="answer",
            rc_primary_source_id="TBK m.49",
            supported_source_ids=["TBK m.49"],
        )
        == "citation_under_emission"
    )
