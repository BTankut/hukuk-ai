from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_training_dataset as builder  # noqa: E402


def test_maybe_apply_duplicate_canonicalization_collapses_selected_cluster(tmp_path: Path) -> None:
    records = [
        {"instruction": "i", "input": "SORU: Q1", "output": "A1"},
        {"instruction": "i", "input": "SORU: Q1", "output": "A2"},
        {"instruction": "i", "input": "SORU: Q2", "output": "B1"},
    ]
    packet_file = tmp_path / "packet.json"
    manifest_file = tmp_path / "manifest.json"
    packet_file.write_text(
        json.dumps(
            {
                "clusters": [
                    {
                        "cluster_id": "cluster-01",
                        "question": "Q1",
                        "variants": [
                            {"variant_id": "cluster-01-variant-01", "output": "A2"},
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    manifest_file.write_text(
        json.dumps(
            {
                "selections": [
                    {
                        "cluster_id": "cluster-01",
                        "question": "Q1",
                        "selected_variant_id": "cluster-01-variant-01",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    rewritten, stats = builder.maybe_apply_duplicate_canonicalization(
        records,
        packet_file,
        manifest_file,
    )

    assert len(rewritten) == 2
    assert rewritten[0]["output"] == "A2"
    assert stats is not None
    assert stats["before"]["duplicate_excess_rows"] == 1
    assert stats["after"]["duplicate_excess_rows"] == 0


def test_maybe_apply_duplicate_canonicalization_skips_when_unconfigured() -> None:
    records = [{"instruction": "i", "input": "SORU: Q1", "output": "A1"}]

    rewritten, stats = builder.maybe_apply_duplicate_canonicalization(records, None, None)

    assert rewritten == records
    assert stats is None


def test_finalize_output_row_preserves_only_canonicalization_meta() -> None:
    row = builder.finalize_output_row(
        {
            "instruction": "i",
            "input": "SORU: Q1",
            "output": "A1",
            "_meta": {
                "bucket": "revised_needed",
                "category": "tbk_genel",
                "canonicalized_duplicate_cluster": "cluster-01",
                "selected_variant_id": "cluster-01-variant-02",
                "collapsed_from_rows": 4,
            },
        }
    )

    assert row == {
        "instruction": "i",
        "input": "SORU: Q1",
        "output": "A1",
        "_meta": {
            "canonicalized_duplicate_cluster": "cluster-01",
            "selected_variant_id": "cluster-01-variant-02",
            "collapsed_from_rows": 4,
        },
    }
