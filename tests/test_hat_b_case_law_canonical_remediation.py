import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "hat_b_case_law_canonical_remediation.py"
SPEC = importlib.util.spec_from_file_location("hat_b_case_law_canonical_remediation", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

AYM_BUNDLE = MODULE.AYM_BUNDLE
DANISTAY_BUNDLE = MODULE.DANISTAY_BUNDLE
YARGITAY_BUNDLE = MODULE.YARGITAY_BUNDLE
_clean_text = MODULE._clean_text
parse_danistay_units = MODULE.parse_danistay_units
parse_yargitay_units = MODULE.parse_yargitay_units


def test_clean_text_strips_tags_and_entities() -> None:
    assert _clean_text("<p>A&nbsp;B</p>\n<div>C</div>") == "A B C"


def test_parse_yargitay_units_reads_all_select_groups() -> None:
    groups = parse_yargitay_units(YARGITAY_BUNDLE.read_text(encoding="utf-8", errors="replace"))
    assert "Hukuk Genel Kurulu" in groups["yargitayMah"]
    assert "1. Hukuk Dairesi" in groups["hukuk"]
    assert "1. Ceza Dairesi" in groups["ceza"]


def test_parse_danistay_units_reads_daire_options() -> None:
    units = parse_danistay_units(DANISTAY_BUNDLE.read_text(encoding="utf-8", errors="replace"))
    assert "1. Daire" in units
    assert "İdare Dava Daireleri Kurulu" in units


def test_aym_bundle_contains_visible_totals() -> None:
    text = AYM_BUNDLE.read_text(encoding="utf-8", errors="replace")
    assert "5533 Karar Bulundu" in text
    assert "16738 Karar Bulundu" in text
