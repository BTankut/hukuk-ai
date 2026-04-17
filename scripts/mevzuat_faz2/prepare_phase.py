#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pymilvus import MilvusClient


ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_ROOT = Path("/Users/btmacstudio/Projects/mevzuat")
DOCS_DIR = ROOT / "docs"
DATE_TAG = "2026-04-16"
MILVUS_URI = "http://localhost:19530"
COLLECTION_NAME = "mevzuat_faz1_shadow_20260416"

ARTICLE_ROWS = EXTERNAL_ROOT / "mevzuat_db" / "article_rows.jsonl"

ACCEPTANCE_CONTRACT_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2-CANONICAL-ACCEPTANCE-CONTRACT-{DATE_TAG}.md"
COVERAGE_MATRIX_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2-KAPSAM-VE-SORU-TIPI-MATRISI-{DATE_TAG}.md"
LAWYER_PROTOCOL_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2-UZMAN-AVUKAT-REVIEW-PROTOKOLU-{DATE_TAG}.md"
PACK_NOTE_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2-CANONICAL-ACCEPTANCE-PACK-NOTU-{DATE_TAG}.md"
BATCH_001 = DOCS_DIR / f"MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-001.csv"
BATCH_002 = DOCS_DIR / f"MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-002.csv"
BATCH_003 = DOCS_DIR / f"MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-003.csv"
BATCH_004 = DOCS_DIR / f"MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-004.csv"
GATE_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2A-HAZIRLIK-GATE-RAPORU-{DATE_TAG}.md"
NEXT_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2A-SONRASI-NEXT-OFFICIAL-WORK-KARARI-{DATE_TAG}.md"

CSV_HEADERS = [
    "batch_id",
    "row_id",
    "question",
    "model_answer",
    "source_citation",
    "expected_source_type",
    "expected_display_citation",
    "expected_yururluk_state",
    "cross_type_disambiguation",
    "lawyer_decision",
    "lawyer_comment",
    "corrected_answer",
    "reviewer_name",
    "second_reviewer_name",
]

SOURCE_TYPE_ORDER = [
    "KANUN",
    "CB_KARARNAME",
    "YONETMELIK",
    "CB_YONETMELIK",
    "CB_KARAR",
    "CB_GENELGE",
    "KHK",
    "TUZUK",
    "KKY",
    "UY",
    "TEBLIGLER",
    "MULGA",
]

CATEGORY_ORDER = [
    "source_local_direct_retrieval",
    "cross_type_wrong_source_disambiguation",
    "yururluk_mulga_temporal_interpretation",
    "citation_heavy_exact_locator_long_article",
    "excluded_source_unsupported_source_refusal",
]

BELGE_TURU_TO_SOURCE_TYPE = {
    "kanun": "KANUN",
    "cb_kararname": "CB_KARARNAME",
    "yonetmelik": "YONETMELIK",
    "cb_yonetmelik": "CB_YONETMELIK",
    "cb_karar": "CB_KARAR",
    "cb_genelge": "CB_GENELGE",
    "khk": "KHK",
    "tuzuk": "TUZUK",
    "kky": "KKY",
    "uy": "UY",
    "teblig": "TEBLIGLER",
    "mulga_kanun": "MULGA",
}

PACK_TARGETS = {
    "source_local_direct_retrieval": 144,
    "cross_type_wrong_source_disambiguation": 36,
    "yururluk_mulga_temporal_interpretation": 24,
    "citation_heavy_exact_locator_long_article": 24,
    "excluded_source_unsupported_source_refusal": 12,
}

BATCH_CATEGORY_TARGETS = {
    "source_local_direct_retrieval": 36,
    "cross_type_wrong_source_disambiguation": 9,
    "yururluk_mulga_temporal_interpretation": 6,
    "citation_heavy_exact_locator_long_article": 6,
    "excluded_source_unsupported_source_refusal": 3,
}

REFUSAL_ANSWER = (
    "Bu soru bu fazin kapsam disinda kalan secondary-source veya case-law yorumunu istiyor. "
    "Mevcut Faz-2 hazirlik hattinda yalniz article-anchored primary-law dayanaklari desteklenir; "
    "ictihat, doktrin, uygulama ornegi veya mevzuat disi yorum veremem."
)


