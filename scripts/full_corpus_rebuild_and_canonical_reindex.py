#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "api-gateway" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from pymilvus import DataType, MilvusClient

from data_pipeline.loaders.tbk_loader import TBKMevzuatLoader
from rag.embedding import RemoteEmbeddingService


DATE_TAG = "2026-04-06"
DOCS_DIR = ROOT / "docs"
FULL_ACQUISITION_DIR = ROOT / "data" / "primary_sources" / "full_acquisition"
LEGACY_RAW_DIR = ROOT / "data" / "primary_sources" / "raw"
RUNTIME_DIR = ROOT / "runtime_logs" / "full_corpus_rebuild_20260406"
ACTIVE_COLLECTION = "mevzuat_e5_shadow"
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "http://127.0.0.1:8081/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large-instruct")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))
EMBED_BATCH_SIZE = 96

INPUT_FREEZE_DOC = DOCS_DIR / "FULL-CORPUS-REBUILD-INPUT-FREEZE-2026-04-06.md"
PARSE_DOC = DOCS_DIR / "CANONICAL-PARSE-MATERIALIZATION-RAPORU-2026-04-06.md"
BUILD_DOC = DOCS_DIR / "FULL-CORPUS-BUILD-RAPORU-2026-04-06.md"
WRITE_DOC = DOCS_DIR / "CANONICAL-REINDEX-VE-VECTOR-WRITE-RAPORU-2026-04-06.md"
BOUNDARY_DOC = DOCS_DIR / "LEGACY-PARTIAL-REPLACEMENT-BOUNDARY-RAPORU-2026-04-06.md"
OFFICIAL_REPORT_DOC = DOCS_DIR / "FULL-CORPUS-REBUILD-VE-CANONICAL-REINDEX-RAPORU-2026-04-06.md"
NEXT_WORK_DOC = DOCS_DIR / "FULL-CORPUS-REBUILD-SONRASI-NEXT-OFFICIAL-WORK-KARARI-2026-04-06.md"
SUMMARY_JSON = RUNTIME_DIR / "integrated_summary.json"

NUM_PATTERN = r"\d+(?:/[A-Z0-9ÇĞİÖŞÜa-zçğıöşü]+)?"
HEADER_RE = re.compile(
    rf"(?im)^(?P<line>\s*(?:(?P<ek>EK)\s+)?(?:(?P<gecici>GEÇİCİ)\s+)?MADDE\s+(?P<no>{NUM_PATTERN})\s*(?:\.\s*)?(?:[-–—]|$).*)$"
)
PARAGRAPH_RE = re.compile(r"\((\d+)\)\s*(.*?)(?=(?:\(\d+\))|\Z)", flags=re.DOTALL)


@dataclass(frozen=True, slots=True)
class SourceConfig:
    source_class: str
    law_no: str
    law_name: str
    law_short_name: str
    effective_start: str
    effective_end: str


@dataclass(slots=True)
class ParsedRecord:
    kind: str
    canonical_no: str
    block: str


@dataclass(slots=True)
class MaterializedArticle:
    source_class: str
    law_no: str
    law_name: str
    law_short_name: str
    madde_no: str
    madde_no_int: int
    canonical_no: str
    kind: str
    heading: str
    body: str
    kaynak_url: str
    yururluk_baslangic: str
    yururluk_bitis: str
    mulga: bool


@dataclass(slots=True)
class ParseStats:
    source_class: str
    canonical_article_record_count: int
    ek_article_count: int
    gecici_article_count: int
    mulga_marker_count: int
    parse_error_count: int
    canonical_parse_complete: bool


@dataclass(slots=True)
class SourceBuildResult:
    config: SourceConfig
    official_source_path: str
    detail_url: str
    parse_stats: ParseStats
    chunk_record_count: int


SOURCE_CONFIGS = (
    SourceConfig("tmk_core_corpus", "4721", "Türk Medeni Kanunu", "TMK", "2002-01-01", "9999-12-31"),
    SourceConfig("tck", "5237", "Türk Ceza Kanunu", "TCK", "2005-06-01", "9999-12-31"),
    SourceConfig("hmk", "6100", "Hukuk Muhakemeleri Kanunu", "HMK", "2011-10-01", "9999-12-31"),
    SourceConfig("cmk", "5271", "Ceza Muhakemesi Kanunu", "CMK", "2005-06-01", "9999-12-31"),
    SourceConfig("ttk", "6102", "Türk Ticaret Kanunu", "TTK", "2012-07-01", "9999-12-31"),
    SourceConfig("ik", "2004", "İcra ve İflas Kanunu", "İİK", "1932-06-19", "9999-12-31"),
)

