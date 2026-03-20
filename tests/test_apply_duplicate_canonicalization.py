from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import apply_duplicate_canonicalization as canonicalization  # noqa: E402


def test_apply_manifest_collapses_selected_question_cluster() -> None:
    records = [
        {"instruction": "i", "input": "SORU: Q1", "output": "A1"},
        {"instruction": "i", "input": "SORU: Q1", "output": "A2"},
        {"instruction": "i", "input": "SORU: Q2", "output": "B1"},
    ]
    packet = {
        "clusters": [
            {
                "cluster_id": "cluster-01",
                "question": "Q1",
                "variants": [
                    {"variant_id": "cluster-01-variant-01", "output": "A2"},
                ],
            }
        ]
    }
    manifest = {
        "selections": [
            {
                "cluster_id": "cluster-01",
                "question": "Q1",
                "selected_variant_id": "cluster-01-variant-01",
            }
        ]
    }

    rewritten, stats = canonicalization.apply_manifest(records, packet, manifest)

    assert len(rewritten) == 2
    assert rewritten[0]["output"] == "A2"
    assert rewritten[0]["_meta"]["canonicalized_duplicate_cluster"] == "cluster-01"
    assert stats["before"]["duplicate_excess_rows"] == 1
    assert stats["after"]["duplicate_excess_rows"] == 0
