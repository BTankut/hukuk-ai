from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
API_GATEWAY_VENV_PYTHON = ROOT / "api-gateway" / ".venv" / "bin" / "python"
ACTIVE_RUNTIME_COLLECTION = "mevzuat_e5_shadow"
FAZ1_CANDIDATE_PREFIX = "mevzuat_faz1_shadow_"


def _run_milvus_json(script: str) -> Any:
    result = subprocess.run(
        [str(API_GATEWAY_VENV_PYTHON), "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "milvus metadata command failed")
    return json.loads(result.stdout)


def list_serving_role_collections() -> list[str]:
    payload = _run_milvus_json(
        """
import json
from pymilvus import MilvusClient
client = MilvusClient(uri="http://127.0.0.1:19530")
names = sorted(
    name
    for name in client.list_collections()
    if name == "mevzuat_e5_shadow" or name.startswith("mevzuat_faz1_shadow_")
)
print(json.dumps(names, ensure_ascii=False))
"""
    )
    return [str(name) for name in payload]


def collection_metadata(collection_name: str) -> dict[str, Any]:
    payload = _run_milvus_json(
        f"""
import json
from pymilvus import MilvusClient
client = MilvusClient(uri="http://127.0.0.1:19530")
desc = client.describe_collection(collection_name={collection_name!r})
stats = client.get_collection_stats(collection_name={collection_name!r})
dim = None
for field in desc.get("fields", []):
    if field.get("name") == "embedding":
        params = field.get("params") or {{}}
        raw_dim = params.get("dim")
        dim = int(raw_dim) if raw_dim is not None else None
payload = {{
    "collection_name": {collection_name!r},
    "vector_dimension": dim,
    "row_count": int(stats.get("row_count", 0)),
    "aliases": desc.get("aliases", []),
}}
print(json.dumps(payload, ensure_ascii=False))
"""
    )
    return {
        "collection_name": str(payload["collection_name"]),
        "vector_dimension": int(payload["vector_dimension"]) if payload.get("vector_dimension") is not None else None,
        "row_count": int(payload["row_count"]),
        "aliases": list(payload.get("aliases") or []),
    }


def _sort_key(entry: dict[str, Any]) -> tuple[int, int, str]:
    return (
        int(entry.get("vector_dimension") or 0),
        int(entry.get("row_count") or 0),
        str(entry.get("collection_name") or ""),
    )


def build_candidate_inventory() -> list[dict[str, Any]]:
    raw_entries = [collection_metadata(name) for name in list_serving_role_collections()]
    faz1_candidates = [entry for entry in raw_entries if str(entry["collection_name"]).startswith(FAZ1_CANDIDATE_PREFIX)]
    eligible = [entry for entry in faz1_candidates if int(entry.get("vector_dimension") or 0) == 1024]
    if not eligible:
        raise RuntimeError("no 1024-dim mevzuat faz1 candidate found")

    authoritative = max(eligible, key=_sort_key)
    stale_candidates = [entry for entry in faz1_candidates if entry["collection_name"] != authoritative["collection_name"]]
    stale = max(stale_candidates, key=_sort_key) if stale_candidates else None

    inventory: list[dict[str, Any]] = []
    for entry in raw_entries:
        item = dict(entry)
        name = str(item["collection_name"])
        if name == ACTIVE_RUNTIME_COLLECTION:
            item["intended_role"] = "active_runtime_baseline"
            item["serving_candidate_eligible"] = False
        elif name == authoritative["collection_name"]:
            item["intended_role"] = "authoritative_serving_candidate"
            item["serving_candidate_eligible"] = True
        elif stale is not None and name == stale["collection_name"]:
            item["intended_role"] = "stale_literal_candidate_serving_disabled"
            item["serving_candidate_eligible"] = False
        else:
            item["intended_role"] = "non_authoritative_candidate_serving_disabled"
            item["serving_candidate_eligible"] = False
        inventory.append(item)

    preferred_order = {
        ACTIVE_RUNTIME_COLLECTION: 0,
        authoritative["collection_name"]: 2,
    }
    if stale is not None:
        preferred_order[stale["collection_name"]] = 1

    inventory.sort(key=lambda item: (preferred_order.get(str(item["collection_name"]), 99), str(item["collection_name"])))
    return inventory


def select_authoritative_candidate(inventory: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    inventory = inventory or build_candidate_inventory()
    for entry in inventory:
        if entry.get("serving_candidate_eligible"):
            return entry
    raise RuntimeError("authoritative serving candidate not found")


def load_authoritative_candidate_collection_name() -> str:
    return str(select_authoritative_candidate()["collection_name"])


def select_stale_candidate(inventory: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    inventory = inventory or build_candidate_inventory()
    for entry in inventory:
        if entry.get("intended_role") == "stale_literal_candidate_serving_disabled":
            return entry
    raise RuntimeError("stale candidate not found")


def load_stale_candidate_collection_name() -> str:
    return str(select_stale_candidate()["collection_name"])
