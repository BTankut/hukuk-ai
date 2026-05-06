#!/usr/bin/env python3
"""Fail-closed Phase 24HR shadow collection builder.

The default `plan` command is local-only and writes the exact guarded execution
plan. The `build-shadow` command can mutate Milvus, so it refuses to run unless
both `--execute` and the explicit option-A authorization token are provided.
It never changes live 8000, starts a gateway, or switches productization state.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase24hr_shadow_build_dry_run import (
    BASE_COLLECTION,
    CHUNKED_SPANS,
    EMBEDDING_MODEL,
    MAX_MILVUS_TEXT_LENGTH,
    REPORTS_DIR,
    TARGET_COLLECTION,
    VECTOR_DIMENSION,
    build_manifest_rows,
    read_jsonl,
    rel,
    sha256_file,
)


MILVUS_URI = "http://localhost:19530"
EMBEDDING_BASE_URL = "http://127.0.0.1:8081/v1"
AUTHORIZATION_TOKEN = "OPTION_A_APPROVED_PHASE24HR"

OUT_BUILD_PLAN_MD = REPORTS_DIR / "phase_24HR_shadow_collection_build_plan.md"
OUT_BUILD_REPORT_MD = REPORTS_DIR / "phase_24HR_shadow_collection_build_report.md"
OUT_RUNTIME_PROVENANCE_JSON = REPORTS_DIR / "phase_24HR_shadow_runtime_provenance.json"
DRY_RUN_SUMMARY = REPORTS_DIR / "phase_24HR_shadow_collection_dry_run_summary.json"
DRY_RUN_MANIFEST_JSONL = REPORTS_DIR / "phase_24HR_shadow_collection_dry_run_manifest.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_dry_run_summary() -> dict[str, Any]:
    if not DRY_RUN_SUMMARY.exists():
        raise FileNotFoundError(f"Missing dry-run summary: {rel(DRY_RUN_SUMMARY)}")
    summary = json.loads(DRY_RUN_SUMMARY.read_text(encoding="utf-8"))
    if summary.get("status") != "PASS":
        raise RuntimeError(f"Dry-run summary is not PASS: {summary.get('status')}")
    return summary


def load_spans_and_manifest() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    summary = load_dry_run_summary()
    spans = read_jsonl(CHUNKED_SPANS)
    manifest_rows = build_manifest_rows(spans)
    if len(manifest_rows) != int(summary.get("delta_row_count", -1)):
        raise RuntimeError(
            f"Dry-run manifest drift: summary={summary.get('delta_row_count')} rebuilt={len(manifest_rows)}"
        )
    return spans, manifest_rows, summary


def write_plan(args: argparse.Namespace) -> dict[str, Any]:
    _spans, manifest_rows, summary = load_spans_and_manifest()
    plan = {
        "generated_at_utc": utc_now(),
        "status": "READY_FOR_OPTION_A_AUTHORIZATION",
        "base_collection": args.base_collection,
        "target_collection": args.target_collection,
        "milvus_uri": args.milvus_uri,
        "embedding_base_url": args.embedding_base_url,
        "embedding_model": args.embedding_model,
        "vector_dimension": VECTOR_DIMENSION,
        "delta_row_count": len(manifest_rows),
        "dry_run_summary": rel(DRY_RUN_SUMMARY),
        "dry_run_manifest_jsonl": rel(DRY_RUN_MANIFEST_JSONL),
        "authorization_token_required": AUTHORIZATION_TOKEN,
        "execute_required": True,
        "live_8000_modified": False,
        "candidate_gateway_started": False,
        "model_inference_called": False,
        "milvus_modified_by_plan": False,
    }
    lines = [
        "# Phase 24HR Shadow Collection Build Plan",
        "",
        f"- generated_at_utc: `{plan['generated_at_utc']}`",
        f"- status: `{plan['status']}`",
        f"- base_collection: `{plan['base_collection']}`",
        f"- target_collection: `{plan['target_collection']}`",
        f"- delta_row_count: `{plan['delta_row_count']}`",
        f"- embedding_model: `{plan['embedding_model']}`",
        f"- vector_dimension: `{VECTOR_DIMENSION}`",
        f"- dry_run_summary: `{plan['dry_run_summary']}`",
        f"- dry_run_manifest_jsonl: `{plan['dry_run_manifest_jsonl']}`",
        "- live_8000_modified: `false`",
        "- milvus_modified_by_plan: `false`",
        "- candidate_gateway_started: `false`",
        "- model_inference_called: `false`",
        "",
        "## Guarded Execution Command",
        "",
        "```bash",
        "python3 scripts/benchmark/phase24hr_shadow_collection_build.py build-shadow \\",
        f"  --execute --authorization-token {AUTHORIZATION_TOKEN} \\",
        f"  --base-collection {args.base_collection} \\",
        f"  --target-collection {args.target_collection}",
        "```",
        "",
        "## Safety Notes",
        "",
        "- Without `--execute`, the builder refuses to mutate Milvus.",
        f"- Without `--authorization-token {AUTHORIZATION_TOKEN}`, the builder refuses before connecting to Milvus.",
        "- The target collection must be distinct from the base collection and must end with `_phase24hr`.",
        "- Existing target collection rebuild requires `--force-target-rebuild`; base collection is never dropped.",
        "- Live `8000`, Open WebUI, internal eval, serving candidate, productization, model path, prompt, and top-k are not changed by this script.",
    ]
    if not getattr(args, "no_write", False):
        OUT_BUILD_PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
    return plan


def ensure_authorized(args: argparse.Namespace) -> None:
    if not args.execute:
        raise RuntimeError("Refusing Milvus mutation: pass --execute only after owner option-A authorization.")
    if args.authorization_token != AUTHORIZATION_TOKEN:
        raise RuntimeError("Refusing Milvus mutation: missing or invalid option-A authorization token.")
    if args.base_collection == args.target_collection:
        raise RuntimeError("Refusing Milvus mutation: target collection must differ from base collection.")
    if not args.target_collection.endswith("_phase24hr"):
        raise RuntimeError("Refusing Milvus mutation: target collection must end with `_phase24hr`.")


def milvus_client(uri: str):
    try:
        from pymilvus import MilvusClient
    except Exception as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("pymilvus is required; run with the api-gateway Python environment.") from exc
    return MilvusClient(uri=uri)


def make_index_params(client: Any, *, index_type: str, mmap_enabled: bool):
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type=index_type,
        metric_type="COSINE",
        mmap_enabled=mmap_enabled,
    )
    return index_params


def create_target_collection(
    client: Any,
    *,
    target_collection: str,
    force_target_rebuild: bool,
    create_index_on_create: bool,
    index_type: str,
    mmap_enabled: bool,
) -> None:
    from pymilvus import DataType, MilvusClient

    if client.has_collection(collection_name=target_collection):
        if not force_target_rebuild:
            raise RuntimeError(
                f"Target collection already exists: {target_collection}. "
                "Use --force-target-rebuild only after confirming it is not live."
            )
        client.drop_collection(collection_name=target_collection)

    schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=256)
    schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
    schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=VECTOR_DIMENSION, mmap_enabled=mmap_enabled)
    schema.add_field(field_name="metadata", datatype=DataType.JSON)

    if create_index_on_create:
        client.create_collection(
            collection_name=target_collection,
            schema=schema,
            index_params=make_index_params(client, index_type=index_type, mmap_enabled=mmap_enabled),
        )
    else:
        client.create_collection(collection_name=target_collection, schema=schema)


def query_existing_ids(client: Any, collection: str, ids: list[str]) -> set[str]:
    existing: set[str] = set()
    for start in range(0, len(ids), 100):
        batch = ids[start : start + 100]
        expr = "id in [" + ",".join(json.dumps(item) for item in batch) + "]"
        rows = client.query(collection_name=collection, filter=expr, output_fields=["id"], limit=len(batch))
        existing.update(str(row["id"]) for row in rows)
    return existing


def embed_texts(texts: list[str], *, base_url: str, model: str, timeout: int = 120) -> list[list[float]]:
    payload = json.dumps({"model": model, "input": texts}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    data = parsed.get("data", [])
    if len(data) != len(texts):
        raise RuntimeError(f"Embedding response count mismatch: expected {len(texts)}, got {len(data)}")
    vectors = [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]
    for vector in vectors:
        if len(vector) != VECTOR_DIMENSION:
            raise RuntimeError(f"Embedding dimension mismatch: expected {VECTOR_DIMENSION}, got {len(vector)}")
    return vectors


def clone_base_collection(
    client: Any,
    *,
    base_collection: str,
    target_collection: str,
    batch_size: int,
    flush_every: int,
) -> int:
    iterator = client.query_iterator(
        collection_name=base_collection,
        batch_size=batch_size,
        output_fields=["id", "text", "embedding", "metadata"],
    )
    inserted = 0
    try:
        while True:
            rows = iterator.next()
            if not rows:
                break
            client.insert(collection_name=target_collection, data=rows)
            inserted += len(rows)
            if flush_every > 0 and inserted % flush_every < len(rows):
                client.flush(collection_name=target_collection)
            if inserted % 50000 < len(rows):
                print(f"[phase24hr] cloned_rows={inserted}", flush=True)
    finally:
        iterator.close()
    return inserted


def make_delta_row(span: dict[str, Any], manifest_row: dict[str, Any], embedding: list[float]) -> dict[str, Any]:
    text = f"{span.get('display_citation', '')}\n{span.get('body', '')}".strip()[:MAX_MILVUS_TEXT_LENGTH]
    return {
        "id": manifest_row["proposed_id"],
        "text": text,
        "embedding": embedding,
        "metadata": manifest_row["metadata"],
    }


def write_build_reports(report: dict[str, Any]) -> None:
    OUT_RUNTIME_PROVENANCE_JSON.write_text(
        json.dumps(
            {
                **report,
                "candidate_runtime_contract": {
                    "api_url": "not_started",
                    "milvus_collection": report["target_collection"],
                    "dgx_model": "/models/merged_model_fabric_stage_20260321",
                    "embedding_model": report["embedding_model"],
                    "live_8000_cutover": False,
                    "candidate_gateway_started": False,
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Phase 24HR Shadow Collection Build Report",
        "",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        f"- build_status: `{report['build_status']}`",
        f"- base_collection: `{report['base_collection']}`",
        f"- target_collection: `{report['target_collection']}`",
        f"- base_entity_count: `{report['base_entity_count']}`",
        f"- cloned_base_entity_count: `{report['cloned_base_entity_count']}`",
        f"- target_entity_count: `{report['target_entity_count']}`",
        f"- delta_entity_count: `{report['delta_entity_count']}`",
        f"- vector_dimension: `{report['vector_dimension']}`",
        f"- embedding_model: `{report['embedding_model']}`",
        f"- proposed_id_collision_count: `{report['proposed_id_collision_count']}`",
        f"- index_type: `{report['index_type']}`",
        f"- load_after_build: `{str(report['load_after_build']).lower()}`",
        "- live_8000_cutover: `false`",
        "- candidate_gateway_started: `false`",
        "",
        f"Runtime provenance: `{rel(OUT_RUNTIME_PROVENANCE_JSON)}`.",
    ]
    OUT_BUILD_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_shadow(args: argparse.Namespace) -> dict[str, Any]:
    ensure_authorized(args)
    spans, manifest_rows, summary = load_spans_and_manifest()
    client = milvus_client(args.milvus_uri)
    if not client.has_collection(collection_name=args.base_collection):
        raise RuntimeError(f"Base collection not found: {args.base_collection}")

    base_stats = client.get_collection_stats(collection_name=args.base_collection)
    base_count = int(base_stats.get("row_count", base_stats.get("num_entities", 0)))
    proposed_ids = [row["proposed_id"] for row in manifest_rows]
    existing_delta_ids = query_existing_ids(client, args.base_collection, proposed_ids)
    if existing_delta_ids:
        raise RuntimeError(f"Refusing build due to existing delta IDs in base collection: {sorted(existing_delta_ids)[:5]}")

    create_target_collection(
        client,
        target_collection=args.target_collection,
        force_target_rebuild=args.force_target_rebuild,
        create_index_on_create=not args.defer_index,
        index_type=args.index_type,
        mmap_enabled=args.mmap_enabled,
    )
    cloned_count = clone_base_collection(
        client,
        base_collection=args.base_collection,
        target_collection=args.target_collection,
        batch_size=args.clone_batch_size,
        flush_every=args.clone_flush_every,
    )

    delta_rows: list[dict[str, Any]] = []
    for start in range(0, len(spans), args.embedding_batch_size):
        span_batch = spans[start : start + args.embedding_batch_size]
        manifest_batch = manifest_rows[start : start + args.embedding_batch_size]
        texts = [f"{span.get('display_citation', '')}\n{span.get('body', '')}".strip() for span in span_batch]
        vectors = embed_texts(texts, base_url=args.embedding_base_url, model=args.embedding_model)
        for span, manifest_row, vector in zip(span_batch, manifest_batch, vectors):
            delta_rows.append(make_delta_row(span, manifest_row, vector))
        print(f"[phase24hr] embedded_delta_spans={min(start + len(span_batch), len(spans))}/{len(spans)}", flush=True)

    for start in range(0, len(delta_rows), args.delta_insert_batch_size):
        batch = delta_rows[start : start + args.delta_insert_batch_size]
        client.insert(collection_name=args.target_collection, data=batch)
        print(f"[phase24hr] inserted_delta_rows={min(start + len(batch), len(delta_rows))}/{len(delta_rows)}", flush=True)

    client.flush(collection_name=args.target_collection)
    if args.defer_index:
        client.create_index(
            collection_name=args.target_collection,
            index_params=make_index_params(client, index_type=args.index_type, mmap_enabled=args.mmap_enabled),
            timeout=args.index_timeout,
        )
    if args.load_after_build:
        client.load_collection(collection_name=args.target_collection)
        time.sleep(2)
    target_stats = client.get_collection_stats(collection_name=args.target_collection)
    target_count = int(target_stats.get("row_count", target_stats.get("num_entities", 0)))

    report = {
        "generated_at_utc": utc_now(),
        "build_status": "PASS" if target_count >= base_count + len(delta_rows) else "FAIL",
        "base_collection": args.base_collection,
        "target_collection": args.target_collection,
        "base_entity_count": base_count,
        "cloned_base_entity_count": cloned_count,
        "target_entity_count": target_count,
        "delta_entity_count": len(delta_rows),
        "vector_dimension": VECTOR_DIMENSION,
        "embedding_model": args.embedding_model,
        "embedding_base_url": args.embedding_base_url,
        "index_type": args.index_type,
        "defer_index": bool(args.defer_index),
        "load_after_build": bool(args.load_after_build),
        "mmap_enabled": bool(args.mmap_enabled),
        "proposed_id_collision_count": len(existing_delta_ids),
        "dry_run_summary_hash": sha256_file(DRY_RUN_SUMMARY),
        "dry_run_manifest_hash": sha256_file(DRY_RUN_MANIFEST_JSONL),
        "source_span_count": summary.get("delta_row_count"),
        "live_8000_cutover": False,
        "candidate_gateway_started": False,
    }
    write_build_reports(report)
    return report


def command_plan(args: argparse.Namespace) -> int:
    write_plan(args)
    return 0


def command_build_shadow(args: argparse.Namespace) -> int:
    report = build_shadow(args)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["build_status"] == "PASS" else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", MILVUS_URI))
    plan.add_argument("--base-collection", default=BASE_COLLECTION)
    plan.add_argument("--target-collection", default=TARGET_COLLECTION)
    plan.add_argument("--embedding-base-url", default=os.getenv("EMBEDDING_BASE_URL", EMBEDDING_BASE_URL))
    plan.add_argument("--embedding-model", default=os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL))
    plan.add_argument("--no-write", action="store_true", help="Print the plan JSON without rewriting the markdown artifact.")
    plan.set_defaults(func=command_plan)

    build = subparsers.add_parser("build-shadow")
    build.add_argument("--execute", action="store_true")
    build.add_argument("--authorization-token", default="")
    build.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", MILVUS_URI))
    build.add_argument("--base-collection", default=BASE_COLLECTION)
    build.add_argument("--target-collection", default=TARGET_COLLECTION)
    build.add_argument("--embedding-base-url", default=os.getenv("EMBEDDING_BASE_URL", EMBEDDING_BASE_URL))
    build.add_argument("--embedding-model", default=os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL))
    build.add_argument("--clone-batch-size", type=int, default=1000)
    build.add_argument("--clone-flush-every", type=int, default=25000)
    build.add_argument("--embedding-batch-size", type=int, default=16)
    build.add_argument("--delta-insert-batch-size", type=int, default=100)
    build.add_argument("--index-type", default="FLAT")
    build.add_argument("--index-timeout", type=int, default=1800)
    build.add_argument("--mmap-enabled", action=argparse.BooleanOptionalAction, default=True)
    build.add_argument("--defer-index", action=argparse.BooleanOptionalAction, default=True)
    build.add_argument("--load-after-build", action=argparse.BooleanOptionalAction, default=False)
    build.add_argument("--force-target-rebuild", action="store_true")
    build.set_defaults(func=command_build_shadow)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return int(args.func(args))
    except RuntimeError as exc:
        print(json.dumps({"status": "REFUSED", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
