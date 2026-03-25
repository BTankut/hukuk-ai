from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.faz11.build_authority_error_subset import build_subset
from scripts.faz11.build_v3_170_authority_summary import build_authority_summary


def _report(*, question_id: str, normalized: str, model: str, generation: str, preprojection: str, raw: str):
    return {
        "report_meta": {
            "checkpoint_ref": "ckpt",
            "api_url": "http://127.0.0.1:8118",
        },
        "per_question": [
            {
                "question_id": question_id,
                "trace": {
                    "v3_runtime_parity_trace": {
                        "preprojection_hash": preprojection,
                        "stages": [
                            {"stage": "normalized_request", "hash": normalized, "payload": {}},
                            {"stage": "model_request_payload", "hash": model, "payload": {}},
                            {"stage": "generation_contract", "hash": generation, "payload": {}},
                            {
                                "stage": "worker_assignment_tuple",
                                "hash": "worker",
                                "payload": {"pinned_worker_id": "worker-0"},
                            },
                            {
                                "stage": "session_namespace_after_payload_freeze",
                                "hash": "ns",
                                "payload": {"namespace": "hukuk-ai:<request-local>"},
                            },
                            {"stage": "raw_answer_object", "hash": raw, "payload": {}},
                        ],
                    }
                },
            }
        ],
    }


class Faz11AuthoritySummaryTests(unittest.TestCase):
    def test_zero_mismatch_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            questions_path = Path(tmpdir) / "questions.json"
            questions_path.write_text(
                json.dumps([{"question_id": "TBK-051", "question_text": "q"}], ensure_ascii=False),
                encoding="utf-8",
            )
            summary = build_authority_summary(
                rc_g_report=_report(
                    question_id="TBK-051",
                    normalized="a",
                    model="b",
                    generation="c",
                    preprojection="d",
                    raw="e",
                ),
                rc_j_report=_report(
                    question_id="TBK-051",
                    normalized="a",
                    model="b",
                    generation="c",
                    preprojection="d",
                    raw="e",
                ),
                questions_path=questions_path,
                rc_g_gateway_pid="101",
                rc_j_gateway_pid="202",
                run_id="run-1",
                family_id="v3-170",
            )
        self.assertEqual(summary["authoritative_mismatch_count"], 0)
        self.assertEqual(summary["preprojection_hash_mismatch_count"], 0)
        self.assertEqual(summary["raw_answer_hash_mismatch_count"], 0)
        self.assertEqual(summary["parity_runtime_error_count"], 0)
        self.assertEqual(summary["authoritative_rows"][0]["process_id"], "202")

    def test_preprojection_and_raw_mismatch_are_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            questions_path = Path(tmpdir) / "questions.json"
            questions_path.write_text(
                json.dumps([{"question_id": "TBK-051", "question_text": "q"}], ensure_ascii=False),
                encoding="utf-8",
            )
            summary = build_authority_summary(
                rc_g_report=_report(
                    question_id="TBK-051",
                    normalized="a",
                    model="b",
                    generation="c",
                    preprojection="d",
                    raw="e",
                ),
                rc_j_report=_report(
                    question_id="TBK-051",
                    normalized="a",
                    model="b",
                    generation="c",
                    preprojection="x",
                    raw="y",
                ),
                questions_path=questions_path,
                rc_g_gateway_pid="101",
                rc_j_gateway_pid="202",
                run_id="run-1",
                family_id="v3-170",
            )
        self.assertEqual(summary["authoritative_mismatch_count"], 1)
        self.assertEqual(summary["preprojection_hash_mismatch_count"], 1)
        self.assertEqual(summary["raw_answer_hash_mismatch_count"], 1)
        self.assertEqual(summary["first_mismatch_ordinal"], 1)
        self.assertEqual(summary["last_mismatch_ordinal"], 1)

    def test_error_rerun_replaces_runtime_error_for_effective_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            questions_path = Path(tmpdir) / "questions.json"
            questions_path.write_text(
                json.dumps([{"question_id": "TBK-051", "question_text": "q"}], ensure_ascii=False),
                encoding="utf-8",
            )
            reference_with_error = _report(
                question_id="TBK-051",
                normalized="a",
                model="b",
                generation="c",
                preprojection="d",
                raw="e",
            )
            reference_with_error["per_question"][0]["error"] = "connection refused"
            rerun_reference = _report(
                question_id="TBK-051",
                normalized="a",
                model="b",
                generation="c",
                preprojection="d",
                raw="e",
            )
            summary = build_authority_summary(
                rc_g_report=reference_with_error,
                rc_j_report=_report(
                    question_id="TBK-051",
                    normalized="a",
                    model="b",
                    generation="c",
                    preprojection="d",
                    raw="e",
                ),
                questions_path=questions_path,
                rc_g_gateway_pid="101",
                rc_j_gateway_pid="202",
                run_id="run-1",
                family_id="v3-170",
                rc_g_rerun_report=rerun_reference,
                rc_g_rerun_gateway_pid="303",
            )
        self.assertEqual(summary["reference_first_run_runtime_error_count"], 1)
        self.assertEqual(summary["reference_error_rerun_row_count"], 1)
        self.assertEqual(summary["parity_runtime_error_count"], 0)
        self.assertEqual(summary["authoritative_mismatch_count"], 0)
        self.assertFalse(summary["authoritative_rows"][0]["first_run_authoritative"])
        self.assertEqual(summary["authoritative_rows"][0]["reference_process_id"], "303")

    def test_id_only_question_bank_is_normalized_for_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            questions_path = Path(tmpdir) / "questions.json"
            questions_path.write_text(
                json.dumps([{"id": "TBK-051", "question_text": "q"}], ensure_ascii=False),
                encoding="utf-8",
            )
            summary = build_authority_summary(
                rc_g_report=_report(
                    question_id="TBK-051",
                    normalized="a",
                    model="b",
                    generation="c",
                    preprojection="d",
                    raw="e",
                ),
                rc_j_report=_report(
                    question_id="TBK-051",
                    normalized="a",
                    model="b",
                    generation="c",
                    preprojection="d",
                    raw="e",
                ),
                questions_path=questions_path,
                rc_g_gateway_pid="101",
                rc_j_gateway_pid="202",
                run_id="run-1",
                family_id="v3-170",
            )
        self.assertEqual(summary["question_count"], 1)
        self.assertEqual(summary["authoritative_rows"][0]["question_id"], "TBK-051")

    def test_id_only_question_bank_is_normalized_for_error_subset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            questions_path = Path(tmpdir) / "questions.json"
            report_path = Path(tmpdir) / "report.json"
            questions_path.write_text(
                json.dumps(
                    [
                        {"id": "TBK-051", "question_text": "q1"},
                        {"id": "TBK-052", "question_text": "q2"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = _report(
                question_id="TBK-051",
                normalized="a",
                model="b",
                generation="c",
                preprojection="d",
                raw="e",
            )
            report["per_question"].append(
                {
                    "question_id": "TBK-052",
                    "error": "connection refused",
                    "trace": {"v3_runtime_parity_trace": {"stages": []}},
                }
            )
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            subset = build_subset(report_path=report_path, questions_path=questions_path)
        self.assertEqual([row["question_id"] for row in subset], ["TBK-052"])


if __name__ == "__main__":
    unittest.main()