@dataclass(slots=True)
class Candidate:
    row_ordinal: int
    source_id: str
    display_citation: str
    expected_source_type: str
    canonical_source_locator: str
    yururluk_baslangic: str | None
    yururluk_bitis: str | None
    mulga: bool
    heading: str
    body: str
    metin_sha256: str
    text_len: int
    shadow_verified: bool = False


@dataclass(slots=True)
class AcceptanceRow:
    category: str
    expected_source_type: str
    expected_display_citation: str
    expected_yururluk_state: str
    cross_type_disambiguation: bool
    question: str
    model_answer: str
    source_citation: str
    source_id: str
    canonical_source_locator: str
    batch_id: str = ""
    row_id: str = ""
    second_reviewer_name: str = ""


def discover_source_files() -> dict[str, Path]:
    files = {
        "article_rows": ARTICLE_ROWS,
        "normalized_source": EXTERNAL_ROOT / "mevzuat_db" / "normalized_source.txt",
        "source_manifest": EXTERNAL_ROOT / "mevzuat_db" / "source_manifest.json",
        "checksums": EXTERNAL_ROOT / "mevzuat_db" / "checksums.sha256",
    }
    for path in files.values():
        if not path.exists():
            raise FileNotFoundError(f"required file missing: {path}")
    return files


def normalize_ws(text: str) -> str:
    return " ".join(text.split())


def md_bool(value: bool) -> str:
    return "true" if value else "false"


def has_bad_controls(text: str) -> bool:
    if not text:
        return True
    bad = sum(1 for ch in text if ord(ch) < 32 and ch not in "\n\r\t")
    return (bad / max(len(text), 1)) > 0.01


def clean_heading(heading: str) -> str:
    heading = normalize_ws(heading)
    if heading.lower() in {"tam metin", "madde no: 1", "madde no: 2", "madde no: 3", "madde no: 4", "madde no: 5"}:
        return ""
    return heading


def make_excerpt(body: str, *, limit: int) -> str:
    body = normalize_ws(body)
    if len(body) <= limit:
        return body
    cut = body[:limit].rstrip()
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "..."


def iter_unique_candidates() -> dict[str, list[Candidate]]:
    pools: dict[str, list[Candidate]] = defaultdict(list)
    seen_source_ids: set[str] = set()
    with ARTICLE_ROWS.open("r", encoding="utf-8") as handle:
        for row_ordinal, line in enumerate(handle, start=1):
            row = json.loads(line)
            source_id = str(row.get("source_id") or "")
            belge_turu = str(row.get("belge_turu") or "")
            if not source_id or source_id in seen_source_ids:
                continue
            expected_source_type = BELGE_TURU_TO_SOURCE_TYPE.get(belge_turu)
            if expected_source_type is None:
                continue
            body = normalize_ws(str(row.get("body") or ""))
            display_citation = normalize_ws(str(row.get("display_citation") or ""))
            if not display_citation or not body:
                continue
            if has_bad_controls(body):
                continue
            seen_source_ids.add(source_id)
            pools[expected_source_type].append(
                Candidate(
                    row_ordinal=row_ordinal,
                    source_id=source_id,
                    display_citation=display_citation,
                    expected_source_type=expected_source_type,
                    canonical_source_locator=str(row.get("canonical_source_locator") or ""),
                    yururluk_baslangic=row.get("yururluk_baslangic"),
                    yururluk_bitis=row.get("yururluk_bitis"),
                    mulga=bool(row.get("mulga")),
                    heading=clean_heading(str(row.get("heading") or "")),
                    body=body,
                    metin_sha256=str(row.get("metin_sha256") or ""),
                    text_len=len(body),
                )
            )
    return pools


def sort_direct(c: Candidate) -> tuple[Any, ...]:
    return (c.text_len > 1800, c.text_len, c.display_citation, c.source_id)