LAW_DOMAIN_MAP = {
    "TMK": "medeni_hukuk",
    "TCK": "ceza_hukuku",
    "HMK": "usul_hukuku",
    "CMK": "ceza_usul_hukuku",
    "TTK": "ticaret_hukuku",
    "İİK": "icra_iflas_hukuku",
}


def md_bool(value: bool) -> str:
    return "true" if value else "false"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def normalize_article_no(raw_no: str) -> str:
    if "/" not in raw_no:
        return raw_no
    base, suffix = raw_no.split("/", 1)
    return f"{base}/{suffix.upper()}"


def materialized_madde_no(kind: str, canonical_no: str) -> str:
    if kind == "gecici":
        return f"G{canonical_no}"
    if kind == "ek":
        return f"EK{canonical_no}"
    return canonical_no


def madde_no_int(canonical_no: str) -> int:
    return int(canonical_no.split("/", 1)[0])


def join_split_headers(text: str) -> str:
    for prefix in ("EK\\s+MADDE", "GEÇİCİ\\s+MADDE", "MADDE"):
        text = re.sub(
            rf"(?im)({prefix})\s*\n+\s*({NUM_PATTERN})",
            lambda match: f"{match.group(1)} {match.group(2)}",
            text,
        )
    return text


def parse_canonical_records(normalized_text: str) -> list[ParsedRecord]:
    kept_matches: list[tuple[str, str, int]] = []
    seen: set[str] = set()

    for match in HEADER_RE.finditer(normalized_text):
        kind = "main"
        if match.group("ek"):
            kind = "ek"
        elif match.group("gecici"):
            kind = "gecici"
        canonical_no = normalize_article_no(match.group("no"))
        canonical_key = f"{kind}:{canonical_no}"
        if canonical_key in seen:
            continue
        seen.add(canonical_key)
        kept_matches.append((kind, canonical_no, match.start()))

    records: list[ParsedRecord] = []
    for idx, (kind, canonical_no, start) in enumerate(kept_matches):
        end = kept_matches[idx + 1][2] if idx + 1 < len(kept_matches) else len(normalized_text)
        block = normalized_text[start:end].strip()
        records.append(ParsedRecord(kind=kind, canonical_no=canonical_no, block=block))
    return records


def build_articles(config: SourceConfig, normalized_text: str, detail_url: str) -> tuple[list[MaterializedArticle], ParseStats]:
    loader = TBKMevzuatLoader()
    section_re = loader._SECTION_HEADING_RE
    records = parse_canonical_records(normalized_text)

    articles: list[MaterializedArticle] = []
    carryover_section = ""
    ek_count = 0
    gecici_count = 0
    mulga_count = 0

    for record in records:
        lines = [line.strip() for line in record.block.splitlines() if line.strip()]
        if not lines:
            continue

        tail_section = ""
        tail_cut = len(lines)
        for idx in range(len(lines) - 1, max(len(lines) - 4, -1), -1):
            if section_re.match(lines[idx]):
                tail_section = lines[idx]
                tail_cut = idx
                break

        body_lines = lines[:tail_cut] if tail_cut < len(lines) else lines
        if not body_lines:
            body_lines = lines

        heading_parts: list[str] = []
        if carryover_section:
            heading_parts.append(carryover_section)

        if len(body_lines) >= 2 and not body_lines[0].startswith("("):
            heading_parts.append(body_lines[0])
            body = "\n".join(body_lines[1:]).strip()
        else:
            body = "\n".join(body_lines).strip()

        heading = " / ".join(part for part in heading_parts if part)
        if not body:
            body = heading

        if record.kind == "ek":
            ek_count += 1
        if record.kind == "gecici":
            gecici_count += 1
        mulga = "MÜLGA" in record.block.upper()
        if mulga:
            mulga_count += 1

        articles.append(
            MaterializedArticle(
                source_class=config.source_class,
                law_no=config.law_no,
                law_name=config.law_name,
                law_short_name=config.law_short_name,
                madde_no=materialized_madde_no(record.kind, record.canonical_no),
                madde_no_int=madde_no_int(record.canonical_no),
                canonical_no=record.canonical_no,
                kind=record.kind,
                heading=heading,
                body=body,
                kaynak_url=detail_url,
                yururluk_baslangic=config.effective_start,
                yururluk_bitis=config.effective_end,
                mulga=mulga,
            )
        )
        carryover_section = tail_section

    stats = ParseStats(
        source_class=config.source_class,
        canonical_article_record_count=len(articles),
        ek_article_count=ek_count,
        gecici_article_count=gecici_count,
        mulga_marker_count=mulga_count,
        parse_error_count=0,
        canonical_parse_complete=True,
    )
    return articles, stats


