from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/benchmark/phase8_article_alignment_audit.py"
SPEC = importlib.util.spec_from_file_location("phase8_article_alignment_audit", MODULE_PATH)
assert SPEC and SPEC.loader
phase8_article_alignment_audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase8_article_alignment_audit)

audit_bucket_for = phase8_article_alignment_audit.audit_bucket_for
select_mini_audit = phase8_article_alignment_audit.select_mini_audit


def test_phase8_audit_bucket_mapping() -> None:
    assert audit_bucket_for("exact") == "exact"
    assert audit_bucket_for("neighbor") == "neighbor"
    assert audit_bucket_for("title_only") == "title_only_or_weak"
    assert audit_bucket_for("unknown") == "title_only_or_weak"
    assert audit_bucket_for("none") == "clearly_wrong"


def test_phase8_mini_audit_selects_each_bucket() -> None:
    rows = []
    for bucket, alignment in (
        ("exact", "exact"),
        ("neighbor", "neighbor"),
        ("title_only_or_weak", "title_only"),
        ("clearly_wrong", "none"),
    ):
        for index in range(6):
            rows.append(
                {
                    "qid": f"{bucket}-{index}",
                    "score_0_10_proxy": str(index),
                    "audit_bucket": bucket,
                    "article_alignment": alignment,
                }
            )

    selected = select_mini_audit(rows, per_bucket=5)

    assert len(selected) == 20
    assert {row["audit_bucket"] for row in selected} == {
        "exact",
        "neighbor",
        "title_only_or_weak",
        "clearly_wrong",
    }
