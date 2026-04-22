from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/benchmark/phase10_completeness_calibration.py"
SPEC = importlib.util.spec_from_file_location("phase10_completeness_calibration", MODULE_PATH)
assert SPEC and SPEC.loader
phase10_completeness_calibration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase10_completeness_calibration)


def test_task_type_slots_are_specific_for_temporal_validity() -> None:
    slots = phase10_completeness_calibration.must_have_slots("temporal_validity")

    assert "temporal_validity" in slots
    assert "exact_source_identity" in slots


def test_unknown_task_type_uses_generic_legal_answer_slots() -> None:
    slots = phase10_completeness_calibration.must_have_slots("unknown_task")

    assert slots == ("governing_source", "exact_source_identity", "result_or_holding")
