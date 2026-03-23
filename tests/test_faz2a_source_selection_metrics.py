from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "faz2a"))

from build_source_selection_metrics import build_payload, render_markdown


def test_build_payload_computes_required_breakdown(tmp_path):
    report_path = tmp_path / "eval.json"
    report = {
        "report_meta": {"eval_family": "faz1-50"},
        "per_question": [
            {
                "expected_sources": ["TBK m.49"],
                "answer_contract": {
                    "primary_source_id": "TBK m.49",
                    "unsupported_reason": None,
                },
                "trace": {
                    "retrieval": {
                        "pre_rerank_chunks": [{"source_id": "TBK m.49"}],
                    },
                    "context_assembly": {
                        "allowed_source_whitelist": ["TBK m.49"],
                    },
                },
                "final_reason": None,
            },
            {
                "expected_sources": ["TBK m.50"],
                "answer_contract": {
                    "primary_source_id": "TBK m.49",
                    "unsupported_reason": "citation_out_of_whitelist",
                },
                "trace": {
                    "retrieval": {
                        "pre_rerank_chunks": [{"source_id": "TBK m.49"}],
                    },
                    "context_assembly": {
                        "allowed_source_whitelist": ["TBK m.49"],
                    },
                },
                "final_reason": "citation_out_of_whitelist",
            },
        ],
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")

    payload = build_payload([report_path])

    assert payload["reports"][0]["label"] == "faz1-50"
    assert payload["reports"][0]["question_count"] == 2
    assert payload["reports"][0]["retrieved_correct_source_at_k"] == 0.5
    assert payload["reports"][0]["assembled_correct_source_present"] == 0.5
    assert payload["reports"][0]["model_selected_correct_source"] == 0.5
    assert payload["reports"][0]["whitelist_violation_rate"] == 0.5


def test_render_markdown_contains_required_columns():
    payload = {
        "generated_at": "2026-03-23T00:00:00+00:00",
        "reports": [
            {
                "label": "faz1-50",
                "question_count": 1,
                "retrieved_correct_source_at_k": 1.0,
                "assembled_correct_source_present": 1.0,
                "model_selected_correct_source": 1.0,
                "whitelist_violation_rate": 0.0,
                "law_scope_mismatch_rate": 0.0,
                "temporal_mismatch_rate": 0.0,
            }
        ],
        "overall": {
            "question_count": 1,
            "retrieved_correct_source_at_k": 1.0,
            "assembled_correct_source_present": 1.0,
            "model_selected_correct_source": 1.0,
            "whitelist_violation_rate": 0.0,
            "law_scope_mismatch_rate": 0.0,
            "temporal_mismatch_rate": 0.0,
        },
    }

    markdown = render_markdown(payload)

    assert "| set | n | retrieved@k | assembled_present | model_selected |" in markdown
    assert "## Overall" in markdown
