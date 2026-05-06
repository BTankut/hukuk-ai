#!/usr/bin/env python3
"""Read-only verification for the Phase 24HR Milvus shadow collection."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase24hr_shadow_build_dry_run import (
    EXPECTED_RAW_SHA256,
    REPORTS_DIR,
    TARGET_COLLECTION,
    rel,
)
from phase24hr_shadow_collection_build import BASE_COLLECTION, DRY_RUN_MANIFEST_JSONL, MILVUS_URI


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = REPORTS_DIR / "phase_24HR_shadow_collection_verify.csv"
OUT_JSON = REPORTS_DIR / "phase_24HR_shadow_collection_verify.json"
OUT_MD = REPORTS_DIR / "phase_24HR_shadow_collection_verify.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def milvus_client(uri: str):
    from pymilvus import MilvusClient

    return MilvusClient(uri=uri)


def query_ids(client: Any, collection: str, ids: list[str], *, output_fields: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for start in range(0, len(ids), 100):
        batch = ids[start : start + 100]
        expr = "id in [" + ",".join(json.dumps(item) for item in batch) + "]"
        rows.extend(client.query(collection_name=collection, filter=expr, output_fields=output_fields, limit=len(batch)))
    return rows


def load_state(client: Any, collection: str) -> str:
    try:
        state = client.get_load_state(collection_name=collection)
    except Exception as exc:  # pragma: no cover - version/server dependent
        return f"unavailable:{type(exc).__name__}:{exc}"
    return str(state)


def row_status(check_id: str, status: str, expected: str, observed: str, evidence: str) -> dict[str, str]:
    return {
        "check_id": check_id,
        "status": status,
        "expected": expected,
        "observed": observed,
        "evidence": evidence,
    }


def verify() -> tuple[list[dict[str, str]], dict[str, Any]]:
    manifest = read_jsonl(DRY_RUN_MANIFEST_JSONL)
    ids = [str(row["proposed_id"]) for row in manifest]
    expected_by_id = {str(row["proposed_id"]): row for row in manifest}

    client = milvus_client(os.getenv("MILVUS_URI", MILVUS_URI))
    base_exists = client.has_collection(collection_name=BASE_COLLECTION)
    target_exists = client.has_collection(collection_name=TARGET_COLLECTION)
    rows: list[dict[str, str]] = [
        row_status("base_collection_exists", "PASS" if base_exists else "FAIL", "exists", str(base_exists), BASE_COLLECTION),
        row_status("target_collection_exists", "PASS" if target_exists else "FAIL", "exists", str(target_exists), TARGET_COLLECTION),
    ]
    if not base_exists or not target_exists:
        summary = {
            "generated_at_utc": utc_now(),
            "status": "FAIL",
            "row_count": len(rows),
            "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
            "fail_count": sum(1 for row in rows if row["status"] == "FAIL"),
            "live_8000_modified": False,
            "candidate_gateway_started": False,
            "model_inference_called": False,
            "milvus_modified": False,
        }
        return rows, summary

    base_count = int(client.get_collection_stats(collection_name=BASE_COLLECTION).get("row_count", 0))
    target_count = int(client.get_collection_stats(collection_name=TARGET_COLLECTION).get("row_count", 0))
    target_rows = query_ids(client, TARGET_COLLECTION, ids, output_fields=["id", "text", "metadata"])
    base_collision_rows = query_ids(client, BASE_COLLECTION, ids, output_fields=["id"])
    target_by_id = {str(row.get("id")): row for row in target_rows}
    missing_ids = sorted(set(ids) - set(target_by_id))

    rows.extend(
        [
            row_status("base_entity_count", "PASS" if base_count > 0 else "FAIL", ">0", str(base_count), BASE_COLLECTION),
            row_status(
                "target_entity_count",
                "PASS" if target_count >= base_count + len(ids) else "FAIL",
                f">= {base_count + len(ids)}",
                str(target_count),
                TARGET_COLLECTION,
            ),
            row_status(
                "target_delta_rows_found",
                "PASS" if not missing_ids else "FAIL",
                str(len(ids)),
                str(len(target_rows)),
                rel(DRY_RUN_MANIFEST_JSONL),
            ),
            row_status(
                "base_delta_id_collision",
                "PASS" if not base_collision_rows else "FAIL",
                "0",
                str(len(base_collision_rows)),
                BASE_COLLECTION,
            ),
        ]
    )

    metadata_failures: list[str] = []
    text_failures: list[str] = []
    for row_id, expected in expected_by_id.items():
        target_row = target_by_id.get(row_id)
        if not target_row:
            continue
        metadata = target_row.get("metadata") or {}
        expected_metadata = expected.get("metadata") or {}
        text = str(target_row.get("text") or "")
        checks = {
            "canonical_source_key_v2": expected["canonical_source_key_v2"],
            "binding_source_key": expected["binding_source_key"],
            "source_identifier": "19631",
            "source_family": "teblig",
            "source_family_raw": "TEBLIGLER",
            "raw_sha256": EXPECTED_RAW_SHA256,
            "qid_dependency": "TEB-04",
            "phase24hr_backfill": True,
            "canonical_span_materialized": True,
            "selected_document_has_materialized_body_span": True,
        }
        for key, expected_value in checks.items():
            if metadata.get(key) != expected_value:
                metadata_failures.append(f"{row_id}:{key}={metadata.get(key)!r}")
        if metadata.get("metadata_sha256") and metadata.get("metadata_sha256") != expected.get("metadata_sha256"):
            metadata_failures.append(f"{row_id}:metadata_sha256_drift")
        if metadata.get("shadow_text_truncated") is not False:
            text_failures.append(f"{row_id}:shadow_text_truncated={metadata.get('shadow_text_truncated')!r}")
        if len(text) != int(expected_metadata.get("shadow_text_length") or len(text)):
            text_failures.append(f"{row_id}:text_length={len(text)} expected={expected_metadata.get('shadow_text_length')}")

    load_state_text = load_state(client, TARGET_COLLECTION)
    rows.extend(
        [
            row_status(
                "delta_metadata_integrity",
                "PASS" if not metadata_failures else "FAIL",
                "all expected metadata values",
                "ok" if not metadata_failures else "|".join(metadata_failures[:5]),
                TARGET_COLLECTION,
            ),
            row_status(
                "delta_text_not_truncated",
                "PASS" if not text_failures else "FAIL",
                "no truncation and expected text lengths",
                "ok" if not text_failures else "|".join(text_failures[:5]),
                TARGET_COLLECTION,
            ),
            row_status(
                "target_load_state_observed",
                "PASS" if "Loaded" in load_state_text or "loaded" in load_state_text.lower() else "WARN",
                "loaded if server exposes load state",
                load_state_text,
                TARGET_COLLECTION,
            ),
        ]
    )

    fail_count = sum(1 for row in rows if row["status"] == "FAIL")
    summary = {
        "generated_at_utc": utc_now(),
        "status": "PASS" if fail_count == 0 else "FAIL",
        "row_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
        "warn_count": sum(1 for row in rows if row["status"] == "WARN"),
        "fail_count": fail_count,
        "base_collection": BASE_COLLECTION,
        "target_collection": TARGET_COLLECTION,
        "base_entity_count": base_count,
        "target_entity_count": target_count,
        "delta_row_count": len(ids),
        "target_delta_rows_found": len(target_rows),
        "base_delta_id_collision_count": len(base_collision_rows),
        "load_state": load_state_text,
        "live_8000_modified": False,
        "candidate_gateway_started": False,
        "model_inference_called": False,
        "milvus_modified": False,
    }
    return rows, summary


def write_outputs(rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    fields = ["check_id", "status", "expected", "observed", "evidence"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    OUT_JSON.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Phase 24HR Shadow Collection Verify",
        "",
        f"- generated_at_utc: `{summary['generated_at_utc']}`",
        f"- status: `{summary['status']}`",
        f"- row_count: `{summary['row_count']}`",
        f"- pass_count: `{summary['pass_count']}`",
        f"- warn_count: `{summary.get('warn_count', 0)}`",
        f"- fail_count: `{summary['fail_count']}`",
        f"- base_collection: `{summary.get('base_collection', BASE_COLLECTION)}`",
        f"- target_collection: `{summary.get('target_collection', TARGET_COLLECTION)}`",
        f"- base_entity_count: `{summary.get('base_entity_count', '')}`",
        f"- target_entity_count: `{summary.get('target_entity_count', '')}`",
        f"- delta_row_count: `{summary.get('delta_row_count', '')}`",
        f"- target_delta_rows_found: `{summary.get('target_delta_rows_found', '')}`",
        f"- base_delta_id_collision_count: `{summary.get('base_delta_id_collision_count', '')}`",
        f"- load_state: `{summary.get('load_state', '')}`",
        "- live_8000_modified: `false`",
        "- candidate_gateway_started: `false`",
        "- model_inference_called: `false`",
        "",
        "| check | status | expected | observed |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['check_id']}` | `{row['status']}` | {row['expected'].replace('|', '\\|')} | {row['observed'].replace('|', '\\|')} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows, summary = verify()
    write_outputs(rows, summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
