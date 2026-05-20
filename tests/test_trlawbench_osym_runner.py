from __future__ import annotations

from evaluation.external.trlawbench_osym.runner import (
    build_prompt,
    build_summary,
    classify_domain,
    extract_selected_option,
    preflight_dataset,
)


def _sample_question(answer: str = "C") -> dict[str, object]:
    return {
        "id": 1,
        "question_name": "2024 ADALET BAKANLIĞI SINAVLARI ADLİ YARGI TESTİ - 1",
        "question": "6098 sayılı Türk Borçlar Kanunu'na göre doğru seçenek hangisidir?",
        "options": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
        "answer": answer,
    }


def test_preflight_accepts_valid_dataset() -> None:
    result = preflight_dataset([_sample_question()])

    assert result.passed is True
    assert result.payload["question_count"] == 1
    assert result.questions[0]["answer"] == "C"


def test_preflight_records_invalid_shape_without_question_text() -> None:
    bad = _sample_question("Z")
    result = preflight_dataset([bad, bad])

    assert result.passed is False
    assert result.payload["duplicate_ids"] == ["1"]
    assert result.payload["invalid_answers"] == [{"id": "1", "answer": "Z"}, {"id": "1", "answer": "Z"}]
    assert "6098" not in str(result.payload)


def test_prompt_excludes_answer_key() -> None:
    prompt = build_prompt(_sample_question())

    assert "SEÇENEK: <A-E>" in prompt
    assert "Cevap anahtarına erişimin yoktur" in prompt
    assert "yargı kararı" not in prompt.lower()
    assert '"answer"' not in prompt
    assert "\nC\n" not in prompt


def test_extract_selected_option_order() -> None:
    assert extract_selected_option("SEÇENEK: B\nKısa gerekçe")["predicted_answer"] == "B"
    assert extract_selected_option("Cevap: D\nKısa gerekçe")["answer_parse_method"] == "cevap_line"
    assert extract_selected_option("B) en yakın seçenektir")["answer_parse_method"] == "first_standalone_option_marker"
    assert extract_selected_option("Belirsiz")["unparseable"] is True


def test_domain_and_metrics_summary() -> None:
    question = _sample_question()
    row = {
        "id": "1",
        "domain": classify_domain(question),
        "exam_year": 2024,
        "runtime_mode": "app",
        "is_correct": True,
        "unparseable": False,
        "blocked": False,
        "latency_ms": 100.0,
        "verification_status": "pass",
        "source_card_count": 1,
        "source_types_used": ["mevzuat"],
        "possible_current_law_conflict": False,
        "review_needed": False,
        "failure_bucket": "none",
    }

    summary = build_summary([row], dataset_count=1)

    assert row["domain"] == "borçlar"
    assert summary["raw_accuracy"] == 1.0
    assert summary["source_card_presence_rate"] == 1.0
    assert summary["verification_pass_rate"] == 1.0
    assert summary["failure_buckets"]["wrong_legal_rule"] == 0