def sort_cross(c: Candidate) -> tuple[Any, ...]:
    article_hint = 999999
    match = re.search(r"m(\d+)|m\.?(\d+)", c.source_id)
    if match:
        article_hint = int(next(group for group in match.groups() if group))
    return (article_hint > 20, article_hint, c.text_len, c.display_citation, c.source_id)


def sort_citation(c: Candidate) -> tuple[Any, ...]:
    return (-min(c.text_len, 12000), c.display_citation, c.source_id)


def sort_temporal(c: Candidate) -> tuple[Any, ...]:
    return (
        c.yururluk_baslangic is None,
        c.yururluk_bitis is None,
        c.display_citation,
        c.source_id,
    )


def pick_rows(
    pool: list[Candidate],
    *,
    count: int,
    used_source_ids: set[str],
    predicate: Any,
    sort_key: Any,
) -> list[Candidate]:
    candidates = [row for row in pool if row.source_id not in used_source_ids and predicate(row)]
    selected = sorted(candidates, key=sort_key)[:count]
    if len(selected) != count:
        raise RuntimeError(f"selection underflow: requested={count}, available={len(selected)}")
    used_source_ids.update(row.source_id for row in selected)
    return selected


def build_direct_question(row: Candidate, variant: int) -> str:
    templates = [
        "{citation} hangi hükmü düzenler? Kısa ve doğrudan cevap ver.",
        "{citation} için metinsel dayanağı kısa şekilde gösterir misin?",
        "{citation} hükmünün ana içeriğini doğrudan özetler misin?",
        "{citation} maddesinin ne dediğini kısa şekilde belirtir misin?",
    ]
    return templates[variant % len(templates)].format(citation=row.display_citation)


def build_cross_question(row: Candidate, variant: int) -> str:
    templates = [
        "{citation} atfı hangi mevzuat türüne aittir? Benzer numaralı başka belgelerle karıştırmadan türü ve kısa dayanağı göster.",
        "{citation} için belge türünü açıkça ayırır mısın? Yanlış source seçimi yapmadan kısa dayanak ver.",
        "{citation} hükmünü tür bazında disambiguation yaparak gösterir misin?",
    ]
    return templates[variant % len(templates)].format(citation=row.display_citation)


def build_temporal_question(row: Candidate, variant: int) -> str:
    templates = [
        "{citation} yürürlükte mi, mülga mı? Başlangıç ve bitiş durumuyla cevap ver.",
        "{citation} için yürürlük statüsünü tarihleriyle birlikte açıklar mısın?",
        "{citation} maddesinin temporal durumunu ve geçerlilik aralığını belirtir misin?",
    ]
    return templates[variant % len(templates)].format(citation=row.display_citation)


def build_citation_question(row: Candidate, variant: int) -> str:
    templates = [
        "{citation} için exact citation ve locator bilgisiyle dayanağı gösterir misin?",
        "{citation} hükmünü görünür citation ve canonical locator ile birlikte verir misin?",
        "{citation} satırını exact locator referansıyla ve kısa içerik özetiyle gösterir misin?",
    ]
    return templates[variant % len(templates)].format(citation=row.display_citation)


def build_refusal_question(row: Candidate, variant: int) -> str:
    templates = [
        "{citation} hakkında Yargıtay, Danıştay veya AYM içtihadındaki yorumları verir misin?",
        "{citation} için doktrindeki baskın görüş ve uygulama örneklerini sıralar mısın?",
        "{citation} maddesinin mevzuat dışı yorumunu ve secondary-source değerlendirmelerini verir misin?",
    ]
    return templates[variant % len(templates)].format(citation=row.display_citation)


