from __future__ import annotations

from rag.answer_slots import (
    resolve_required_slot_matrix_for_query,
    runtime_slots_for_matrix_slot_calibrated,
)


def test_phase20b_yonetmelik_family_slots_are_calibrated_systemically():
    resolution = resolve_required_slot_matrix_for_query(
        query="Mesafeli sözleşmeler yönetmeliğinde cayma hakkı istisnası ve usulü nedir?",
        template="exception",
        requested_source_families=["yonetmelik"],
    )

    assert resolution.matrix_version.endswith("+phase20b")
    assert "YONETMELIK" in resolution.family_labels
    assert "governing_regulation" in resolution.matrix_slots
    assert "procedure_or_condition" in resolution.matrix_slots
    assert "exception_or_limitation" in resolution.matrix_slots
    assert "governing_source" in resolution.runtime_slots
    assert "exact_source_identity" in resolution.runtime_slots
    assert "procedure_or_consequence" in resolution.runtime_slots
    assert "scenario_applicability" in resolution.runtime_slots


def test_phase20b_teblig_family_adds_exception_slot():
    resolution = resolve_required_slot_matrix_for_query(
        query="Tebliğdeki uygulama formülü ve istisna nedir?",
        template="procedure",
        requested_source_families=["teblig"],
    )

    assert resolution.matrix_version.endswith("+phase20b")
    assert "TEBLIGLER" in resolution.family_labels
    assert "exception_or_limitation" in resolution.matrix_slots
    assert "exception_or_limitation" in resolution.runtime_slots


def test_phase20b_cb_karar_relation_slot_is_query_scoped():
    relation_resolution = resolve_required_slot_matrix_for_query(
        query="9903 sayılı karar ile uygulama tebliği arasındaki dayanak ilişkisi nedir?",
        template="comparison_or_temporal",
        requested_source_families=["cb_karar"],
    )
    plain_resolution = resolve_required_slot_matrix_for_query(
        query="9903 sayılı kararın yürürlük tarihi nedir?",
        template="comparison_or_temporal",
        requested_source_families=["cb_karar"],
    )

    assert "supporting_regulation_or_teblig_relation" in relation_resolution.matrix_slots
    assert "supporting_regulation_or_teblig_relation" not in plain_resolution.matrix_slots
    assert runtime_slots_for_matrix_slot_calibrated(
        "supporting_regulation_or_teblig_relation"
    ) == ["hierarchy_or_conflict_rule", "document_selection_reason"]


def test_phase20b_non_target_family_keeps_phase18_matrix_version():
    resolution = resolve_required_slot_matrix_for_query(
        query="İş Kanunu m.18 hangi sonucu doğurur?",
        template="direct",
        requested_source_families=["kanun"],
    )

    assert not resolution.matrix_version.endswith("+phase20b")
