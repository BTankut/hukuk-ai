from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz2b"))

from build_rc_c_family_eval_summary import build_family_summary


def test_build_family_summary_detects_metric_and_acceptance_failures():
    report = {
        "summary": {
            "citation_rate": 0.82,
            "correct_source_rate": 0.72,
            "hallucination_rate": 0.06,
            "refusal_accuracy": 0.86,
        },
        "per_question": [
            {
                "final_mode": "answer",
                "trace": {
                    "final_mode": "answer",
                    "final_reason": None,
                    "law_scope_signal": {"scope_class": "single_law_high_conf"},
                },
            },
            {
                "final_mode": "answer",
                "trace": {
                    "final_mode": "answer",
                    "final_reason": "citation_out_of_whitelist",
                    "law_scope_signal": {"scope_class": "single_law_high_conf"},
                },
            },
        ],
    }

    result = build_family_summary("faz1-50", report)

    assert result["passes"] is False
    assert result["metric_results"]["citation_rate"] is False
    assert result["acceptance"]["whitelist_violation_leak_count"] == 1
    assert result["acceptance_results"]["trace_coverage_rate"] is True


def test_build_family_summary_passes_clean_family():
    report = {
        "summary": {
            "citation_rate": 0.95,
            "correct_source_rate": 0.85,
            "hallucination_rate": 0.04,
            "refusal_accuracy": 0.95,
        },
        "per_question": [
            {
                "final_mode": "answer",
                "trace": {
                    "final_mode": "answer",
                    "final_reason": None,
                    "law_scope_signal": {"scope_class": "single_law_high_conf"},
                },
            },
            {
                "final_mode": "refusal",
                "trace": {
                    "final_mode": "refusal",
                    "final_reason": "law_scope_mismatch",
                    "law_scope_signal": {"scope_class": "single_law_high_conf"},
                },
            },
        ],
    }

    result = build_family_summary("v3-170", report)

    assert result["passes"] is True
    assert result["acceptance"]["law_scope_answer_leak_count"] == 0
    assert result["acceptance"]["schema_validation_pass_rate"] == 1.0
