from __future__ import annotations

from evaluation.external.trlawbench_osym.runner import (
    build_prompt,
    build_summary,
    classify_domain,
    classify_question_source,
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

    assert "SEÇENEK: <A|B|C|D|E>" in prompt
    assert "Cevap anahtarına erişimin yoktur" in prompt
    assert "varsa yargı kararı" in prompt.lower()
    assert '"answer"' not in prompt
    assert "\nC\n" not in prompt


def test_extract_selected_option_order() -> None:
    assert extract_selected_option("SEÇENEK: A\nGEREKÇE: kısa")["answer_parse_method"] == "secenek_first_line"
    assert extract_selected_option("danışman cevabı", {"answer_contract": {"selected_option": "B"}})["predicted_answer"] == "B"
    assert extract_selected_option("Cevap: D\nKısa gerekçe")["answer_parse_method"] == "cevap_line"
    assert extract_selected_option("Doğru seçenek: C'dir\nKısa gerekçe")["answer_parse_method"] == "dogru_secenek_line"
    assert extract_selected_option("E) en yakın seçenektir")["answer_parse_method"] == "first_standalone_option_marker"
    assert extract_selected_option("1. Kısa sonuç\nKaynaklı danışman metni")["unparseable"] is True
    assert extract_selected_option("Cevap: A\nDoğru seçenek: B")["answer_parse_method"] == "conflicting_choices"
    assert extract_selected_option("Belirsiz")["unparseable"] is True


def test_blocked_no_choice_is_summary_bucket() -> None:
    row = {
        "id": "1",
        "domain": "borçlar",
        "question_source": "adalet_bakanligi",
        "exam_year": 2024,
        "runtime_mode": "app_rag_mcq",
        "is_correct": False,
        "unparseable": False,
        "blocked": True,
        "latency_ms": 10.0,
        "verification_status": "not_run",
        "source_card_count": 0,
        "source_types_used": [],
        "possible_current_law_conflict": False,
        "review_needed": True,
        "failure_bucket": "blocked_no_choice",
        "choice_evidence_status": "blocked",
    }

    summary = build_summary([row], dataset_count=1, mode="app_rag_mcq")

    assert summary["unparseable_count"] == 0
    assert summary["blocked_count"] == 1
    assert summary["failure_buckets"]["blocked_no_choice"] == 1


def test_domain_and_metrics_summary() -> None:
    question = _sample_question()
    row = {
        "id": "1",
        "domain": classify_domain(question),
        "question_source": classify_question_source(str(question["question_name"])),
        "exam_year": 2024,
        "runtime_mode": "app_rag_mcq",
        "is_correct": True,
        "unparseable": False,
        "blocked": False,
        "latency_ms": 100.0,
        "verification_status": "pass",
        "source_card_count": 1,
        "source_types_used": ["mevzuat"],
        "choice_evidence_status": "evidence_used",
        "possible_current_law_conflict": False,
        "review_needed": False,
        "failure_bucket": "none",
    }

    summary = build_summary([row], dataset_count=1, mode="app_rag_mcq")

    assert row["domain"] == "borçlar"
    assert row["question_source"] == "adalet_bakanligi"
    assert summary["mode"] == "app_rag_mcq"
    assert summary["raw_accuracy"] == 1.0
    assert summary["raw_accuracy_against_answer_key"] == 1.0
    assert summary["source_card_presence_rate"] == 1.0
    assert summary["verification_pass_rate"] == 1.0
    assert summary["limited_evidence_count"] == 0
    assert summary["failure_buckets"]["wrong_option_verified"] == 0
