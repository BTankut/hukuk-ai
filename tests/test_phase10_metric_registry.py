from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/benchmark/hukuk_ai_100_metric_registry.py"
SPEC = importlib.util.spec_from_file_location("hukuk_ai_100_metric_registry", MODULE_PATH)
assert SPEC and SPEC.loader
metric_registry = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = metric_registry
SPEC.loader.exec_module(metric_registry)


def test_right_document_wrong_span_requires_family_and_document_alignment() -> None:
    aligned_row = {
        "failure_classes": "missing_required_content_signal | partial_grounding_only",
        "family_match_score": "1.00",
        "document_match_score": "1.00",
    }
    wrong_doc_row = {
        "failure_classes": "wrong_document | missing_required_content_signal | partial_grounding_only",
        "family_match_score": "1.00",
        "document_match_score": "0.00",
    }

    assert metric_registry.right_document_wrong_article_or_span(aligned_row) is True
    assert metric_registry.right_document_wrong_article_or_span(wrong_doc_row) is False


def test_rubric_completeness_separates_structural_fullness_from_private_rubric() -> None:
    row = {
        "failure_classes": "missing_required_content_signal | partial_grounding_only",
        "required_fact_coverage_score": "0.97",
        "minimum_answer_facts_present": "True",
    }

    assert (
        metric_registry.rubric_completeness_class(row)
        == "structurally_full_but_legally_misaligned"
    )


def test_metric_consistency_rejects_mismatched_artifact_counts() -> None:
    scored_rows = [
        {
            "qid": "Q1",
            "failure_classes": "missing_required_content_signal | partial_grounding_only",
            "family_match_score": "1.00",
            "document_match_score": "1.00",
            "minimum_answer_facts_present": "True",
            "required_fact_coverage_score": "0.9",
            "selected_article_equals_claimed_article": "True",
        }
    ]
    coverage_rows = [{"qid": "Q1", "coverage_status": "candidate_collision_or_metadata"}]
    trace_rows = [{"qid": "Q1", "mechanism": "evidence insufficiency"}]

    result = metric_registry.validate_metric_consistency(
        scored_rows=scored_rows,
        coverage_rows=coverage_rows,
        trace_rows=trace_rows,
    )

    assert result["valid"] is False
    assert {item["artifact"] for item in result["mismatches"]} == {
        "coverage_backlog",
        "trace_forensics",
    }
