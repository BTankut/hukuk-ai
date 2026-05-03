#!/usr/bin/env python3
"""Phase 24J-R2 normalized provenance rerun reporting utilities."""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports/benchmark"
RUNS_DIR = REPORTS_DIR / "runs"

BASE_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill"
TARGET_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j"
BASE_API = "http://127.0.0.1:8032/v1"
TARGET_API = "http://127.0.0.1:8033/v1"
BASE_PORT = 8032
TARGET_PORT = 8033
MILVUS_URI = "http://localhost:19530"
DGX_BASE_URL = "http://192.168.12.243:30000/v1"
DGX_MODEL = "/models/merged_model_fabric_stage_20260321"
EMBEDDING_BASE_URL = "http://127.0.0.1:8081/v1"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"
RELEASE_LANE_ID = "phase24j_r2_normalized_pair"
API_VERSION_LABEL = "2026-05-03-phase24j-r2-normalized"
API_KEY = "benchmark"
VECTOR_DIMENSION = 1024

PLAN_MD = REPORTS_DIR / "phase_24J_R2_provenance_normalization_plan.md"
PLAN_JSON = REPORTS_DIR / "phase_24J_R2_provenance_normalization_plan.json"
COLLECTION_VERIFY_MD = REPORTS_DIR / "phase_24J_R2_collection_load_verification.md"
COLLECTION_VERIFY_JSON = REPORTS_DIR / "phase_24J_R2_collection_load_verification.json"
RUNTIME_PAIR_MD = REPORTS_DIR / "phase_24J_R2_runtime_pair_provenance.md"
RUNTIME_PAIR_JSON = REPORTS_DIR / "phase_24J_R2_runtime_pair_provenance.json"
CRITICAL_SMOKE_MD = REPORTS_DIR / "phase_24J_R2_critical_guard_paired_smoke.md"
CRITICAL_SMOKE_CSV = REPORTS_DIR / "phase_24J_R2_critical_guard_paired_smoke.csv"
RESIDUAL_SMOKE_MD = REPORTS_DIR / "phase_24J_R2_residual_targeted_paired_smoke.md"
RESIDUAL_SMOKE_CSV = REPORTS_DIR / "phase_24J_R2_residual_targeted_paired_smoke.csv"
DECISION_MD = REPORTS_DIR / "phase_24J_R2_normalized_provenance_decision.md"
FINAL_REPORT_MD = REPORTS_DIR / "phase_24J_R2_normalized_provenance_rerun_report.md"

CRITICAL_QIDS = ("MULGA-01", "MULGA-05", "TEB-06")
RESIDUAL_QIDS = (
    "KANUN-12",
    "KKY-03",
    "TUZUK-04",
    "YON-04",
    "MULGA-01",
    "MULGA-05",
    "TEB-04",
    "TEB-06",
    "CBG-01",
    "CBKAR-08",
    "UY-01",
    "YON-05",
)

