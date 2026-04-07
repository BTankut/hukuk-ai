import importlib.util
from pathlib import Path
import sys


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "hat_b_case_law_full_materialization_v3.py"
)
SPEC = importlib.util.spec_from_file_location("hat_b_case_law_full_materialization_v3", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

AYM_BUNDLE = MODULE.AYM_BUNDLE
DANISTAY_BUNDLE = MODULE.DANISTAY_BUNDLE
YARGITAY_BUNDLE = MODULE.YARGITAY_BUNDLE
_clean_text = MODULE._clean_text
_page_limit = MODULE._page_limit
_round_ratio = MODULE._round_ratio
parse_danistay_units = MODULE.parse_danistay_units
parse_yargitay_units = MODULE.parse_yargitay_units


def test_clean_text_strips_tags_and_entities() -> None:
    assert _clean_text("<p>A&nbsp;B</p>\n<div>C</div>") == "A B C"


def test_page_limit_full_fetches_small_shards() -> None:
    assert _page_limit(240, 100, 300, 3) == 3
    assert _page_limit(40, 100, 300, 3) == 1


def test_page_limit_caps_large_shards() -> None:
    assert _page_limit(5000, 100, 300, 3) == 3
    assert _page_limit(1500, 100, 1000, 5) == 5


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


def test_round_ratio_returns_eight_decimal_precision() -> None:
    assert _round_ratio(20, 22271) == round(20 / 22271, 8)
