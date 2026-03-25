from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz12"))

from build_output_parity_frontier_pack import build_frontier_pack  # noqa: E402
from build_output_parity_localization import build_localization  # noqa: E402
from build_output_parity_report import build_report  # noqa: E402
from build_output_parity_summary import build_summary  # noqa: E402
from faz12_lib import parity_fields, stage_map  # noqa: E402


def _question_row(question_id: str, *, answer: str, citations: list[str], final_mode: str = "answer", error: str | None = None):
    return {
        "question_id": question_id,
        "answer_text": answer,
        "cited_sources": citations,
        "final_mode": final_mode,
        "has_citation": bool(citations),
        "correct_source_rate": 1.0 if citations else 0.0,
        "is_hallucination": False,
        "refusal_correct": 1.0 if final_mode == "refusal" else 0.0,
        "error": error,
        "trace": {
            "v3_runtime_parity_trace": {
                "preprojection_hash": "same-preprojection",
                "stages": [
                    {
                        "stage": "response_envelope",
                        "hash": f"env-{question_id}-{final_mode}",
                        "payload": {
                            "citations": citations,
                            "guardrails_reasons": [],
                            "blocked": False,
                            "final_mode": final_mode,
                            "final_reason": None,
                            "answer_contract": {},
                        },
                    },
                    {
                        "stage": "eval_client_parsed_object",
                        "hash": f"parsed-{question_id}-{answer}",
                        "payload": {
                            "answer_text": answer,
                            "citations": citations,
                            "blocked": False,
                            "final_mode": final_mode,
                            "final_reason": None,
                            "answer_contract": {},
                        },
                    },
                    {
                        "stage": "normalized_parity_object",
                        "hash": f"norm-{question_id}-{answer}",
                        "payload": {
                            "final_mode": final_mode,
                            "answer_body": answer if final_mode != "refusal" else "",
                            "refusal_body": answer if final_mode == "refusal" else "",
                            "refusal_reason": None,
                            "ordered_citation_list": citations,
                            "ordered_source_id_list": citations,
                            "ordered_canonical_norm_keys": citations,
                            "visible_citation_projection": citations,
                        },
                    },
                ],
            }
        },
    }


def test_stage_map_supports_list_trace() -> None:
    row = _question_row("Q1", answer="a", citations=["TBK m.1"])
    mapping = stage_map(row)
    assert "normalized_parity_object" in mapping
    fields = parity_fields(row)
    assert fields["cited_projection_hash"]
    assert fields["serialized_output_hash"]


def test_build_report_uses_allowed_reference_rerun(tmp_path: Path) -> None:
    questions_path = tmp_path / "questions.json"
    questions_path.write_text('[{"question_id":"Q1"}]\n', encoding="utf-8")

    reference_first = {"report_meta": {"eval_family": "faz1-50", "checkpoint_ref": "rc-g"}, "per_question": [_question_row("Q1", answer="a", citations=["TBK m.1"], error="timeout")]}
    reference_rerun = {"per_question": [_question_row("Q1", answer="a", citations=["TBK m.1"])]}
    candidate_first = {"report_meta": {"eval_family": "faz1-50", "checkpoint_ref": "rc-j"}, "per_question": [_question_row("Q1", answer="a", citations=["TBK m.1"])]}

    report = build_report(
        family_id="faz1-50",
        questions_path=questions_path,
        reference_report=reference_first,
        candidate_report=candidate_first,
        reference_run_label="rc_g",
        candidate_run_label="rc_j",
        reference_rerun_report=reference_rerun,
    )

    assert report["reference_runtime_error_count"] == 0
    assert report["reference_error_rerun_row_count"] == 1
    assert report["output_parity_reopened"] is True


def test_frontier_and_localization_from_single_mismatch(tmp_path: Path) -> None:
    questions_path = tmp_path / "questions.json"
    questions_path.write_text('[{"question_id":"Q1"}]\n', encoding="utf-8")

    reference = {"report_meta": {"eval_family": "faz1-50", "checkpoint_ref": "rc-g"}, "per_question": [_question_row("Q1", answer="a", citations=["TBK m.1"])]}
    candidate = {"report_meta": {"eval_family": "faz1-50", "checkpoint_ref": "rc-j"}, "per_question": [_question_row("Q1", answer="b", citations=["TBK m.1"])]}

    per_family = build_report(
        family_id="faz1-50",
        questions_path=questions_path,
        reference_report=reference,
        candidate_report=candidate,
        reference_run_label="rc_g",
        candidate_run_label="rc_j",
    )
    summary = build_summary([per_family])
    assert summary["all_families_pass"] is False

    frontier = build_frontier_pack([per_family])
    assert frontier["frontier_count"] == 1
    replay, reconciliation = build_localization(frontier)
    assert replay["frontier_count"] == 1
    assert reconciliation["localization_pass"] is True
