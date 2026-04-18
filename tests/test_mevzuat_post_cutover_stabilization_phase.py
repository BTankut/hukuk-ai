from pathlib import Path
import importlib.util
import sys


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "mevzuat_cutover"
    / "run_post_cutover_stabilization_runtime_verification_phase.py"
)
SPEC = importlib.util.spec_from_file_location("mevzuat_post_cutover_stabilization_phase", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_active_runtime_collection_is_authoritative_candidate():
    assert MODULE.ACTIVE_RUNTIME_COLLECTION == "mevzuat_faz1_shadow_20260418_compat1024"


def test_smoke_round_count_and_sleep_window_are_fixed():
    assert MODULE.SMOKE_ROUND_COUNT == 2
    assert MODULE.STABILIZATION_WINDOW_SLEEP_SECONDS == 5


def test_doc_names_are_bound_for_post_cutover_phase():
    assert "POST-CUTOVER-ACTIVE-RUNTIME-FREEZE" in MODULE.ACTIVE_FREEZE_DOC.name
    assert "POST-CUTOVER-STABILIZATION-WINDOW" in MODULE.WINDOW_DOC.name
    assert "POST-CUTOVER-RUNTIME-SMOKE" in MODULE.SMOKE_DOC.name
    assert "POST-CUTOVER-ROLLBACK" in MODULE.ROLLBACK_DOC.name
    assert "POST-CUTOVER-STABILIZATION-GATE" in MODULE.GATE_DOC.name
    assert "POST-CUTOVER-STABILIZATION-SONRASI" in MODULE.NEXT_DOC.name


def test_regression_count_tracks_pass_to_fail_only():
    immediate = [
        {"smoke_key": "retrieval:KANUN-A", "case_result": "PASS"},
        {"smoke_key": "live:KANUN-A", "case_result": "PASS"},
    ]
    stabilization = [
        {"smoke_key": "retrieval:KANUN-A", "case_result": "FAIL"},
        {"smoke_key": "live:KANUN-A", "case_result": "PASS"},
    ]
    assert MODULE.compute_observed_regression_count(immediate, stabilization) == 1


def test_render_next_doc_pass_path():
    rendered = MODULE.render_next_doc("PASS - Mevzuat Post-Cutover Stabilization And Runtime Verification Closed")
    assert "primary-law runtime authoritative line closed" in rendered
