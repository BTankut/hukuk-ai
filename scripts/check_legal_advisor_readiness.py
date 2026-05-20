#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _sqlite_has_tables(path: Path, tables: set[str]) -> tuple[bool, str | None]:
    if not path.exists():
        return False, "missing"
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=5.0) as conn:
            conn.execute("PRAGMA query_only=ON")
            found = {
                str(row[0])
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')")
            }
    except sqlite3.DatabaseError as exc:
        return False, f"sqlite_unreadable:{exc.__class__.__name__}"
    missing = sorted(tables - found)
    if missing:
        return False, f"sqlite_missing_tables:{','.join(missing)}"
    return True, None


def main() -> int:
    processed_dir = Path(
        os.getenv("JUDICIAL_PROCESSED_DIR", "/Users/btmacstudio/Projects/yargi/_work/final_package/processed")
    )
    exact_path = Path(os.getenv("JUDICIAL_EXACT_LOOKUP_PATH", str(processed_dir / "judicial_exact_lookup.sqlite")))
    lexical_path = Path(os.getenv("JUDICIAL_LEXICAL_INDEX_PATH", str(processed_dir / "judicial_lexical_index.sqlite")))
    chunk_refs_path = Path(os.getenv("JUDICIAL_CHUNK_REFS_PATH", str(exact_path)))
    judicial_enabled = _bool_env("JUDICIAL_RUNTIME_ENABLED")
    milvus_enabled = _bool_env("MILVUS_ENABLED")

    failures: list[str] = []
    if not os.getenv("DGX_BASE_URL"):
        failures.append("DGX_BASE_URL_missing")
    if not os.getenv("DGX_MODEL"):
        failures.append("DGX_MODEL_missing")
    if _bool_env("LEGAL_ADVISOR_LLM_ENABLED", True) and not os.getenv("DGX_MODEL"):
        failures.append("legal_advisor_llm_model_missing")

    exact_ok = False
    lexical_ok = False
    chunk_refs_ok = False
    if judicial_enabled:
        if not processed_dir.is_dir():
            failures.append("judicial_processed_dir_missing")
        exact_ok, exact_error = _sqlite_has_tables(exact_path, {"decisions", "lookup", "chunk_refs"})
        lexical_ok, lexical_error = _sqlite_has_tables(lexical_path, {"chunks", "chunks_fts"})
        chunk_refs_ok = exact_ok if chunk_refs_path == exact_path else chunk_refs_path.exists()
        if exact_error:
            failures.append(f"judicial_exact_lookup_{exact_error}")
        if lexical_error:
            failures.append(f"judicial_lexical_index_{lexical_error}")
        if not chunk_refs_ok:
            failures.append("judicial_chunk_refs_unavailable")

    if milvus_enabled:
        for name in ("MILVUS_URI", "MILVUS_COLLECTION", "EMBEDDING_BACKEND", "EMBEDDING_MODEL"):
            if not os.getenv(name):
                failures.append(f"{name}_missing")

    payload: dict[str, Any] = {
        "pass": not failures,
        "failures": failures,
        "repo": str(ROOT),
        "llm_configured": bool(os.getenv("DGX_BASE_URL") and os.getenv("DGX_MODEL")),
        "llm_model": os.getenv("DGX_MODEL"),
        "milvus_enabled": milvus_enabled,
        "mevzuat_collection": os.getenv("MILVUS_COLLECTION", "hukuk_chunks"),
        "embedding_backend": os.getenv("EMBEDDING_BACKEND", "hashing"),
        "judicial_runtime_enabled": judicial_enabled,
        "judicial_processed_dir": str(processed_dir),
        "judicial_exact_lookup_available": exact_ok,
        "judicial_lexical_index_available": lexical_ok,
        "judicial_chunk_refs_available": chunk_refs_ok,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
