from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


def _candidate_article_rows_paths() -> list[Path]:
    configured = os.getenv("MEVZUAT_ARTICLE_ROWS_PATH", "").strip()
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured))

    repo_root = Path(__file__).resolve().parents[3]
    candidates.extend(
        [
            Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl"),
            repo_root / "data" / "mevzuat_db" / "article_rows.jsonl",
        ]
    )

    ordered: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        ordered.append(path)
        seen.add(path)
    return ordered


def _resolve_article_rows_path() -> Path | None:
    for path in _candidate_article_rows_paths():
        if path.exists():
            return path
    return None


@lru_cache(maxsize=1)
def load_source_title_catalog() -> dict[str, str]:
    path = _resolve_article_rows_path()
    if path is None:
        return {}

    catalog: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            title = str(
                row.get("belge_adi")
                or row.get("kanun_adi")
                or row.get("law_name")
                or ""
            ).strip()
            if not title:
                continue

            source_id = str(row.get("source_id") or "").strip()
            source_prefix = source_id.split(":", 1)[0] if source_id else ""
            keys = [
                source_prefix,
                str(row.get("belge_no") or "").strip(),
                str(row.get("kanun_no") or "").strip(),
                str(row.get("belge_kisa_adi") or "").strip(),
                str(row.get("kanun_kisa_adi") or "").strip(),
                str(row.get("law_short_name") or "").strip(),
            ]
            for key in keys:
                if key and key not in catalog:
                    catalog[key] = title
    return catalog


def resolve_source_title(metadata: dict[str, Any] | None) -> str | None:
    if not metadata:
        return None

    for field in ("source_title", "belge_adi", "kanun_adi", "law_name"):
        value = metadata.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()

    catalog = load_source_title_catalog()
    if not catalog:
        return None

    source_id = str(metadata.get("source_id") or "").strip()
    source_prefix = source_id.split(":", 1)[0] if source_id else ""
    candidate_keys = [
        source_prefix,
        str(metadata.get("belge_no") or "").strip(),
        str(metadata.get("kanun_no") or "").strip(),
        str(metadata.get("belge_kisa_adi") or "").strip(),
        str(metadata.get("kanun_kisa_adi") or "").strip(),
        str(metadata.get("law_short_name") or "").strip(),
    ]
    for key in candidate_keys:
        if key and key in catalog:
            return catalog[key]
    return None


def enrich_metadata_with_source_title(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}

    title = resolve_source_title(metadata)
    if not title:
        return metadata

    enriched = dict(metadata)
    enriched.setdefault("source_title", title)
    enriched.setdefault("belge_adi", title)
    enriched.setdefault("kanun_adi", title)
    return enriched
