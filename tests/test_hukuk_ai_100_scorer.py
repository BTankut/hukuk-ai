from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/benchmark/score_hukuk_ai_100.py"
SPEC = importlib.util.spec_from_file_location("score_hukuk_ai_100", MODULE_PATH)
assert SPEC and SPEC.loader
score_hukuk_ai_100 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score_hukuk_ai_100)

score_row = score_hukuk_ai_100.score_row
term_present = score_hukuk_ai_100.term_present


def test_term_present_matches_turkish_ascii_variants() -> None:
    text = "TKHK:6502:m10:f0 tuketicinin korunmasi hakkinda kanun"

    assert term_present("6502 sayılı Tüketicinin Korunması Hakkında Kanun", text)


def test_term_present_matches_dotless_i_content_signals() -> None:
    text = "yillik 270 saat siniri ve isci onayi gerekir"

    assert term_present("yıllık 270 saat sınırı", text)
    assert term_present("işçi onayı", text)


def test_score_row_passes_phase7_suppression_flags_through() -> None:
    answer = {
        "qid": "X-01",
        "primary_type": "KANUN",
        "task_type": "unit",
        "answer": "4857 sayili Is Kanunu madde 41 yillik 270 saat siniri",
        "citations": "IK m.41",
        "source_titles": "Is Kanunu",
        "source_ids": "IK:4857:m41:f0",
        "doc_types": "kanun",
        "confidence_0_100": "35",
        "final_reason": "manual review",
        "answer_mode": "insufficient_grounding",
        "grounding_status": "not_grounded",
        "source_family_claimed": "KANUN",
        "source_title_claimed": "Is Kanunu",
        "source_identifier_claimed": "IK m.41",
        "article_or_section_claimed": "madde:41",
        "effective_state_claimed": "active",
        "temporal_qualification": "2026",
        "needs_manual_review": "True",
        "contract_valid": "True",
        "contract_repaired": "True",
        "claimed_source_parse_success": "True",
        "confidence_policy_ok": "True",
        "uncertainty_disclosed": "True",
        "manual_review_flag": "True",
        "unsupported_confident_answer": "False",
        "retrieval_trace_id": "trace-1",
        "article_lock_failed": "True",
        "support_insufficient_for_specific_claim": "True",
        "temporal_clause_missing": "False",
        "answer_suppressed_due_to_evidence_gap": "True",
    }
    key = {
        "q_id": "X-01",
        "gold_documents": "4857 sayılı İş Kanunu",
        "must_include": "yıllık 270 saat sınırı",
        "auto_fail_if": "",
        "max_points": "10",
    }

    row = score_row(answer, key)

    assert row["article_lock_failed"] == "True"
    assert row["support_insufficient_for_specific_claim"] == "True"
    assert row["temporal_clause_missing"] == "False"
    assert row["answer_suppressed_due_to_evidence_gap"] == "True"


def test_score_row_computes_article_alignment_when_missing() -> None:
    answer = {
        "qid": "X-02",
        "primary_type": "KANUN",
        "task_type": "unit",
        "answer": "4857 sayili Is Kanunu madde 41",
        "citations": "IK m.41",
        "source_titles": "Is Kanunu",
        "source_ids": "IK:4857:m41:f0",
        "doc_types": "kanun",
        "confidence_0_100": "75",
        "final_reason": "grounded",
        "answer_mode": "direct_answer",
        "grounding_status": "fully_grounded",
        "source_family_claimed": "KANUN",
        "source_title_claimed": "Is Kanunu",
        "source_identifier_claimed": "IK m.41",
        "article_or_section_claimed": "madde:41",
        "effective_state_claimed": "active",
        "temporal_qualification": "2026",
        "needs_manual_review": "False",
        "contract_valid": "True",
        "contract_repaired": "False",
        "claimed_source_parse_success": "True",
        "confidence_policy_ok": "True",
        "uncertainty_disclosed": "True",
        "manual_review_flag": "False",
        "unsupported_confident_answer": "False",
        "retrieval_trace_id": "trace-2",
        "selected_article": "41",
        "article_match_type": "source_local_support",
    }
    key = {
        "q_id": "X-02",
        "gold_documents": "4857 sayılı İş Kanunu",
        "must_include": "",
        "auto_fail_if": "",
        "max_points": "10",
    }

    row = score_row(answer, key)

    assert row["article_alignment"] == "exact"
    assert row["selected_article_equals_claimed_article"] == "True"
