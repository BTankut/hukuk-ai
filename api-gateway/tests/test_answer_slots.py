from __future__ import annotations

from rag.answer_slots import (
    _phase20_materialize_answer_slot_evidence_values,
    build_verified_answer_slots,
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


def test_phase20c_fills_scope_from_selected_result_evidence_when_supported():
    resolution = resolve_required_slot_matrix_for_query(
        query="Elektronik tebligat yönetmeliğinin kapsamı nedir?",
        template="condition",
        requested_source_families=["yonetmelik"],
    )
    answer_slots, summary = build_verified_answer_slots(
        required_slot_resolution=resolution,
        evidence_slot_values=[
            {
                "slot_name": "result_or_holding",
                "slot_value": (
                    "Bu Yönetmeliğin amacı ve kapsamı, elektronik ortamda yapılacak "
                    "tebligata ilişkin usul ve esasları düzenlemektir."
                ),
                "evidence_span_id": "29033 m.1/f.0",
                "evidence_article": "1",
                "slot_confidence": 0.7,
                "slot_missing_reason": "selected_span_excerpt",
            }
        ],
    )

    slots = {slot["slot_name"]: slot for slot in answer_slots}
    assert slots["scope"]["fill_status"] == "filled"
    assert slots["scope"]["slot_missing_reason"] is None
    assert summary["answer_slot_filled_count"] >= 1


def test_phase20c_fills_relation_slot_from_relation_bearing_evidence():
    resolution = resolve_required_slot_matrix_for_query(
        query="Elektronik tebligat yönetmeliği hangi kanuna dayanır?",
        template="comparison_or_temporal",
        requested_source_families=["yonetmelik"],
    )
    answer_slots, _summary = build_verified_answer_slots(
        required_slot_resolution=resolution,
        evidence_slot_values=[
            {
                "slot_name": "temporal_validity",
                "slot_value": (
                    "Bu Yönetmelik, 7201 sayılı Tebligat Kanunu uyarınca tebligat "
                    "çıkarmaya yetkili makamlar bakımından uygulanır."
                ),
                "evidence_span_id": "29033 m.1/f.0",
                "evidence_article": "1",
                "slot_confidence": 0.72,
                "slot_missing_reason": "effective_state_or_temporal_clause",
            }
        ],
    )

    slots = {slot["slot_name"]: slot for slot in answer_slots}
    assert slots["relation_to_law_if_question_asks"]["fill_status"] == "filled"
    assert slots["relation_to_law_if_question_asks"]["evidence_span_keys"] == ["29033 m.1/f.0"]


def test_phase20c_does_not_fill_exception_slot_without_exception_signal():
    resolution = resolve_required_slot_matrix_for_query(
        query="Tebliğdeki sözleşme kuralı ve istisna nedir?",
        template="exception",
        requested_source_families=["teblig"],
    )
    answer_slots, _summary = build_verified_answer_slots(
        required_slot_resolution=resolution,
        evidence_slot_values=[
            {
                "slot_name": "result_or_holding",
                "slot_value": "Döviz cinsinden sözleşmelere ilişkin genel uygulama kuralı düzenlenir.",
                "evidence_span_id": "11990 m.8/f.0",
                "evidence_article": "8",
                "slot_confidence": 0.7,
                "slot_missing_reason": "selected_span_excerpt",
            }
        ],
    )

    slots = {slot["slot_name"]: slot for slot in answer_slots}
    assert slots["exception_or_limitation"]["fill_status"] == "missing"


def test_phase20c_materializes_verified_matrix_slots_without_overriding_existing_rows():
    materialized = _phase20_materialize_answer_slot_evidence_values(
        evidence_required_slot_values=[
            {
                "slot_name": "governing_source",
                "slot_value": "Mevcut kaynak satırı korunur.",
                "evidence_span_id": "source m.1/f.0",
                "slot_confidence": 0.7,
            }
        ],
        answer_slots=[
            {
                "slot_name": "governing_source",
                "value": "Bu değer mevcut satırı ezmemeli.",
                "evidence_span_keys": ["source m.2/f.0"],
                "evidence_article_or_span": "2",
                "fill_status": "filled",
                "verifier_status": "verified",
                "confidence_0_100": 95,
            },
            {
                "slot_name": "procedure_or_consequence",
                "value": "Başvuru usulü seçili kaynak spanından doğrulanmıştır.",
                "evidence_span_keys": ["source m.3/f.0"],
                "evidence_article_or_span": "3",
                "fill_status": "filled",
                "verifier_status": "verified",
                "confidence_0_100": 84,
            },
            {
                "slot_name": "exception_or_limitation",
                "value": "Doğrulanmamış değer materyalize edilmez.",
                "evidence_span_keys": ["source m.4/f.0"],
                "evidence_article_or_span": "4",
                "fill_status": "unsupported",
                "verifier_status": "needs_review",
                "confidence_0_100": 80,
            },
        ],
    )

    rows = {row["slot_name"]: row for row in materialized}
    assert rows["governing_source"]["slot_value"] == "Mevcut kaynak satırı korunur."
    assert rows["procedure_or_consequence"]["evidence_span_id"] == "source m.3/f.0"
    assert rows["procedure_or_consequence"]["slot_confidence"] == 0.84
    assert "exception_or_limitation" not in rows
