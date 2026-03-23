from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.faz3.build_guardrail_blocker_pack import build_blocker_pack, load_eval_rows, load_jsonl_rows


def _write_report(path: Path, *, family: str, question_id: str, final_mode: str, final_reason: str | None, answer_text: str, primary_source_id: str | None, cited_sources: list[str]) -> None:
    payload = {
        "report_meta": {"eval_family": family},
        "per_question": [
            {
                "question_id": question_id,
                "question_text": f"Question for {question_id}",
                "answer_text": answer_text,
                "cited_sources": cited_sources,
                "final_mode": final_mode,
                "final_reason": final_reason,
                "trace": {
                    "final_mode": final_mode,
                    "final_reason": final_reason,
                    "answer_contract": {
                        "answer_text": answer_text,
                        "primary_source_id": primary_source_id,
                        "secondary_source_ids": [],
                        "claim_units": [],
                    },
                },
                "answer_contract": {
                    "answer_text": answer_text,
                    "primary_source_id": primary_source_id,
                    "secondary_source_ids": [],
                    "claim_units": [],
                },
            }
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_blocker_pack_filters_only_two_blocker_classes(tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.jsonl"
    diff_path.write_text(
        "\n".join(
            [
                '{"question_id":"Q1","family":"faz1-50","expected_mode":"answer","expected_source_id":"TBK m.1","rc_a_final_mode":"answer","rc_a_primary_source_id":"TBK m.1","regression_class":"false_refusal_after_guardrail"}',
                '{"question_id":"Q2","family":"v2-95","expected_mode":"answer","expected_source_id":"TBK m.2","rc_a_final_mode":"answer","rc_a_primary_source_id":"TBK m.2","regression_class":"true_guardrail_block"}',
                '{"question_id":"Q3","family":"v3-170","expected_mode":"answer","expected_source_id":"TBK m.3","rc_a_final_mode":"answer","rc_a_primary_source_id":"TBK m.3","regression_class":"scope_parser_false_positive"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rc_a_faz1 = tmp_path / "rc_a_faz1.json"
    rc_a_v2 = tmp_path / "rc_a_v2.json"
    rc_a_v3 = tmp_path / "rc_a_v3.json"
    rc_c_faz1 = tmp_path / "rc_c_faz1.json"
    rc_c_v2 = tmp_path / "rc_c_v2.json"
    rc_c_v3 = tmp_path / "rc_c_v3.json"

    _write_report(rc_a_faz1, family="faz1-50", question_id="Q1", final_mode="answer", final_reason=None, answer_text="A [Kaynak: TBK m.1].", primary_source_id="TBK m.1", cited_sources=["TBK m.1"])
    _write_report(rc_a_v2, family="v2-95", question_id="Q2", final_mode="answer", final_reason=None, answer_text="B [Kaynak: TBK m.2].", primary_source_id="TBK m.2", cited_sources=["TBK m.2"])
    _write_report(rc_a_v3, family="v3-170", question_id="Q3", final_mode="answer", final_reason=None, answer_text="C [Kaynak: TBK m.3].", primary_source_id="TBK m.3", cited_sources=["TBK m.3"])
    _write_report(rc_c_faz1, family="faz1-50", question_id="Q1", final_mode="refusal", final_reason="insufficient_supported_evidence", answer_text="A [Kaynak: TBK m.1].", primary_source_id=None, cited_sources=["TBK m.1"])
    _write_report(rc_c_v2, family="v2-95", question_id="Q2", final_mode="answer", final_reason=None, answer_text="B [Kaynak: TBK m.2].", primary_source_id="TBK m.2", cited_sources=["TBK m.2"])
    _write_report(rc_c_v3, family="v3-170", question_id="Q3", final_mode="refusal", final_reason="law_scope_mismatch", answer_text="C [Kaynak: TBK m.3].", primary_source_id=None, cited_sources=["TBK m.3"])

    rows, summary = build_blocker_pack(
        diff_rows=load_jsonl_rows(diff_path),
        rc_a_reports=load_eval_rows([rc_a_faz1, rc_a_v2, rc_a_v3]),
        rc_c_reports=load_eval_rows([rc_c_faz1, rc_c_v2, rc_c_v3]),
        expected_total=2,
    )

    assert summary["total_records"] == 2
    assert summary["by_class"] == {
        "false_refusal_after_guardrail": 1,
        "true_guardrail_block": 1,
    }
    assert [row["question_id"] for row in rows] == ["Q1", "Q2"]


def test_build_blocker_pack_raises_on_unexpected_total(tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.jsonl"
    diff_path.write_text(
        '{"question_id":"Q1","family":"faz1-50","expected_mode":"answer","expected_source_id":"TBK m.1","rc_a_final_mode":"answer","rc_a_primary_source_id":"TBK m.1","regression_class":"false_refusal_after_guardrail"}\n',
        encoding="utf-8",
    )
    rc_a = tmp_path / "rc_a.json"
    rc_c = tmp_path / "rc_c.json"
    _write_report(rc_a, family="faz1-50", question_id="Q1", final_mode="answer", final_reason=None, answer_text="A [Kaynak: TBK m.1].", primary_source_id="TBK m.1", cited_sources=["TBK m.1"])
    _write_report(rc_c, family="faz1-50", question_id="Q1", final_mode="refusal", final_reason="insufficient_supported_evidence", answer_text="A [Kaynak: TBK m.1].", primary_source_id=None, cited_sources=["TBK m.1"])

    try:
        build_blocker_pack(
            diff_rows=load_jsonl_rows(diff_path),
            rc_a_reports=load_eval_rows([rc_a]),
            rc_c_reports=load_eval_rows([rc_c]),
            expected_total=2,
        )
    except RuntimeError as exc:
        assert "Expected 2 blocker rows, found 1" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for mismatched blocker total")
