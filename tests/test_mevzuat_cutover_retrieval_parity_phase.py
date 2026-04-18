from pathlib import Path
import importlib.util
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "mevzuat_cutover" / "run_retrieval_runtime_parity_phase.py"
SPEC = importlib.util.spec_from_file_location("mevzuat_cutover_retrieval_parity_phase", MODULE_PATH)
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


def test_evaluate_runtime_smoke_case_accepts_supported_numeric_answer():
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
    result = MODULE.evaluate_runtime_smoke_case(case, body)
    assert result["source_correct"] is True
    assert result["wrong_source"] is False
    assert result["case_result"] == "PASS"


def test_evaluate_runtime_smoke_case_accepts_temporal_refusal_for_mulga():
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
    result = MODULE.evaluate_runtime_smoke_case(case, body)
    assert result["source_correct"] is True
    assert result["wrong_source"] is False
    assert result["case_result"] == "PASS"


def test_render_next_doc_ready_path():
    rendered = MODULE.render_next_doc("READY - Mevzuat Retrieval Runtime Parity Remediation Closed")
    assert "controlled cutover execution rerun" in rendered


def test_heading_parity_matches_accepts_synthetic_madde_no_heading():
    text = "24653 m.1\nMADDE 1 – Örnek metin"
    assert MODULE.heading_parity_matches("Madde No: 1", text) is True
