#!/usr/bin/env python3
"""Build Phase 11 source visibility / index-truth audit artifacts.

The audit is intentionally systemic: it compares benchmark gold document
descriptions against the canonical source catalog and the live Milvus index.
It does not encode QID-specific routing fixes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
API_SRC = REPO_ROOT / "api-gateway" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from rag.source_catalog import load_canonical_source_catalog, normalize_canonical_text
DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260422T180225Z_phase10_full"
DEFAULT_COVERAGE_CSV = REPO_ROOT / "reports/benchmark/phase_10_coverage_backlog.csv"
DEFAULT_ANSWER_KEY = REPO_ROOT / "evaluation/private/hukuk_ai_100_answer_key_private.csv"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_11a_visibility_truth_table.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_11a_visibility_truth_audit.md"

FAMILY_ALIASES = {
    "CB_GENELGE": "cb_genelge",
    "CB_KARAR": "cb_karar",
    "CB_KARARNAME": "cb_kararname",
    "CB_YONETMELIK": "cb_yonetmelik",
    "KANUN": "kanun",
    "KHK": "khk",
    "KKY": "kky",
    "MULGA": "mulga_kanun",
    "MULGA_KANUN": "mulga_kanun",
    "TEBLIGLER": "teblig",
    "TEBLIG": "teblig",
    "TUZUK": "tuzuk",
    "UY": "uy",
    "YONETMELIK": "yonetmelik",
}

GENERIC_TITLE_TOKENS = {
    "ait",
    "ana",
    "baz",
    "bazi",
    "dair",
    "esas",
    "esaslar",
    "genel",
    "gore",
    "gorev",
    "hakkinda",
    "icin",
    "ile",
    "ilgili",
    "iliskin",
    "kanun",
    "kanunu",
    "kapsaminda",
    "madde",
    "no",
    "olan",
    "sayili",
    "usul",
    "ve",
    "yonetmeligi",
    "yonetmelik",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--coverage-csv", type=Path, default=DEFAULT_COVERAGE_CSV)
    parser.add_argument("--answer-key", type=Path, default=DEFAULT_ANSWER_KEY)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--milvus-uri", default="http://localhost:19530")
    parser.add_argument("--milvus-collection", default="mevzuat_faz1_shadow_20260418_compat1024")
    parser.add_argument("--skip-milvus", action="store_true")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_jsonl_by_qid(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            qid = str(record.get("qid") or "")
            if qid:
                rows[qid] = record
    return rows


def trace_payload(record: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(record, dict):
        return {}
    response = record.get("response")
    if isinstance(response, dict) and isinstance(response.get("trace"), dict):
        return response["trace"]
    trace = record.get("trace")
    return trace if isinstance(trace, dict) else {}


def chunks_from_trace(trace: dict[str, Any], key: str) -> list[dict[str, Any]]:
    retrieval = trace.get("retrieval")
    if isinstance(retrieval, dict) and isinstance(retrieval.get(key), list):
        return [chunk for chunk in retrieval[key] if isinstance(chunk, dict)]
    return []


def canonical_family(value: Any) -> str:
    raw = str(value or "").strip().upper().replace(" ", "_")
    return FAMILY_ALIASES.get(raw, raw.lower())


def split_documents(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*\|\s*", value or "") if part.strip()]


def title_tokens(value: Any) -> set[str]:
    normalized = normalize_canonical_text(value)
    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", normalized)
        if token not in GENERIC_TITLE_TOKENS
    }


def numeric_tokens(value: Any) -> set[str]:
    return set(re.findall(r"\b\d{2,}\b", normalize_canonical_text(value)))


def infer_doc_family_from_title(value: Any) -> str:
    normalized = normalize_canonical_text(value)
    if not normalized:
        return ""
    if "cumhurbaskanligi genelgesi" in normalized or re.search(r"\bgenelge(si)?\b", normalized):
        return "cb_genelge"
    if "kanun hukmunde kararname" in normalized:
        return "khk"
    if "cumhurbaskanligi kararnamesi" in normalized or "kararname numarasi" in normalized:
        return "cb_kararname"
    if "karar sayisi" in normalized or "cumhurbaskani karari" in normalized or normalized.endswith(" karar"):
        return "cb_karar"
    if re.search(r"\bteblig(i|ler|leri|e|de|den|in)?\b", normalized):
        return "teblig"
    if "tuzuk" in normalized or "tuzug" in normalized:
        return "tuzuk"
    if "universitesi" in normalized and ("onlisans" in normalized or "lisans" in normalized):
        return "uy"
    if "kanunu" in normalized or re.search(r"\bkanun\b", normalized):
        return "kanun"
    if "yonetmelik" in normalized or "yonetmelig" in normalized:
        return "yonetmelik"
    return ""


def family_conflict_penalty(expected_doc: str, candidate_title: Any) -> float:
    expected_family = infer_doc_family_from_title(expected_doc)
    candidate_family = infer_doc_family_from_title(candidate_title)
    if not expected_family or not candidate_family or expected_family == candidate_family:
        return 0.0
    compatible_regulation_families = {"yonetmelik", "kky", "uy", "cb_yonetmelik"}
    if expected_family in compatible_regulation_families and candidate_family in compatible_regulation_families:
        return 0.0
    return 12.0


def title_overlap(expected_doc: str, candidate_title: Any) -> tuple[int, float, float]:
    expected_tokens = title_tokens(expected_doc)
    candidate_tokens = title_tokens(candidate_title)
    if not expected_tokens or not candidate_tokens:
        return 0, 0.0, 0.0
    overlap = len(expected_tokens & candidate_tokens)
    return (
        overlap,
        overlap / max(len(expected_tokens), 1),
        overlap / max(len(candidate_tokens), 1),
    )


def exact_title_containment(expected_doc: str, candidate_title: Any) -> bool:
    expected_norm = normalize_canonical_text(expected_doc)
    candidate_norm = normalize_canonical_text(candidate_title)
    if len(title_tokens(expected_doc)) < 2 or len(title_tokens(candidate_title)) < 2:
        return False
    return bool(expected_norm and candidate_norm and (expected_norm in candidate_norm or candidate_norm in expected_norm))


def reliable_catalog_match(expected_doc: str, record: dict[str, Any], score: float) -> bool:
    title = record.get("canonical_title") or ""
    overlap, expected_ratio, candidate_ratio = title_overlap(expected_doc, title)
    expected_numbers = numeric_tokens(expected_doc)
    record_numbers = numeric_tokens(
        " ".join(
            str(record.get(key) or "")
            for key in (
                "canonical_identifier",
                "canonical_identifier_display",
                "decision_number",
                "kararname_number",
                "genelge_number",
                "teblig_number",
                "regulation_number",
            )
        )
    )
    has_number_hit = bool(expected_numbers & (record_numbers | numeric_tokens(record_text(record))))
    if exact_title_containment(expected_doc, title):
        return True
    if score >= 24.0 and overlap >= 2 and expected_ratio >= 0.45:
        return True
    if overlap >= 3 and expected_ratio >= 0.62:
        return True
    if has_number_hit and overlap >= 2 and expected_ratio >= 0.55 and candidate_ratio >= 0.35:
        return True
    return False


def record_text(record: dict[str, Any]) -> str:
    values = [
        record.get("canonical_title"),
        record.get("canonical_identifier"),
        record.get("canonical_identifier_display"),
        " ".join(record.get("alias_titles") or []),
    ]
    return normalize_canonical_text(" ".join(str(value or "") for value in values))


def score_catalog_record(expected_doc: str, expected_family: str, record: dict[str, Any]) -> float:
    expected_norm = normalize_canonical_text(expected_doc)
    expected_tokens = title_tokens(expected_doc)
    expected_numbers = numeric_tokens(expected_doc)
    text = record_text(record)
    record_tokens = title_tokens(record.get("canonical_title") or "")
    record_numbers = numeric_tokens(
        " ".join(
            str(record.get(key) or "")
            for key in (
                "canonical_identifier",
                "canonical_identifier_display",
                "decision_number",
                "kararname_number",
                "genelge_number",
                "teblig_number",
                "regulation_number",
            )
        )
    )

    score = 0.0
    if expected_norm and expected_norm in text:
        score += 10.0
    if record.get("canonical_title") and normalize_canonical_text(record.get("canonical_title")) in expected_norm:
        score += 8.0
    if expected_numbers:
        hits = len(expected_numbers & (record_numbers | numeric_tokens(text)))
        score += hits * 5.0
    overlap = len(expected_tokens & record_tokens)
    if expected_tokens:
        score += (overlap / max(len(expected_tokens), 1)) * 8.0
        if overlap >= min(3, len(expected_tokens)):
            score += 3.0
    if str(record.get("source_family_canonical") or "") == expected_family:
        score += 2.0
    score -= family_conflict_penalty(expected_doc, record.get("canonical_title") or "")
    return round(max(score, 0.0), 4)


def best_catalog_matches(
    *,
    catalog: dict[str, dict[str, Any]],
    expected_doc: str,
    expected_family: str,
    limit: int = 3,
) -> list[tuple[str, dict[str, Any], float]]:
    matches: list[tuple[str, dict[str, Any], float]] = []
    for source_key, record in catalog.items():
        score = score_catalog_record(expected_doc, expected_family, record)
        if score >= 5.0 and reliable_catalog_match(expected_doc, record, score):
            matches.append((source_key, record, score))
    matches.sort(key=lambda item: (-item[2], item[0]))
    return matches[:limit]


def chunk_title(chunk: dict[str, Any]) -> str:
    return " ".join(
        str(chunk.get(key) or "")
        for key in (
            "source_title",
            "full_title",
            "belge_adi",
            "law_name",
            "canonical_title_family_normalized",
        )
    )


def chunk_matches_expected_doc(chunk: dict[str, Any], expected_doc: str) -> bool:
    title = chunk_title(chunk)
    if not title:
        return False
    if family_conflict_penalty(expected_doc, title) > 0:
        return False
    overlap, expected_ratio, candidate_ratio = title_overlap(expected_doc, title)
    if exact_title_containment(expected_doc, title):
        return True
    if overlap >= 3 and expected_ratio >= 0.62:
        return True
    expected_numbers = numeric_tokens(expected_doc)
    chunk_numbers = numeric_tokens(
        " ".join(
            str(chunk.get(key) or "")
            for key in (
                "source",
                "source_identifier",
                "canonical_identifier_display",
                "law_no",
                "law_short_name",
                "regulation_number",
                "decision_number",
                "kararname_number",
                "genelge_number",
                "teblig_number",
            )
        )
    )
    return bool(expected_numbers & chunk_numbers) and overlap >= 2 and expected_ratio >= 0.55 and candidate_ratio >= 0.35


def chunk_matches_source_key(chunk: dict[str, Any], source_key: str) -> bool:
    source_key = str(source_key or "").strip()
    if not source_key:
        return False
    values = {
        str(chunk.get(key) or "").strip()
        for key in (
            "source",
            "law_no",
            "law_short_name",
            "regulation_number",
            "decision_number",
            "kararname_number",
            "genelge_number",
            "teblig_number",
        )
    }
    return source_key in values


def first_seen_rank_for_match(
    chunks: list[dict[str, Any]],
    *,
    source_key: str,
    expected_doc: str,
) -> int | None:
    for index, chunk in enumerate(chunks, start=1):
        if chunk_matches_source_key(chunk, source_key):
            return index
        if expected_doc and chunk_matches_expected_doc(chunk, expected_doc):
            return index
    return None


def first_seen_rank(chunks: list[dict[str, Any]], gold_documents: str) -> int | None:
    expected_docs = split_documents(gold_documents) or [gold_documents]
    for index, chunk in enumerate(chunks, start=1):
        if any(chunk_matches_expected_doc(chunk, expected_doc) for expected_doc in expected_docs):
            return index
    return None


def make_milvus_client(uri: str) -> Any | None:
    try:
        from pymilvus import MilvusClient

        return MilvusClient(uri=uri)
    except Exception:
        return None


def index_status_for_source(
    *,
    client: Any | None,
    collection: str,
    source_key: str,
    record: dict[str, Any],
) -> str:
    if client is None:
        return "not_checked"
    candidates = [
        source_key,
        str(record.get("canonical_identifier") or ""),
        str(record.get("decision_number") or ""),
        str(record.get("kararname_number") or ""),
        str(record.get("genelge_number") or ""),
        str(record.get("teblig_number") or ""),
        str(record.get("regulation_number") or ""),
    ]
    for value in [candidate.strip() for candidate in candidates if candidate and candidate.strip()]:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        expr = (
            f'metadata["belge_no"] == "{escaped}" || '
            f'metadata["kanun_no"] == "{escaped}" || '
            f'metadata["belge_kisa_adi"] == "{escaped}" || '
            f'metadata["kanun_kisa_adi"] == "{escaped}"'
        )
        try:
            result = client.query(
                collection_name=collection,
                filter=expr,
                limit=1,
                output_fields=["id"],
            )
        except Exception:
            continue
        if result:
            return "index_present"
    return "not_found_in_index"


def classify_visibility(
    *,
    best_match: tuple[str, dict[str, Any], float] | None,
    expected_family: str,
    matched_doc_family: str,
    first_pre_rank: int | None,
    index_status: str,
) -> tuple[str, str, str]:
    if best_match is None or index_status == "not_found_in_index":
        if first_pre_rank is not None:
            return (
                "visible_but_lost_after_retrieval",
                "selector_identity",
                "Source appears in initial candidates, but no reliable catalog/index identity lock was found; inspect trace metadata and selector identity.",
            )
        return (
            "truly_missing_from_index",
            "corpus_ingestion",
            "Acquire or reindex canonical source rows; no reliable catalog/index match was found.",
        )
    source_key, record, _score = best_match
    actual_family = str(record.get("source_family_canonical") or "")
    compatible_regulation_families = {"yonetmelik", "kky", "uy", "cb_yonetmelik"}
    if (
        matched_doc_family
        and matched_doc_family != expected_family
        and not (expected_family in compatible_regulation_families and matched_doc_family == "yonetmelik")
    ):
        target_family = matched_doc_family
    else:
        target_family = expected_family
    matched_doc_is_companion = bool(matched_doc_family and matched_doc_family != expected_family and target_family != expected_family)
    if actual_family and actual_family != target_family:
        return (
            "present_but_family_misclassified",
            "canonical_mapping",
            f"Fix source family mapping for `{source_key}` from `{actual_family}` toward title-inferred `{target_family}` or update benchmark family expectation if audit confirms catalog is correct.",
        )
    if matched_doc_is_companion and first_pre_rank is None:
        return (
            "present_but_not_retrieved",
            "retrieval_routing",
            "Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.",
        )
    if first_pre_rank is None:
        return (
            "present_but_not_retrieved",
            "retrieval_routing",
            "Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.",
        )
    return (
        "visible_but_lost_after_retrieval",
        "selector_identity",
        "Source appears in initial candidates; inspect selector/reranker identity lock and article-span choice.",
    )


def build_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    coverage_rows = [row for row in read_csv(args.coverage_csv) if row.get("primary_owner") == "needs_corpus_acquisition"]
    answer_key = {row["q_id"]: row for row in read_csv(args.answer_key)} if args.answer_key.exists() else {}
    traces = read_jsonl_by_qid(args.run_dir / "trace.jsonl")
    catalog = load_canonical_source_catalog()
    client = None if args.skip_milvus else make_milvus_client(args.milvus_uri)

    rows: list[dict[str, Any]] = []
    for coverage in coverage_rows:
        qid = coverage.get("qid", "")
        expected_family = canonical_family(coverage.get("expected_family", ""))
        gold_documents = answer_key.get(qid, {}).get("gold_documents") or coverage.get("expected_source", "")
        trace = trace_payload(traces.get(qid))
        pre_chunks = chunks_from_trace(trace, "pre_rerank_chunks")
        post_chunks = chunks_from_trace(trace, "post_rerank_chunks")

        expected_docs = split_documents(gold_documents) or [gold_documents]
        best_match: tuple[str, dict[str, Any], float] | None = None
        best_doc = ""
        for expected_doc in expected_docs:
            matches = best_catalog_matches(
                catalog=catalog,
                expected_doc=expected_doc,
                expected_family=expected_family,
            )
            if matches and (best_match is None or matches[0][2] > best_match[2]):
                best_match = matches[0]
                best_doc = expected_doc

        if best_match is not None:
            first_pre = first_seen_rank_for_match(pre_chunks, source_key=best_match[0], expected_doc=best_doc)
            first_post = first_seen_rank_for_match(post_chunks, source_key=best_match[0], expected_doc=best_doc)
        else:
            first_pre = first_seen_rank(pre_chunks, gold_documents)
            first_post = first_seen_rank(post_chunks, gold_documents)
        retrieval_path = (
            f"pre_rerank:{first_pre}"
            if first_pre is not None
            else (f"post_rerank:{first_post}" if first_post is not None else "not_seen_in_run_trace")
        )

        index_status = "not_checked"
        matched_source_key = ""
        matched_title = ""
        matched_family = ""
        matched_score = ""
        if best_match is not None:
            matched_source_key, matched_record, score = best_match
            matched_title = str(matched_record.get("canonical_title") or "")
            matched_family = str(matched_record.get("source_family_canonical") or "")
            matched_score = str(score)
            index_status = index_status_for_source(
                client=client,
                collection=args.milvus_collection,
                source_key=matched_source_key,
                record=matched_record,
            )

        status, owner, resolution_action = classify_visibility(
            best_match=best_match,
            expected_family=expected_family,
            matched_doc_family=infer_doc_family_from_title(best_doc),
            first_pre_rank=first_pre,
            index_status=index_status,
        )
        rows.append(
            {
                "qid": qid,
                "expected_family": coverage.get("expected_family", ""),
                "expected_title": gold_documents,
                "expected_identifier": ", ".join(sorted(numeric_tokens(gold_documents))),
                "visibility_probe_status": status,
                "first_seen_rank": first_pre if first_pre is not None else "",
                "first_seen_post_rank": first_post if first_post is not None else "",
                "retrieval_path": retrieval_path,
                "resolution_action": resolution_action,
                "owner": owner,
                "coverage_status": coverage.get("coverage_status", ""),
                "matched_expected_doc": best_doc,
                "matched_source_key": matched_source_key,
                "matched_title": matched_title,
                "matched_family": matched_family,
                "matched_title_inferred_family": infer_doc_family_from_title(matched_title),
                "matched_expected_doc_inferred_family": infer_doc_family_from_title(best_doc),
                "matched_score": matched_score,
                "milvus_index_status": index_status,
                "gold_seen_pre": coverage.get("gold_seen_pre", ""),
                "gold_seen_post": coverage.get("gold_seen_post", ""),
                "pre_top_sources": coverage.get("pre_top_sources", ""),
                "post_top_sources": coverage.get("post_top_sources", ""),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "qid",
        "expected_family",
        "expected_title",
        "expected_identifier",
        "visibility_probe_status",
        "first_seen_rank",
        "first_seen_post_rank",
        "retrieval_path",
        "resolution_action",
        "owner",
        "coverage_status",
        "matched_expected_doc",
        "matched_source_key",
        "matched_title",
        "matched_family",
        "matched_title_inferred_family",
        "matched_expected_doc_inferred_family",
        "matched_score",
        "milvus_index_status",
        "gold_seen_pre",
        "gold_seen_post",
        "pre_top_sources",
        "post_top_sources",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]], run_dir: Path) -> None:
    status_counts = Counter(row["visibility_probe_status"] for row in rows)
    owner_counts = Counter(row["owner"] for row in rows)
    family_counts = Counter(row["expected_family"] for row in rows)
    index_counts = Counter(row["milvus_index_status"] for row in rows)
    lines = [
        "# Phase 11A Source Visibility / Index Truth Audit",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows_analyzed: {len(rows)}",
        "",
        "## Visibility Probe Status",
    ]
    for status, count in status_counts.most_common():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Owner Counts"])
    for owner, count in owner_counts.most_common():
        lines.append(f"- {owner}: {count}")
    lines.extend(["", "## Milvus Index Status"])
    for status, count in index_counts.most_common():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Expected Family Counts"])
    for family, count in family_counts.most_common():
        lines.append(f"- {family}: {count}")
    lines.extend(["", "## Open Rows"])
    for row in rows:
        lines.append(
            f"- {row['qid']}: status={row['visibility_probe_status']}; expected={row['expected_family']}; "
            f"matched_family={row['matched_family'] or 'none'}; index={row['milvus_index_status']}; "
            f"path={row['retrieval_path']}; owner={row['owner']}; action={row['resolution_action']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "- `truly_missing_from_index`: no reliable canonical catalog/index match was found.",
            "- `present_but_not_retrieved`: source exists in catalog/index but was absent from initial retrieval candidates.",
            "- `present_but_family_misclassified`: source exists, but canonical family does not align with expected family.",
            "- `visible_but_lost_after_retrieval`: source is visible before selection; next owner is selector/identity, not corpus acquisition.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = build_rows(args)
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, rows, args.run_dir)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
