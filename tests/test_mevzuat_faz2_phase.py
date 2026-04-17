from __future__ import annotations

from collections import Counter

from scripts.mevzuat_faz2.prepare_phase import (
    AcceptanceRow,
    CATEGORY_ORDER,
    BATCH_CATEGORY_TARGETS,
    assign_batches,
    has_bad_controls,
    render_gate_doc,
)


def _row(category: str, source_type: str, index: int) -> AcceptanceRow:
    return AcceptanceRow(
        category=category,
        expected_source_type=source_type,
        expected_display_citation=f"{source_type} m.{index}",
        expected_yururluk_state="YURURLUKTE",
        cross_type_disambiguation=category == "cross_type_wrong_source_disambiguation",
        question=f"Q {category} {index}",
        model_answer=f"A {category} {index}",
        source_citation=f"{source_type} m.{index}",
        source_id=f"{source_type}:{index}",
        canonical_source_locator=f"law://{source_type.lower()}/{index}",
        second_reviewer_name="REQUIRED" if category == "cross_type_wrong_source_disambiguation" else "",
    )


def test_has_bad_controls_detects_binary_like_text() -> None:
    assert has_bad_controls("\x05\x06\x07 garbled text")
    assert not has_bad_controls("Amaç MADDE 1 Bu hüküm yürürlüktedir.")


def test_assign_batches_preserves_exact_category_targets() -> None:
    rows: list[AcceptanceRow] = []
    source_types = ["KANUN", "CB_KARARNAME", "YONETMELIK", "CB_YONETMELIK"]
    for category in CATEGORY_ORDER:
        target = BATCH_CATEGORY_TARGETS[category] * 4
        for index in range(target):
            rows.append(_row(category, source_types[index % len(source_types)], index))

    assigned = assign_batches(rows)
    assert len(assigned) == 240

    batch_counts = Counter(row.batch_id for row in assigned)
    assert batch_counts == {
        "MEVZUAT-FAZ-2-BATCH-001": 60,
        "MEVZUAT-FAZ-2-BATCH-002": 60,
        "MEVZUAT-FAZ-2-BATCH-003": 60,
        "MEVZUAT-FAZ-2-BATCH-004": 60,
    }

    for batch_id in sorted(batch_counts):
        category_counts = Counter(row.category for row in assigned if row.batch_id == batch_id)
        assert category_counts == BATCH_CATEGORY_TARGETS


def test_render_gate_doc_ready_for_well_formed_pack() -> None:
    rows: list[AcceptanceRow] = []
    source_types = [
        "KANUN",
        "CB_KARARNAME",
        "YONETMELIK",
        "CB_YONETMELIK",
        "CB_KARAR",
        "CB_GENELGE",
        "KHK",
        "TUZUK",
        "KKY",
        "UY",
        "TEBLIGLER",
        "MULGA",
    ]
    for category in CATEGORY_ORDER:
        target = BATCH_CATEGORY_TARGETS[category] * 4
        for index in range(target):
            rows.append(_row(category, source_types[index % len(source_types)], index))
    assigned = assign_batches(rows)
    decision, gate_text = render_gate_doc(assigned)
    assert decision == "READY - Mevzuat Faz-2 Lawyer Review Packs Produced"
    assert "cross-type second review flagged" in gate_text