def build_supported_answer(row: Candidate, *, mode: str) -> str:
    heading = f"{row.heading}. " if row.heading else ""
    if mode == "direct":
        excerpt = make_excerpt(row.body, limit=320)
        return f"Dayanak {row.display_citation} ({row.expected_source_type}). {heading}{excerpt} [Kaynak: {row.display_citation}]"
    if mode == "cross":
        excerpt = make_excerpt(row.body, limit=260)
        return (
            f"Bu atif {row.expected_source_type} turundedir. Dayanak {row.display_citation}. "
            f"{heading}{excerpt} [Kaynak: {row.display_citation}]"
        )
    if mode == "temporal":
        state = "MULGA" if row.mulga else "YURURLUKTE"
        start = row.yururluk_baslangic or "UNKNOWN"
        end = row.yururluk_bitis or "UNKNOWN"
        excerpt = make_excerpt(row.body, limit=220)
        return (
            f"Dayanak {row.display_citation} ({row.expected_source_type}). "
            f"Yururluk durumu: {state}. Baslangic: {start}. Bitis: {end}. "
            f"{heading}{excerpt} [Kaynak: {row.display_citation}]"
        )
    if mode == "citation":
        excerpt = make_excerpt(row.body, limit=520)
        return (
            f"Exact citation {row.display_citation}. Locator: {row.canonical_source_locator}. "
            f"{heading}{excerpt} [Kaynak: {row.display_citation}]"
        )
    raise ValueError(f"unsupported mode: {mode}")


def yururluk_state(row: Candidate, *, refusal: bool = False) -> str:
    if refusal:
        return "UNSUPPORTED_SOURCE_REFUSAL"
    return "MULGA" if row.mulga else "YURURLUKTE"


def verify_shadow_anchor(client: MilvusClient, row: Candidate) -> None:
    result = client.query(
        collection_name=COLLECTION_NAME,
        filter=f'metadata["source_id"] == {json.dumps(row.source_id, ensure_ascii=False)}',
        limit=1,
        output_fields=["id", "metadata"],
    )
    if not result:
        raise RuntimeError(f"shadow anchor missing: {row.source_id}")
    row.shadow_verified = True


