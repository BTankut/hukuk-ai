from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.faz13.build_authoritative_mismatch_table import build_table
from scripts.faz13.build_authoritative_frontier_pack import build_frontier_pack
from scripts.faz13.build_authoritative_localization import build_localization
from scripts.faz13.build_authoritative_output_parity_report import build_report


def _question_bank(path: Path) -> None:
    payload = {
        "questions": [
            {"question_id": "Q1", "question": "Soru 1"},
            {"question_id": "Q2", "question": "Soru 2"},
        ]
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _report(*, q1_mode: str = "answer", q1_guardrails: list[str] | None = None, q2_error: str | None = None) -> dict:
    rows = [
        {
            "question_id": "Q1",
            "answer_text": "cevap",
            "has_citation": True,
            "correct_source_rate": 1.0,
            "is_hallucination": False,
            "refusal_correct": 1.0,
            "trace": {
                "parity_trace": {
                    "preprojection_hash": "pre-q1",
                    "stages": [
                        {"stage": "normalized_request", "hash": "n-q1"},
                        {"stage": "model_request_payload", "hash": "m-q1"},
                        {"stage": "generation_contract", "hash": "g-q1"},
                        {"stage": "worker_assignment_tuple", "payload": {"pinned_worker_id": "w1", "process_id": "p1"}},
                        {"stage": "session_namespace_after_payload_freeze", "payload": {"namespace": "s1"}},
                        {"stage": "cache_namespace_or_cache_key", "payload": {"namespace": "c1"}},
                        {
                            "stage": "normalized_parity_object",
                            "payload": {
                                "final_mode": q1_mode,
                                "answer_body": "" if q1_mode == "refusal" else "cevap",
                                "refusal_body": "red" if q1_mode == "refusal" else "",
                                "refusal_reason": "rule" if q1_mode == "refusal" else None,
                                "ordered_citation_list": ["TBK m.1"],
                                "visible_citation_projection": ["TBK m.1"],
                                "ordered_source_id_list": ["tbk_1"],
                                "ordered_canonical_norm_keys": ["tbk_1"],
                            },
                        },
                        {"stage": "response_envelope", "payload": {"guardrails_reasons": q1_guardrails or []}},
                        {"stage": "eval_client_parsed_object", "payload": {"answer_text": "cevap"}},
                    ]
                }
            },
        },
        {
            "question_id": "Q2",
            "answer_text": "",
            "has_citation": False,
            "correct_source_rate": 0.0,
            "is_hallucination": False,
            "refusal_correct": 0.0,
            "error": q2_error,
            "trace": {
                "parity_trace": {
                    "preprojection_hash": "pre-q2",
                    "stages": [
                        {"stage": "normalized_request", "hash": "n-q2"},
                        {"stage": "model_request_payload", "hash": "m-q2"},
                        {"stage": "generation_contract", "hash": "g-q2"},
                        {
                            "stage": "normalized_parity_object",
                            "payload": {
                                "final_mode": "answer",
                                "answer_body": "",
                                "refusal_body": "",
                                "refusal_reason": None,
                                "ordered_citation_list": [],
                                "visible_citation_projection": [],
                                "ordered_source_id_list": [],
                                "ordered_canonical_norm_keys": [],
                            },
                        },
                        {"stage": "response_envelope", "payload": {"guardrails_reasons": []}},
                        {"stage": "eval_client_parsed_object", "payload": {"answer_text": ""}},
                    ]
                }
            },
        },
    ]
    return {
        "report_meta": {"checkpoint_ref": "ckpt", "model_ref": "gateway-api", "eval_family": "faz1-50"},
        "per_question": rows,
    }


class Faz13OutputParityTests(unittest.TestCase):
    def test_build_report_detects_final_mode_and_accounting_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            questions_path = Path(tmpdir) / "questions.json"
            _question_bank(questions_path)
            reference = _report(q1_mode="answer", q2_error="timeout")
            candidate = _report(q1_mode="refusal", q2_error=None)
            report = build_report(
                run_id="faz13",
                family_id="faz1-50",
                questions_path=questions_path,
                reference_report=reference,
                candidate_report=candidate,
                reference_run_label="rc_g",
                candidate_run_label="rc_j",
            )
            self.assertEqual(report["mismatch_count"], 2)
            self.assertEqual(report["final_mode_mapping_hash_mismatch_count"], 1)
            self.assertEqual(report["normalized_request_hash_mismatch_count"], 0)
            reasons = {row["question_id"]: row["primary_reason"] for row in report["mismatch_rows"]}
            self.assertEqual(reasons["Q1"], "final_mode_mapping_delta")
            self.assertEqual(reasons["Q2"], "authority_effective_view_accounting_mismatch")

    def test_frontier_and_localization_close_without_unexplained(self) -> None:
        report = {
            "family_id": "faz1-50",
            "mismatch_rows": [
                {
                    "family_id": "faz1-50",
                    "question_id": "Q1",
                    "ordinal_index": 1,
                    "first_divergence_stage": "preprojection_anchor_hash",
                    "primary_reason": "preprojection_anchor_drift",
                },
                {
                    "family_id": "faz1-50",
                    "question_id": "Q2",
                    "ordinal_index": 2,
                    "first_divergence_stage": "final_mode_mapping_hash",
                    "primary_reason": "final_mode_mapping_delta",
                },
            ],
        }
        pack = build_frontier_pack([report])
        replay, reconciliation = build_localization(pack)
        self.assertEqual(pack["frontier_count"], 2)
        self.assertEqual(replay["unexplained_count"], 0)
        self.assertTrue(reconciliation["localization_pass"])

    def test_mismatch_table_collects_rows(self) -> None:
        report = {
            "family_id": "v3-170",
            "mismatch_rows": [
                {
                    "family_id": "v3-170",
                    "question_id": "Q9",
                    "ordinal_index": 9,
                    "final_mode_mapping_hash_mismatch": 1,
                    "first_divergence_stage": "final_mode_mapping_hash",
                    "primary_reason": "final_mode_mapping_delta",
                }
            ],
        }
        table = build_table([report])
        self.assertEqual(table["mismatch_count"], 1)
        self.assertEqual(table["family_breakdown"]["v3-170"], 1)
        self.assertEqual(table["rows"][0]["primary_reason"], "final_mode_mapping_delta")


if __name__ == "__main__":
    unittest.main()
