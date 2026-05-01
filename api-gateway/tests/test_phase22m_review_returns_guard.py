from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "benchmark"
    / "check_phase22m_review_returns.py"
)

spec = importlib.util.spec_from_file_location("check_phase22m_review_returns", SCRIPT_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


P0_COLUMNS = [
    "qid",
    "legal_reviewer_decision",
    "legal_reviewer_notes",
    "confirmed_expected_source",
    "confirmed_article_or_clause",
    "official_source_url",
    "effective_state_decision",
    "current_law_relation",
    "backfill_required",
]

P1_COLUMNS = [
    "qid",
    "legal_reviewer_decision",
    "legal_reviewer_notes",
    "expected_source_if_any",
    "taxonomy_decision",
    "runtime_relabel_allowed",
    "backfill_required",
]

OFFICIAL_COLUMNS = [
    "source_title",
    "official_url",
    "downloaded",
    "raw_file_path",
    "sha256",
    "parser_ready",
    "article_boundaries_detectable",
]


def returns_dir(tmp_path: Path) -> Path:
    path = tmp_path / "reports" / "benchmark" / "legal_review_returns"
    path.mkdir(parents=True)
    return path


def write_csv(path: Path, columns: list[str]) -> None:
    path.write_text(",".join(columns) + "\n", encoding="utf-8")


def write_complete_returns(base: Path) -> None:
    write_csv(base / "filled_phase_22M_P0_manual_legal_review_packet.csv", P0_COLUMNS)
    write_csv(base / "filled_phase_22M_P1_manual_taxonomy_review_packet.csv", P1_COLUMNS)
    write_csv(
        base / "filled_phase_22M_official_source_acquisition_checklist.csv",
        OFFICIAL_COLUMNS,
    )


def test_phase22m_guard_blocks_when_files_missing(tmp_path: Path) -> None:
    returns_dir(tmp_path)

    code, message = guard.check(tmp_path)

    assert code == 2
    assert "Phase 22F blocked: filled legal review CSVs missing" in message


def test_phase22m_guard_reports_missing_columns(tmp_path: Path) -> None:
    base = returns_dir(tmp_path)
    write_complete_returns(base)
    write_csv(
        base / "filled_phase_22M_P0_manual_legal_review_packet.csv",
        ["qid", "legal_reviewer_decision"],
    )

    code, message = guard.check(tmp_path)

    assert code == 3
    assert "missing required columns" in message
    assert "confirmed_expected_source" in message


def test_phase22m_guard_passes_with_complete_columns(tmp_path: Path) -> None:
    base = returns_dir(tmp_path)
    write_complete_returns(base)

    code, message = guard.check(tmp_path)

    assert code == 0
    assert message == "Phase 22M-R2 intake may proceed"
