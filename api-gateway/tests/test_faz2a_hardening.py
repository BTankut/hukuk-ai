from __future__ import annotations

from datetime import date

from faz2a_hardening import canonicalize_source_id, harden_answer


def _evidence(*source_ids: str) -> list[dict[str, object]]:
    return [
        {
            "source_id": source_id,
            "citation": source_id,
            "source": source_id.split(" ", 1)[0],
            "law_no": None,
            "law_short_name": source_id.split(" ", 1)[0],
            "madde_no": source_id.split("m.", 1)[1],
            "fikra_no": None,
            "yururluk_baslangic": None,
            "yururluk_bitis": None,
            "mulga": None,
            "excerpt": f"{source_id} örnek metni",
        }
        for source_id in source_ids
    ]


def test_canonicalize_source_id_accepts_legacy_chunk_style():
    assert canonicalize_source_id("tbk-49-f1") == "TBK m.49"


def test_harden_answer_keeps_supported_answer_in_answer_mode():
    evidence = _evidence("TBK m.49")

    result = harden_answer(
        answer_text="Haksız fiil sorumluluğu vardır. [Kaynak: TBK m.49]",
        citations=["TBK m.49"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="TBK m.49 nedir?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[("TBK", "49")],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TBK m.49"],
        today=date(2026, 3, 23),
    )

    assert result.final_mode == "answer"
    assert result.final_reason is None
    assert result.citations == ["TBK m.49"]
    assert result.answer_contract["primary_source_id"] == "TBK m.49"
    assert result.answer_contract["claim_units"][0]["source_id"] == "TBK m.49"


def test_harden_answer_blocks_law_scope_mismatch():
    evidence = _evidence("TMK m.194")

    result = harden_answer(
        answer_text="Aile konutu koruması vardır. [Kaynak: TMK m.194]",
        citations=["TMK m.194"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="TBK m.349 kapsamında cevap ver.",
        mentioned_laws=["TBK"],
        explicit_article_refs=[("TBK", "349")],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TMK m.194"],
        today=date(2026, 3, 23),
    )

    assert result.final_mode == "refusal"
    assert result.final_reason == "law_scope_mismatch"
    assert result.citations == []
    assert result.internal_blocked is False


def test_harden_answer_blocks_citation_out_of_whitelist():
    evidence = _evidence("TBK m.49")

    result = harden_answer(
        answer_text="Haksız fiil. [Kaynak: TBK m.49]",
        citations=["TBK m.49"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="TBK m.49 nedir?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[("TBK", "49")],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=[],
        today=date(2026, 3, 23),
    )

    assert result.final_mode == "refusal"
    assert result.final_reason == "citation_out_of_whitelist"
    assert result.answer_contract["unsupported_reason"] == "citation_out_of_whitelist"
    assert result.internal_blocked is True


def test_harden_answer_reuses_single_supported_source_for_narrow_claim():
    evidence = _evidence("TBK m.49")

    result = harden_answer(
        answer_text="Haksız fiil sorumluluğu vardır.",
        citations=["TBK m.49"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="TBK m.49 nedir?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[("TBK", "49")],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TBK m.49"],
        today=date(2026, 3, 23),
    )

    assert result.final_mode == "answer"
    assert result.final_reason is None
    assert result.answer_contract["claim_units"][0]["source_id"] == "TBK m.49"


def test_harden_answer_blocks_temporal_mismatch_for_current_question():
    evidence = _evidence("TBK m.49")
    evidence[0]["yururluk_bitis"] = "2020-01-01"

    result = harden_answer(
        answer_text="Haksız fiil sorumluluğu vardır. [Kaynak: TBK m.49]",
        citations=["TBK m.49"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="TBK m.49 nedir?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[("TBK", "49")],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TBK m.49"],
        today=date(2026, 3, 23),
    )

    assert result.final_mode == "refusal"
    assert result.final_reason == "temporal_mismatch"
    assert result.answer_contract["source_validity"] == "repealed"
    assert result.internal_blocked is True


def test_harden_answer_allows_historical_source_when_target_date_matches():
    evidence = _evidence("TBK m.49")
    evidence[0]["yururluk_baslangic"] = "2000-01-01"
    evidence[0]["yururluk_bitis"] = "2020-01-01"

    result = harden_answer(
        answer_text="2019 itibarıyla hüküm uygulanır. [Kaynak: TBK m.49]",
        citations=["TBK m.49"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="2019 yılında TBK m.49 nasıldı?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[("TBK", "49")],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TBK m.49"],
        today=date(2026, 3, 23),
    )

    assert result.final_mode == "answer"
    assert result.final_reason is None
    assert result.answer_contract["source_validity"] == "historical"


def test_harden_answer_blocks_narrow_claim_when_multiple_sources_are_unbound():
    evidence = _evidence("TBK m.49", "TBK m.50")

    result = harden_answer(
        answer_text="Haksız fiil ve tazminat değerlendirilir.",
        citations=["TBK m.49", "TBK m.50"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="Haksız fiil nedir?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TBK m.49", "TBK m.50"],
        today=date(2026, 3, 23),
    )

    assert result.final_mode == "refusal"
    assert result.final_reason == "claim_support_missing"


def test_harden_answer_skips_claim_binding_for_broad_procedure_question_without_explicit_article():
    evidence = _evidence("TBK m.146", "TBK m.156")

    result = harden_answer(
        answer_text=(
            "Bu soru bakımından doğrudan değerlendirilmesi gereken başlıca hükümler şunlardır:\n"
            "- [Kaynak: TBK m.146] On yıllık zamanaşımı uygulanır.\n"
            "- [Kaynak: TBK m.156] Kesilme halinde yeni süre işlemeye başlar."
        ),
        citations=["TBK m.146", "TBK m.156"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="TBK'ya göre genel zamanaşımı süresi kaç yıldır ve hangi tarihten itibaren işlemeye başlar?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TBK m.146", "TBK m.156"],
        today=date(2026, 3, 23),
    )

    assert result.final_mode == "answer"
    assert result.final_reason is None
    assert result.citations == ["TBK m.146", "TBK m.156"]
    assert result.answer_contract["claim_units"] == []


def test_harden_answer_drops_out_of_scope_secondary_citations_for_single_law_high_conf():
    evidence = _evidence("TBK m.237", "TMK m.706")

    result = harden_answer(
        answer_text=(
            "Taşınmaz satış sözleşmesi resmi şekle tabidir [Kaynak: TBK m.237]. "
            "Noter onayı tek başına yeterli değildir [Kaynak: TMK m.706]."
        ),
        citations=["TBK m.237", "TMK m.706"],
        blocked=False,
        verification={"verdict": "pass"},
        question_raw="TBK'ya göre taşınmaz satış sözleşmesi hangi şekle tabidir?",
        mentioned_laws=["TBK"],
        explicit_article_refs=[],
        law_filter=None,
        assembled_evidence=evidence,
        allowed_source_whitelist=["TBK m.237", "TMK m.706"],
        today=date(2026, 3, 23),
    )

    assert result.final_mode == "answer"
    assert result.final_reason is None
    assert result.citations == ["TBK m.237"]
    assert result.answer_contract["primary_source_id"] == "TBK m.237"
    assert result.answer_contract["secondary_source_ids"] == []