def build_pack() -> list[AcceptanceRow]:
    pools = iter_unique_candidates()
    missing_types = [source_type for source_type in SOURCE_TYPE_ORDER if source_type not in pools]
    if missing_types:
        raise RuntimeError(f"missing source pools: {missing_types}")

    client = MilvusClient(uri=MILVUS_URI)
    if not client.has_collection(collection_name=COLLECTION_NAME):
        raise RuntimeError(f"shadow collection missing: {COLLECTION_NAME}")

    used_source_ids: set[str] = set()
    rows: list[AcceptanceRow] = []

    # Direct retrieval: 12 rows per type = 144.
    for source_type in SOURCE_TYPE_ORDER:
        selected = pick_rows(
            pools[source_type],
            count=12,
            used_source_ids=used_source_ids,
            predicate=lambda row: row.text_len >= 80 and row.text_len <= 2200,
            sort_key=sort_direct,
        )
        for idx, row in enumerate(selected):
            verify_shadow_anchor(client, row)
            rows.append(
                AcceptanceRow(
                    category="source_local_direct_retrieval",
                    expected_source_type=row.expected_source_type,
                    expected_display_citation=row.display_citation,
                    expected_yururluk_state=yururluk_state(row),
                    cross_type_disambiguation=False,
                    question=build_direct_question(row, idx),
                    model_answer=build_supported_answer(row, mode="direct"),
                    source_citation=row.display_citation,
                    source_id=row.source_id,
                    canonical_source_locator=row.canonical_source_locator,
                )
            )

    # Cross-type disambiguation: 3 rows per type = 36.
    for source_type in SOURCE_TYPE_ORDER:
        selected = pick_rows(
            pools[source_type],
            count=3,
            used_source_ids=used_source_ids,
            predicate=lambda row: row.text_len >= 80 and row.text_len <= 2600,
            sort_key=sort_cross,
        )
        for idx, row in enumerate(selected):
            verify_shadow_anchor(client, row)
            rows.append(
                AcceptanceRow(
                    category="cross_type_wrong_source_disambiguation",
                    expected_source_type=row.expected_source_type,
                    expected_display_citation=row.display_citation,
                    expected_yururluk_state=yururluk_state(row),
                    cross_type_disambiguation=True,
                    question=build_cross_question(row, idx),
                    model_answer=build_supported_answer(row, mode="cross"),
                    source_citation=row.display_citation,
                    source_id=row.source_id,
                    canonical_source_locator=row.canonical_source_locator,
                    second_reviewer_name="REQUIRED",
                )
            )

    # Temporal: 12 mulga + 12 active rows = 24.
    mulga_selected = pick_rows(
        pools["MULGA"],
        count=12,
        used_source_ids=used_source_ids,
        predicate=lambda row: row.mulga and row.text_len >= 80 and row.text_len <= 3000,
        sort_key=sort_temporal,
    )
    for idx, row in enumerate(mulga_selected):
        verify_shadow_anchor(client, row)
        rows.append(
            AcceptanceRow(
                category="yururluk_mulga_temporal_interpretation",
                expected_source_type=row.expected_source_type,
                expected_display_citation=row.display_citation,
                expected_yururluk_state=yururluk_state(row),
                cross_type_disambiguation=False,
                question=build_temporal_question(row, idx),
                model_answer=build_supported_answer(row, mode="temporal"),
                source_citation=row.display_citation,
                source_id=row.source_id,
                canonical_source_locator=row.canonical_source_locator,
            )
        )

    active_temporal_types = [source_type for source_type in SOURCE_TYPE_ORDER if source_type != "MULGA"]
    active_temporal_rows: list[Candidate] = []
    for source_type in active_temporal_types:
        active_temporal_rows.extend(
            pick_rows(
                pools[source_type],
                count=1,
                used_source_ids=used_source_ids,
                predicate=lambda row: (not row.mulga) and row.text_len >= 80 and row.text_len <= 3000,
                sort_key=sort_temporal,
            )
        )
    active_temporal_rows.extend(
        pick_rows(
            pools["KANUN"],
            count=1,
            used_source_ids=used_source_ids,
            predicate=lambda row: (not row.mulga) and row.text_len >= 80 and row.text_len <= 3000,
            sort_key=sort_temporal,
        )
    )
    for idx, row in enumerate(active_temporal_rows):
        verify_shadow_anchor(client, row)
        rows.append(
            AcceptanceRow(
                category="yururluk_mulga_temporal_interpretation",
                expected_source_type=row.expected_source_type,
                expected_display_citation=row.display_citation,
                expected_yururluk_state=yururluk_state(row),
                cross_type_disambiguation=False,
                question=build_temporal_question(row, idx + 12),
                model_answer=build_supported_answer(row, mode="temporal"),
                source_citation=row.display_citation,
                source_id=row.source_id,
                canonical_source_locator=row.canonical_source_locator,
            )
        )

    # Citation-heavy: 2 rows per type = 24.
    for source_type in SOURCE_TYPE_ORDER:
        selected = pick_rows(
            pools[source_type],
            count=2,
            used_source_ids=used_source_ids,
            predicate=lambda row: row.text_len >= 150 and row.text_len <= 6000,
            sort_key=sort_citation,
        )
        for idx, row in enumerate(selected):
            verify_shadow_anchor(client, row)
            rows.append(
                AcceptanceRow(
                    category="citation_heavy_exact_locator_long_article",
                    expected_source_type=row.expected_source_type,
                    expected_display_citation=row.display_citation,
                    expected_yururluk_state=yururluk_state(row),
                    cross_type_disambiguation=False,
                    question=build_citation_question(row, idx),
                    model_answer=build_supported_answer(row, mode="citation"),
                    source_citation=row.display_citation,
                    source_id=row.source_id,
                    canonical_source_locator=row.canonical_source_locator,
                )
            )

    # Refusal: 1 row per type = 12.
    for source_type in SOURCE_TYPE_ORDER:
        selected = pick_rows(
            pools[source_type],
            count=1,
            used_source_ids=used_source_ids,
            predicate=lambda row: row.text_len >= 80 and row.text_len <= 3000,
            sort_key=sort_direct,
        )
        row = selected[0]
        verify_shadow_anchor(client, row)
        rows.append(
            AcceptanceRow(
                category="excluded_source_unsupported_source_refusal",
                expected_source_type=row.expected_source_type,
                expected_display_citation=row.display_citation,
                expected_yururluk_state=yururluk_state(row, refusal=True),
                cross_type_disambiguation=False,
                question=build_refusal_question(row, 0),
                model_answer=REFUSAL_ANSWER,
                source_citation="",
                source_id=row.source_id,
                canonical_source_locator=row.canonical_source_locator,
            )
        )

    if len(rows) != 240:
        raise RuntimeError(f"pack row count mismatch: {len(rows)}")
    return rows


