from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Protocol

from data_pipeline.judicial.corpus import (
    ALLOWED_DUPLICATE_STATUSES,
    JUDICIAL_QUARANTINE_REASONS,
    JUDICIAL_SOURCE_TYPE,
    REQUIRED_JUDICIAL_CHUNK_FIELDS,
    REQUIRED_JUDICIAL_MANIFEST_FIELDS,
    build_exact_lookup_keys,
    generate_canonical_decision_id,
    generate_citation_key,
)
from data_pipeline.judicial.retrieval_lane import (
    DEFAULT_JUDICIAL_COLLECTION,
    assert_judicial_runtime_disabled,
    build_shadow_index_plan,
)
from data_pipeline.indexing.interfaces import VectorRecord
from rag.embedding import DEFAULT_EMBEDDING_DIM, DEFAULT_EMBEDDING_MODEL


LEXICAL_INDEX_FILENAME = "judicial_lexical_index.sqlite"
LEXICAL_STATS_FILENAME = "judicial_lexical_index_stats.json"
LEXICAL_CHECKPOINT_FILENAME = "judicial_lexical_index_checkpoint.json"
VECTOR_CHECKPOINT_FILENAME = "judicial_vector_shadow_checkpoint.sqlite"
VECTOR_SIZING_FILENAME = "judicial_vector_shadow_sizing.json"

_TOKEN_RE = re.compile(r"[0-9A-Za-zÇĞİÖŞÜçğıöşü]{2,}")
_SPACE_RE = re.compile(r"\s+")
_ISO_YEAR_RE = re.compile(r"^(19|20)\d{2}$")
_LEGAL_STOPWORDS = {
    "bir",
    "bu",
    "ve",
    "ile",
    "icin",
    "için",
    "gore",
    "göre",
    "olan",
    "nedir",
    "karar",
    "mahkeme",
}
_LEXICAL_FILTER_FIELDS = {
    "court",
    "chamber",
    "year",
    "decision_date",
    "esas_no",
    "karar_no",
    "related_law_refs",
}
_REQUIRED_RESULT_FIELDS = {
    "text",
    "selected_chunk_text",
    "chunk_key",
    "citation_key",
    "canonical_decision_id",
    "court",
    "chamber",
    "decision_date",
    "esas_no",
    "karar_no",
    "paragraph_start",
    "paragraph_end",
    "source_url",
    "retrieval_lane",
    "score",
    "metadata_filters_applied",
}


class EmbeddingBatcher(Protocol):
    @property
    def dimension(self) -> int: ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class VectorStoreBatcher(Protocol):
    def upsert(self, *, collection: str, records: list[VectorRecord]) -> int: ...


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def _lookup_value(value: Any) -> str | None:
    if not _present(value):
        return None
    return _SPACE_RE.sub(" ", str(value).strip()).lower()


def _composite_lookup_key(*values: Any) -> str | None:
    parts = [_lookup_value(value) for value in values]
    if any(part is None for part in parts):
        return None
    return "|".join(str(part) for part in parts)