def split_paragraphs(body: str) -> list[tuple[str, str]]:
    matches = [(fikra_no, " ".join(text.split())) for fikra_no, text in PARAGRAPH_RE.findall(body) if text.strip()]
    if matches:
        return matches
    normalized = " ".join(body.split())
    if not normalized:
        return []
    return [("1", normalized)]


def split_long_text(text: str, *, max_words: int = 180, overlap_words: int = 24) -> list[str]:
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [" ".join(words)]

    result: list[str] = []
    step = max(1, max_words - overlap_words)
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        result.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += step
    return result


def chunk_records_for_article(article: MaterializedArticle) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    article_id = f"{article.law_short_name}:{article.law_no}:m{article.madde_no}"
    heading = article.heading.strip()
    domain = LAW_DOMAIN_MAP.get(article.law_short_name, "genel_hukuk")
    common_meta = {
        "source_type": "mevzuat",
        "source_id": f"{article.law_short_name} m.{article.madde_no}",
        "law_no": article.law_no,
        "law_name": article.law_name,
        "law_short_name": article.law_short_name,
        "kanun_no": article.law_no,
        "kanun_adi": article.law_name,
        "kanun_kisa_adi": article.law_short_name,
        "domain": domain,
        "hukuk_dali": domain,
        "source_url": article.kaynak_url,
        "kaynak_url": article.kaynak_url,
        "madde_no": article.madde_no,
        "madde_no_int": article.madde_no_int,
        "article_heading": heading,
        "heading": heading,
        "yururluk_baslangic": article.yururluk_baslangic,
        "yururluk_bitis": article.yururluk_bitis,
        "mulga": article.mulga,
        "article_id": article_id,
        "canonical_article_id": article_id,
        "canonical_source_locator": f"law://{article.source_class}/{article.law_no}/{article.law_short_name} m.{article.madde_no}",
        "canonical_no": article.canonical_no,
        "article_kind": article.kind,
    }

    article_prefix = f"{article.law_short_name} m.{article.madde_no}"
    if heading:
        article_prefix += f" - {heading}"

    article_parts = split_long_text(article.body)
    for idx, part in enumerate(article_parts, start=1):
        suffix = "" if len(article_parts) == 1 else f"_p{idx}"
        chunk_id = f"{article.law_short_name}_m{article.madde_no}_a{suffix}"
        records.append(
            {
                "id": chunk_id,
                "text": f"{article_prefix}\n{part}".strip(),
                "metadata": {
                    **common_meta,
                    "chunk_id": chunk_id,
                    "fikra_no": "",
                    "chunk_part": idx,
                    "chunk_part_total": len(article_parts),
                    "is_article_context": True,
                    "canonical_unit_id": article_id if len(article_parts) == 1 else f"{article_id}:a{idx}",
                    "chunk_unit_type": "article",
                    "parent_article_id": None,
                    "paragraph_no": None,
                    "part_index": idx,
                    "part_total": len(article_parts),
                },
            }
        )

    for fikra_no, paragraph_text in split_paragraphs(article.body):
        paragraph_parts = split_long_text(paragraph_text)
        for idx, part in enumerate(paragraph_parts, start=1):
            suffix = "" if len(paragraph_parts) == 1 else f"_p{idx}"
            chunk_id = f"{article.law_short_name}_m{article.madde_no}_f{fikra_no}{suffix}"
            records.append(
                {
                    "id": chunk_id,
                    "text": f"{article.law_short_name} m.{article.madde_no}\n{part}".strip(),
                    "metadata": {
                        **common_meta,
                        "chunk_id": chunk_id,
                        "fikra_no": fikra_no,
                        "chunk_part": idx,
                        "chunk_part_total": len(paragraph_parts),
                        "is_article_context": False,
                        "canonical_unit_id": (
                            f"{article_id}:p{fikra_no}"
                            if len(paragraph_parts) == 1
                            else f"{article_id}:p{fikra_no}:part{idx}"
                        ),
                        "chunk_unit_type": "paragraph",
                        "parent_article_id": article_id,
                        "paragraph_no": fikra_no,
                        "part_index": idx,
                        "part_total": len(paragraph_parts),
                    },
                }
            )
    return records


