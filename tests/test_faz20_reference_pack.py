from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str((Path(__file__).resolve().parents[1] / "scripts/faz20")))

from build_reference_pack import build_reference_payload  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_faz20_reference_pack_normalizes_known_truths() -> None:
    faz13 = build_reference_payload(REPO_ROOT, "faz13")
    faz18 = build_reference_payload(REPO_ROOT, "faz18")
    faz19 = build_reference_payload(REPO_ROOT, "faz19")

    faz13_v3 = next(row for row in faz13["families"] if row["family_name"] == "v3-170")
    faz18_faz1 = next(row for row in faz18["families"] if row["family_name"] == "faz1-50")
    faz19_v3 = next(row for row in faz19["families"] if row["family_name"] == "v3-170")

    assert faz13_v3["mismatch_count"] == 6
    assert faz13_v3["mismatch_question_ids"] == [
        "TBK-051",
        "TBK-054",
        "TBK-055",
        "TBK-057",
        "TBK-058",
        "TBK-061",
    ]
    assert faz13_v3["first_divergence_stage_set"] == ["final_mode_mapping_hash"]
    assert faz18_faz1["mismatch_count"] == 1
    assert faz18_faz1["mismatch_question_ids"] == ["TBK-027"]
    assert faz19_v3["mismatch_count"] == 0
    assert faz19_v3["mismatch_question_ids"] == []
    assert faz19["reference_pack_integrity_pass"] is True
    assert faz19["reference_pack_contradiction_count"] == 0
