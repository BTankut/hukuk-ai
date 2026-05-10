from __future__ import annotations

import hashlib
import json
from pathlib import Path

from data_pipeline.manifest_validator import normalize_source_family, validate_article_rows


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _row(**overrides: object) -> dict[str, object]:
    body = str(overrides.pop("body", "Madde 1 - Test metni."))
    row: dict[str, object] = {
        "belge_turu": "kanun",
        "belge_no": "6098",
        "belge_adi": "Turk Borclar Kanunu",
        "kanun_no": "6098",
        "kanun_adi": "Turk Borclar Kanunu",
        "source_id": "6098:6098:m1:f0:from2012-07-01:to9999-12-31",
        "madde_no": "1",
        "fikra_no": "0",
        "kind": "main",
        "body": body,
        "kaynak_url": "https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5",
        "resmi_gazete_tarih": "2011-02-04",
        "yururluk_baslangic": "2012-07-01",
        "yururluk_bitis": "9999-12-31",
        "mulga": False,
        "metin_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }
    row.update(overrides)
    return row


def test_source_family_normalization_covers_closure_values() -> None:
    assert normalize_source_family("KANUN") == "kanun"
    assert normalize_source_family("TEBLIGLER") == "teblig"
    assert normalize_source_family("KKY") == "kurul_karari"
    assert normalize_source_family("UY") == "usul_yonerge"
    assert normalize_source_family("unexpected") == "other"


def test_validate_article_rows_passes_complete_manifest(tmp_path: Path) -> None:
    rows_path = tmp_path / "article_rows.jsonl"
    _write_jsonl(
        rows_path,
        [
            _row(madde_no="1", source_id="6098:6098:m1:f0:from2012-07-01:to9999-12-31"),
            _row(
                madde_no="2",
                source_id="6098:6098:m2:f0:from2012-07-01:to9999-12-31",
                body="Madde 2 - Ikinci test metni.",
            ),
        ],
    )

    result = validate_article_rows(rows_path)

    assert result["pass"] is True
    assert result["required_missing_total"] == 0
    assert result["duplicate_source_id_count"] == 0
    assert result["hash_mismatch_count"] == 0
    assert result["document_count"] == 1
    assert result["manifest_hash"]


def test_validate_article_rows_fails_missing_required_metadata(tmp_path: Path) -> None:
    rows_path = tmp_path / "article_rows.jsonl"
    _write_jsonl(
        rows_path,
        [
            _row(
                resmi_gazete_tarih=None,
                yururluk_baslangic=None,
            )
        ],
    )

    result = validate_article_rows(rows_path)

    assert result["pass"] is False
    assert result["required_missing_by_field"]["official_gazette_date"] == 1
    assert result["required_missing_by_field"]["effective_start_date"] == 1
    assert "effective_state" not in result["required_missing_by_field"]
    assert result["unknown_effective_state_count"] == 1


def test_validate_article_rows_detects_hash_mismatch(tmp_path: Path) -> None:
    rows_path = tmp_path / "article_rows.jsonl"
    _write_jsonl(rows_path, [_row(metin_sha256="not-the-body-hash")])

    result = validate_article_rows(rows_path)

    assert result["pass"] is False
    assert result["hash_checked_count"] == 1
    assert result["hash_mismatch_count"] == 1


def test_validate_article_rows_uses_official_metadata_overrides(tmp_path: Path) -> None:
    rows_path = tmp_path / "article_rows.jsonl"
    overrides_path = tmp_path / "official_overrides.json"
    _write_jsonl(
        rows_path,
        [
            _row(
                resmi_gazete_tarih=None,
                yururluk_baslangic=None,
                source_id="6098:6098:m1:f0:from1900-01-01:to9999-12-31",
            )
        ],
    )
    overrides_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "source_id": "kanun:6098",
                        "official_gazette_date": "2011-02-04",
                        "publish_date": "2011-02-04",
                        "effective_start_date": "2012-07-01",
                        "version_date": "2011-02-04",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = validate_article_rows(rows_path, metadata_overrides_path=overrides_path)

    assert result["pass"] is True
    assert result["metadata_override_count"] == 1


def test_validate_article_rows_uses_source_id_temporal_end_date(tmp_path: Path) -> None:
    rows_path = tmp_path / "article_rows.jsonl"
    _write_jsonl(
        rows_path,
        [
            _row(
                belge_turu="mulga_kanun",
                source_id="7354:7354:m1:f0:from2022-02-14:to1900-01-01",
                yururluk_bitis=None,
                mulga=True,
            )
        ],
    )

    result = validate_article_rows(rows_path)

    assert result["pass"] is True
    assert "effective_end_date" not in result["required_missing_by_field"]
