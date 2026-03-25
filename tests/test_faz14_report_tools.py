from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.faz14.build_output_parity_repair_frontier_pack import build_frontier_pack
from scripts.faz14.build_output_parity_repair_localization import build_localization
from scripts.faz14.build_output_repair_report import build_report


def _question_bank(path: Path) -> None:
    payload = {"questions": [{"question_id": "Q1", "question": "Soru 1"}]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _report(*, guardrails: list[str]) -> dict:
    return {
        "report_meta": {"checkpoint_ref": "ckpt", "model_ref": "gateway-api", "eval_family": "v3-170"},
        "per_question": [
            {
                "question_id": "Q1",
                "answer_text": "cevap [Kaynak: TBK m.1]",
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
                            {
                                "stage": "normalized_parity_object",
                                "payload": {
                                    "final_mode": "answer",
                                    "answer_body": "cevap [Kaynak: TBK m.1]",
                                    "refusal_body": "",
                                    "refusal_reason": None,
                                    "ordered_citation_list": ["TBK m.1"],
                                    "visible_citation_projection": ["TBK m.1"],
                                    "ordered_source_id_list": ["TBK m.1"],
                                    "ordered_canonical_norm_keys": ["TBK m.1"],
                                },
                            },
                            {"stage": "response_envelope", "payload": {"guardrails_reasons": guardrails}},
                            {"stage": "eval_client_parsed_object", "payload": {"answer_text": "cevap [Kaynak: TBK m.1]"}},
                        ],
                    }
                },
            }
        ],
    }


class Faz14ReportToolTests(unittest.TestCase):
    def test_targeted_report_accepts_allowed_projection_only_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            questions_path = Path(tmpdir) / "questions.json"
            _question_bank(questions_path)
            reference = _report(guardrails=["source_lock_fallback"])
            candidate = _report(guardrails=["source_lock_fallback"])
            diagnostic = _report(guardrails=[])
            report = build_report(
                run_id="faz14",
                family_id="v3-170",
                questions_path=questions_path,
                reference_report=reference,
                candidate_report=candidate,
                diagnostic_report=diagnostic,
                reference_run_label="rc_g",
                candidate_run_label="rc_l",
            )
            self.assertEqual(report["mismatch_count"], 0)
            self.assertEqual(report["changed_field_outside_contract_count"], 0)
            self.assertEqual(
                report["allowed_changed_field_set"],
                ["blocked_reason_set_hash", "final_mode_mapping_hash", "response_envelope_hash"],
            )

    def test_localization_marks_repair_surface_breach(self) -> None:
        pack = build_frontier_pack(
            [
                {
                    "family_id": "v3-170",
                    "mismatch_rows": [
                        {
                            "question_id": "Q1",
                            "ordinal_index": 1,
                            "first_divergence_stage": "final_answer_payload_hash",
                            "primary_reason": "repair_surface_breach",
                        }
                    ],
                }
            ]
        )
        replay, reconciliation = build_localization(pack)
        self.assertEqual(replay["repair_surface_breach_count"], 1)
        self.assertTrue(reconciliation["localization_pass"])


if __name__ == "__main__":
    unittest.main()