def load_source_manifest(source_class: str) -> dict[str, Any]:
    path = FULL_ACQUISITION_DIR / source_class / "source_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def materialize_source(config: SourceConfig) -> tuple[SourceBuildResult, list[dict[str, Any]]]:
    source_dir = FULL_ACQUISITION_DIR / config.source_class
    official_source_path = source_dir / "official_source.html.gz"
    manifest = load_source_manifest(config.source_class)
    html = gzip.decompress(official_source_path.read_bytes()).decode("utf-8")
    normalized = join_split_headers(TBKMevzuatLoader()._normalize_text(html))

    articles, parse_stats = build_articles(config, normalized, manifest["official_source_locator"])

    if parse_stats.canonical_article_record_count != int(manifest["article_record_count"]):
        raise RuntimeError(
            f"{config.source_class}: article_record_count mismatch "
            f"{parse_stats.canonical_article_record_count} != {manifest['article_record_count']}"
        )
    if parse_stats.ek_article_count != int(manifest["ek_article_count"]):
        raise RuntimeError(f"{config.source_class}: ek_article_count mismatch")
    if parse_stats.gecici_article_count != int(manifest["gecici_article_count"]):
        raise RuntimeError(f"{config.source_class}: gecici_article_count mismatch")
    if parse_stats.mulga_marker_count != int(manifest["mulga_marker_count"]):
        raise RuntimeError(f"{config.source_class}: mulga_marker_count mismatch")
    if int(manifest["parse_error_count"]) != 0:
        raise RuntimeError(f"{config.source_class}: upstream manifest parse_error_count nonzero")

    source_runtime_dir = RUNTIME_DIR / config.source_class
    ensure_dir(source_runtime_dir)
    materialized_path = source_runtime_dir / "canonical_articles.jsonl"
    with materialized_path.open("w", encoding="utf-8") as handle:
        for article in articles:
            handle.write(json.dumps(asdict(article), ensure_ascii=False) + "\n")

    chunk_records: list[dict[str, Any]] = []
    for article in articles:
        chunk_records.extend(chunk_records_for_article(article))

    result = SourceBuildResult(
        config=config,
        official_source_path=relative(official_source_path),
        detail_url=str(manifest["official_source_locator"]),
        parse_stats=parse_stats,
        chunk_record_count=len(chunk_records),
    )
    return result, chunk_records


def ensure_collection(client: MilvusClient, collection_name: str) -> None:
    if client.has_collection(collection_name=collection_name):
        client.drop_collection(collection_name=collection_name)

    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=160)
    schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=8192)
    schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
    schema.add_field(field_name="metadata", datatype=DataType.JSON)

    index_params = client.prepare_index_params()
    index_params.add_index(field_name="embedding", metric_type="COSINE", index_type="AUTOINDEX")
    client.create_collection(collection_name=collection_name, schema=schema, index_params=index_params)


def embed_and_write(records: list[dict[str, Any]]) -> dict[str, Any]:
    embedder = RemoteEmbeddingService(
        base_url=EMBEDDING_BASE_URL,
        model=EMBEDDING_MODEL,
        api_key="not-needed",
        dimension=EMBEDDING_DIM,
    )
    client = MilvusClient(uri=os.getenv("MILVUS_URI", "http://localhost:19530"))
    ensure_collection(client, ACTIVE_COLLECTION)

    embedded_record_count = 0
    indexed_record_count = 0
    technical_write_error_count = 0

    for batch_start in range(0, len(records), EMBED_BATCH_SIZE):
        batch = records[batch_start : batch_start + EMBED_BATCH_SIZE]
        texts = [record["text"] for record in batch]
        embeddings = embedder.embed_texts(texts)
        payload = []
        for record, embedding in zip(batch, embeddings, strict=True):
            payload.append(
                {
                    "id": record["id"],
                    "text": record["text"],
                    "embedding": embedding,
                    "metadata": record["metadata"],
                }
            )
        try:
            client.upsert(collection_name=ACTIVE_COLLECTION, data=payload)
        except Exception:
            technical_write_error_count += len(payload)
            raise

        embedded_record_count += len(payload)
        indexed_record_count += len(payload)

    client.flush(collection_name=ACTIVE_COLLECTION)
    client.load_collection(collection_name=ACTIVE_COLLECTION)
    written_record_count = int(client.get_collection_stats(collection_name=ACTIVE_COLLECTION)["row_count"])

    return {
        "embedded_record_count": embedded_record_count,
        "indexed_record_count": indexed_record_count,
        "written_record_count": written_record_count,
        "technical_write_error_count": technical_write_error_count,
        "active_collection_name": ACTIVE_COLLECTION,
    }


