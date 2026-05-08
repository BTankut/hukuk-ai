from pathlib import Path

from rag.phase24hy_replacement_guard import (
    apply_phase24hy_metadata_replacement_guard,
    evaluate_phase24hy_replacement,
)


def test_candidate_cannot_replace_primary_without_strong_metadata_lock(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HY_REPLACEMENT_GUARD", "true")

    decision = evaluate_phase24hy_replacement(
        base_primary_source_key="base",
        candidate_primary_source_key="candidate",
        base_family="kanun",
        candidate_family="kanun",
        requested_family="kanun",
        candidate_role="primary_source",
        candidate_metadata_lock_strength="weak",
        base_domain_score=80,
        candidate_domain_score=120,
        candidate_title_match_type="strong_overlap",
        candidate_article="5",
        candidate_article_match_type="source_local_support",
    )

    assert decision["replacement_allowed"] is False
    assert decision["replacement_block_reason"] == "candidate_metadata_lock_not_strong"
    assert decision["primary_source_preserved"] is True


def test_supporting_source_cannot_replace_primary(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HY_REPLACEMENT_GUARD", "true")

    decision = evaluate_phase24hy_replacement(
        base_primary_source_key="base",
        candidate_primary_source_key="support",
        base_family="kanun",
        candidate_family="yonetmelik",
        requested_family="kanun",
        candidate_role="supporting_source",
        candidate_metadata_lock_strength="strong",
        base_domain_score=70,
        candidate_domain_score=140,
        candidate_title_match_type="strong_overlap",
    )

    assert decision["replacement_allowed"] is False
    assert decision["replacement_block_reason"] == "candidate_role_not_primary"
    assert decision["supporting_only_added"] is True


def test_identifier_drift_blocked_when_primary_unchanged(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HY_REPLACEMENT_GUARD", "true")

    decision = evaluate_phase24hy_replacement(
        base_primary_source_key="same",
        candidate_primary_source_key="same",
        base_family="kanun",
        candidate_family="kanun",
        requested_family="kanun",
        candidate_role="primary_source",
        candidate_metadata_lock_strength="strong",
        identifier_ambiguity_increases=True,
    )

    assert decision["replacement_attempted"] is False
    assert decision["primary_source_preserved"] is True
    assert decision["identifier_drift_blocked"] is True


def test_article_drift_blocked_when_primary_unchanged(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HY_REPLACEMENT_GUARD", "true")

    decision = evaluate_phase24hy_replacement(
        base_primary_source_key="same",
        candidate_primary_source_key="same",
        base_family="kanun",
        candidate_family="kanun",
        requested_family="kanun",
        candidate_role="primary_source",
        candidate_metadata_lock_strength="strong",
        base_article="10",
        base_article_match_type="source_local_support",
        candidate_article="0",
        candidate_article_match_type="title_only",
    )

    assert decision["replacement_attempted"] is False
    assert decision["primary_source_preserved"] is True
    assert decision["article_drift_blocked"] is True


def test_active_teb_not_rewritten_as_mulga(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HY_REPLACEMENT_GUARD", "true")

    decision = evaluate_phase24hy_replacement(
        base_primary_source_key="active-teblig",
        candidate_primary_source_key="historical-teblig",
        base_family="teblig",
        candidate_family="mulga_kanun",
        requested_family="teblig",
        candidate_role="primary_source",
        candidate_metadata_lock_strength="strong",
        base_domain_score=50,
        candidate_domain_score=120,
        candidate_title_match_type="strong_overlap",
        candidate_article="1",
        candidate_article_match_type="source_local_support",
        base_effective_state="active",
        candidate_effective_state="repealed",
    )

    assert decision["replacement_allowed"] is False
    assert decision["replacement_block_reason"] in {
        "candidate_family_domain_not_compatible",
        "active_teb_not_rewritten_as_mulga",
    }


def test_ambiguous_tuzuk_does_not_select_concrete_source(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HY_REPLACEMENT_GUARD", "true")

    selector = {
        "metadata_lookup_hit": True,
        "metadata_lookup_source": "normalized_title_lookup",
        "metadata_lookup_confidence": 0.9,
        "selected_source_keys": ["candidate"],
        "selected_families": ["tuzuk"],
        "candidates": [
            {
                "source_key": "candidate",
                "source_family": "tuzuk",
                "metadata_lookup_source": "normalized_title_lookup",
                "metadata_lookup_confidence": 0.9,
                "score": 95,
                "match_reasons": ["title_overlap:2"],
            }
        ],
    }

    guarded = apply_phase24hy_metadata_replacement_guard(
        selector,
        query="Tuzuk ile alt duzenleme celisir ise normlar hiyerarsisi nasil uygulanir?",
        source_family_resolution={"expected_family_prior": "tuzuk"},
    )

    assert guarded["metadata_lookup_hit"] is False
    assert guarded["selected_source_keys"] == []
    assert (
        guarded["phase24hy_metadata_replacement_guard"]["replacement_block_reason"]
        == "metadata_candidate_lock_not_strong"
    )


def test_kanun_same_family_replacement_requires_domain_improvement(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HY_REPLACEMENT_GUARD", "true")

    decision = evaluate_phase24hy_replacement(
        base_primary_source_key="base-law",
        candidate_primary_source_key="candidate-law",
        base_family="kanun",
        candidate_family="kanun",
        requested_family="kanun",
        candidate_role="primary_source",
        candidate_metadata_lock_strength="strong",
        base_domain_score=100,
        candidate_domain_score=101,
        candidate_title_match_type="strong_overlap",
        candidate_article="7",
        candidate_article_match_type="source_local_support",
    )

    assert decision["replacement_allowed"] is False
    assert decision["replacement_block_reason"] == "kanun_same_family_replacement_requires_domain_improvement"


def test_no_qid_specific_phase24hy_logic():
    root = Path(__file__).resolve().parents[1]
    checked = "\n".join(
        [
            (root / "src" / "rag" / "phase24hy_replacement_guard.py").read_text(encoding="utf-8"),
            (root / "src" / "rag" / "source_identity.py").read_text(encoding="utf-8"),
        ]
    )

    forbidden_fragments = [
        "KANUN-",
        "TEB-",
        "TUZUK-",
        "YON-",
        "CBY-",
        "KKY-",
        "UY-",
        "MULGA-",
        "CBG-",
        "CBKAR-",
    ]
    assert not any(fragment in checked for fragment in forbidden_fragments)
