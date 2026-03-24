from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz8"))

import build_first_divergence_replay as replay  # noqa: E402
import build_preprojection_hash_gate as hash_gate  # noqa: E402
import build_rc_h_parity_frontier as frontier  # noqa: E402


def test_build_rc_h_parity_frontier_counts_errors_and_mismatches() -> None:
    parity_report = {
        "mismatches": [{"question_id": "TBK-001", "kind": "normalized_output_mismatch", "fields": ["answer_body"]}]
    }
    eval_report = {
        "report_meta": {"eval_family": "faz1-50"},
        "per_question": [
            {"question_id": "TBK-001"},
            {"question_id": "TBK-002", "error": "timed out"},
        ],
    }
    summary = frontier.build_summary(frontier._frontier_rows(parity_report, eval_report))

    assert summary["frontier_total"] == 2
    assert summary["mismatch_total"] == 1
    assert summary["parity_runtime_error_total"] == 1


def test_preprojection_hash_gate_detects_hash_mismatch() -> None:
    reference_report = {
        "report_meta": {"eval_family": "faz1-50"},
        "per_question": [{"question_id": "TBK-001", "trace": {"parity_trace": {"stages": [{"stage": "raw_answer_object", "hash": "aaa"}]}}}],
    }
    candidate_report = {
        "report_meta": {"eval_family": "faz1-50"},
        "per_question": [{"question_id": "TBK-001", "trace": {"parity_trace": {"stages": [{"stage": "raw_answer_object", "hash": "bbb"}]}}}],
    }

    summary = hash_gate.build_gate(reference_report, candidate_report)

    assert summary["preprojection_hash_mismatch_count"] == 1


def test_first_divergence_marks_parity_runtime_error() -> None:
    summary = replay.build_replay(
        frontier_rows=[{"family": "faz1-50", "question_id": "TBK-001", "kind": "parity_runtime_error", "error": "timed out"}],
        reference_reports={"faz1-50": {"report_meta": {"eval_family": "faz1-50"}, "per_question": [{"question_id": "TBK-001"}]}},
        candidate_reports={"faz1-50": {"report_meta": {"eval_family": "faz1-50"}, "per_question": [{"question_id": "TBK-001", "error": "timed out"}]}},
    )

    assert summary["unexplained_count"] == 0
    assert summary["rows"][0]["primary_reason"] == "parity_runtime_error"
