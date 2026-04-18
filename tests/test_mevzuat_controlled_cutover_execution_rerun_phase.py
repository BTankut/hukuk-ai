from pathlib import Path
import importlib.util
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "mevzuat_cutover" / "run_controlled_cutover_execution_rerun_phase.py"
SPEC = importlib.util.spec_from_file_location("mevzuat_cutover_execution_rerun_phase", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_select_smoke_cases_returns_expected_shape():
    cases = MODULE.select_smoke_cases(MODULE.SOURCE_ARTICLE_ROWS)
    assert len(cases) == 6
    assert {case.case_id for case in cases} == {
        "KANUN-A",
        "CBK-A",
        "YONETMELIK-A",
        "CB-YONETMELIK-A",
        "TEBLIG-A",
        "MULGA-A",
    }


def test_evaluate_runtime_case_accepts_supported_answer():
    case = MODULE.SmokeCase(
        case_id="KANUN-A",
        label="3224 m.1",
        belge_turu="kanun",
        query_text="3224 m.1",
        expected_source_id="3224:3224:m1:f0:from1985-06-25:to9999-12-31",
        expected_display_citation="3224 m.1",
        expected_mulga_hidden=False,
    )
    body = {
        "final_mode": "partial",
        "citations": ["3224 m.1"],
        "answer_contract": {"primary_source_id": "3224 m.1"},
    }
    result = MODULE.evaluate_runtime_case(case, 200, body, None)
    assert result["source_correct"] is True
    assert result["wrong_source"] is False
    assert result["runtime_error"] is False


def test_evaluate_runtime_case_accepts_temporal_refusal():
    case = MODULE.SmokeCase(
        case_id="MULGA-A",
        label="7354 m.2",
        belge_turu="kanun",
        query_text="7354 m.2",
        expected_source_id="7354:7354:m2:f0:from2022-02-14:to1900-01-01",
        expected_display_citation="7354 m.2",
        expected_mulga_hidden=True,
    )
    body = {
        "final_mode": "refusal",
        "unsupported_reason": "temporal_mismatch",
        "citations": [],
        "answer_contract": {"primary_source_id": "7354 m.2", "unsupported_reason": "temporal_mismatch"},
    }
    result = MODULE.evaluate_runtime_case(case, 200, body, None)
    assert result["source_correct"] is True
    assert result["wrong_source"] is False


def test_evaluate_runtime_case_detects_vector_runtime_error():
    case = MODULE.SmokeCase(
        case_id="KANUN-A",
        label="3224 m.1",
        belge_turu="kanun",
        query_text="3224 m.1",
        expected_source_id="3224:3224:m1:f0:from1985-06-25:to9999-12-31",
        expected_display_citation="3224 m.1",
        expected_mulga_hidden=False,
    )
    result = MODULE.evaluate_runtime_case(case, 500, None, "vector dimension mismatch on search")
    assert result["runtime_error"] is True
    assert result["error_class"] == "vector_dimension_mismatch"


def test_render_next_doc_no_go_path():
    rendered = MODULE.render_next_doc("NO-GO - Mevzuat Controlled Cutover Execution Rerun")
    assert "controlled cutover remediation" in rendered
