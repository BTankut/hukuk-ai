from pathlib import Path
import importlib.util
import sys


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "mevzuat_cutover"
    / "run_cutover_switch_path_trace_isolation_phase.py"
)
SPEC = importlib.util.spec_from_file_location("mevzuat_cutover_switch_path_trace_isolation_phase", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_build_smoke_cases_materializes_unique_seven_rows() -> None:
    cases = MODULE.build_smoke_cases(MODULE.SOURCE_ARTICLE_ROWS, MODULE.FAILED_V3_SUMMARY_JSON)
    assert len(cases) == 7
    assert len({case.smoke_case_id for case in cases}) == 7
    assert cases[-1].smoke_case_id == "LIVE-KANUN-A"


def test_render_next_doc_ready_path() -> None:
    rendered = MODULE.render_next_doc("READY - Mevzuat Cutover Switch Path Trace And Isolation Closed")
    assert "cutover targeted remediation" in rendered


def test_build_divergence_row_marks_first_true_stage() -> None:
    pre_row = {
        "smoke_case_id": "KANUN-A",
        "resolved_collection": "mevzuat_e5_shadow",
        "resolved_filters": {"metadata_filter": None},
        "resolved_scope": {"law_scope_signal": "single"},
        "topk_source_ids": ["A"],
        "rerank_input_output": {"pre": ["A"], "post": ["A"]},
        "final_context_payload": {"assembled_context_char_count": 10},
        "final_response_citations": ["A m.1"],
    }
    post_row = {
        "smoke_case_id": "KANUN-A",
        "resolved_collection": "mevzuat_faz1_shadow_20260416",
        "resolved_filters": {"metadata_filter": None},
        "resolved_scope": {"law_scope_signal": "single"},
        "topk_source_ids": [],
        "rerank_input_output": {"pre": [], "post": []},
        "final_context_payload": {"assembled_context_char_count": 0},
        "final_response_citations": [],
    }
    row = MODULE.build_divergence_row(pre_row, post_row)
    assert row["collection_diff"] is True
    assert row["first_divergence_stage"] == "collection_diff"
