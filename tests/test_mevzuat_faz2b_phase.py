from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mevzuat_faz2b.prepare_phase import (
    build_outputs,
    render_gate_doc,
)


def test_build_outputs_produces_exact_counts() -> None:
    outputs = build_outputs()

    problem_core = outputs["problem_core"]
    sentinel_rows = outputs["sentinel_rows"]
    batch1_rows = outputs["batch1_rows"]
    batch2_rows = outputs["batch2_rows"]

    assert len(problem_core) == 32
    assert len(sentinel_rows) == 24
    assert len(batch1_rows) == 28
    assert len(batch2_rows) == 28

    assert sum(1 for row in batch1_rows if row["is_problem_core"] == "true") == 16
    assert sum(1 for row in batch2_rows if row["is_problem_core"] == "true") == 16
    assert sum(1 for row in batch1_rows if row["is_sentinel_control"] == "true") == 12
    assert sum(1 for row in batch2_rows if row["is_sentinel_control"] == "true") == 12


def test_surface_distribution_is_exact() -> None:
    outputs = build_outputs()
    all_rows = outputs["batch1_rows"] + outputs["batch2_rows"]

    surface_counts = Counter(row["surface_name"] for row in all_rows)
    assert surface_counts == {
        "excluded_source_unsupported_source_refusal": 12,
        "yururluk_mulga_temporal_interpretation": 13,
        "citation_heavy_exact_locator_long_article": 15,
        "cross_type_wrong_source_disambiguation": 8,
        "source_local_direct_retrieval": 8,
    }

    cross_type_rows = [row for row in all_rows if row["cross_type_disambiguation"] == "true"]
    assert len(cross_type_rows) == 8
    assert all(row["second_reviewer_name"] == "REQUIRED" for row in cross_type_rows)

    problem_rows = [row for row in all_rows if row["is_problem_core"] == "true"]
    assert all(row["second_reviewer_name"] == "REQUIRED" for row in problem_rows)


def test_gate_decision_is_ready() -> None:
    outputs = build_outputs()
    decision, gate_doc = render_gate_doc(
        batch1=outputs["batch1_rows"],
        batch2=outputs["batch2_rows"],
        problem_core=outputs["problem_core"],
        sentinel_rows=outputs["sentinel_rows"],
    )
    assert decision == "READY - Mevzuat Faz-2B Real Lawyer Review Packs Produced"
    assert "problem_core_row_count" in gate_doc