HASH_GLOBS = {
    "source_catalog_hashes": [
        "api-gateway/src/rag/source_catalog.py",
        "api-gateway/src/rag/retriever.py",
        "api-gateway/src/source_family_resolver.py",
        "reports/benchmark/phase_05_canonical_source_catalog.csv",
        "data/primary_sources/full_acquisition/*/source_manifest.json",
        "data/primary_sources/full_acquisition/*/normalized_source.txt",
    ],
    "source_supplement_hashes": [
        "api-gateway/src/rag/source_supplements.py",
        "reports/benchmark/phase_16*_corpus_materialization*.csv",
        "reports/benchmark/phase_16*_source_key_v2_collision_report.csv",
        "reports/benchmark/phase_17*_corpus_materialization*.csv",
        "reports/benchmark/phase_17*_sourcekey_binding_audit.csv",
        "reports/benchmark/phase_18e_side_backlog_source_materialization_report.md",
    ],
    "config_hashes": [
        "api-gateway/src/rag/required_slot_matrix.py",
        "api-gateway/src/rag/required_slot_matrix.json",
        "configs/evaluation/hukuk_ai_100_public_questions.csv",
        "evaluation/hukuk_ai_100_article_alignment.py",
        "evaluation/hukuk_ai_100_source_schema.py",
        "scripts/benchmark/run_hukuk_ai_100.py",
        "scripts/benchmark/score_hukuk_ai_100.py",
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    path = path if path.is_absolute() else REPO_ROOT / path
    return path.relative_to(REPO_ROOT).as_posix()


def run_cmd(args: list[str]) -> str:
    return subprocess.check_output(args, cwd=REPO_ROOT, text=True).strip()


def git_sha() -> str:
    return run_cmd(["git", "rev-parse", "HEAD"])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_globs(patterns: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pattern in patterns:
        matches = sorted(glob.glob(str(REPO_ROOT / pattern)))
        if not matches and not any(ch in pattern for ch in "*?[]"):
            matches = [str(REPO_ROOT / pattern)]
        for raw in matches:
            path = Path(raw)
            rows.append(
                {
                    "path": rel(path) if path.exists() else pattern,
                    "exists": path.exists(),
                    "bytes": path.stat().st_size if path.exists() else None,
                    "sha256": sha256_file(path) if path.exists() else None,
                }
            )
    return rows


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_trace(run_dir: Path) -> dict[str, dict[str, Any]]:
    traces: dict[str, dict[str, Any]] = {}
    trace_path = run_dir / "trace.jsonl"
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            obj = json.loads(line)
            traces[obj["qid"]] = obj
    return traces


def nested_get(obj: dict[str, Any], *path: str, default: Any = "") -> Any:
    current: Any = obj
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def url_json(url: str, *, api_key: str | None = None, timeout: int = 10) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {
                "ok": True,
                "status": response.status,
                "payload": json.loads(response.read().decode("utf-8")),
                "url": url,
            }
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": str(exc), "url": url}
    except Exception as exc:
        return {"ok": False, "error": repr(exc), "url": url}


def api_env(collection: str) -> dict[str, str]:
    return {
        "DGX_BASE_URL": DGX_BASE_URL,
        "DGX_MODEL": DGX_MODEL,
        "MILVUS_ENABLED": "true",
        "MILVUS_URI": MILVUS_URI,
        "MILVUS_COLLECTION": collection,
        "EMBEDDING_BACKEND": "remote",
        "EMBEDDING_BASE_URL": EMBEDDING_BASE_URL,
        "EMBEDDING_MODEL": EMBEDDING_MODEL,
        "RELEASE_LANE_ID": RELEASE_LANE_ID,
        "RELEASE_CONTROLS_STRICT": "true",
        "API_VERSION_LABEL": API_VERSION_LABEL,
        "API_AUTH_ENABLED": "true",
        "API_AUTH_KEYS": API_KEY,
        "AUDIT_LOG_ENABLED": "false",
        "ALLOW_ANONYMOUS_INTERNAL_SMOKE": "false",
        "SESSION_STORE_BACKEND": "memory",
        "SESSION_STORE_REDIS_REQUIRED": "false",
        "SESSION_STORE_REDIS_PING_ON_STARTUP": "false",
        "TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK": "true",
        "PARITY_TRACE_ENABLED": "false",
        "RERANKER_ENABLED": "false",
        "GUARDRAILS_ENABLED": "false",
        "PRESIDIO_ENABLED": "false",
        "USE_VERIFICATION": "false",
    }


def write_plan(_args: argparse.Namespace) -> None:
    data = {
        "generated_at_utc": utc_now(),
        "same_git_sha": git_sha(),
        "same_code_checkout": str(REPO_ROOT),
        "same_env_except": ["MILVUS_COLLECTION", "api_port"],
        "base_api": BASE_API,
        "target_api": TARGET_API,
        "base_port": BASE_PORT,
        "target_port": TARGET_PORT,
        "base_collection": BASE_COLLECTION,
        "target_collection": TARGET_COLLECTION,
        "api_command_template": (
            "env <normalized_env> MILVUS_COLLECTION=<collection> "
            "api-gateway/.venv/bin/python -m uvicorn api-gateway.src.main:app "
            "--host 127.0.0.1 --port <port> --log-level info"
        ),
        "normalized_env": api_env("<collection>"),
        "collection_load_verification_command": (
            "api-gateway/.venv/bin/python scripts/benchmark/phase24j_r2_normalized_provenance.py verify-collections"
        ),
        "health_check_command": "curl -sS http://127.0.0.1:<port>/v1/health",
        "models_check_command": "curl -sS -H 'Authorization: Bearer benchmark' http://127.0.0.1:<port>/v1/models",
        "trace_completeness_check": "trace.jsonl must contain non-empty rerank_list and assembled_evidence for critical guard qids",
        "hashes": {name: hash_globs(patterns) for name, patterns in HASH_GLOBS.items()},
    }
    write_json(PLAN_JSON, data)
    lines = [
        "# Phase 24J-R2 Provenance Normalization Plan",
        "",
        f"- generated_at_utc: `{data['generated_at_utc']}`",
        f"- same_git_sha: `{data['same_git_sha']}`",
        f"- base_api: `{BASE_API}`",
        f"- target_api: `{TARGET_API}`",
        f"- base_collection: `{BASE_COLLECTION}`",
        f"- target_collection: `{TARGET_COLLECTION}`",
        "- status: `PASS`",
        "",
        "## Normalized Runtime Contract",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| DGX_MODEL | `{DGX_MODEL}` |",
        f"| EMBEDDING_MODEL | `{EMBEDDING_MODEL}` |",
        f"| vector_dimension | `{VECTOR_DIMENSION}` |",
        "| guardrails | `false` |",
        "| verification | `false` |",
        "| presidio | `false` |",
        f"| RELEASE_LANE_ID | `{RELEASE_LANE_ID}` |",
        f"| API_VERSION_LABEL | `{API_VERSION_LABEL}` |",
        "",
        "Only `MILVUS_COLLECTION` and API port may differ between BASE and TARGET candidate runtimes.",
        "",
        "## Command Template",
        "",
        "```bash",
        data["api_command_template"],
        "```",
        "",
        "## Verification Commands",
        "",
        "```bash",
        data["collection_load_verification_command"],
        data["health_check_command"],
        data["models_check_command"],
        "```",
    ]
    PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def milvus_client():
    try:
        from pymilvus import MilvusClient
    except Exception as exc:
        raise RuntimeError("pymilvus is required; run with api-gateway/.venv/bin/python") from exc
    return MilvusClient(uri=MILVUS_URI)


def collection_dimension(desc: dict[str, Any]) -> int | None:
    for field in desc.get("fields", []):
        if field.get("name") == "embedding":
            dim = field.get("params", {}).get("dim")
            return int(dim) if dim is not None else None
    return None


def collection_state_value(state: Any) -> str:
    raw = state.get("state") if isinstance(state, dict) else state
    return str(raw).split(".")[-1].replace(">", "").replace("<LoadState: ", "")


def verify_collections(_args: argparse.Namespace) -> None:
    client = milvus_client()
    expected = {BASE_COLLECTION: 349403, TARGET_COLLECTION: 349420}
    rows = []
    for collection, expected_count in expected.items():
        before = collection_state_value(client.get_load_state(collection_name=collection))
        if before != "Loaded":
            client.load_collection(collection_name=collection)
            time.sleep(2)
        after = collection_state_value(client.get_load_state(collection_name=collection))
        stats = client.get_collection_stats(collection_name=collection)
        desc = client.describe_collection(collection_name=collection)
        indexes = client.list_indexes(collection_name=collection)
        row_count = int(stats.get("row_count", -1))
        dim = collection_dimension(desc)
        rows.append(
            {
                "collection": collection,
                "expected_entity_count": expected_count,
                "entity_count": row_count,
                "load_state_before": before,
                "load_state_after": after,
                "vector_dimension": dim,
                "indexes": indexes,
                "index_available": "embedding" in indexes,
                "acceptance": after == "Loaded" and row_count == expected_count and dim == VECTOR_DIMENSION and "embedding" in indexes,
            }
        )
    data = {
        "generated_at_utc": utc_now(),
        "milvus_uri": MILVUS_URI,
        "collections": rows,
        "acceptance": all(row["acceptance"] for row in rows),
    }
    write_json(COLLECTION_VERIFY_JSON, data)
    lines = [
        "# Phase 24J-R2 Collection Load Verification",
        "",
        f"- generated_at_utc: `{data['generated_at_utc']}`",
        f"- milvus_uri: `{MILVUS_URI}`",
        f"- acceptance: `{'PASS' if data['acceptance'] else 'FAIL'}`",
        "",
        "| collection | expected | actual | load_before | load_after | dim | index_available | acceptance |",
        "|---|---:|---:|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['collection']} | {row['expected_entity_count']} | {row['entity_count']} | "
            f"{row['load_state_before']} | {row['load_state_after']} | {row['vector_dimension']} | "
            f"`{row['index_available']}` | `{'PASS' if row['acceptance'] else 'FAIL'}` |"
        )
    COLLECTION_VERIFY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not data["acceptance"]:
        raise SystemExit("Collection load verification failed")


def lsof_pid(port: int) -> str:
    try:
        return run_cmd(["sh", "-lc", f"lsof -ti tcp:{port} | head -1"])
    except subprocess.CalledProcessError:
        return ""


def proc_env(pid: str) -> dict[str, str]:
    if not pid:
        return {}
    try:
        raw = run_cmd(["ps", "eww", "-p", pid])
    except subprocess.CalledProcessError:
        return {}
    env: dict[str, str] = {}
    for token in raw.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        if key in {
            "DGX_BASE_URL",
            "DGX_MODEL",
            "MILVUS_COLLECTION",
            "EMBEDDING_BACKEND",
            "EMBEDDING_BASE_URL",
            "EMBEDDING_MODEL",
            "RELEASE_LANE_ID",
            "API_VERSION_LABEL",
            "GUARDRAILS_ENABLED",
            "PRESIDIO_ENABLED",
            "USE_VERIFICATION",
            "RERANKER_ENABLED",
        }:
            env[key] = value
    return env


def runtime_probe(label: str, api_url: str, port: int) -> dict[str, Any]:
    pid = lsof_pid(port)
    return {
        "label": label,
        "api_url": api_url,
        "port": port,
        "pid": pid,
        "health": url_json(f"{api_url}/health"),
        "models": url_json(f"{api_url}/models", api_key=API_KEY),
        "model_detail": url_json(f"{api_url}/models/hukuk-ai-poc", api_key=API_KEY),
        "process_env": proc_env(pid),
    }


def runtime_pair(args: argparse.Namespace) -> None:
    base = runtime_probe("BASE", args.base_api, args.base_port)
    target = runtime_probe("TARGET", args.target_api, args.target_port)
    allowed_env_diff = {"MILVUS_COLLECTION"}
    env_diffs = {}
    for key in sorted(set(base["process_env"]) | set(target["process_env"])):
        if base["process_env"].get(key) != target["process_env"].get(key):
            env_diffs[key] = {"base": base["process_env"].get(key), "target": target["process_env"].get(key)}
    health_diffs = {}
    for key in ("lane", "api_version", "guardrails", "retriever", "verification"):
        base_value = nested_get(base, "health", "payload", key, default=None)
        target_value = nested_get(target, "health", "payload", key, default=None)
        if base_value != target_value:
            health_diffs[key] = {"base": base_value, "target": target_value}
    acceptance = (
        bool(base["health"]["ok"])
        and bool(target["health"]["ok"])
        and bool(base["models"]["ok"])
        and bool(target["models"]["ok"])
        and bool(base["model_detail"]["ok"])
        and bool(target["model_detail"]["ok"])
        and set(env_diffs).issubset(allowed_env_diff)
        and not health_diffs
    )
    data = {
        "generated_at_utc": utc_now(),
        "git_sha": git_sha(),
        "base": base,
        "target": target,
        "env_diffs": env_diffs,
        "health_diffs": health_diffs,
        "allowed_env_diff": sorted(allowed_env_diff),
        "acceptance": acceptance,
    }
    write_json(RUNTIME_PAIR_JSON, data)
    lines = [
        "# Phase 24J-R2 Runtime Pair Provenance",
        "",
        f"- generated_at_utc: `{data['generated_at_utc']}`",
        f"- git_sha: `{data['git_sha']}`",
        f"- acceptance: `{'PASS' if acceptance else 'FAIL'}`",
        "",
        "| runtime | api_url | pid | health | models | lane | api_version | collection |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for item in (base, target):
        lines.append(
            f"| {item['label']} | `{item['api_url']}` | `{item['pid']}` | `{item['health']['ok']}` | "
            f"`{item['models']['ok']}` | `{nested_get(item, 'health', 'payload', 'lane')}` | "
            f"`{nested_get(item, 'health', 'payload', 'api_version')}` | "
            f"`{item['process_env'].get('MILVUS_COLLECTION', '')}` |"
        )
    lines.extend(["", "## Env Diffs", "", "```json", json.dumps(env_diffs, indent=2, ensure_ascii=False), "```"])
    lines.extend(["", "## Health Diffs", "", "```json", json.dumps(health_diffs, indent=2, ensure_ascii=False), "```"])
    RUNTIME_PAIR_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not acceptance:
        raise SystemExit("Runtime pair provenance acceptance failed")


def trace_summary(trace_obj: dict[str, Any]) -> dict[str, Any]:
    extracted = trace_obj.get("extracted") or {}
    trace = nested_get(trace_obj, "response", "trace", default={}) or {}
    return {
        "selected_source": extracted.get("source_title_claimed", ""),
        "selected_span": extracted.get("selected_main_span_id", ""),
        "selected_source_key": extracted.get("selected_canonical_source_key_v2", ""),
        "rerank_list_present": bool(trace.get("rerank_list")),
        "assembled_evidence_present": bool(trace.get("assembled_evidence")),
        "rerank_list_count": len(trace.get("rerank_list") or []),
        "assembled_evidence_count": len(trace.get("assembled_evidence") or []),
        "contract_valid": extracted.get("contract_valid", ""),
        "unsupported_confident": extracted.get("unsupported_confident_answer", ""),
        "source_key_v2_collision": extracted.get("source_key_v2_collision_detected", ""),
        "binding_collision": extracted.get("binding_source_key_collision_detected", ""),
        "repealed_as_active": extracted.get("repealed_as_active", ""),
    }


def boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def paired_smoke(args: argparse.Namespace) -> dict[str, Any]:
    base_run = Path(args.base_run)
    target_run = Path(args.target_run)
    base_scored = {row["qid"]: row for row in read_csv(base_run / "scored.csv")}
    target_scored = {row["qid"]: row for row in read_csv(target_run / "scored.csv")}
    base_traces = read_trace(base_run)
    target_traces = read_trace(target_run)
    qids = CRITICAL_QIDS if args.scope == "critical" else RESIDUAL_QIDS
    rows = []
    for qid in qids:
        base_score = base_scored[qid]
        target_score = target_scored[qid]
        base_trace = trace_summary(base_traces[qid])
        target_trace = trace_summary(target_traces[qid])
        rows.append(
            {
                "qid": qid,
                "base_score": base_score.get("score_0_10_proxy", ""),
                "target_score": target_score.get("score_0_10_proxy", ""),
                "base_pass": base_score.get("pass_fail_proxy", ""),
                "target_pass": target_score.get("pass_fail_proxy", ""),
                "base_selected_source": base_trace["selected_source"],
                "target_selected_source": target_trace["selected_source"],
                "base_selected_span": base_trace["selected_span"],
                "target_selected_span": target_trace["selected_span"],
                "base_rerank_list_present": base_trace["rerank_list_present"],
                "target_rerank_list_present": target_trace["rerank_list_present"],
                "base_assembled_evidence_present": base_trace["assembled_evidence_present"],
                "target_assembled_evidence_present": target_trace["assembled_evidence_present"],
                "base_contract_valid": base_trace["contract_valid"],
                "target_contract_valid": target_trace["contract_valid"],
                "base_unsupported_confident": base_trace["unsupported_confident"],
                "target_unsupported_confident": target_trace["unsupported_confident"],
                "base_source_key_v2_collision": base_trace["source_key_v2_collision"],
                "target_source_key_v2_collision": target_trace["source_key_v2_collision"],
                "base_binding_collision": base_trace["binding_collision"],
                "target_binding_collision": target_trace["binding_collision"],
                "base_rerank_list_count": base_trace["rerank_list_count"],
                "target_rerank_list_count": target_trace["rerank_list_count"],
                "base_assembled_evidence_count": base_trace["assembled_evidence_count"],
                "target_assembled_evidence_count": target_trace["assembled_evidence_count"],
            }
        )
    target_contract_valid_all = all(str(row["target_contract_valid"]).lower() == "true" for row in rows)
    target_no_unsupported = all(not boolish(row["target_unsupported_confident"]) for row in rows)
    target_no_source_collision = all(not boolish(row["target_source_key_v2_collision"]) for row in rows)
    target_no_binding_collision = all(not boolish(row["target_binding_collision"]) for row in rows)
    target_evidence_non_empty = all(row["target_rerank_list_present"] and row["target_assembled_evidence_present"] for row in rows)
    no_critical_regression = all(
        row["target_pass"] == row["base_pass"] == "PASS" or row["qid"] not in CRITICAL_QIDS for row in rows
    )
    acceptance = (
        target_contract_valid_all
        and target_no_unsupported
        and target_no_source_collision
        and target_no_binding_collision
        and target_evidence_non_empty
        and no_critical_regression
    )
    out_csv = CRITICAL_SMOKE_CSV if args.scope == "critical" else RESIDUAL_SMOKE_CSV
    out_md = CRITICAL_SMOKE_MD if args.scope == "critical" else RESIDUAL_SMOKE_MD
    write_csv(
        out_csv,
        rows,
        [
            "qid",
            "base_score",
            "target_score",
            "base_pass",
            "target_pass",
            "base_selected_source",
            "target_selected_source",
            "base_selected_span",
            "target_selected_span",
            "base_rerank_list_present",
            "target_rerank_list_present",
            "base_assembled_evidence_present",
            "target_assembled_evidence_present",
            "base_contract_valid",
            "target_contract_valid",
            "base_unsupported_confident",
            "target_unsupported_confident",
            "base_source_key_v2_collision",
            "target_source_key_v2_collision",
            "base_binding_collision",
            "target_binding_collision",
            "base_rerank_list_count",
            "target_rerank_list_count",
            "base_assembled_evidence_count",
            "target_assembled_evidence_count",
        ],
    )
    title = "Critical Guard Paired Smoke" if args.scope == "critical" else "Residual Targeted Paired Smoke"
    lines = [
        f"# Phase 24J-R2 {title}",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- base_run: `{rel(base_run)}`",
        f"- target_run: `{rel(target_run)}`",
        f"- qid_count: `{len(rows)}`",
        f"- acceptance: `{'PASS' if acceptance else 'FAIL'}`",
        "",
        "| qid | base | target | base_span | target_span | target_rerank | target_evidence |",
        "|---|---|---|---|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['qid']} | {row['base_pass']} {row['base_score']} | {row['target_pass']} {row['target_score']} | "
            f"`{row['base_selected_span']}` | `{row['target_selected_span']}` | "
            f"{row['target_rerank_list_count']} | {row['target_assembled_evidence_count']} |"
        )
    lines.extend(
        [
            "",
            "## Gate Summary",
            "",
            f"- target_contract_valid_all: `{target_contract_valid_all}`",
            f"- target_unsupported_confident_answer_zero: `{target_no_unsupported}`",
            f"- target_source_key_v2_collision_zero: `{target_no_source_collision}`",
            f"- target_binding_collision_zero: `{target_no_binding_collision}`",
            f"- target_rerank_and_evidence_non_empty: `{target_evidence_non_empty}`",
            f"- no_critical_regression_vs_base: `{no_critical_regression}`",
        ]
    )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "scope": args.scope,
        "acceptance": acceptance,
        "target_evidence_non_empty": target_evidence_non_empty,
        "no_critical_regression": no_critical_regression,
    }


def decision(args: argparse.Namespace) -> None:
    critical_exists = CRITICAL_SMOKE_CSV.exists()
    residual_exists = RESIDUAL_SMOKE_CSV.exists()
    critical_rows = read_csv(CRITICAL_SMOKE_CSV) if critical_exists else []
    target_trace_empty = any(
        row.get("target_rerank_list_present") == "False" or row.get("target_assembled_evidence_present") == "False"
        for row in critical_rows
    )
    target_loses_guards = any(row.get("qid") in CRITICAL_QIDS and row.get("base_pass") == "PASS" and row.get("target_pass") != "PASS" for row in critical_rows)
    if target_trace_empty:
        option = "Option D - TARGET trace still empty"
        next_action = "Open runtime collection binding / load bug investigation"
    elif target_loses_guards:
        option = "Option C - TARGET still loses guards"
        next_action = "Open selector/evidence assembly audit"
    elif residual_exists:
        option = "Option A - TARGET clean and paired residual smoke available"
        next_action = "Open Phase 24K-R2 full shadow benchmark only if residual gate passed"
    else:
        option = "Option B - TARGET clean but residual improvement not evaluated"
        next_action = "Keep Phase24J collection as diagnostic only"
    lines = [
        "# Phase 24J-R2 Normalized Provenance Decision",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- decision: `{option}`",
        f"- full_shadow_authorized: `{'false' if option.startswith(('Option C', 'Option D', 'Option B')) else 'conditional'}`",
        "",
        "## Basis",
        "",
        f"- critical_guard_smoke_exists: `{critical_exists}`",
        f"- residual_targeted_smoke_exists: `{residual_exists}`",
        f"- target_trace_empty: `{target_trace_empty}`",
        f"- target_loses_guards: `{target_loses_guards}`",
        "",
        "## Next Action",
        "",
        next_action,
        "",
        "Productization remains closed. Fine-tuning remains closed. Internal eval remains closed.",
    ]
    DECISION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def final_report(args: argparse.Namespace) -> None:
    decision_text = DECISION_MD.read_text(encoding="utf-8") if DECISION_MD.exists() else ""
    decision_line = next((line for line in decision_text.splitlines() if line.startswith("- decision:")), "- decision: `UNKNOWN`")
    commits = args.commits or []
    lines = [
        "# Phase 24J-R2 Normalized Provenance Rerun Report",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        decision_line,
        "- productization_status: `CLOSED`",
        "- fine_tuning_status: `CLOSED`",
        "",
        "## Commit SHA List",
        "",
        "| Commit | Scope |",
        "|---|---|",
    ]
    for item in commits:
        sha, _, label = item.partition(":")
        lines.append(f"| `{sha}` | {label or 'Phase 24J-R2 artifact'} |")
    lines.extend(
        [
            "| report commit | Report Phase 24J-R2 normalized provenance rerun outcome |",
            "",
            "## Artifacts",
            "",
            f"- provenance normalization plan: `{rel(PLAN_MD)}`",
            f"- collection load verification: `{rel(COLLECTION_VERIFY_MD)}`",
            f"- runtime pair provenance: `{rel(RUNTIME_PAIR_MD)}`",
            f"- critical guard paired smoke: `{rel(CRITICAL_SMOKE_MD)}`",
            f"- residual targeted paired smoke: `{rel(RESIDUAL_SMOKE_MD) if RESIDUAL_SMOKE_MD.exists() else 'not run'}`",
            f"- decision: `{rel(DECISION_MD)}`",
            "",
            "## Final Position",
            "",
            "No productization, fine-tuning, internal eval, or full shadow benchmark is authorized unless the decision artifact explicitly opens that gate.",
            "",
            "Live `8000` was not modified by Phase 24J-R2. Final health must be recorded in the task closeout.",
        ]
    )
    FINAL_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan").set_defaults(func=write_plan)
    sub.add_parser("verify-collections").set_defaults(func=verify_collections)
    runtime_parser = sub.add_parser("runtime-pair")
    runtime_parser.add_argument("--base-api", default=BASE_API)
    runtime_parser.add_argument("--target-api", default=TARGET_API)
    runtime_parser.add_argument("--base-port", type=int, default=BASE_PORT)
    runtime_parser.add_argument("--target-port", type=int, default=TARGET_PORT)
    runtime_parser.set_defaults(func=runtime_pair)
    smoke_parser = sub.add_parser("paired-smoke")
    smoke_parser.add_argument("--scope", choices=["critical", "residual"], required=True)
    smoke_parser.add_argument("--base-run", required=True)
    smoke_parser.add_argument("--target-run", required=True)
    smoke_parser.set_defaults(func=lambda args: paired_smoke(args))
    sub.add_parser("decision").set_defaults(func=decision)
    final_parser = sub.add_parser("final-report")
    final_parser.add_argument("--commits", nargs="*")
    final_parser.set_defaults(func=final_report)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
