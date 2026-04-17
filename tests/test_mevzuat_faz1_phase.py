from __future__ import annotations

from pathlib import Path

from scripts.mevzuat_faz1.run_phase import (
    build_shadow_primary_id,
    build_shadow_vector,
    discover_source_files,
    render_next_doc,
)


def test_build_shadow_vector_is_stable_and_normalized() -> None:
    vec1 = build_shadow_vector("HMK m.107")
    vec2 = build_shadow_vector("HMK m.107")
    assert len(vec1) == 256
    assert vec1 == vec2
    norm = sum(value * value for value in vec1)
    assert 0.99 <= norm <= 1.01


def test_discover_source_files_exact_layout(tmp_path: Path) -> None:
    base = tmp_path / "mevzuat"
    source_dir = base / "mevzuat_db"
    source_dir.mkdir(parents=True)
    for name in ("article_rows.jsonl", "normalized_source.txt", "source_manifest.json", "checksums.sha256"):
        (source_dir / name).write_text("", encoding="utf-8")
    found = discover_source_files(base)
    assert found["article_rows"] == source_dir / "article_rows.jsonl"
    assert found["normalized_source"] == source_dir / "normalized_source.txt"
    assert found["source_manifest"] == source_dir / "source_manifest.json"
    assert found["checksums"] == source_dir / "checksums.sha256"


def test_build_shadow_primary_id_is_stable_per_row() -> None:
    row = {"source_id": "HMK:6100:m107:f0:from2011-10-01:to9999-12-31"}
    assert build_shadow_primary_id(row, row_ordinal=12) == "HMK:6100:m107:f0:from2011-10-01:to9999-12-31::row:12"


def test_render_next_doc_pass_and_fail() -> None:
    text_pass = render_next_doc("PASS - Mevzuat Faz-1 Shadow Integration Closed")
    text_fail = render_next_doc("NO-GO - Mevzuat Faz-1 Shadow Integration")
    assert "mevzuat faz-2 integrated acceptance and lawyer review" in text_pass
    assert "mevzuat faz-1 remediation under canonical current authority" in text_fail
