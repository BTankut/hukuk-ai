from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "mevzuat_cutover"
    / "run_cutover_state_binding_live_serving_remediation_phase.py"
)
SPEC = importlib.util.spec_from_file_location("mevzuat_cutover_state_binding_phase", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_load_remediated_candidate_prefers_compat_collection() -> None:
    assert MODULE.load_remediated_candidate() == "mevzuat_faz1_shadow_20260418_compat1024"


def test_build_smoke_cases_uses_failed_v2_contract_shape() -> None:
    failed_summary = MODULE.load_json(MODULE.FAILED_RERUN_SUMMARY_JSON)
    cases = MODULE.build_smoke_cases(MODULE.SOURCE_ARTICLE_ROWS, failed_summary)
    assert len(cases) == 7
    assert cases[0].query_text == "3224 m.1"
    assert cases[-1].case_id == "LIVE-KANUN-A"
    assert cases[-1].query_text == "3224 m.1"


def test_render_next_doc_ready_path() -> None:
    rendered = MODULE.render_next_doc("READY - Mevzuat Cutover State Binding And Live Serving Remediation Closed")
    assert "mevzuat controlled cutover execution rerun" in rendered
