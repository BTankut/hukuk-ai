from __future__ import annotations

from datetime import date

from faz2a_hardening import harden_answer_diagnostic


def _evidence(*rows: tuple[str, str | None]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for source_id, fikra_no in rows:
        items.append(
            {
                "source_id": source_id,
                "citation": source_id,
                "source": source_id.split(" ", 1)[0],
                "law_no": "6098" if source_id.startswith("TBK") else None,
                "law_short_name": source_id.split(" ", 1)[0],
                "madde_no": source_id.split("m.", 1)[1],
                "fikra_no": fikra_no,
                "yururluk_baslangic": None,
                "yururluk_bitis": None,
                "mulga": None,
                "excerpt": f"{source_id} örnek metni",
            }
        )
    return items


def test_rc_f_prefers_parser_target_as_primary_source() -> None:
    evidence = _evidence(("TBK m.49", None), ("TBK m.50", None))

    result = harden_answer_diagnostic(
        answer_text=(
            "- TBK m.49 kusur sorumluluğunu düzenler. [Kaynak: TBK m.49]\n"
            "- TBK m.50 ise ispat yükünü düzenler. [Kaynak: TBK m.50]"
        ),
        citations=["TBK m.49", "TBK m.50"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="TBK m.49 uyarınca kusur sorumluluğu nedir?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[("TBK", "49")],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TBK m.49", "TBK m.50"],
        today=date(2026, 3, 24),
        recovery_profile="rc_f",
    )

    assert result.final_mode == "answer"
    assert result.citations == ["TBK m.49", "TBK m.50"]
    assert result.answer_contract["primary_source_id"] == "TBK m.49"
    assert result.diagnostics["citation_projection"]["canonical_details"]["primary_canonical_norm_key"] == "norm|6098|49|__|__|__|0"


def test_rc_f_treats_article_target_as_supported_when_evidence_is_paragraph_level() -> None:
    evidence = _evidence(("TBK m.49", "1"))

    result = harden_answer_diagnostic(
        answer_text="TBK m.49 haksız fiil sorumluluğunu düzenler. [Kaynak: TBK m.49]",
        citations=["TBK m.49"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="TBK m.49 nedir?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[("TBK", "49")],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TBK m.49"],
        today=date(2026, 3, 24),
        recovery_profile="rc_f",
    )

    assert result.final_mode == "answer"
    assert result.answer_contract["primary_source_id"] == "TBK m.49"
    assert result.diagnostics["citation_projection"]["canonical_details"]["primary_canonical_norm_key"] == "norm|6098|49|1|__|__|0"


def test_rc_f_recovers_partial_only_when_claims_are_dropped() -> None:
    evidence = _evidence(("TBK m.49", None))

    result = harden_answer_diagnostic(
        answer_text=(
            "- TBK m.49 haksız fiil sorumluluğunu düzenler. [Kaynak: TBK m.49]\n"
            "- İkinci iddia için kaynak verilmedi."
        ),
        citations=["TBK m.49"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="TBK m.49 nedir ve ikinci sonuç nedir?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[("TBK", "49")],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TBK m.49"],
        today=date(2026, 3, 24),
        recovery_profile="rc_f",
    )

    assert result.final_mode == "partial"
    assert result.answer_contract["primary_source_id"] == "TBK m.49"
    assert result.citations == ["TBK m.49"]