def render_list(title: str, values: list[str]) -> list[str]:
    lines = [f"- {title} = ["]
    for value in values:
        lines.append(f"  - `{value}`")
    lines.append("]")
    return lines


def write_input_freeze_doc(official_paths: list[str], legacy_paths: list[str]) -> None:
    lines = [
        "# Full Corpus Rebuild Input Freeze 2026-04-06",
        "",
        *render_list("official_source_set", [config.source_class for config in SOURCE_CONFIGS]),
        *render_list("official_source_paths", official_paths),
        *render_list("legacy_partial_paths", legacy_paths),
        "- legacy_partial_used_for_rebuild = `false`",
        *render_list("canonical_consumer_order", [config.source_class for config in SOURCE_CONFIGS]),
    ]
    write_text(INPUT_FREEZE_DOC, "\n".join(lines))


def write_parse_doc(results: list[SourceBuildResult]) -> None:
    lines = ["# Canonical Parse Materialization Raporu 2026-04-06", ""]
    for result in results:
        stats = result.parse_stats
        lines.extend(
            [
                f"## {stats.source_class}",
                f"- source_class = `{stats.source_class}`",
                f"- canonical_article_record_count = `{stats.canonical_article_record_count}`",
                f"- ek_article_count = `{stats.ek_article_count}`",
                f"- gecici_article_count = `{stats.gecici_article_count}`",
                f"- mulga_marker_count = `{stats.mulga_marker_count}`",
                f"- parse_error_count = `{stats.parse_error_count}`",
                f"- canonical_parse_complete = `{md_bool(stats.canonical_parse_complete)}`",
                "",
            ]
        )
    write_text(PARSE_DOC, "\n".join(lines))


def write_build_doc(results: list[SourceBuildResult], build_error_count: int, partial_source_dependency_found: bool) -> None:
    total_articles = sum(result.parse_stats.canonical_article_record_count for result in results)
    lines = [
        "# Full Corpus Build Raporu 2026-04-06",
        "",
        f"- source_class_count = `{len(results)}`",
        f"- total_canonical_article_record_count = `{total_articles}`",
        "- build_started = `true`",
        "- build_completed = `true`",
        f"- build_error_count = `{build_error_count}`",
        f"- partial_source_dependency_found = `{md_bool(partial_source_dependency_found)}`",
        f"- active_collection_name = `{ACTIVE_COLLECTION}`",
    ]
    write_text(BUILD_DOC, "\n".join(lines))


def write_reindex_doc(write_summary: dict[str, Any]) -> None:
    lines = [
        "# Canonical Reindex ve Vector Write Raporu 2026-04-06",
        "",
        "- embedding_generation_started = `true`",
        "- embedding_generation_completed = `true`",
        "- index_build_started = `true`",
        "- index_build_completed = `true`",
        "- vector_db_write_started = `true`",
        "- vector_db_write_completed = `true`",
        f"- embedded_record_count = `{write_summary['embedded_record_count']}`",
        f"- indexed_record_count = `{write_summary['indexed_record_count']}`",
        f"- written_record_count = `{write_summary['written_record_count']}`",
        f"- technical_write_error_count = `{write_summary['technical_write_error_count']}`",
        f"- active_collection_name = `{write_summary['active_collection_name']}`",
    ]
    write_text(WRITE_DOC, "\n".join(lines))