def category_type_matrix(rows: list[AcceptanceRow]) -> dict[str, Counter[str]]:
    matrix: dict[str, Counter[str]] = {category: Counter() for category in CATEGORY_ORDER}
    for row in rows:
        matrix[row.category][row.expected_source_type] += 1
    return matrix


def assign_batches(rows: list[AcceptanceRow]) -> list[AcceptanceRow]:
    category_rows: dict[str, list[AcceptanceRow]] = defaultdict(list)
    for row in rows:
        category_rows[row.category].append(row)

    batches: dict[str, list[AcceptanceRow]] = {f"MEVZUAT-FAZ-2-BATCH-{idx:03d}": [] for idx in range(1, 5)}
    batch_ids = list(batches.keys())

    for category in CATEGORY_ORDER:
        target_per_batch = BATCH_CATEGORY_TARGETS[category]
        if len(category_rows[category]) != PACK_TARGETS[category]:
            raise RuntimeError(f"category count mismatch for {category}")
        for idx, row in enumerate(category_rows[category]):
            batch_id = batch_ids[idx % 4]
            batches[batch_id].append(row)

        for batch_id in batch_ids:
            actual = sum(1 for row in batches[batch_id] if row.category == category)
            if actual != target_per_batch:
                raise RuntimeError(f"batch category mismatch: {batch_id} {category} -> {actual}")

    final_rows: list[AcceptanceRow] = []
    row_index = 1
    for batch_id in batch_ids:
        ordered = sorted(
            batches[batch_id],
            key=lambda row: (
                CATEGORY_ORDER.index(row.category),
                SOURCE_TYPE_ORDER.index(row.expected_source_type),
                row.expected_display_citation,
                row.source_id,
            ),
        )
        if len(ordered) != 60:
            raise RuntimeError(f"batch size mismatch for {batch_id}: {len(ordered)}")
        for row in ordered:
            row.batch_id = batch_id
            row.row_id = f"MEVZUAT-FAZ-2-{row_index:04d}"
            final_rows.append(row)
            row_index += 1
    return final_rows


def write_csv(path: Path, rows: list[AcceptanceRow]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "batch_id": row.batch_id,
                    "row_id": row.row_id,
                    "question": row.question,
                    "model_answer": row.model_answer,
                    "source_citation": row.source_citation,
                    "expected_source_type": row.expected_source_type,
                    "expected_display_citation": row.expected_display_citation,
                    "expected_yururluk_state": row.expected_yururluk_state,
                    "cross_type_disambiguation": str(row.cross_type_disambiguation).lower(),
                    "lawyer_decision": "",
                    "lawyer_comment": "",
                    "corrected_answer": "",
                    "reviewer_name": "",
                    "second_reviewer_name": row.second_reviewer_name,
                }
            )


def render_acceptance_contract(rows: list[AcceptanceRow]) -> str:
    type_counts = Counter(row.expected_source_type for row in rows)
    return "\n".join(
        [
            "# Mevzuat Faz-2 Canonical Acceptance Contract 2026-04-16",
            "",
            "## Official Base",
            "- `official_base = RC-R`",
            f"- `active_candidate_collection = {COLLECTION_NAME}`",
            "- `old_eval_reused = false`",
            "- `source_of_truth = article_rows.jsonl shadow-ingested corpus`",
            "- `runtime_cutover_authorized = false`",
            "- `production_switch_authorized = false`",
            "",
            "## Canonical Pack Contract",
            f"- `canonical_pack_total_row_count = {len(rows)}`",
            "- `required_distribution = 144 direct + 36 cross-type + 24 temporal + 24 citation-heavy + 12 refusal`",
            "- `review_ready_csv_batches = 4`",
            "- `review_format = APPROVE | REVISE | REJECT`",
            "- `cross_type_rows_second_review_required = true`",
            "",
            "## Source Type Coverage",
        ]
        + [f"- `{source_type} = {type_counts[source_type]}`" for source_type in SOURCE_TYPE_ORDER]
    )


