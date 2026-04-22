#!/usr/bin/env python3
"""Run Phase 7A index visibility probes for acquisition targets.

The probe reads the Phase 7 acquisition tracker and measures four source-level
visibility signals without mutating Milvus:

* dense candidate set includes the expected/compatible family
* exact identifier query finds a matching source
* normalized title query finds a matching source
* year/family-filtered query finds a matching source
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
API_SRC = REPO_ROOT / "api-gateway/src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from rag.source_catalog import canonical_source_family, enrich_metadata_with_source_title  # noqa: E402


DEFAULT_TRACKER = REPO_ROOT / "reports/benchmark/phase_07_acquisition_tracker.csv"
DEFAULT_CATALOG = REPO_ROOT / "reports/benchmark/phase_05_canonical_source_catalog.csv"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_07_visibility_probe.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_07_visibility_probe.md"

DEFAULT_MILVUS_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024"

FIELDNAMES = [
    "qid",
    "expected_family",
    "expected_source_title",
    "expected_identifier",
    "expected_identifier_type",
    "availability_status",
    "owner",
    "action_type",
    "resolution_status",
    "next_action",
    "catalog_match_found",
    "catalog_source_key",
    "catalog_family",
    "catalog_title",
    "catalog_score",
    "candidate_family_found",
    "candidate_strict_family_found",
    "candidate_source_found",
    "exact_identifier_query_found",
    "normalized_title_query_found",
    "year_issuer_filtered_query_found",
    "phase7_blocker_type",
    "dense_probe_error",
    "scalar_probe_error",
    "top_dense_sources",
    "exact_identifier_hits",
    "normalized_title_hits",
    "year_issuer_filtered_hits",
]

TR_ASCII_TRANS = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
    }
)

STOPWORDS = {
    "ait",
    "arasinda",
    "bagli",
    "bazı",
    "bazi",
    "bir",
    "dair",
    "de",
    "da",
    "duzeyindeki",
    "esaslar",
    "hakkinda",
    "ile",
    "ilgili",
    "iliskin",
    "kanun",
    "kanunu",
    "kurulmasina",
    "kuruluslari",
    "kurum",
    "kurumlar",
    "madde",
    "no",
    "olan",
    "sayili",
    "usul",
    "ve",
    "veya",
}

FAMILY_ALIASES = {
    "CB_KARAR": "cb_karar",
    "CB_YONETMELIK": "cb_yonetmelik",
    "KANUN": "kanun",
    "YONETMELIK": "yonetmelik",
    "UY": "uy",
    "TUZUK": "tuzuk",
    "KKY": "kky",
    "TEBLIGLER": "teblig",
}

COMPATIBLE_FAMILIES = {
    "cb_karar": {"cb_karar"},
    "cb_yonetmelik": {"cb_yonetmelik", "kky", "yonetmelik"},
    "kanun": {"kanun", "mulga_kanun"},
    "yonetmelik": {"yonetmelik", "kky", "uy", "cb_yonetmelik"},
    "uy": {"uy"},
    "tuzuk": {"tuzuk"},
    "kky": {"kky", "yonetmelik"},
    "teblig": {"teblig"},
}

RAW_FAMILY_VALUES = {
    "cb_karar": {"cb_karar"},
    "cb_yonetmelik": {"cb_yonetmelik", "kky", "yonetmelik"},
    "kanun": {"kanun", "mulga_kanun"},
    "yonetmelik": {"yonetmelik", "kky", "uy", "cb_yonetmelik"},
    "uy": {"uy"},
    "tuzuk": {"tuzuk"},
    "kky": {"kky", "yonetmelik"},
    "teblig": {"teblig"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracker", type=Path, default=DEFAULT_TRACKER)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", "http://localhost:19530"))
    parser.add_argument("--collection", default=os.getenv("MILVUS_COLLECTION", DEFAULT_MILVUS_COLLECTION))
    parser.add_argument("--embedding-base-url", default=os.getenv("EMBEDDING_BASE_URL", "http://127.0.0.1:8081/v1"))
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large-instruct"),
    )
    parser.add_argument("--embedding-dim", default=os.getenv("EMBEDDING_DIM", "1024"))
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--skip-dense", action="store_true", help="Only run scalar/catalog probes.")
    return parser.parse_args()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_text(value: Any) -> str:
    text = clean(value).casefold().translate(TR_ASCII_TRANS)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def significant_tokens(value: Any, *, limit: int = 6) -> list[str]:
    tokens: list[str] = []
    for token in normalize_text(value).split():
        if len(token) < 3 or token in STOPWORDS or token.isdigit():
            continue
        if token not in tokens:
            tokens.append(token)
    return tokens[:limit]


def expected_family_canonical(expected_family: str) -> str:
    return FAMILY_ALIASES.get(clean(expected_family).upper(), normalize_text(expected_family).replace(" ", "_"))


def compatible_families(expected_family: str) -> set[str]:
    family = expected_family_canonical(expected_family)
    return COMPATIBLE_FAMILIES.get(family, {family} if family else set())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def csv_bool(value: bool) -> str:
    return "true" if value else "false"


def quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def or_expr(clauses: Iterable[str]) -> str:
    values = [clause for clause in clauses if clause]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return "(" + " || ".join(values) + ")"


def and_expr(clauses: Iterable[str]) -> str:
    values = [clause for clause in clauses if clause]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return "(" + " && ".join(values) + ")"


def identifier_values(row: dict[str, str]) -> list[str]:
    values: list[str] = []
    primary = clean(row.get("expected_identifier"))
    if primary:
        values.append(primary)
    related = clean(row.get("expected_related_identifiers"))
    for item in related.split("|"):
        item = clean(item)
        if not item:
            continue
        values.append(item.split(":", 1)[-1])
    return list(dict.fromkeys(values))


def identifier_filter(values: list[str]) -> str:
    clauses: list[str] = []
    for value in values:
        escaped = quote(value)
        clauses.extend(
            [
                f'metadata["belge_no"] == "{escaped}"',
                f'metadata["kanun_no"] == "{escaped}"',
                f'metadata["belge_kisa_adi"] == "{escaped}"',
                f'metadata["kanun_kisa_adi"] == "{escaped}"',
                f'metadata["canonical_identifier"] == "{escaped}"',
                f'text like "%{escaped}%"',
            ]
        )
    return or_expr(clauses)


def title_filter(title: str, *, max_terms: int = 4) -> str:
    original_terms = re.findall(r"[A-Za-zÇĞİÖŞÜÂÎÛçğıöşüâîû0-9]{3,}", clean(title))
    normalized_lookup = set(significant_tokens(title, limit=max_terms))
    terms: list[str] = []
    for term in original_terms:
        if normalize_text(term) in normalized_lookup and term not in terms:
            terms.append(term)
    if not terms:
        terms = significant_tokens(title, limit=max_terms)
    clauses: list[str] = []
    for term in terms[:max_terms]:
        variants = {
            term.upper(),
            normalize_text(term).upper(),
            term,
        }
        clauses.append(or_expr([f'text like "%{quote(variant)}%"' for variant in variants if variant]))
    return and_expr(clauses)


def family_filter(expected_family: str) -> str:
    family = expected_family_canonical(expected_family)
    raw_values = RAW_FAMILY_VALUES.get(family, {family})
    return or_expr([f'metadata["belge_turu"] == "{quote(value)}"' for value in raw_values if value])


def extract_years(*values: Any) -> list[str]:
    years: set[str] = set()
    for value in values:
        for year in re.findall(r"\b(18\d{2}|19\d{2}|20\d{2})\b", clean(value)):
            years.add(year)
    return sorted(years)


def year_family_filter(row: dict[str, str], catalog_match: dict[str, str] | None) -> str:
    years = extract_years(
        row.get("expected_source"),
        row.get("expected_source_title"),
        catalog_match.get("official_gazette_date") if catalog_match else "",
        catalog_match.get("effective_start") if catalog_match else "",
        catalog_match.get("year_signals") if catalog_match else "",
    )
    clauses = [family_filter(row.get("expected_family", ""))]
    if years:
        clauses.append(or_expr([f'metadata["resmi_gazete_tarih"] like "%{year}%"' for year in years[:3]]))
    identifiers = identifier_values(row)
    if identifiers:
        clauses.append(identifier_filter(identifiers[:3]))
    else:
        clauses.append(title_filter(row.get("expected_source_title", ""), max_terms=3))
    return and_expr(clauses)


def source_family_from_metadata(metadata: dict[str, Any] | None) -> str:
    enriched = enrich_metadata_with_source_title(metadata or {})
    return canonical_source_family(enriched)


def source_title_from_metadata(metadata: dict[str, Any] | None) -> str:
    enriched = enrich_metadata_with_source_title(metadata or {})
    return clean(
        enriched.get("canonical_title")
        or enriched.get("source_title")
        or enriched.get("belge_adi")
        or enriched.get("kanun_adi")
        or enriched.get("law_name")
        or enriched.get("title")
    )


def source_identifier_from_metadata(metadata: dict[str, Any] | None) -> str:
    metadata = metadata or {}
    return clean(
        metadata.get("canonical_identifier")
        or metadata.get("belge_no")
        or metadata.get("kanun_no")
        or metadata.get("belge_kisa_adi")
        or metadata.get("kanun_kisa_adi")
        or str(metadata.get("source_id") or "").split(":", 1)[0]
    )


def row_matches_expected_source(hit: dict[str, Any], tracker_row: dict[str, str]) -> bool:
    metadata = hit.get("metadata") if isinstance(hit, dict) else {}
    family = source_family_from_metadata(metadata)
    compatible = family in compatible_families(tracker_row.get("expected_family", ""))
    if not compatible:
        return False
    expected_identifiers = set(identifier_values(tracker_row))
    hit_identifier = source_identifier_from_metadata(metadata)
    text = clean(hit.get("text") if isinstance(hit, dict) else "")
    title = source_title_from_metadata(metadata)
    title_norm = normalize_text(title)
    text_norm = normalize_text(text)
    haystack = normalize_text(f"{title} {text} {hit_identifier}")
    expected_title_tokens = set(significant_tokens(tracker_row.get("expected_source_title", ""), limit=8))
    title_overlap = len(expected_title_tokens & set(haystack.split()))
    title_ratio = title_overlap / max(len(expected_title_tokens), 1)
    expected_title_norm = normalize_text(tracker_row.get("expected_source_title"))
    contains_title = bool(expected_title_norm and (expected_title_norm in title_norm or expected_title_norm in text_norm))
    if len(expected_title_tokens) <= 2:
        title_strong = bool(expected_title_tokens) and title_overlap == len(expected_title_tokens)
    else:
        title_strong = contains_title or (title_overlap >= 3 and title_ratio >= 0.75)
    identifier_match = bool(expected_identifiers and expected_identifiers & set(re.findall(r"[0-9][0-9A-Za-z/\-.]*", haystack)))
    identifier_match = identifier_match or (hit_identifier in expected_identifiers if hit_identifier else False)
    if title_strong:
        return True
    return bool(identifier_match and title_overlap >= min(2, len(expected_title_tokens)))


def format_hit(hit: dict[str, Any]) -> str:
    metadata = hit.get("metadata") or {}
    display = clean(metadata.get("display_citation")) or clean(hit.get("id"))
    family = source_family_from_metadata(metadata)
    title = source_title_from_metadata(metadata) or clean(hit.get("text"))[:80]
    return f"{display} [{family}] {title[:100]}"


def query_milvus(client: Any, *, collection: str, filter_expr: str, limit: int = 8) -> tuple[list[dict[str, Any]], str]:
    if not filter_expr:
        return [], ""
    try:
        rows = client.query(
            collection_name=collection,
            filter=filter_expr,
            limit=limit,
            output_fields=["id", "text", "metadata"],
        )
        return rows, ""
    except Exception as exc:  # pragma: no cover - exercised only against live Milvus drift
        return [], f"{type(exc).__name__}: {exc}"


def catalog_score(row: dict[str, str], catalog_row: dict[str, str]) -> float:
    expected_family = expected_family_canonical(row.get("expected_family", ""))
    compatible = catalog_row.get("source_family_canonical") in compatible_families(row.get("expected_family", ""))
    strict = catalog_row.get("source_family_canonical") == expected_family
    if not compatible:
        return 0.0
    expected_title_tokens = set(significant_tokens(row.get("expected_source_title", ""), limit=10))
    catalog_title_tokens = set(significant_tokens(catalog_row.get("canonical_title_normalized") or catalog_row.get("canonical_title"), limit=16))
    overlap = len(expected_title_tokens & catalog_title_tokens)
    overlap_ratio = overlap / max(len(expected_title_tokens), 1)
    identifiers = set(identifier_values(row))
    catalog_identifier = clean(catalog_row.get("canonical_identifier"))
    identifier_match = bool(catalog_identifier and catalog_identifier in identifiers)
    cross_refs = set(clean(catalog_row.get("cross_refs")).split(" | "))
    cross_ref_match = bool(identifiers & cross_refs)
    contains_title = normalize_text(row.get("expected_source_title")) in normalize_text(catalog_row.get("canonical_title"))
    title_strong = contains_title or (overlap >= 4 and overlap_ratio >= 0.65)
    if not (identifier_match or title_strong):
        return 0.0
    score = 0.0
    if strict:
        score += 20
    elif compatible:
        score += 12
    if identifier_match:
        score += 45
    elif cross_ref_match:
        score += 18
    if contains_title:
        score += 20
    score += overlap_ratio * 30
    return score


def best_catalog_match(row: dict[str, str], catalog_rows: list[dict[str, str]]) -> dict[str, str] | None:
    scored: list[tuple[float, dict[str, str]]] = []
    for catalog_row in catalog_rows:
        score = catalog_score(row, catalog_row)
        if score >= 28:
            scored.append((score, catalog_row))
    if not scored:
        return None
    return sorted(scored, key=lambda item: (-item[0], item[1].get("source_key", "")))[0][1] | {
        "_score": f"{sorted(scored, key=lambda item: (-item[0], item[1].get('source_key', '')))[0][0]:.2f}"
    }


def dense_probe(retriever: Any, row: dict[str, str], *, top_k: int) -> tuple[list[Any], str]:
    if retriever is None:
        return [], "dense_probe_skipped"
    query = clean(row.get("expected_source_title"))
    if row.get("expected_related_sources"):
        query = f"{query} {row['expected_related_sources']}"
    try:
        results, _stats = retriever.retrieve(query=query, top_k=top_k)
        return results, ""
    except Exception as exc:  # pragma: no cover - exercised only against live embedding/Milvus drift
        return [], f"{type(exc).__name__}: {exc}"


def retrieval_result_to_hit(result: Any) -> dict[str, Any]:
    return {
        "id": getattr(result, "chunk_id", ""),
        "text": getattr(result, "text", ""),
        "metadata": getattr(result, "metadata", {}) or {},
    }


def dense_signals(results: list[Any], row: dict[str, str]) -> tuple[bool, bool, bool, str]:
    hits = [retrieval_result_to_hit(result) for result in results]
    expected = expected_family_canonical(row.get("expected_family", ""))
    families = [source_family_from_metadata(hit.get("metadata")) for hit in hits]
    candidate_strict_family_found = expected in families if expected else False
    candidate_family_found = bool(set(families) & compatible_families(row.get("expected_family", "")))
    candidate_source_found = any(row_matches_expected_source(hit, row) for hit in hits)
    return (
        candidate_family_found,
        candidate_strict_family_found,
        candidate_source_found,
        " || ".join(format_hit(hit) for hit in hits[:5]),
    )


def configure_env(args: argparse.Namespace) -> None:
    os.environ.setdefault("MILVUS_URI", args.milvus_uri)
    os.environ.setdefault("MILVUS_COLLECTION", args.collection)
    os.environ.setdefault("EMBEDDING_BACKEND", "remote")
    os.environ.setdefault("EMBEDDING_BASE_URL", args.embedding_base_url)
    os.environ.setdefault("EMBEDDING_MODEL", args.embedding_model)
    os.environ.setdefault("EMBEDDING_DIM", str(args.embedding_dim))
    os.environ.setdefault("DGX_API_KEY", "not-needed")


def build_clients(args: argparse.Namespace) -> tuple[Any, Any | None]:
    from pymilvus import MilvusClient

    client = MilvusClient(uri=args.milvus_uri)
    if args.skip_dense:
        return client, None
    from rag.retriever import MilvusRetriever

    return client, MilvusRetriever.from_env(collection=args.collection, top_k=args.top_k)


def status_for_probe(
    *,
    catalog_match: dict[str, str] | None,
    candidate_source_found: bool,
    exact_identifier_found: bool,
    title_found: bool,
    year_found: bool,
) -> tuple[str, str, str]:
    any_scalar = exact_identifier_found or title_found or year_found
    if catalog_match and candidate_source_found:
        return (
            "indexed_and_retrieval_visible",
            "visibility_resolved_pending_benchmark_rerun",
            "visibility_resolved",
        )
    if catalog_match and any_scalar:
        return (
            "indexed_but_dense_retrieval_gap",
            "indexed_visibility_resolved_selector_or_dense_retrieval_repair",
            "gold_document_not_retrieved",
        )
    if catalog_match:
        return ("catalog_only_not_indexed", "open_reindex_required", "not_retrieved_or_not_indexed")
    if candidate_source_found:
        return (
            "indexed_and_retrieval_visible_catalog_backfill_required",
            "visibility_resolved_catalog_backfill_required",
            "visibility_resolved",
        )
    if any_scalar:
        return (
            "indexed_without_catalog_match",
            "metadata_catalog_backfill_required",
            "gold_document_not_retrieved",
        )
    return ("not_available_in_current_corpus", "open_source_acquisition_required", "not_retrieved_or_not_indexed")


def build_probe_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    configure_env(args)
    tracker_rows = read_csv(args.tracker)
    catalog_rows = read_csv(args.catalog)
    client, retriever = build_clients(args)
    rows: list[dict[str, str]] = []
    for row in tracker_rows:
        catalog_match = best_catalog_match(row, catalog_rows)
        dense_results, dense_error = dense_probe(retriever, row, top_k=args.top_k)
        candidate_family_found, candidate_strict_family_found, candidate_source_found, top_dense_sources = dense_signals(
            dense_results,
            row,
        )

        exact_hits, exact_error = query_milvus(
            client,
            collection=args.collection,
            filter_expr=identifier_filter(identifier_values(row)),
        )
        title_hits, title_error = query_milvus(
            client,
            collection=args.collection,
            filter_expr=title_filter(row.get("expected_source_title", "")),
        )
        year_hits, year_error = query_milvus(
            client,
            collection=args.collection,
            filter_expr=year_family_filter(row, catalog_match),
        )
        exact_found = any(row_matches_expected_source(hit, row) for hit in exact_hits)
        title_found = any(row_matches_expected_source(hit, row) for hit in title_hits)
        year_found = any(row_matches_expected_source(hit, row) for hit in year_hits)
        availability_status, resolution_status, blocker_type = status_for_probe(
            catalog_match=catalog_match,
            candidate_source_found=candidate_source_found,
            exact_identifier_found=exact_found,
            title_found=title_found,
            year_found=year_found,
        )
        next_action = row.get("next_action", "")
        if resolution_status == "visibility_resolved_pending_benchmark_rerun":
            next_action = "rerun_benchmark_then_close_if_score_recovers"
        elif resolution_status == "visibility_resolved_catalog_backfill_required":
            next_action = "backfill_source_catalog_metadata_then_rerun_benchmark"
        elif resolution_status == "indexed_visibility_resolved_selector_or_dense_retrieval_repair":
            next_action = "repair_dense_source_selection_or_selector"
        elif resolution_status == "open_reindex_required":
            next_action = "reindex_catalog_source_into_serving_collection"
        elif resolution_status == "open_source_acquisition_required":
            next_action = "acquire_primary_source_then_reindex"
        rows.append(
            {
                "qid": row.get("qid", ""),
                "expected_family": row.get("expected_family", ""),
                "expected_source_title": row.get("expected_source_title", ""),
                "expected_identifier": row.get("expected_identifier", ""),
                "expected_identifier_type": row.get("expected_identifier_type", ""),
                "availability_status": availability_status,
                "owner": row.get("owner", ""),
                "action_type": row.get("action_type", ""),
                "resolution_status": resolution_status,
                "next_action": next_action,
                "catalog_match_found": csv_bool(catalog_match is not None),
                "catalog_source_key": (catalog_match or {}).get("source_key", ""),
                "catalog_family": (catalog_match or {}).get("source_family_canonical", ""),
                "catalog_title": (catalog_match or {}).get("canonical_title", ""),
                "catalog_score": (catalog_match or {}).get("_score", ""),
                "candidate_family_found": csv_bool(candidate_family_found),
                "candidate_strict_family_found": csv_bool(candidate_strict_family_found),
                "candidate_source_found": csv_bool(candidate_source_found),
                "exact_identifier_query_found": csv_bool(exact_found),
                "normalized_title_query_found": csv_bool(title_found),
                "year_issuer_filtered_query_found": csv_bool(year_found),
                "phase7_blocker_type": blocker_type,
                "dense_probe_error": dense_error,
                "scalar_probe_error": " | ".join(error for error in (exact_error, title_error, year_error) if error),
                "top_dense_sources": top_dense_sources,
                "exact_identifier_hits": " || ".join(format_hit(hit) for hit in exact_hits[:5]),
                "normalized_title_hits": " || ".join(format_hit(hit) for hit in title_hits[:5]),
                "year_issuer_filtered_hits": " || ".join(format_hit(hit) for hit in year_hits[:5]),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], *, args: argparse.Namespace) -> None:
    status_counts = Counter(row["resolution_status"] for row in rows)
    availability_counts = Counter(row["availability_status"] for row in rows)
    blocker_counts = Counter(row["phase7_blocker_type"] for row in rows)
    family_counts = Counter(row["expected_family"] for row in rows)
    open_rows = [
        row
        for row in rows
        if row["resolution_status"] in {"open_reindex_required", "open_source_acquisition_required"}
    ]
    gold_doc_rows = [row for row in rows if row["phase7_blocker_type"] == "gold_document_not_retrieved"]
    lines = [
        "# Phase 7A Visibility Probe",
        "",
        f"- tracker: `{args.tracker}`",
        f"- catalog: `{args.catalog}`",
        f"- collection: `{args.collection}`",
        f"- top_k: {args.top_k}",
        f"- rows: {len(rows)}",
        f"- open_acquisition_or_reindex_rows: {len(open_rows)}",
        f"- gold_document_not_retrieved_rows: {len(gold_doc_rows)}",
        "",
        "## Acceptance Signals",
        f"- needs_corpus_acquisition_open_rows_target_le_8: {'PASS' if len(open_rows) <= 8 else 'FAIL'} ({len(open_rows)}/8)",
        f"- gold_document_not_retrieved_rows_phase6_baseline_6_target_le_3: {'PASS' if len(gold_doc_rows) <= 3 else 'FAIL'} ({len(gold_doc_rows)}/3)",
        f"- every_open_row_has_owner_and_next_action: {'PASS' if all(row.get('owner') and row.get('next_action') for row in open_rows) else 'FAIL'}",
        "",
        "## Availability Status",
    ]
    for status, count in availability_counts.most_common():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Resolution Status"])
    for status, count in status_counts.most_common():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Phase 7 Blocker Type"])
    for blocker, count in blocker_counts.most_common():
        lines.append(f"- {blocker}: {count}")
    lines.extend(["", "## Family Counts"])
    for family, count in family_counts.most_common():
        lines.append(f"- {family}: {count}")
    lines.extend(["", "## Open Rows"])
    if open_rows:
        for row in open_rows:
            lines.append(
                f"- {row['qid']}: status={row['resolution_status']}; action={row['action_type']}; "
                f"owner={row['owner']}; next={row['next_action']}; title={row['expected_source_title'][:100]}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Visibility-Resolved Rows"])
    resolved_rows = [row for row in rows if row["availability_status"] == "indexed_and_retrieval_visible"]
    if resolved_rows:
        for row in resolved_rows:
            lines.append(
                f"- {row['qid']}: catalog={row['catalog_source_key']} [{row['catalog_family']}]; "
                f"title={row['catalog_title'][:100]}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Visibility-Resolved With Catalog Backfill"])
    catalog_backfill_rows = [
        row
        for row in rows
        if row["availability_status"] == "indexed_and_retrieval_visible_catalog_backfill_required"
    ]
    if catalog_backfill_rows:
        for row in catalog_backfill_rows:
            lines.append(
                f"- {row['qid']}: status={row['resolution_status']}; next={row['next_action']}; "
                f"title={row['expected_source_title'][:100]}"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Interpretation",
            "- `indexed_and_retrieval_visible` can move out of corpus-acquisition ownership after the next benchmark rerun.",
            "- `indexed_and_retrieval_visible_catalog_backfill_required` means live retrieval can see the source, but the source-level catalog needs metadata alignment.",
            "- `indexed_but_dense_retrieval_gap` means the source exists in catalog/scalar probes but current dense retrieval still misses it.",
            "- `catalog_only_not_indexed` requires reindexing from the canonical article source into the serving Milvus collection.",
            "- `not_available_in_current_corpus` remains a real source acquisition or parser coverage gap.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = build_probe_rows(args)
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, rows, args=args)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
