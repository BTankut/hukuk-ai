from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_build_guardrail_regression_diff(tmp_path: Path) -> None:
    rc_a = {
        "report_meta": {"eval_family": "faz1-50"},
        "per_question": [
            {
                "question_id": "Q1",
                "question_text": "TBK m.49 nedir?",
                "answer_text": "TBK m.49 şöyledir. [Kaynak: TBK m.49]",
                "cited_sources": ["TBK m.49"],
                "expected_sources": ["TBK m.49"],
                "refusal_expected": False,
                "correct_source_rate": 1.0,
                "refusal_correct": True,
                "is_hallucination": False,
            }
        ],
    }
    rc_b = {
        "report_meta": {"eval_family": "faz1-50"},
        "per_question": [
            {
                "question_id": "Q1",
                "cited_sources": [],
                "expected_sources": ["TBK m.49"],
                "refusal_expected": False,
                "correct_source_rate": 0.0,
                "refusal_correct": False,
                "is_hallucination": False,
                "final_mode": "refusal",
                "final_reason": "law_scope_mismatch",
                "answer_contract": {
                    "primary_source_id": None,
                },
                "trace": {
                    "question_type": "single_article",
                    "law_scope_signal": {"expected_law_scope": ["TBK"], "scope_ambiguous": False},
                    "allowed_source_whitelist": ["TBK m.49"],
                },
            }
        ],
    }

    rc_a_path = tmp_path / "rc_a.json"
    rc_b_path = tmp_path / "rc_b.json"
    rc_a_path.write_text(json.dumps(rc_a), encoding="utf-8")
    rc_b_path.write_text(json.dumps(rc_b), encoding="utf-8")

    output_jsonl = tmp_path / "diff.jsonl"
    output_md = tmp_path / "diff.md"

    subprocess.run(
        [
            sys.executable,
            "scripts/faz2b/build_guardrail_regression_diff.py",
            "--rc-a-report",
            str(rc_a_path),
            "--rc-b-report",
            str(rc_b_path),
            "--output-jsonl",
            str(output_jsonl),
            "--output-md",
            str(output_md),
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )

    row = json.loads(output_jsonl.read_text(encoding="utf-8").splitlines()[0])
    assert row["regression_class"] == "scope_parser_false_positive"
    assert row["rc_a_primary_source_id"] == "TBK m.49"
    assert "false_refusal_after_guardrail" in output_md.read_text(encoding="utf-8")
