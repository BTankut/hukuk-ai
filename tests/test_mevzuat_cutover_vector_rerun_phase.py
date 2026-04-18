from pathlib import Path
import importlib.util
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "mevzuat_cutover" / "run_vector_blocker_rerun_phase.py"
SPEC = importlib.util.spec_from_file_location("mevzuat_cutover_vector_rerun_phase", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_build_shadow_primary_id_is_stable():
    row = {"source_id": "HMK:6100:m107:f0:from2011-10-01:to9999-12-31"}
    assert MODULE.build_shadow_primary_id(row, row_ordinal=42) == "HMK:6100:m107:f0:from2011-10-01:to9999-12-31::row:42"


def test_trim_text_for_storage_marks_truncation():
    text = "a" * (MODULE.TEXT_MAX_LENGTH + 100)
    trimmed, truncated = MODULE.trim_text_for_storage(text)
    assert truncated is True
    assert len(trimmed.encode("utf-8")) <= MODULE.TEXT_MAX_LENGTH
    assert trimmed.endswith("[TRUNCATED_FOR_COMPATIBLE_CANDIDATE]")


def test_render_next_doc_pass_path():
    rendered = MODULE.render_next_doc("PASS - Mevzuat Vector Blocker Remediation And Cutover Rerun Closed")
    assert "post-cutover stabilization and runtime verification" in rendered