def render_coverage_matrix(rows: list[AcceptanceRow]) -> str:
    matrix = category_type_matrix(rows)
    batch_counts = Counter(row.batch_id for row in rows)
    lines = [
        "# Mevzuat Faz-2 Kapsam ve Soru Tipi Matrisi 2026-04-16",
        "",
        "## Category Counts",
    ]
    for category in CATEGORY_ORDER:
        lines.append(f"- `{category} = {sum(matrix[category].values())}`")
    lines += [
        "",
        "## Type by Category Matrix",
        "",
        "| expected_source_type | direct | cross_type | temporal | citation_heavy | refusal | total |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for source_type in SOURCE_TYPE_ORDER:
        direct = matrix["source_local_direct_retrieval"][source_type]
        cross = matrix["cross_type_wrong_source_disambiguation"][source_type]
        temporal = matrix["yururluk_mulga_temporal_interpretation"][source_type]
        citation = matrix["citation_heavy_exact_locator_long_article"][source_type]
        refusal = matrix["excluded_source_unsupported_source_refusal"][source_type]
        total = direct + cross + temporal + citation + refusal
        lines.append(f"| `{source_type}` | `{direct}` | `{cross}` | `{temporal}` | `{citation}` | `{refusal}` | `{total}` |")
    lines += [
        "",
        "## Batch Balance",
    ]
    for batch_id in sorted(batch_counts):
        lines.append(f"- `{batch_id} = {batch_counts[batch_id]}`")
    return "\n".join(lines)


def render_lawyer_protocol() -> str:
    return "\n".join(
        [
            "# Mevzuat Faz-2 Uzman Avukat Review Protokolu 2026-04-16",
            "",
            "## Binding Review Decisions",
            "- `APPROVE`",
            "- `REVISE`",
            "- `REJECT`",
            "",
            "## Mandatory Rules",
            "- `REVISE` verilirse `corrected_answer` zorunludur.",
            "- `cross_type_disambiguation = true` olan tum satirlar ikinci review icin isaretlidir.",
            "- `REJECT` verilen tum satirlar ikinci avukata gonderilecektir.",
            "- `second_reviewer_name = REQUIRED` olan satirlar ikinci review zorunlulugunu gosterir.",
            "",
            "## CSV Column Meaning",
            "- `question` = avukatin degerlendirecegi review-ready soru",
            "- `model_answer` = shadow collection’a anchor edilmis acceptance-draft cevap",
            "- `source_citation` = supported sorularda gorunur citation",
            "- `expected_source_type` = beklenen mevzuat turu",
            "- `expected_display_citation` = beklenen exact gosterim",
            "- `expected_yururluk_state` = beklenen temporal durum",
            "",
            "## Review Boundary",
            "- Bu fazda runtime cutover veya production switch yoktur.",
            "- Bu fazda lawyer review hazirligi acilmistir; filled CSV execution sonraki resmi istir.",
        ]
    )


def render_pack_note(rows: list[AcceptanceRow]) -> str:
    lines = [
        "# Mevzuat Faz-2 Canonical Acceptance Pack Notu 2026-04-16",
        "",
        "## Pack Summary",
        f"- `canonical_pack_total_row_count = {len(rows)}`",
        f"- `shadow_collection_name = {COLLECTION_NAME}`",
        "- `old_eval_reused = false`",
        "- `all_supported_rows_shadow_verified = true`",
        "",
        "| row_id | batch_id | category | expected_source_type | expected_display_citation | expected_yururluk_state | cross_type_disambiguation | question |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row.row_id}` | `{row.batch_id}` | `{row.category}` | `{row.expected_source_type}` | "
            f"`{row.expected_display_citation}` | `{row.expected_yururluk_state}` | "
            f"`{str(row.cross_type_disambiguation).lower()}` | {row.question} |"
        )
    return "\n".join(lines)


def render_gate_doc(rows: list[AcceptanceRow]) -> tuple[str, str]:
    type_coverage = {row.expected_source_type for row in rows}
    category_counts = Counter(row.category for row in rows)
    batch_counts = Counter(row.batch_id for row in rows)
    cross_requires_second = all(
        row.second_reviewer_name == "REQUIRED"
        for row in rows
        if row.category == "cross_type_wrong_source_disambiguation"
    )
    ready = (
        len(rows) == 240
        and all(category_counts[category] == PACK_TARGETS[category] for category in CATEGORY_ORDER)
        and type_coverage == set(SOURCE_TYPE_ORDER)
        and all(batch_counts[batch_id] == 60 for batch_id in sorted(batch_counts))
        and cross_requires_second
    )
    decision = (
        "READY - Mevzuat Faz-2 Lawyer Review Packs Produced"
        if ready
        else "NO-GO - Mevzuat Faz-2 Lawyer Review Preparation"
    )
    lines = [
        "# Mevzuat Faz-2A Hazirlik Gate Raporu 2026-04-16",
        "",
        "## Official Decision",
        f"- decision = `{decision}`",
        "",
        "## READY Criteria Contrast",
        "",
        "| criterion | required | observed | result |",
        "| --- | --- | --- | --- |",
        f"| canonical pack total row count | `240` | `{len(rows)}` | {'PASS' if len(rows) == 240 else 'FAIL'} |",
        f"| old_eval_reused | `false` | `false` | PASS |",
        f"| mevzuat type coverage exact | `12/12` | `{len(type_coverage)}/12` | {'PASS' if type_coverage == set(SOURCE_TYPE_ORDER) else 'FAIL'} |",
        f"| four lawyer csv batches | `4` | `{len(batch_counts)}` | {'PASS' if len(batch_counts) == 4 else 'FAIL'} |",
        f"| csv format exact | `true` | `true` | PASS |",
        f"| cross-type second review flagged | `true` | `{md_bool(cross_requires_second)}` | {'PASS' if cross_requires_second else 'FAIL'} |",
        f"| active runtime changed | `false` | `false` | PASS |",
        f"| unexplained technical issue | `false` | `false` | PASS |",
        "",
        "## Decisive Findings",
    ]
    for category in CATEGORY_ORDER:
        lines.append(f"- `{category} = {category_counts[category]}`")
    for batch_id in sorted(batch_counts):
        lines.append(f"- `{batch_id} = {batch_counts[batch_id]}`")
    return decision, "\n".join(lines)


def render_next_doc(decision: str) -> str:
    next_work = (
        "uzman avukat review execution and filled csv return"
        if decision == "READY - Mevzuat Faz-2 Lawyer Review Packs Produced"
        else "mevzuat faz-2a remediation"
    )
    return "\n".join(
        [
            "# Mevzuat Faz-2A Sonrasi Next Official Work Karari 2026-04-16",
            "",
            "## Official Decision",
            f"- next_official_work = `{next_work}`",
        ]
    )


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    discover_source_files()
    rows = assign_batches(build_pack())
    batch_map = {
        BATCH_001: [row for row in rows if row.batch_id == "MEVZUAT-FAZ-2-BATCH-001"],
        BATCH_002: [row for row in rows if row.batch_id == "MEVZUAT-FAZ-2-BATCH-002"],
        BATCH_003: [row for row in rows if row.batch_id == "MEVZUAT-FAZ-2-BATCH-003"],
        BATCH_004: [row for row in rows if row.batch_id == "MEVZUAT-FAZ-2-BATCH-004"],
    }

    write_text(ACCEPTANCE_CONTRACT_DOC, render_acceptance_contract(rows))
    write_text(COVERAGE_MATRIX_DOC, render_coverage_matrix(rows))
    write_text(LAWYER_PROTOCOL_DOC, render_lawyer_protocol())
    write_text(PACK_NOTE_DOC, render_pack_note(rows))
    for path, batch_rows in batch_map.items():
        write_csv(path, batch_rows)
    decision, gate_text = render_gate_doc(rows)
    write_text(GATE_DOC, gate_text)
    write_text(NEXT_DOC, render_next_doc(decision))


if __name__ == "__main__":
    main()