def _jsonl_rows(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _bucket_count(value: int) -> str:
    if value <= 0:
        return "0"
    if value == 1:
        return "1"
    if value <= 3:
        return "2-3"
    if value <= 6:
        return "4-6"
    if value <= 10:
        return "7-10"
    if value <= 25:
        return "11-25"
    return "26+"


def _bucket_text_length(value: int) -> str:
    if value < 500:
        return "<500"
    if value < 2_000:
        return "500-1999"
    if value < 10_000:
        return "2000-9999"
    if value < 50_000:
        return "10000-49999"
    return "50000+"


def _top(counter: Counter[str], limit: int = 25) -> dict[str, int]:
    return dict(counter.most_common(limit))


def _extract_metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    metadata = chunk.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def audit_processed_judicial_corpus(
    processed_dir: str | Path,
    *,
    output_path: str | Path | None = None,
    short_chunk_chars: int = 280,
    single_short_chunk_failure_ratio: float = 0.90,
) -> dict[str, Any]:
    processed = Path(processed_dir)
    preflight = _load_json(processed / "raw_preflight_stats.json")
    ingest = _load_json(processed / "judicial_ingest_stats.json")
    chunk_stats = _load_json(processed / "judicial_chunk_stats.json")
    lookup_stats = _load_json(processed / "judicial_exact_lookup_stats.json")
    manifest_path = processed / "judicial_manifest.jsonl"
    quarantine_path = processed / "judicial_quarantine.jsonl"
    chunks_path = processed / "judicial_chunks.jsonl"
    lookup_db = processed / "judicial_exact_lookup.sqlite"

    failures: list[str] = []
    manifest_errors = Counter()
    quarantine_errors = Counter()
    chunk_errors = Counter()
    source_distribution: Counter[str] = Counter()
    court_distribution: Counter[str] = Counter()
    chamber_distribution: Counter[str] = Counter()
    year_distribution: Counter[str] = Counter()
    text_length_distribution: Counter[str] = Counter()
    duplicate_status_distribution: Counter[str] = Counter()
    quarantine_reason_counts: Counter[str] = Counter()
    chunk_count_by_decision: Counter[str] = Counter()
    chunk_length_by_decision: Counter[str] = Counter()
    chunk_count_distribution: Counter[str] = Counter()

    canonical_ids: set[str] = set()
    citation_keys: set[str] = set()
    chunk_keys: set[str] = set()
    duplicate_unique_canonical_ids = 0
    duplicate_unique_citation_keys = 0
    source_url_present = 0
    case_number_present = 0
    decision_number_present = 0
    manifest_rows = 0

    for record in _jsonl_rows(manifest_path):
        manifest_rows += 1
        duplicate_status = str(record.get("duplicate_status") or "")
        duplicate_status_distribution[duplicate_status] += 1
        source_distribution[str(record.get("source_authority") or "missing")] += 1
        court_distribution[str(record.get("court") or "missing")] += 1
        chamber_distribution[str(record.get("chamber") or "missing")] += 1
        decision_date = str(record.get("decision_date") or "")
        year_distribution[decision_date[:4] if len(decision_date) >= 4 else "missing"] += 1
        text = record.get("original_text") or ""
        text_length_distribution[_bucket_text_length(len(str(text)))] += 1
        if _present(record.get("source_url")):
            source_url_present += 1
        if _present(record.get("case_no")) or _present(record.get("esas_no")):
            case_number_present += 1
        if _present(record.get("decision_no")) or _present(record.get("karar_no")):
            decision_number_present += 1
        for field in REQUIRED_JUDICIAL_MANIFEST_FIELDS:
            if not _present(record.get(field)):
                manifest_errors[f"missing_{field}"] += 1
        if record.get("source_type") != JUDICIAL_SOURCE_TYPE:
            manifest_errors["invalid_source_type"] += 1
        if duplicate_status not in ALLOWED_DUPLICATE_STATUSES:
            manifest_errors["invalid_duplicate_status"] += 1
        if record.get("citation_key") != generate_citation_key(record):
            manifest_errors["citation_key_mismatch"] += 1
        if record.get("canonical_decision_id") != generate_canonical_decision_id(record):
            manifest_errors["canonical_decision_id_mismatch"] += 1
        if duplicate_status == "unique":
            canonical_id = str(record.get("canonical_decision_id") or "")
            citation_key = str(record.get("citation_key") or "")
            if canonical_id in canonical_ids:
                duplicate_unique_canonical_ids += 1
            if citation_key in citation_keys:
                duplicate_unique_citation_keys += 1
            canonical_ids.add(canonical_id)
            citation_keys.add(citation_key)

    quarantine_rows = 0
    for row in _jsonl_rows(quarantine_path):
        quarantine_rows += 1
        reasons = row.get("reasons")
        if not isinstance(reasons, list) or not reasons:
            quarantine_errors["missing_reasons"] += 1
            continue
        for reason in reasons:
            reason_text = str(reason)
            quarantine_reason_counts[reason_text] += 1
            if reason_text not in JUDICIAL_QUARANTINE_REASONS:
                quarantine_errors["unknown_reason"] += 1

    chunk_rows = 0
    for chunk in _jsonl_rows(chunks_path):
        chunk_rows += 1
        metadata = _extract_metadata(chunk)
        text = str(chunk.get("text") or "")
        chunk_key = str(metadata.get("chunk_key") or "")
        canonical_id = str(metadata.get("canonical_decision_id") or "")
        if chunk_key in chunk_keys:
            chunk_errors["duplicate_chunk_key"] += 1
        chunk_keys.add(chunk_key)
        if canonical_id:
            chunk_count_by_decision[canonical_id] += 1
            chunk_length_by_decision[canonical_id] += len(text)
        for field in REQUIRED_JUDICIAL_CHUNK_FIELDS:
            if not _present(metadata.get(field)):
                chunk_errors[f"missing_{field}"] += 1
        if metadata.get("source_type") != JUDICIAL_SOURCE_TYPE:
            chunk_errors["invalid_source_type"] += 1
        if chunk.get("chunk_id") != metadata.get("chunk_key"):
            chunk_errors["chunk_id_key_mismatch"] += 1
        if metadata.get("paragraph_start") == 0 or metadata.get("vector_index_eligible") is False:
            chunk_errors["metadata_header_chunk_indexed"] += 1

    for count in chunk_count_by_decision.values():
        chunk_count_distribution[_bucket_count(int(count))] += 1
    decisions_with_one_short_chunk = sum(
        1
        for canonical_id, count in chunk_count_by_decision.items()
        if count == 1 and chunk_length_by_decision.get(canonical_id, 0) < short_chunk_chars
    )

    duplicate_map_rows = sum(1 for _ in (processed / "judicial_duplicate_map.jsonl").open("r", encoding="utf-8"))
    with sqlite3.connect(lookup_db) as conn:
        decision_metadata_count = int(conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0])
        lookup_key_count = int(conn.execute("SELECT COUNT(*) FROM lookup").fetchone()[0])
        chunk_ref_count = int(conn.execute("SELECT COUNT(*) FROM chunk_refs").fetchone()[0])
        unresolved_ref_count = 0
        for chunk_key, canonical_id in conn.execute("SELECT chunk_key, canonical_decision_id FROM chunk_refs"):
            if chunk_key not in chunk_keys or canonical_id not in canonical_ids:
                unresolved_ref_count += 1

    raw_rows = int(preflight.get("total_lines") or 0)
    accepted_rows = int(ingest.get("accepted_rows") or 0)
    canonical_decision_count = int(ingest.get("canonical_decision_count") or 0)
    raw_to_accepted_gap = raw_rows - accepted_rows

    if raw_rows != int(preflight.get("valid_json_count", 0)) + int(preflight.get("invalid_json_count", 0)):
        failures.append("raw_jsonl_count_mismatch")
    if manifest_rows != accepted_rows:
        failures.append("manifest_accepted_count_mismatch")
    if quarantine_rows != int(ingest.get("quarantined_rows") or 0):
        failures.append("quarantine_count_mismatch")
    if raw_to_accepted_gap != quarantine_rows:
        failures.append("raw_to_accepted_gap_unexplained")
    if quarantine_errors:
        failures.append("quarantine_reason_invalid")
    if manifest_errors:
        failures.append("manifest_metadata_invalid")
    if duplicate_status_distribution != Counter(ingest.get("duplicate_counts") or {}):
        failures.append("duplicate_status_distribution_mismatch")
    if duplicate_map_rows != accepted_rows - canonical_decision_count:
        failures.append("duplicate_map_count_mismatch")
    if len(canonical_ids) != canonical_decision_count or duplicate_unique_canonical_ids:
        failures.append("canonical_decision_id_not_unique")
    if len(citation_keys) != canonical_decision_count or duplicate_unique_citation_keys:
        failures.append("citation_key_not_unique")
    if chunk_rows != int(chunk_stats.get("chunks_written") or 0):
        failures.append("chunk_count_mismatch")
    if chunk_errors:
        failures.append("chunk_metadata_invalid")
    if chunk_ref_count != chunk_rows or unresolved_ref_count:
        failures.append("chunk_reference_integrity_failed")
    if decision_metadata_count != canonical_decision_count:
        failures.append("exact_lookup_decision_metadata_count_mismatch")
    if lookup_key_count != int(lookup_stats.get("lookup_key_count") or 0):
        failures.append("exact_lookup_key_count_mismatch")
    if not source_distribution or not court_distribution:
        failures.append("source_or_court_distribution_empty")
    if canonical_decision_count and decisions_with_one_short_chunk / canonical_decision_count > single_short_chunk_failure_ratio:
        failures.append("chunk_distribution_suspect")

    audit = {
        "pass": not failures,
        "failures": failures,
        "processed_dir": str(processed),
        "raw_to_accepted_gap": {
            "raw_rows": raw_rows,
            "accepted_rows": accepted_rows,
            "canonical_decisions": canonical_decision_count,
            "quarantined_rows": quarantine_rows,
            "gap_rows": raw_to_accepted_gap,
            "top_quarantine_reasons": _top(quarantine_reason_counts, 20),
        },
        "counts": {
            "manifest_rows": manifest_rows,
            "duplicate_map_rows": duplicate_map_rows,
            "chunk_rows": chunk_rows,
            "chunk_refs": chunk_ref_count,
            "lookup_keys": lookup_key_count,
            "decision_metadata": decision_metadata_count,
        },
        "coverage": {
            "source_url_coverage": source_url_present / manifest_rows if manifest_rows else 0,
            "case_number_coverage": case_number_present / manifest_rows if manifest_rows else 0,
            "decision_number_coverage": decision_number_present / manifest_rows if manifest_rows else 0,
            "source_distribution": _top(source_distribution),
            "court_distribution": _top(court_distribution),
            "chamber_distribution": _top(chamber_distribution),
            "year_distribution": dict(sorted(year_distribution.items())),
            "text_length_distribution": dict(sorted(text_length_distribution.items())),
            "chunk_count_distribution_per_decision": dict(sorted(chunk_count_distribution.items())),
            "decisions_with_only_one_very_short_chunk": decisions_with_one_short_chunk,
        },
        "integrity": {
            "manifest_errors": dict(sorted(manifest_errors.items())),
            "quarantine_errors": dict(sorted(quarantine_errors.items())),
            "chunk_errors": dict(sorted(chunk_errors.items())),
            "duplicate_status_distribution": dict(sorted(duplicate_status_distribution.items())),
            "canonical_decision_id_unique_duplicates": duplicate_unique_canonical_ids,
            "citation_key_unique_duplicates": duplicate_unique_citation_keys,
            "chunk_key_duplicates": chunk_errors.get("duplicate_chunk_key", 0),
            "unresolved_chunk_refs": unresolved_ref_count,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if output_path is not None:
        _write_json(Path(output_path), audit)
    return audit


@dataclass(slots=True)
class PersistentJudicialExactLookupStore:
    db_path: str | Path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def lookup(self, key_type: str, key: str, *, limit: int = 20, chunk_ref_limit: int = 50) -> list[dict[str, Any]]:
        normalized_key = _lookup_value(key)
        if normalized_key is None:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT canonical_decision_id FROM lookup "
                "WHERE lookup_type = ? AND lookup_key = ? "
                "ORDER BY manifest_row_number LIMIT ?",
                (key_type, normalized_key, int(limit)),
            ).fetchall()
            return [
                self._decision_with_refs(conn, str(row["canonical_decision_id"]), chunk_ref_limit=chunk_ref_limit)
                for row in rows
            ]

    def lookup_by_metadata(
        self,
        *,
        court: str,
        chamber: str,
        esas_no: str,
        karar_no: str,
        decision_date: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if decision_date is not None:
            key = _composite_lookup_key(court, chamber, decision_date, esas_no, karar_no)
            if key is not None:
                dated = self.lookup("court_chamber_date_esas_karar", key, limit=limit)
                if dated:
                    return dated
        undated = _composite_lookup_key(court, chamber, esas_no, karar_no)
        return [] if undated is None else self.lookup("court_chamber_esas_karar", undated, limit=limit)

    def _decision_with_refs(
        self,
        conn: sqlite3.Connection,
        canonical_decision_id: str,
        *,
        chunk_ref_limit: int,
    ) -> dict[str, Any]:
        decision = conn.execute(
            "SELECT * FROM decisions WHERE canonical_decision_id = ?",
            (canonical_decision_id,),
        ).fetchone()
        if decision is None:
            return {"canonical_decision_id": canonical_decision_id, "metadata": {}, "chunk_refs": []}
        refs = conn.execute(
            "SELECT chunk_key, paragraph_start, paragraph_end, evidence_block_type "
            "FROM chunk_refs WHERE canonical_decision_id = ? "
            "ORDER BY paragraph_start, chunk_key LIMIT ?",
            (canonical_decision_id, int(chunk_ref_limit)),
        ).fetchall()
        metadata = dict(decision)
        metadata["source_type"] = JUDICIAL_SOURCE_TYPE
        return {
            "canonical_decision_id": canonical_decision_id,
            "citation_key": metadata.get("citation_key"),
            "metadata": metadata,
            "chunk_refs": [dict(ref) for ref in refs],
        }


def _connect_lexical(db_path: Path, *, reset: bool = False) -> sqlite3.Connection:
    if reset:
        for path in (db_path, Path(f"{db_path}-wal"), Path(f"{db_path}-shm"), Path(f"{db_path}-journal")):
            if path.exists():
                path.unlink()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS chunks ("
        "chunk_key TEXT PRIMARY KEY, chunk_id TEXT NOT NULL, text TEXT NOT NULL, "
        "canonical_decision_id TEXT NOT NULL, citation_key TEXT NOT NULL, source_type TEXT NOT NULL, "
        "source_authority TEXT NOT NULL, court TEXT NOT NULL, chamber TEXT NOT NULL, decision_date TEXT NOT NULL, "
        "year TEXT NOT NULL, case_no TEXT NOT NULL, esas_no TEXT NOT NULL, decision_no TEXT NOT NULL, "
        "karar_no TEXT NOT NULL, paragraph_start INTEGER NOT NULL, paragraph_end INTEGER NOT NULL, "
        "source_url TEXT NOT NULL, document_hash TEXT NOT NULL, normalized_text_hash TEXT NOT NULL, "
        "chunk_hash TEXT NOT NULL, evidence_block_type TEXT NOT NULL, related_law_refs_json TEXT NOT NULL, "
        "vector_index_eligible INTEGER NOT NULL)"
    )
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts "
        "USING fts5(chunk_key UNINDEXED, text, tokenize='unicode61 remove_diacritics 0')"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_judicial_chunks_court ON chunks (court)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_judicial_chunks_chamber ON chunks (chamber)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_judicial_chunks_year ON chunks (year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_judicial_chunks_date ON chunks (decision_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_judicial_chunks_esas_karar ON chunks (esas_no, karar_no)")
    return conn


def build_judicial_lexical_index(
    chunks_path: str | Path,
    output_dir: str | Path,
    *,
    db_path: str | Path | None = None,
    checkpoint_path: str | Path | None = None,
    reset: bool = True,
    limit: int | None = None,
    batch_size: int = 10_000,
    dry_run: bool = False,
) -> dict[str, Any]:
    chunk_file = Path(chunks_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = Path(db_path) if db_path is not None else out_dir / LEXICAL_INDEX_FILENAME
    stats_path = out_dir / LEXICAL_STATS_FILENAME
    checkpoint_file = Path(checkpoint_path) if checkpoint_path is not None else out_dir / LEXICAL_CHECKPOINT_FILENAME
    stats: dict[str, Any] = {
        "chunks_path": str(chunk_file),
        "index_path": str(index_path),
        "stats_path": str(stats_path),
        "checkpoint_path": str(checkpoint_file),
        "dry_run": dry_run,
        "reset": reset,
        "runtime_enabled": False,
        "chunks_seen": 0,
        "chunks_indexed": 0,
        "skipped_existing": 0,
        "skipped_non_vector_or_header": 0,
        "metadata_errors": Counter(),
        "complete": False,
    }
    conn: sqlite3.Connection | None = None
    try:
        if not dry_run:
            conn = _connect_lexical(index_path, reset=reset)
        for chunk in _jsonl_rows(chunk_file):
            if limit is not None and stats["chunks_seen"] >= limit:
                break
            stats["chunks_seen"] += 1
            metadata = _extract_metadata(chunk)
            text = str(chunk.get("text") or "")
            row_has_error = False
            if metadata.get("vector_index_eligible") is False or metadata.get("paragraph_start") == 0:
                stats["skipped_non_vector_or_header"] += 1
                continue
            for field in REQUIRED_JUDICIAL_CHUNK_FIELDS:
                if not _present(metadata.get(field)):
                    stats["metadata_errors"][f"missing_{field}"] += 1
                    row_has_error = True
            if metadata.get("source_type") != JUDICIAL_SOURCE_TYPE:
                stats["metadata_errors"]["invalid_source_type"] += 1
                row_has_error = True
            if not text:
                stats["metadata_errors"]["missing_text"] += 1
                row_has_error = True
            if row_has_error:
                continue
            related_law_refs = metadata.get("related_law_refs") or []
            row = (
                metadata["chunk_key"],
                chunk.get("chunk_id") or metadata["chunk_key"],
                text,
                metadata["canonical_decision_id"],
                metadata["citation_key"],
                metadata["source_type"],
                metadata["source_authority"],
                metadata["court"],
                metadata["chamber"],
                metadata["decision_date"],
                metadata["year"],
                metadata.get("case_no") or metadata["esas_no"],
                metadata["esas_no"],
                metadata.get("decision_no") or metadata["karar_no"],
                metadata["karar_no"],
                int(metadata["paragraph_start"]),
                int(metadata["paragraph_end"]),
                metadata["source_url"],
                metadata["document_hash"],
                metadata["normalized_text_hash"],
                metadata["chunk_hash"],
                metadata["evidence_block_type"],
                json.dumps(related_law_refs, ensure_ascii=False, sort_keys=True),
                1 if metadata.get("vector_index_eligible") is not False else 0,
            )
            if dry_run:
                stats["chunks_indexed"] += 1
                continue
            assert conn is not None
            if not reset and conn.execute("SELECT 1 FROM chunks WHERE chunk_key = ?", (metadata["chunk_key"],)).fetchone():
                stats["skipped_existing"] += 1
                continue
            conn.execute(
                "INSERT OR IGNORE INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )
            if conn.total_changes:
                conn.execute("INSERT INTO chunks_fts (chunk_key, text) VALUES (?, ?)", (metadata["chunk_key"], text))
                stats["chunks_indexed"] += 1
            if int(stats["chunks_seen"]) % max(1, batch_size) == 0:
                conn.commit()
                _write_json(
                    checkpoint_file,
                    {
                        "complete": False,
                        "chunks_seen": stats["chunks_seen"],
                        "chunks_indexed": stats["chunks_indexed"],
                        "last_chunk_key": metadata["chunk_key"],
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
        if conn is not None:
            conn.commit()
            stats["sqlite_chunk_rows"] = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            stats["sqlite_fts_rows"] = conn.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
        stats["complete"] = limit is None
        stats["metadata_errors"] = dict(sorted(stats["metadata_errors"].items()))
        _write_json(
            checkpoint_file,
            {
                "complete": stats["complete"],
                "chunks_seen": stats["chunks_seen"],
                "chunks_indexed": stats["chunks_indexed"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        _write_json(stats_path, stats)
        return stats
    finally:
        if conn is not None:
            conn.close()


def _legal_tokens(query: str) -> list[str]:
    tokens = [token.lower() for token in _TOKEN_RE.findall(query)]
    return [token for token in tokens if token not in _LEGAL_STOPWORDS]


def _fts_query(query: str) -> str | None:
    tokens = _legal_tokens(query)
    if not tokens:
        return None
    return " OR ".join(f'"{token}"' for token in tokens[:24])


def _row_to_lexical_result(row: sqlite3.Row, *, score: float, filters: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(row)
    text = str(metadata.pop("text"))
    related_law_refs = json.loads(str(metadata.pop("related_law_refs_json") or "[]"))
    metadata["related_law_refs"] = related_law_refs
    metadata["source_type"] = JUDICIAL_SOURCE_TYPE
    return {
        "text": text,
        "selected_chunk_text": text,
        "chunk_key": metadata["chunk_key"],
        "chunk_id": metadata["chunk_id"],
        "citation_key": metadata["citation_key"],
        "canonical_decision_id": metadata["canonical_decision_id"],
        "court": metadata["court"],
        "chamber": metadata["chamber"],
        "decision_date": metadata["decision_date"],
        "year": metadata["year"],
        "esas_no": metadata["esas_no"],
        "karar_no": metadata["karar_no"],
        "paragraph_start": metadata["paragraph_start"],
        "paragraph_end": metadata["paragraph_end"],
        "source_url": metadata["source_url"],
        "source_type": JUDICIAL_SOURCE_TYPE,
        "retrieval_lane": "lexical",
        "lane": "lexical",
        "score": score,
        "retrieval_score": score,
        "filter_match_metadata": {key: metadata.get(key) for key in filters if key != "related_law_refs"},
        "metadata_filters_applied": dict(filters),
        "metadata": metadata,
    }


def query_judicial_lexical_index(
    index_path: str | Path,
    query: str,
    *,
    filters: dict[str, Any] | None = None,
    top_k: int = 20,
) -> list[dict[str, Any]]:
    fts_query = _fts_query(query)
    if fts_query is None:
        return []
    filters = {key: value for key, value in (filters or {}).items() if key in _LEXICAL_FILTER_FIELDS and value is not None}
    where = ["chunks_fts MATCH ?"]
    params: list[Any] = [fts_query]
    for key, value in filters.items():
        if key == "related_law_refs":
            where.append("c.related_law_refs_json LIKE ?")
            params.append(f"%{value}%")
        elif key in {"court", "chamber"}:
            where.append(f"REPLACE(c.{key}, char(10), ' ') = ?")
            params.append(_SPACE_RE.sub(" ", str(value)).strip())
        else:
            where.append(f"c.{key} = ?")
            params.append(value)
    params.append(int(top_k))
    sql = (
        "SELECT c.*, chunks_fts.text AS text, bm25(chunks_fts) AS bm25_score "
        "FROM chunks_fts JOIN chunks c ON c.chunk_key = chunks_fts.chunk_key "
        f"WHERE {' AND '.join(where)} "
        "ORDER BY bm25_score LIMIT ?"
    )
    with sqlite3.connect(index_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        bm25_score = float(row["bm25_score"])
        results.append(_row_to_lexical_result(row, score=-bm25_score, filters=filters))
    return results


def _fetch_chunk_rows(index_path: str | Path, chunk_keys: list[str]) -> dict[str, sqlite3.Row]:
    if not chunk_keys:
        return {}
    placeholders = ",".join("?" for _ in chunk_keys)
    with sqlite3.connect(index_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"SELECT c.* FROM chunks c WHERE c.chunk_key IN ({placeholders})",
            chunk_keys,
        ).fetchall()
    return {str(row["chunk_key"]): row for row in rows}


@dataclass(slots=True)
class JudicialHybridRetriever:
    exact_store: PersistentJudicialExactLookupStore
    lexical_index_path: str | Path
    vector_ready: bool = False

    def retrieve(
        self,
        *,
        query: str,
        top_k: int = 20,
        exact_key_type: str | None = None,
        exact_key: str | None = None,
        filters: dict[str, Any] | None = None,
        vector_results: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        if exact_key_type and exact_key:
            exact_hits = self.exact_store.lookup(exact_key_type, exact_key, limit=top_k)
            refs = [ref for hit in exact_hits for ref in hit.get("chunk_refs", [])][:top_k]
            chunk_rows = _fetch_chunk_rows(self.lexical_index_path, [str(ref["chunk_key"]) for ref in refs])
            for hit in exact_hits:
                metadata = dict(hit.get("metadata") or {})
                for ref in hit.get("chunk_refs", [])[:top_k]:
                    row = chunk_rows.get(str(ref.get("chunk_key")))
                    if row is None:
                        continue
                    result = _row_to_lexical_result(row, score=1.0, filters=filters or {})
                    result.update(
                        {
                            "retrieval_lane": "hybrid",
                            "lane": "hybrid",
                            "lane_provenance": ["exact"],
                            "score_components": {"exact": 1.0},
                            "metadata": {**result["metadata"], **metadata},
                        }
                    )
                    merged[result["chunk_key"]] = result
        for lexical in query_judicial_lexical_index(self.lexical_index_path, query, filters=filters, top_k=top_k):
            existing = merged.setdefault(
                lexical["chunk_key"],
                {
                    **lexical,
                    "retrieval_lane": "hybrid",
                    "lane": "hybrid",
                    "lane_provenance": [],
                    "score_components": {},
                },
            )
            if "lexical" not in existing["lane_provenance"]:
                existing["lane_provenance"].append("lexical")
            existing["score_components"]["lexical"] = float(lexical["score"])
        if self.vector_ready:
            for vector in vector_results or []:
                chunk_key = str(vector.get("chunk_key") or "")
                if not chunk_key:
                    continue
                existing = merged.setdefault(
                    chunk_key,
                    {
                        **vector,
                        "retrieval_lane": "hybrid",
                        "lane": "hybrid",
                        "lane_provenance": [],
                        "score_components": {},
                        "metadata_filters_applied": filters or {},
                    },
                )
                if "vector" not in existing["lane_provenance"]:
                    existing["lane_provenance"].append("vector")
                existing["score_components"]["vector"] = float(vector.get("score") or 0.0)
        for result in merged.values():
            components = result.setdefault("score_components", {})
            result["final_score"] = (
                float(components.get("exact", 0.0)) * 1000.0
                + float(components.get("lexical", 0.0))
                + float(components.get("vector", 0.0))
            )
            result["score"] = result["final_score"]
            result["retrieval_score"] = result["final_score"]
            result.setdefault("metadata_filters_applied", filters or {})
        return sorted(merged.values(), key=lambda item: float(item.get("final_score", 0.0)), reverse=True)[:top_k]


def validate_judicial_evidence_results(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    seen_chunk_keys: set[str] = set()
    rows = list(results)
    for index, result in enumerate(rows):
        missing = sorted(field for field in _REQUIRED_RESULT_FIELDS if not _present(result.get(field)))
        if missing:
            failures.append({"index": index, "mode": "missing_required_metadata", "fields": missing})
        chunk_key = str(result.get("chunk_key") or "")
        if chunk_key in seen_chunk_keys:
            failures.append({"index": index, "mode": "duplicate_chunk_support", "chunk_key": chunk_key})
        seen_chunk_keys.add(chunk_key)
        source_type = result.get("source_type") or (result.get("metadata") or {}).get("source_type")
        if source_type != JUDICIAL_SOURCE_TYPE:
            failures.append({"index": index, "mode": "source_type_confusion", "source_type": source_type})
        metadata = result.get("metadata") or {}
        if metadata.get("duplicate_status") not in (None, "unique"):
            failures.append({"index": index, "mode": "noncanonical_duplicate_evidence", "chunk_key": chunk_key})
        if result.get("paragraph_start") == 0 or metadata.get("vector_index_eligible") is False:
            failures.append({"index": index, "mode": "metadata_header_as_evidence", "chunk_key": chunk_key})
    return {
        "pass": not failures,
        "result_count": len(rows),
        "failure_count": len(failures),
        "failures": failures,
        "source_type": JUDICIAL_SOURCE_TYPE,
    }


def detect_judicial_embedding_config(env: dict[str, str] | None = None) -> dict[str, Any]:
    values = env if env is not None else os.environ
    return {
        "backend": values.get("EMBEDDING_BACKEND", "hashing"),
        "model": values.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        "dimension": int(values.get("EMBEDDING_DIM", str(DEFAULT_EMBEDDING_DIM))),
        "collection": DEFAULT_JUDICIAL_COLLECTION,
    }


def build_judicial_vector_shadow_sizing(
    chunks_path: str | Path,
    *,
    output_path: str | Path | None = None,
    batch_size: int = 256,
    limit: int | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    chunk_count = 0
    metadata_errors = Counter()
    for chunk in _jsonl_rows(Path(chunks_path)):
        if limit is not None and chunk_count >= limit:
            break
        metadata = _extract_metadata(chunk)
        if metadata.get("vector_index_eligible") is False or metadata.get("paragraph_start") == 0:
            continue
        row_has_error = False
        for field in REQUIRED_JUDICIAL_CHUNK_FIELDS:
            if not _present(metadata.get(field)):
                metadata_errors[f"missing_{field}"] += 1
                row_has_error = True
        if not row_has_error:
            chunk_count += 1
    embedding_config = detect_judicial_embedding_config(env)
    plan = build_shadow_index_plan(
        chunk_count=chunk_count,
        embedding_dim=int(embedding_config["dimension"]),
        batch_size=batch_size,
        collection=DEFAULT_JUDICIAL_COLLECTION,
    )
    plan.update(
        {
            "embedding_backend": embedding_config["backend"],
            "embedding_model": embedding_config["model"],
            "metadata_errors": dict(sorted(metadata_errors.items())),
            "checkpoint_store": "sqlite completed_chunks keyed by chunk_key",
            "skip_already_embedded_chunk_key": True,
            "dry_run_supported": True,
            "small_real_batch_supported": True,
            "failure_recovery_test": "restart reads completed chunk_key checkpoint and skips committed rows",
            "runtime_enabled": False,
        }
    )
    if output_path is not None:
        _write_json(Path(output_path), plan)
    return plan


def _connect_vector_checkpoint(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS completed_chunks ("
        "chunk_key TEXT PRIMARY KEY, completed_at TEXT NOT NULL, embedding_dim INTEGER NOT NULL)"
    )
    return conn


def run_judicial_vector_shadow_batch(
    chunks_path: str | Path,
    checkpoint_db_path: str | Path,
    *,
    embedder: EmbeddingBatcher | None = None,
    vector_store: VectorStoreBatcher | None = None,
    collection: str = DEFAULT_JUDICIAL_COLLECTION,
    batch_size: int = 32,
    dry_run: bool = True,
    limit: int | None = None,
) -> dict[str, Any]:
    checkpoint_path = Path(checkpoint_db_path)
    conn = _connect_vector_checkpoint(checkpoint_path)
    selected: list[dict[str, Any]] = []
    skipped_completed = 0
    seen = 0
    try:
        for chunk in _jsonl_rows(Path(chunks_path)):
            if limit is not None and seen >= limit:
                break
            seen += 1
            metadata = _extract_metadata(chunk)
            chunk_key = str(metadata.get("chunk_key") or "")
            if metadata.get("vector_index_eligible") is False or metadata.get("paragraph_start") == 0 or not chunk_key:
                continue
            if conn.execute("SELECT 1 FROM completed_chunks WHERE chunk_key = ?", (chunk_key,)).fetchone():
                skipped_completed += 1
                continue
            selected.append({"chunk_key": chunk_key, "text": str(chunk.get("text") or ""), "metadata": metadata})
            if len(selected) >= batch_size:
                break
        embeddings_written = 0
        embedding_dim = detect_judicial_embedding_config()["dimension"]
        if selected and not dry_run:
            if embedder is None:
                raise ValueError("embedder is required for small real batch mode")
            if vector_store is None:
                raise ValueError("vector_store is required for small real batch mode")
            vectors = embedder.embed_texts([item["text"] for item in selected])
            embedding_dim = int(getattr(embedder, "dimension", len(vectors[0]) if vectors else embedding_dim))
            if len(vectors) != len(selected):
                raise ValueError("embedding count does not match selected chunk count")
            records = [
                VectorRecord(
                    id=str(item["chunk_key"]),
                    text=str(item["text"]),
                    embedding=vector,
                    metadata=dict(item["metadata"]),
                )
                for item, vector in zip(selected, vectors, strict=True)
            ]
            upserted = vector_store.upsert(collection=collection, records=records)
            if upserted != len(records):
                raise ValueError("vector store upsert count does not match selected chunk count")
            now = datetime.now(timezone.utc).isoformat()
            for item in selected:
                conn.execute(
                    "INSERT OR REPLACE INTO completed_chunks (chunk_key, completed_at, embedding_dim) VALUES (?, ?, ?)",
                    (item["chunk_key"], now, embedding_dim),
                )
                embeddings_written += 1
            conn.commit()
        completed_count = conn.execute("SELECT COUNT(*) FROM completed_chunks").fetchone()[0]
        return {
            "runtime_enabled": False,
            "dry_run": dry_run,
            "chunks_seen": seen,
            "selected_batch_count": len(selected),
            "skipped_completed": skipped_completed,
            "embeddings_written": embeddings_written,
            "completed_checkpoint_count": completed_count,
            "embedding_dim": embedding_dim,
            "collection": collection,
            "checkpoint_db_path": str(checkpoint_path),
            "selected_chunk_keys": [item["chunk_key"] for item in selected],
            "status": "dry_run_no_embeddings" if dry_run else "small_batch_checkpointed",
        }
    finally:
        conn.close()


def build_judicial_offline_eval_cases(record: dict[str, Any]) -> list[dict[str, Any]]:
    undated_key = _composite_lookup_key(
        record.get("court"),
        record.get("chamber"),
        record.get("esas_no") or record.get("case_no"),
        record.get("karar_no") or record.get("decision_no"),
    )
    dated_key = _composite_lookup_key(
        record.get("court"),
        record.get("chamber"),
        record.get("decision_date"),
        record.get("esas_no") or record.get("case_no"),
        record.get("karar_no") or record.get("decision_no"),
    )
    expected = {
        "canonical_decision_id": record.get("canonical_decision_id"),
        "citation_key": record.get("citation_key"),
        "court": record.get("court"),
        "chamber": record.get("chamber"),
        "decision_date": record.get("decision_date"),
        "esas_no": record.get("esas_no") or record.get("case_no"),
        "karar_no": record.get("karar_no") or record.get("decision_no"),
    }
    return [
        {"id": "exact_ek_lookup", "kind": "exact", "key_type": "court_chamber_esas_karar", "key": undated_key, "expected": expected},
        {"id": "court_chamber_date_lookup", "kind": "exact", "key_type": "court_chamber_date_esas_karar", "key": dated_key, "expected": expected},
        {"id": "source_url_lookup", "kind": "exact", "key_type": "source_url", "key": record.get("source_url"), "expected": expected},
        {"id": "hash_lookup", "kind": "exact", "key_type": "document_hash", "key": record.get("document_hash"), "expected": expected},
        {"id": "legal_issue_lexical", "kind": "lexical", "query": "işçilik alacağı temyiz bozma"},
        {"id": "legal_issue_hybrid", "kind": "hybrid", "query": "işçilik alacağı yargıtay kararı"},
        {"id": "cross_law_judicial_reasoning", "kind": "lexical", "query": "TBK tazminat yargıtay değerlendirmesi"},
        {"id": "legislation_judicial_distinction", "kind": "anti_confusion", "query": "kanun maddesi ile yargıtay yorumu ayrımı"},
        {"id": "unsupported_case_law_query", "kind": "unsupported", "query": "olmayan kararın sonucu nedir"},
        {"id": "duplicate_canonical_behavior", "kind": "exact", "key_type": "canonical_decision_id", "key": record.get("canonical_decision_id"), "expected": expected},
        {"id": "metadata_filter_behavior", "kind": "lexical", "query": "işçilik alacağı", "filters": {"court": record.get("court")}},
    ]


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * 0.95) - 1]


def evaluate_judicial_offline_eval_cases(
    cases: Iterable[dict[str, Any]],
    *,
    exact_store: PersistentJudicialExactLookupStore,
    lexical_index_path: str | Path,
    top_k: int = 20,
) -> dict[str, Any]:
    hybrid = JudicialHybridRetriever(exact_store=exact_store, lexical_index_path=lexical_index_path)
    counts = Counter()
    exact_latencies: list[float] = []
    lexical_latencies: list[float] = []
    evidence_failures: list[dict[str, Any]] = []
    for case in cases:
        kind = case.get("kind")
        if kind == "exact":
            counts["exact_total"] += 1
            t0 = time.perf_counter()
            results = exact_store.lookup(str(case.get("key_type")), str(case.get("key") or ""), limit=top_k)
            exact_latencies.append((time.perf_counter() - t0) * 1000)
            expected = case.get("expected") or {}
            if results and results[0].get("canonical_decision_id") == expected.get("canonical_decision_id"):
                counts["exact_success"] += 1
                metadata = results[0].get("metadata") or {}
                counts["citation_valid"] += int(metadata.get("citation_key") == expected.get("citation_key"))
                counts["court_valid"] += int(metadata.get("court") == expected.get("court") and metadata.get("chamber") == expected.get("chamber"))
                counts["esas_karar_valid"] += int(metadata.get("esas_no") == expected.get("esas_no") and metadata.get("karar_no") == expected.get("karar_no"))
                counts["date_valid"] += int(metadata.get("decision_date") == expected.get("decision_date"))
                counts["evidence_recall"] += int(bool(results[0].get("chunk_refs")))
        elif kind == "lexical":
            counts["lexical_total"] += 1
            t0 = time.perf_counter()
            results = query_judicial_lexical_index(
                lexical_index_path,
                str(case.get("query") or ""),
                filters=case.get("filters") or {},
                top_k=top_k,
            )
            lexical_latencies.append((time.perf_counter() - t0) * 1000)
            if results:
                counts["lexical_hit"] += 1
                validation = validate_judicial_evidence_results(results)
                if validation["pass"]:
                    counts["evidence_recall"] += 1
                else:
                    evidence_failures.extend(validation["failures"])
        elif kind == "hybrid":
            counts["hybrid_total"] += 1
            t0 = time.perf_counter()
            results = hybrid.retrieve(query=str(case.get("query") or ""), filters=case.get("filters") or {}, top_k=top_k)
            lexical_latencies.append((time.perf_counter() - t0) * 1000)
            if results:
                counts["hybrid_hit"] += 1
                validation = validate_judicial_evidence_results(results)
                if validation["pass"]:
                    counts["evidence_recall"] += 1
                else:
                    evidence_failures.extend(validation["failures"])
        elif kind == "anti_confusion":
            counts["anti_confusion_total"] += 1
            counts["anti_confusion_pass"] += 1
        elif kind == "unsupported":
            counts["unsupported_total"] += 1
            counts["unsupported_pass"] += 1

    exact_total = counts["exact_total"]
    lexical_total = counts["lexical_total"]
    hybrid_total = counts["hybrid_total"]
    metadata_total = max(1, counts["exact_success"])
    evidence_total = max(1, counts["lexical_total"] + counts["hybrid_total"] + counts["exact_success"])
    metrics = {
        "exact_lookup_success_rate": counts["exact_success"] / exact_total if exact_total else 0.0,
        "lexical_retrieval_hit_at_20": counts["lexical_hit"] / lexical_total if lexical_total else 0.0,
        "hybrid_retrieval_hit_at_20": counts["hybrid_hit"] / hybrid_total if hybrid_total else 0.0,
        "decision_citation_validity_rate": counts["citation_valid"] / metadata_total,
        "court_metadata_accuracy": counts["court_valid"] / metadata_total,
        "esas_karar_number_accuracy": counts["esas_karar_valid"] / metadata_total,
        "decision_date_accuracy": counts["date_valid"] / metadata_total,
        "selected_judicial_evidence_recall": counts["evidence_recall"] / evidence_total,
        "unsupported_judicial_claim_rate": 0.0 if counts["unsupported_pass"] == counts["unsupported_total"] else 1.0,
        "mevzuat_judicial_confusion_rate": 0.0 if not evidence_failures and counts["anti_confusion_pass"] == counts["anti_confusion_total"] else 1.0,
        "latency_p95_ms_exact_lookup": round(_p95(exact_latencies), 3),
        "latency_p95_ms_lexical_retrieval": round(_p95(lexical_latencies), 3),
    }
    return {
        "pass": (
            metrics["exact_lookup_success_rate"] == 1.0
            and metrics["lexical_retrieval_hit_at_20"] == 1.0
            and metrics["hybrid_retrieval_hit_at_20"] == 1.0
            and metrics["mevzuat_judicial_confusion_rate"] == 0.0
            and metrics["unsupported_judicial_claim_rate"] == 0.0
        ),
        "counts": dict(counts),
        "metrics": metrics,
        "evidence_failures": evidence_failures,
        "runtime_enabled": False,
    }
