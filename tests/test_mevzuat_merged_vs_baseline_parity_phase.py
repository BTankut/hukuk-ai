from pathlib import Path
import importlib.util
import sys


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "mevzuat_cutover"
    / "run_merged_vs_baseline_matched_parity_phase.py"
)
SPEC = importlib.util.spec_from_file_location("mevzuat_merged_vs_baseline_parity_phase", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_build_matched_pack_shape():
    smoke_cases = MODULE.select_smoke_cases(MODULE.SOURCE_ARTICLE_ROWS)
    pack = MODULE.build_matched_pack(smoke_cases)
    assert len(pack) == 7
    assert pack[0]["pack_row_id"] == "retrieval:KANUN-A"
    assert pack[-1]["pack_row_id"] == "live:KANUN-A"


def test_pack_identity_is_stable_for_same_input():
    smoke_cases = MODULE.select_smoke_cases(MODULE.SOURCE_ARTICLE_ROWS)
    pack = MODULE.build_matched_pack(smoke_cases)
    assert MODULE.pack_identity(pack) == MODULE.pack_identity(pack)


def test_compare_helpers():
    assert MODULE.compare_counts(7, 7, higher_is_better=True) == "same"
    assert MODULE.compare_counts(7, 6, higher_is_better=True) == "better"
    assert MODULE.compare_counts(0, 1, higher_is_better=False) == "better"
    assert MODULE.compare_bool(True, True) == "same"
    assert MODULE.compare_bool(True, False) == "better"


def test_overall_delta_decision_prefers_worse_then_better():
    assert MODULE.overall_delta_decision(["same", "same"]) == "same"
    assert MODULE.overall_delta_decision(["same", "better"]) == "better"
    assert MODULE.overall_delta_decision(["better", "worse"]) == "worse"


def test_next_doc_same_routes_to_hat_b():
    rendered = MODULE.render_next_doc("same")
    assert "hat-b runtime-track continuation" in rendered


def test_next_doc_worse_routes_to_remediation():
    rendered = MODULE.render_next_doc("worse")
    assert "merged runtime remediation" in rendered
