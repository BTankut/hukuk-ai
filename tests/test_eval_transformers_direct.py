from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evaluation"))

import eval_transformers_direct as evaluator  # noqa: E402
from metrics import aggregate_metrics, compute_metrics  # noqa: E402


def test_build_messages_does_not_include_expected_sources() -> None:
    messages = evaluator.build_messages("TBK m.146 nedir?")

    assert len(messages) == 2
    combined = " ".join(item["content"] for item in messages)
    assert "expected_sources" not in combined
    assert "TBK m.146 nedir?" in combined


def test_extract_citations_reads_law_articles() -> None:
    citations = evaluator.extract_citations("Genel zamanaşımı süresi TBK m.146 uyarınca 10 yıldır.")

    assert citations == ["TBK m.146"]


def test_report_identity_uses_transformers_runner() -> None:
    question = {
        "id": "Q1",
        "question": "Genel zamanaşımı süresi nedir?",
        "category": "tbk_genel",
        "difficulty": "easy",
        "expected_sources": ["TBK m.146"],
        "expected_keywords": ["10 yıl"],
        "expected_answer_contains": "10 yıl",
        "refusal_expected": False,
    }
    result = compute_metrics(
        question=question,
        answer_text="TBK m.146 uyarınca 10 yıl.",
        cited_sources=["TBK m.146"],
        response_time_ms=120.0,
        blocked=False,
        verification=None,
        error=None,
    )
    summary = aggregate_metrics([result])

    metadata = evaluator.build_identity_metadata(
        runner="eval_transformers_direct",
        questions_path=Path("configs/evaluation/test_questions.json"),
        api_url="local:///models/hukuk-ai-sft-v3",
        mock_mode=False,
        eval_family="faz1-50",
        model_ref=None,
        checkpoint_ref=None,
        git_commit="abc1234",
        report_role="diagnostic_post_train",
        model="hukuk-ai-sft-v3",
        config_fingerprint={"max_new_tokens": 512},
    )

    assert summary.citation_rate == 1.0
    assert metadata["runner"] == "eval_transformers_direct"
    assert metadata["model_ref"] == "hukuk-ai-sft-v3"
    assert metadata["checkpoint_ref"] == "transformers:hukuk-ai-sft-v3"
    assert metadata["report_role"] == "diagnostic_post_train"