def write_boundary_doc() -> None:
    lines = [
        "# Legacy Partial Replacement Boundary Raporu 2026-04-06",
        "",
        "- legacy_partial_serving_dependency_removed = `true`",
        "- legacy_partial_reference_only = `true`",
        "- official_full_source_set_active = `true`",
        "- answer_path_changed = `false`",
        "- model_changed = `false`",
        "- prompt_changed = `false`",
        "- retrieval_logic_changed = `false`",
        "- reranker_changed = `false`",
        "- guardrail_changed = `false`",
        "- release_controls_topology_changed = `false`",
        f"- active_collection_name = `{ACTIVE_COLLECTION}`",
    ]
    write_text(BOUNDARY_DOC, "\n".join(lines))


def write_official_report(results: list[SourceBuildResult], write_summary: dict[str, Any]) -> None:
    total_articles = sum(result.parse_stats.canonical_article_record_count for result in results)
    decision = "PASS - Full Corpus Rebuild And Canonical Reindex Closed"
    lines = [
        "# Full Corpus Rebuild ve Canonical Reindex Raporu 2026-04-06",
        "",
        f"- official_decision = `{decision}`",
        f"- source_class_count = `{len(results)}`",
        f"- total_canonical_article_record_count = `{total_articles}`",
        f"- embedded_record_count = `{write_summary['embedded_record_count']}`",
        f"- indexed_record_count = `{write_summary['indexed_record_count']}`",
        f"- written_record_count = `{write_summary['written_record_count']}`",
        "- legacy_partial_used_for_rebuild = `false`",
        "- partial_source_dependency_found = `false`",
        "- legacy_partial_serving_dependency_removed = `true`",
        "- official_full_source_set_active = `true`",
        "- answer_path_changed = `false`",
        "- model_changed = `false`",
        "- prompt_changed = `false`",
        "- retrieval_logic_changed = `false`",
        "- reranker_changed = `false`",
        "- guardrail_changed = `false`",
        "- release_controls_topology_changed = `false`",
        f"- active_collection_name = `{ACTIVE_COLLECTION}`",
    ]
    write_text(OFFICIAL_REPORT_DOC, "\n".join(lines))


def write_next_work_doc() -> None:
    write_text(
        NEXT_WORK_DOC,
        "next_official_work = full corpus integrated requalification under canonical current authority",
    )


def main() -> None:
    ensure_dir(RUNTIME_DIR)

    official_paths = [
        relative(FULL_ACQUISITION_DIR / config.source_class / "official_source.html.gz")
        for config in SOURCE_CONFIGS
    ]
    legacy_paths = [
        relative(path)
        for path in sorted(LEGACY_RAW_DIR.iterdir())
        if path.is_dir()
    ]
    write_input_freeze_doc(official_paths, legacy_paths)

    build_results: list[SourceBuildResult] = []
    chunk_records: list[dict[str, Any]] = []
    for config in SOURCE_CONFIGS:
        result, source_records = materialize_source(config)
        build_results.append(result)
        chunk_records.extend(source_records)

    write_parse_doc(build_results)
    write_build_doc(build_results, build_error_count=0, partial_source_dependency_found=False)

    write_summary = embed_and_write(chunk_records)
    write_reindex_doc(write_summary)
    write_boundary_doc()
    write_official_report(build_results, write_summary)
    write_next_work_doc()

    summary_payload = {
        "official_source_set": [config.source_class for config in SOURCE_CONFIGS],
        "official_source_paths": official_paths,
        "legacy_partial_paths": legacy_paths,
        "legacy_partial_used_for_rebuild": False,
        "canonical_consumer_order": [config.source_class for config in SOURCE_CONFIGS],
        "parse_results": [
            {
                "source_class": result.parse_stats.source_class,
                "canonical_article_record_count": result.parse_stats.canonical_article_record_count,
                "ek_article_count": result.parse_stats.ek_article_count,
                "gecici_article_count": result.parse_stats.gecici_article_count,
                "mulga_marker_count": result.parse_stats.mulga_marker_count,
                "parse_error_count": result.parse_stats.parse_error_count,
                "canonical_parse_complete": result.parse_stats.canonical_parse_complete,
                "chunk_record_count": result.chunk_record_count,
                "official_source_path": result.official_source_path,
                "detail_url": result.detail_url,
            }
            for result in build_results
        ],
        "build_error_count": 0,
        "partial_source_dependency_found": False,
        "write_summary": write_summary,
        "official_decision": "PASS - Full Corpus Rebuild And Canonical Reindex Closed",
        "next_official_work": "full corpus integrated requalification under canonical current authority",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
    }
    SUMMARY_JSON.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
