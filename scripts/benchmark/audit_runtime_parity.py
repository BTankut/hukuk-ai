#!/usr/bin/env python3
"""Audit current hukum-ai gateway/model/vector runtime binding."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.benchmark.run_hukuk_ai_100 import (  # noqa: E402
    CONFIG_HASH_GLOBS,
    SOURCE_CATALOG_HASH_GLOBS,
    SOURCE_SUPPLEMENT_HASH_GLOBS,
    api_root_from_api_url,
    default_milvus_uri,
    effective_runtime_env,
    embedding_probe,
    get_json,
    hash_globs,
    milvus_collection_probe,
    run_command,
)


DEFAULT_OUT_JSON = REPO_ROOT / "reports/benchmark/phase_18_recovery_runtime_parity.json"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_18_recovery_runtime_parity.md"
DRIFT_SOURCE_TARGETS = [
    {
        "qid": "MULGA-02",
        "terms": ["güvenlik soruşturması", "1402"],
        "expected_family": "MULGA",
    },
    {
        "qid": "CBKAR-01",
        "terms": ["ithalat rejimi kararına ek karar", "1362"],
        "expected_family": "CB_KARAR",
    },
    {
        "qid": "YON-01",
        "terms": ["işyeri hekimi", "diğer sağlık personeli"],
        "expected_family": "YONETMELIK",
    },
    {
        "qid": "KANUN-01",
        "terms": ["iş kanunu", "4857"],
        "expected_family": "KANUN",
    },
    {
        "qid": "TEB-01",
        "terms": ["kamu ihale genel tebliği"],
        "expected_family": "TEBLIGLER",
    },
    {
        "qid": "CBG-01",
        "terms": ["rehberlik", "teftiş", "denetim"],
        "expected_family": "CB_GENELGE",
    },
    {
        "qid": "CBG-02",
        "terms": ["is yerlerinde psikolojik taciz", "mobbing"],
        "expected_family": "CB_GENELGE",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default=os.getenv("HUKUK_AI_BASE_URL", "http://127.0.0.1:8000/v1"))
    parser.add_argument("--model", default=os.getenv("HUKUK_AI_MODEL", "hukuk-ai-poc"))
    parser.add_argument("--expect-dgx-model", default="/models/merged_model_fabric_stage_20260321")
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def model_ids(models_response: dict[str, Any]) -> list[str]:
    payload = models_response.get("payload")
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return []
    ids: list[str] = []
    for item in data:
        if isinstance(item, dict) and item.get("id"):
            ids.append(str(item["id"]))
    return ids


def normalize_text(value: Any) -> str:
    return str(value or "").casefold()


def row_haystack(row: dict[str, Any]) -> str:
    metadata = row.get("metadata")
    chunks: list[str] = [str(row.get("id", ""))]
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                chunks.append(f"{key}={value}")
    return normalize_text(" ".join(chunks))


def metadata_family(metadata: dict[str, Any]) -> str:
    for key in ("source_family", "family", "doc_family", "mevzuat_family"):
        if metadata.get(key):
            return str(metadata[key])
    short_name = str(metadata.get("law_short_name") or metadata.get("kanun_kisa_adi") or "").upper()
    if short_name:
        return short_name
    return "UNKNOWN"


def deep_milvus_probe(runtime_env: dict[str, str]) -> dict[str, Any]:
    collection = runtime_env.get("MILVUS_COLLECTION", "")
    if not collection:
        return {"ok": False, "error": "MILVUS_COLLECTION not set"}
    try:
        from pymilvus import MilvusClient  # type: ignore
    except Exception as exc:
        return {"ok": False, "error_type": exc.__class__.__name__, "error": str(exc)}
    try:
        client = MilvusClient(uri=default_milvus_uri(runtime_env))
        rows = client.query(
            collection_name=collection,
            filter="",
            output_fields=["id", "text", "metadata"],
            limit=16384,
        )
    except Exception as exc:
        return {"ok": False, "error_type": exc.__class__.__name__, "error": str(exc)}

    metadata_key_presence: Counter[str] = Counter()
    family_counter: Counter[str] = Counter()
    law_short_name_counter: Counter[str] = Counter()
    source_id_counter: Counter[str] = Counter()
    canonical_key_present = 0
    canonical_article_present = 0
    body_text_present = 0
    body_text_lengths: list[int] = []
    prepared_rows: list[dict[str, Any]] = []
    for row in rows:
        metadata = row.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        for key in metadata:
            metadata_key_presence[key] += 1
        family_counter[metadata_family(metadata)] += 1
        short_name = str(metadata.get("law_short_name") or metadata.get("kanun_kisa_adi") or "UNKNOWN")
        law_short_name_counter[short_name] += 1
        source_id = str(metadata.get("source_id") or metadata.get("canonical_source_locator") or "UNKNOWN")
        source_id_counter[source_id] += 1
        if metadata.get("canonical_source_key_v2"):
            canonical_key_present += 1
        if metadata.get("canonical_article_id"):
            canonical_article_present += 1
        text = str(row.get("text") or "")
        if text.strip():
            body_text_present += 1
            body_text_lengths.append(len(text))
        prepared_rows.append({"id": row.get("id"), "metadata": metadata, "text_length": len(text), "haystack": row_haystack(row)})

    drift_targets: list[dict[str, Any]] = []
    for target in DRIFT_SOURCE_TARGETS:
        terms = [normalize_text(term) for term in target["terms"]]
        matches = [
            row
            for row in prepared_rows
            if all(term in row["haystack"] for term in terms)
        ]
        drift_targets.append(
            {
                "qid": target["qid"],
                "expected_family": target["expected_family"],
                "terms": target["terms"],
                "expected_source_visible": bool(matches),
                "match_count": len(matches),
                "sample_matches": [
                    {
                        "id": row["id"],
                        "text_length": row["text_length"],
                        "source_id": row["metadata"].get("source_id"),
                        "law_name": row["metadata"].get("law_name") or row["metadata"].get("kanun_adi"),
                        "law_short_name": row["metadata"].get("law_short_name")
                        or row["metadata"].get("kanun_kisa_adi"),
                        "canonical_source_locator": row["metadata"].get("canonical_source_locator"),
                        "canonical_article_id": row["metadata"].get("canonical_article_id"),
                    }
                    for row in matches[:5]
                ],
            }
        )

    return {
        "ok": True,
        "queried_rows": len(rows),
        "metadata_key_presence_top": dict(metadata_key_presence.most_common(80)),
        "family_distribution_top": dict(family_counter.most_common(80)),
        "law_short_name_distribution_top": dict(law_short_name_counter.most_common(80)),
        "source_id_distribution_top": dict(source_id_counter.most_common(40)),
        "canonical_source_key_v2_present_count": canonical_key_present,
        "canonical_article_id_present_count": canonical_article_present,
        "body_text_present_count": body_text_present,
        "body_text_min_length": min(body_text_lengths) if body_text_lengths else 0,
        "body_text_max_length": max(body_text_lengths) if body_text_lengths else 0,
        "drift_source_targets": drift_targets,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    api_root = api_root_from_api_url(args.api_url)
    runtime_env, process_probe = effective_runtime_env(args.api_url)
    dgx_base_url = runtime_env.get("DGX_BASE_URL", "").rstrip("/")
    gateway_models = get_json(f"{api_root}/models")
    dgx_models = get_json(f"{dgx_base_url}/models") if dgx_base_url else {"ok": False, "error": "DGX_BASE_URL not set"}
    gateway_model_ids = model_ids(gateway_models)
    dgx_model_ids = model_ids(dgx_models)
    milvus_probe = milvus_collection_probe(runtime_env)
    milvus_deep_probe = deep_milvus_probe(runtime_env)
    git_sha = run_command(["git", "rev-parse", "HEAD"])
    branch = run_command(["git", "branch", "--show-current"])
    status = run_command(["git", "status", "--short"])
    checks = {
        "gateway_model_visible": args.model in gateway_model_ids,
        "dgx_base_url_present": bool(dgx_base_url),
        "dgx_expected_model_visible": args.expect_dgx_model in dgx_model_ids,
        "dgx_model_env_matches_expected": runtime_env.get("DGX_MODEL", "") == args.expect_dgx_model,
        "milvus_collection_present": bool(runtime_env.get("MILVUS_COLLECTION", "")),
        "milvus_entity_count_available": bool(milvus_probe.get("entity_count")),
        "milvus_drift_targets_visible": bool(
            milvus_deep_probe.get("ok")
            and all(
                target.get("expected_source_visible")
                for target in milvus_deep_probe.get("drift_source_targets", [])
            )
        ),
        "milvus_canonical_source_key_v2_present": bool(
            milvus_deep_probe.get("ok")
            and int(milvus_deep_probe.get("canonical_source_key_v2_present_count", 0) or 0) > 0
        ),
        "embedding_base_url_present": bool(runtime_env.get("EMBEDDING_BASE_URL", "")),
        "guardrails_disabled": str(runtime_env.get("GUARDRAILS_ENABLED", "")).lower() == "false",
        "presidio_disabled": str(runtime_env.get("PRESIDIO_ENABLED", "")).lower() == "false",
    }
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": git_sha.get("stdout", ""),
        "branch": branch.get("stdout", ""),
        "dirty_worktree": bool(str(status.get("stdout", "")).strip()),
        "dirty_worktree_status": status.get("stdout", ""),
        "api_url": args.api_url,
        "gateway_model_name": args.model,
        "gateway_health_response": get_json(f"{api_root}/health"),
        "gateway_models_response": gateway_models,
        "gateway_model_ids": gateway_model_ids,
        "gateway_process_probe": process_probe,
        "dgx_base_url": dgx_base_url,
        "dgx_model_env": runtime_env.get("DGX_MODEL", ""),
        "dgx_models_response": dgx_models,
        "dgx_model_ids": dgx_model_ids,
        "milvus_enabled": runtime_env.get("MILVUS_ENABLED", ""),
        "milvus_uri": default_milvus_uri(runtime_env),
        "milvus_collection": runtime_env.get("MILVUS_COLLECTION", ""),
        "milvus_collection_probe": milvus_probe,
        "milvus_deep_probe": milvus_deep_probe,
        "milvus_entity_count": milvus_probe.get("entity_count"),
        "embedding_backend": runtime_env.get("EMBEDDING_BACKEND", ""),
        "embedding_base_url": runtime_env.get("EMBEDDING_BASE_URL", ""),
        "embedding_model": runtime_env.get("EMBEDDING_MODEL", ""),
        "embedding_model_or_endpoint_response": embedding_probe(runtime_env),
        "guardrails_enabled": runtime_env.get("GUARDRAILS_ENABLED", ""),
        "presidio_enabled": runtime_env.get("PRESIDIO_ENABLED", ""),
        "runtime_env": runtime_env,
        "source_catalog_hashes": hash_globs(SOURCE_CATALOG_HASH_GLOBS),
        "source_supplement_hashes": hash_globs(SOURCE_SUPPLEMENT_HASH_GLOBS),
        "config_hashes": hash_globs(CONFIG_HASH_GLOBS),
        "checks": checks,
    }


def write_md(path: Path, report: dict[str, Any]) -> None:
    checks = report["checks"]
    failed = [key for key, value in checks.items() if not value]
    lines = [
        "# Phase 18 Recovery Runtime Parity Audit",
        "",
        f"- timestamp_utc: `{report['timestamp_utc']}`",
        f"- api_url: `{report['api_url']}`",
        f"- gateway_model_name: `{report['gateway_model_name']}`",
        f"- gateway_model_ids: `{', '.join(report['gateway_model_ids'])}`",
        f"- dgx_base_url: `{report['dgx_base_url']}`",
        f"- dgx_model_env: `{report['dgx_model_env']}`",
        f"- dgx_model_ids: `{', '.join(report['dgx_model_ids'])}`",
        f"- milvus_collection: `{report['milvus_collection']}`",
        f"- milvus_entity_count: `{report['milvus_entity_count']}`",
        f"- milvus_queried_rows: `{report.get('milvus_deep_probe', {}).get('queried_rows', 'unknown')}`",
        f"- embedding_backend: `{report['embedding_backend']}`",
        f"- embedding_base_url: `{report['embedding_base_url']}`",
        f"- guardrails_enabled: `{report['guardrails_enabled']}`",
        f"- presidio_enabled: `{report['presidio_enabled']}`",
        f"- dirty_worktree: `{report['dirty_worktree']}`",
        "",
        "## Checks",
        "",
    ]
    for key, value in checks.items():
        lines.append(f"- {key}: `{value}`")
    deep_probe = report.get("milvus_deep_probe", {})
    if isinstance(deep_probe, dict) and deep_probe.get("ok"):
        lines.extend(["", "## Milvus Schema And Content", ""])
        description = report.get("milvus_collection_probe", {}).get("description", {})
        fields = description.get("fields", []) if isinstance(description, dict) else []
        for field in fields:
            if isinstance(field, dict):
                lines.append(f"- field `{field.get('name')}` type `{field.get('type')}` params `{field.get('params')}`")
        lines.append(f"- indexes: `{report.get('milvus_collection_probe', {}).get('indexes')}`")
        lines.append(f"- canonical_source_key_v2_present_count: `{deep_probe.get('canonical_source_key_v2_present_count')}`")
        lines.append(f"- canonical_article_id_present_count: `{deep_probe.get('canonical_article_id_present_count')}`")
        lines.append(f"- body_text_present_count: `{deep_probe.get('body_text_present_count')}`")
        lines.extend(["", "## Milvus Family Distribution Top", ""])
        family_distribution = deep_probe.get("family_distribution_top", {})
        if isinstance(family_distribution, dict):
            for family, count in list(family_distribution.items())[:30]:
                lines.append(f"- {family}: {count}")
        lines.extend(["", "## Drift Source Visibility", ""])
        for target in deep_probe.get("drift_source_targets", []):
            lines.append(
                "- "
                f"{target['qid']}: visible `{target['expected_source_visible']}`, "
                f"matches `{target['match_count']}`, expected_family `{target['expected_family']}`"
            )
    lines.extend(["", "## Decision", ""])
    if failed:
        lines.append(f"- runtime_parity_status: `needs_attention`")
        lines.append(f"- failed_checks: `{', '.join(failed)}`")
    else:
        lines.append("- runtime_parity_status: `pass_for_current_merged_runtime`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_md(args.out_md, report)
    print(json.dumps({"out_json": str(args.out_json), "out_md": str(args.out_md), "checks": report["checks"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
