from pathlib import Path

from rag.phase24hx_constrained_routing import evaluate_phase24hx_replacement
from routers.chat import _phase24hu_secondary_family_recall_policy
from source_family_resolver import SourceFamilyResolution


def _kanun_resolution() -> SourceFamilyResolution:
    return SourceFamilyResolution(
        predicted_family="kanun",
        family_confidence=0.88,
        routing_families=["kanun"],
        preferred_families=["kanun"],
    )


def test_constrained_routing_requires_explicit_source_role_trigger(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HX_CONSTRAINED_ROUTING", "true")

    decision = evaluate_phase24hx_replacement(
        explicit_source_role_trigger=False,
        base_primary_source_key="base",
        candidate_primary_source_key="candidate",
        candidate_role="primary_source",
        base_family="kanun",
        candidate_family="kanun",
        requested_family="kanun",
        metadata_identity_lock_strength="strong",
        title_match_stronger=True,
        domain_match_stronger=True,
    )

    assert decision["replacement_allowed"] is False
    assert decision["replacement_block_reason"] == "no_explicit_source_role_trigger"


def test_candidate_cannot_replace_base_without_strong_metadata_lock(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HX_CONSTRAINED_ROUTING", "true")

    decision = evaluate_phase24hx_replacement(
        explicit_source_role_trigger=True,
        candidate_role="primary_source",
        base_family="kanun",
        candidate_family="kanun",
        requested_family="kanun",
        metadata_identity_lock_strength="medium",
        title_match_stronger=True,
        domain_match_stronger=True,
    )

    assert decision["replacement_allowed"] is False
    assert decision["replacement_block_reason"] == "metadata_identity_lock_not_strong"


def test_cross_family_candidate_becomes_supporting_not_primary(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HX_CONSTRAINED_ROUTING", "true")

    decision = evaluate_phase24hx_replacement(
        explicit_source_role_trigger=True,
        candidate_role="supporting_source",
        base_family="cb_yonetmelik",
        candidate_family="kanun",
        requested_family="cb_yonetmelik",
        metadata_identity_lock_strength="strong",
        title_match_stronger=True,
        domain_match_stronger=True,
    )

    assert decision["replacement_allowed"] is False
    assert decision["supporting_only_added"] is True
    assert decision["replacement_block_reason"] == "cby_authority_document_supporting_only"


def test_active_teb_not_rewritten_as_mulga(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HX_CONSTRAINED_ROUTING", "true")

    decision = evaluate_phase24hx_replacement(
        explicit_source_role_trigger=True,
        candidate_role="primary_source",
        base_family="teblig",
        candidate_family="mulga_kanun",
        requested_family="teblig",
        metadata_identity_lock_strength="strong",
        title_match_stronger=True,
        domain_match_stronger=True,
        base_effective_state="active",
        candidate_effective_state="repealed",
    )

    assert decision["replacement_allowed"] is False
    assert decision["replacement_block_reason"] == "active_teblig_not_rewritten_as_mulga"


def test_ambiguous_tuzuk_does_not_select_concrete_source(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HX_CONSTRAINED_ROUTING", "true")

    decision = evaluate_phase24hx_replacement(
        explicit_source_role_trigger=False,
        candidate_role="primary_source",
        base_family="tuzuk",
        candidate_family="tuzuk",
        requested_family="tuzuk",
        metadata_identity_lock_strength="weak",
        title_match_stronger=False,
        domain_match_stronger=False,
    )

    assert decision["replacement_allowed"] is False
    assert decision["replacement_block_reason"] == "no_explicit_source_role_trigger"


def test_kanun_same_family_replacement_requires_domain_improvement(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24HX_CONSTRAINED_ROUTING", "true")

    blocked = evaluate_phase24hx_replacement(
        explicit_source_role_trigger=True,
        candidate_role="primary_source",
        base_family="kanun",
        candidate_family="kanun",
        requested_family="kanun",
        metadata_identity_lock_strength="strong",
        title_match_stronger=True,
        domain_match_stronger=False,
    )
    allowed = evaluate_phase24hx_replacement(
        explicit_source_role_trigger=True,
        candidate_role="primary_source",
        base_family="kanun",
        candidate_family="kanun",
        requested_family="kanun",
        metadata_identity_lock_strength="strong",
        title_match_stronger=True,
        domain_match_stronger=True,
    )

    assert blocked["replacement_allowed"] is False
    assert blocked["replacement_block_reason"] == "kanun_replacement_requires_domain_and_identity_improvement"
    assert allowed["replacement_allowed"] is True


def test_phase24hx_secondary_recall_is_role_gated(monkeypatch):
    monkeypatch.delenv("ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL", raising=False)
    monkeypatch.setenv("ENABLE_PHASE24HX_CONSTRAINED_ROUTING", "true")

    no_role = _phase24hu_secondary_family_recall_policy(
        query="6502 sayılı kanunda cayma hakkı nedir?",
        requested_source_families=["kanun"],
        source_family_resolution=_kanun_resolution(),
        metadata_lookup_query_signals={"candidate_families": ["kky"]},
    )
    with_role = _phase24hu_secondary_family_recall_policy(
        query="6502 sayılı kanunda cayma hakkı istisnası yönetmelikte nasıl desteklenir?",
        requested_source_families=["kanun"],
        source_family_resolution=_kanun_resolution(),
        metadata_lookup_query_signals={"candidate_families": ["kky"]},
    )

    assert no_role["phase24hu_secondary_family_recall_enabled"] is True
    assert no_role["secondary_family_recall_reason"] == "no_source_role_query_signal"
    assert with_role["secondary_family_recall_reason"] == "source_role_secondary_family_signal"


def test_no_qid_specific_phase24hx_logic():
    root = Path(__file__).resolve().parents[1] / "src"
    source = "\n".join(
        [
            (root / "rag" / "phase24hx_constrained_routing.py").read_text(encoding="utf-8"),
            (root / "routers" / "chat.py").read_text(encoding="utf-8"),
        ]
    )

    for qid in ("KANUN-08", "TEB-04", "TUZUK-05", "YON-05"):
        assert qid not in source

