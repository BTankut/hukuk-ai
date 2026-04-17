from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mevzuat_faz2d.prepare_phase import CONFLICT_IDS, build_outputs


def test_conflict_batch_contains_exactly_five_conflict_rows() -> None:
    outputs = build_outputs()
    csv_rows = outputs["csv_rows"]

    assert len(csv_rows) == 5
    assert [row["row_id"] for row in csv_rows] == CONFLICT_IDS
    assert len({row["row_id"] for row in csv_rows}) == 5


def test_conflict_batch_has_final_arbiter_columns() -> None:
    outputs = build_outputs()
    row = outputs["csv_rows"][0]
    assert "final_decision" in row
    assert "final_comment" in row
    assert "final_corrected_answer" in row
    assert "final_reviewer_name" in row


def test_protocol_and_gate_are_ready() -> None:
    outputs = build_outputs()
    assert "final_reviewer_name" in outputs["protocol_doc"]
    assert "READY - Mevzuat Faz-2D Conflict Resolution Batch Produced" in outputs["gate_doc"]
