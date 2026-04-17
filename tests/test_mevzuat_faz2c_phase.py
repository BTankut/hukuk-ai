from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mevzuat_faz2c.prepare_phase import build_outputs, render_gate_doc


def test_outputs_are_unique_and_exact() -> None:
    outputs = build_outputs()
    batch1_rows = outputs["batch1_rows"]
    batch2_rows = outputs["batch2_rows"]
    all_rows = batch1_rows + batch2_rows

    assert len(all_rows) == 56
    assert len({row["row_id"] for row in all_rows}) == 56
    assert sum(row["is_problem_core"] == "true" for row in all_rows) == 32
    assert sum(row["is_sentinel_control"] == "true" for row in all_rows) == 24


def test_second_reviewer_columns_and_flags_are_present() -> None:
    outputs = build_outputs()
    all_rows = outputs["batch1_rows"] + outputs["batch2_rows"]

    required_rows = [row for row in all_rows if row["second_reviewer_required"] == "true"]
    assert required_rows
    assert all("second_reviewer_decision" in row for row in all_rows)
    assert all("second_reviewer_comment" in row for row in all_rows)
    assert all("second_reviewer_name" in row for row in all_rows)


def test_gate_decision_is_ready() -> None:
    outputs = build_outputs()
    decision, gate_doc = render_gate_doc(outputs["batch1_rows"], outputs["batch2_rows"])
    assert decision == "READY - Mevzuat Faz-2C Human Review Packs Produced"
    assert "duplicate_row_id_count_after" in gate_doc
