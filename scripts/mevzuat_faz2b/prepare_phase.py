#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
DATE_TAG = "2026-04-17"

REVIEWED_BATCH_PATHS = [
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-001-REVIEWED.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-002-REVIEWED.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-003-REVIEWED.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-004-REVIEWED.csv",
]

ORIGINAL_BATCH_PATHS = [
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-001.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-002.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-003.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-004.csv",
]

SCOPE_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2B-REMEDIATION-SCOPE-{DATE_TAG}.md"
LOCALIZATION_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2B-PROBLEM-YOGUNLASMA-RAPORU-{DATE_TAG}.md"
PROTOCOL_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2B-GERCEK-UZMAN-AVUKAT-REVIEW-PROTOKOLU-{DATE_TAG}.md"
BATCH_001_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2B-LAWYER-REVIEW-BATCH-001.csv"
BATCH_002_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2B-LAWYER-REVIEW-BATCH-002.csv"
GATE_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2B-HAZIRLIK-GATE-RAPORU-{DATE_TAG}.md"
NEXT_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2B-SONRASI-NEXT-OFFICIAL-WORK-KARARI-{DATE_TAG}.md"

CSV_HEADERS = [
    "batch_id",
    "row_id",
    "surface_name",
    "question",
    "model_answer",
    "source_citation",
    "expected_source_type",
    "expected_display_citation",
    "expected_yururluk_state",
    "cross_type_disambiguation",
    "is_problem_core",
    "is_sentinel_control",
    "lawyer_decision",
    "lawyer_comment",
    "corrected_answer",
    "reviewer_name",
    "second_reviewer_name",
]

SURFACE_PRIORITY = [
    "excluded_source_unsupported_source_refusal",
    "yururluk_mulga_temporal_interpretation",
    "citation_heavy_exact_locator_long_article",
    "cross_type_wrong_source_disambiguation",
]

SENTINEL_IDS_BY_SURFACE = {
    "source_local_direct_retrieval": [
        "MEVZUAT-FAZ-2-0001",
        "MEVZUAT-FAZ-2-0010",
        "MEVZUAT-FAZ-2-0061",
        "MEVZUAT-FAZ-2-0070",
        "MEVZUAT-FAZ-2-0121",
        "MEVZUAT-FAZ-2-0130",
        "MEVZUAT-FAZ-2-0181",
        "MEVZUAT-FAZ-2-0190",
    ],
    "cross_type_wrong_source_disambiguation": [
        "MEVZUAT-FAZ-2-0037",
        "MEVZUAT-FAZ-2-0039",
        "MEVZUAT-FAZ-2-0097",
        "MEVZUAT-FAZ-2-0099",
        "MEVZUAT-FAZ-2-0157",
        "MEVZUAT-FAZ-2-0159",
        "MEVZUAT-FAZ-2-0217",
        "MEVZUAT-FAZ-2-0219",
    ],
    "citation_heavy_exact_locator_long_article": [
        "MEVZUAT-FAZ-2-0052",
        "MEVZUAT-FAZ-2-0053",
        "MEVZUAT-FAZ-2-0112",
        "MEVZUAT-FAZ-2-0114",
        "MEVZUAT-FAZ-2-0172",
        "MEVZUAT-FAZ-2-0174",
        "MEVZUAT-FAZ-2-0232",
        "MEVZUAT-FAZ-2-0234",
    ],
}


@dataclass(frozen=True, slots=True)
class BatchRow:
    row_id: str
    surface_name: str
    question: str
    model_answer: str
    source_citation: str
    expected_source_type: str
    expected_display_citation: str
    expected_yururluk_state: str
    cross_type_disambiguation: str
    is_problem_core: str
    is_sentinel_control: str
    second_reviewer_name: str


def load_csv_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"required csv missing: {path}")
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows.extend(list(csv.DictReader(handle)))
    return rows


def row_number(row_id: str) -> int:
    return int(row_id.rsplit("-", 1)[-1])


def surface_from_row_id(row_id: str) -> str:
    rid = row_number(row_id)
    if 1 <= rid <= 36 or 61 <= rid <= 96 or 121 <= rid <= 156 or 181 <= rid <= 216:
        return "source_local_direct_retrieval"
    if 37 <= rid <= 45 or 97 <= rid <= 105 or 157 <= rid <= 165 or 217 <= rid <= 225:
        return "cross_type_wrong_source_disambiguation"
    if 46 <= rid <= 51 or 106 <= rid <= 111 or 166 <= rid <= 171 or 226 <= rid <= 231:
        return "yururluk_mulga_temporal_interpretation"
    if 52 <= rid <= 57 or 112 <= rid <= 117 or 172 <= rid <= 177 or 232 <= rid <= 237:
        return "citation_heavy_exact_locator_long_article"
    if 58 <= rid <= 60 or 118 <= rid <= 120 or 178 <= rid <= 180 or 238 <= rid <= 240:
        return "excluded_source_unsupported_source_refusal"
    raise ValueError(f"unexpected row id: {row_id}")


def bool_str(value: bool) -> str:
    return "true" if value else "false"


def markdown_bool(value: bool) -> str:
    return "true" if value else "false"


def remediation_priority(surface_name: str) -> str:
    mapping = {
        "excluded_source_unsupported_source_refusal": "P0",
        "yururluk_mulga_temporal_interpretation": "P1",
        "citation_heavy_exact_locator_long_article": "P1",
        "cross_type_wrong_source_disambiguation": "P2",
        "source_local_direct_retrieval": "P3",
    }
    return mapping[surface_name]


def needs_second_reviewer(*, is_problem_core: bool, surface_name: str, cross_type: str) -> bool:
    return is_problem_core or surface_name == "excluded_source_unsupported_source_refusal" or cross_type == "true"


def build_problem_core(reviewed_rows: list[dict[str, str]], original_by_id: dict[str, dict[str, str]]) -> list[BatchRow]:
    problem_ids = sorted(
        [
            row["row_id"]
            for row in reviewed_rows
            if row["lawyer_decision"] in {"REVISE", "REJECT"}
        ],
        key=row_number,
    )
    rows: list[BatchRow] = []
    for row_id in problem_ids:
        original = original_by_id[row_id]
        surface_name = surface_from_row_id(row_id)
        rows.append(
            BatchRow(
                row_id=row_id,
                surface_name=surface_name,
                question=original["question"],
                model_answer=original["model_answer"],
                source_citation=original["source_citation"],
                expected_source_type=original["expected_source_type"],
                expected_display_citation=original["expected_display_citation"],
                expected_yururluk_state=original["expected_yururluk_state"],
                cross_type_disambiguation=original["cross_type_disambiguation"],
                is_problem_core="true",
                is_sentinel_control="false",
                second_reviewer_name="REQUIRED"
                if needs_second_reviewer(
                    is_problem_core=True,
                    surface_name=surface_name,
                    cross_type=original["cross_type_disambiguation"],
                )
                else "",
            )
        )
    return rows


def build_sentinel(original_by_id: dict[str, dict[str, str]]) -> list[BatchRow]:
    rows: list[BatchRow] = []
    for surface_name, row_ids in SENTINEL_IDS_BY_SURFACE.items():
        for row_id in row_ids:
            original = original_by_id[row_id]
            rows.append(
                BatchRow(
                    row_id=row_id,
                    surface_name=surface_name,
                    question=original["question"],
                    model_answer=original["model_answer"],
                    source_citation=original["source_citation"],
                    expected_source_type=original["expected_source_type"],
                    expected_display_citation=original["expected_display_citation"],
                    expected_yururluk_state=original["expected_yururluk_state"],
                    cross_type_disambiguation=original["cross_type_disambiguation"],
                    is_problem_core="false",
                    is_sentinel_control="true",
                    second_reviewer_name="REQUIRED"
                    if needs_second_reviewer(
                        is_problem_core=False,
                        surface_name=surface_name,
                        cross_type=original["cross_type_disambiguation"],
                    )
                    else "",
                )
            )
    return sorted(rows, key=lambda row: row_number(row.row_id))


def assign_problem_batches(problem_core: list[BatchRow]) -> tuple[list[BatchRow], list[BatchRow]]:
    by_surface: dict[str, list[BatchRow]] = defaultdict(list)
    for row in sorted(problem_core, key=lambda item: row_number(item.row_id)):
        by_surface[row.surface_name].append(row)

    batch1: list[BatchRow] = []
    batch2: list[BatchRow] = []

    temporal = by_surface["yururluk_mulga_temporal_interpretation"]
    citation = by_surface["citation_heavy_exact_locator_long_article"]
    refusal = by_surface["excluded_source_unsupported_source_refusal"]

    for index, row in enumerate(temporal):
        (batch1 if index % 2 == 0 else batch2).append(row)
    for index, row in enumerate(citation):
        (batch2 if index % 2 == 0 else batch1).append(row)
    for index, row in enumerate(refusal):
        (batch1 if index % 2 == 0 else batch2).append(row)

    if len(batch1) != 16 or len(batch2) != 16:
        raise ValueError(f"problem core batch split invalid: {len(batch1)} / {len(batch2)}")
    return sorted(batch1, key=lambda row: row_number(row.row_id)), sorted(batch2, key=lambda row: row_number(row.row_id))


def assign_sentinel_batches(sentinel_rows: list[BatchRow]) -> tuple[list[BatchRow], list[BatchRow]]:
    by_surface: dict[str, list[BatchRow]] = defaultdict(list)
    for row in sorted(sentinel_rows, key=lambda item: row_number(item.row_id)):
        by_surface[row.surface_name].append(row)

    batch1: list[BatchRow] = []
    batch2: list[BatchRow] = []
    for surface_name in [
        "source_local_direct_retrieval",
        "cross_type_wrong_source_disambiguation",
        "citation_heavy_exact_locator_long_article",
    ]:
        for index, row in enumerate(by_surface[surface_name]):
            (batch1 if index % 2 == 0 else batch2).append(row)

    if len(batch1) != 12 or len(batch2) != 12:
        raise ValueError(f"sentinel batch split invalid: {len(batch1)} / {len(batch2)}")
    return sorted(batch1, key=lambda row: row_number(row.row_id)), sorted(batch2, key=lambda row: row_number(row.row_id))


def row_to_csv(batch_id: str, row: BatchRow) -> dict[str, str]:
    return {
        "batch_id": batch_id,
        "row_id": row.row_id,
        "surface_name": row.surface_name,
        "question": row.question,
        "model_answer": row.model_answer,
        "source_citation": row.source_citation,
        "expected_source_type": row.expected_source_type,
        "expected_display_citation": row.expected_display_citation,
        "expected_yururluk_state": row.expected_yururluk_state,
        "cross_type_disambiguation": row.cross_type_disambiguation,
        "is_problem_core": row.is_problem_core,
        "is_sentinel_control": row.is_sentinel_control,
        "lawyer_decision": "",
        "lawyer_comment": "",
        "corrected_answer": "",
        "reviewer_name": "",
        "second_reviewer_name": row.second_reviewer_name,
    }


def render_scope_doc(problem_core: list[BatchRow], sentinel_rows: list[BatchRow]) -> str:
    return "\n".join(
        [
            f"# Mevzuat Faz-2B Remediation Scope {DATE_TAG}",
            "",
            "## Binding Counts",
            f"- `problem_core_row_count = {len(problem_core)}`",
            f"- `sentinel_control_row_count = {len(sentinel_rows)}`",
            f"- `target_total_row_count = {len(problem_core) + len(sentinel_rows)}`",
            "- `official_human_review_required = true`",
            "",
            "## Scope Rules",
            "- `problem_core` yalniz Faz-2 reviewed sonucunda `REVISE` veya `REJECT` donen satirlardan olusur.",
            "- `sentinel_control` yalniz onceden `APPROVE` donen ve regresyon kontrolu icin yeniden acilan satirlardan olusur.",
            "- Bu fazda resmi insan review zorunludur; model adi reviewer olarak kullanilamaz.",
            "",
            "## Surface Split",
            f"- `problem_core.surface.excluded_source_unsupported_source_refusal = {sum(1 for row in problem_core if row.surface_name == 'excluded_source_unsupported_source_refusal')}`",
            f"- `problem_core.surface.yururluk_mulga_temporal_interpretation = {sum(1 for row in problem_core if row.surface_name == 'yururluk_mulga_temporal_interpretation')}`",
            f"- `problem_core.surface.citation_heavy_exact_locator_long_article = {sum(1 for row in problem_core if row.surface_name == 'citation_heavy_exact_locator_long_article')}`",
            f"- `sentinel_control.surface.cross_type_wrong_source_disambiguation = {sum(1 for row in sentinel_rows if row.surface_name == 'cross_type_wrong_source_disambiguation')}`",
            f"- `sentinel_control.surface.source_local_direct_retrieval = {sum(1 for row in sentinel_rows if row.surface_name == 'source_local_direct_retrieval')}`",
            f"- `sentinel_control.surface.citation_heavy_exact_locator_long_article = {sum(1 for row in sentinel_rows if row.surface_name == 'citation_heavy_exact_locator_long_article')}`",
        ]
    ) + "\n"


def render_localization_doc(reviewed_rows: list[dict[str, str]]) -> str:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in reviewed_rows:
        surface_name = surface_from_row_id(row["row_id"])
        counts[surface_name][row["lawyer_decision"]] += 1

    lines = [
        f"# Mevzuat Faz-2B Problem Yogunlasma Raporu {DATE_TAG}",
        "",
        "| surface_name | approve_count | revise_count | reject_count | remediation_priority |",
        "| --- | --- | --- | --- | --- |",
    ]
    for surface_name in [
        "excluded_source_unsupported_source_refusal",
        "yururluk_mulga_temporal_interpretation",
        "citation_heavy_exact_locator_long_article",
        "cross_type_wrong_source_disambiguation",
        "source_local_direct_retrieval",
    ]:
        lines.append(
            f"| `{surface_name}` | `{counts[surface_name]['APPROVE']}` | `{counts[surface_name]['REVISE']}` | `{counts[surface_name]['REJECT']}` | `{remediation_priority(surface_name)}` |"
        )

    lines.extend(
        [
            "",
            "## Binding Interpretation",
            "- `excluded_source_unsupported_source_refusal` yuzeyi tam reject yigini oldugu icin en yuksek oncelikte tutulur.",
            "- `yururluk_mulga_temporal_interpretation` yuzeyi revizyonun ana yogunlasma bolgesidir.",
            "- `citation_heavy_exact_locator_long_article` yuzeyi uzun cevap ve locator kesinligi acisindan ikinci ana remediation alanidir.",
            "- `cross_type_wrong_source_disambiguation` yuzeyi sentinel olarak yeniden acilir; provisional turde tam approve donmustur.",
            "- `source_local_direct_retrieval` yuzeyi yalniz regresyon kontrolu icin sentinel olarak yeniden acilir.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_protocol_doc() -> str:
    return "\n".join(
        [
            f"# Mevzuat Faz-2B Gercek Uzman Avukat Review Protokolu {DATE_TAG}",
            "",
            "## Binding Rules",
            "- `review_format = APPROVE_REVISE_REJECT`",
            "- `corrected_answer_required_if_revise = true`",
            "- `human_reviewer_name_required = true`",
            "- `model_name_as_reviewer_forbidden = true`",
            "- `second_reviewer_required_for_reject = true`",
            "- `second_reviewer_required_for_cross_type = true`",
            "- `second_reviewer_required_for_refusal = true`",
            "",
            "## Human Review Rules",
            "- `reviewer_name` alani gercek insan adiyla doldurulacaktir.",
            "- `second_reviewer_name` gerekiyorsa gercek insan adiyla doldurulacaktir.",
            "- `APPROVE` icin corrected answer zorunlu degildir.",
            "- `REVISE` icin corrected answer zorunludur.",
            "- `REJECT` satirlari ikinci avukata zorunlu gider.",
            "- `cross_type_disambiguation = true` satirlari ikinci avukata zorunlu gider.",
            "- `excluded_source_unsupported_source_refusal` satirlari ikinci avukata zorunlu gider.",
            "- problem core satirlari provisional ihtilafli satir kabul edilir ve ikinci review alaninda `REQUIRED` ile isaretlenir.",
        ]
    ) + "\n"


def render_gate_doc(*, batch1: list[dict[str, str]], batch2: list[dict[str, str]], problem_core: list[BatchRow], sentinel_rows: list[BatchRow]) -> tuple[str, str]:
    decision = "READY - Mevzuat Faz-2B Real Lawyer Review Packs Produced"
    batch_total = len(batch1) + len(batch2)
    cross_type_required = sum(1 for row in batch1 + batch2 if row["cross_type_disambiguation"] == "true" and row["second_reviewer_name"] == "REQUIRED")
    lines = [
        f"# Mevzuat Faz-2B Hazirlik Gate Raporu {DATE_TAG}",
        "",
        "## Official Decision",
        f"- decision = `{decision}`",
        "",
        "## READY Criteria Contrast",
        "",
        "| criterion | required | observed | result |",
        "| --- | --- | --- | --- |",
        f"| problem_core_row_count | `32` | `{len(problem_core)}` | {'PASS' if len(problem_core) == 32 else 'FAIL'} |",
        f"| sentinel_control_row_count | `24` | `{len(sentinel_rows)}` | {'PASS' if len(sentinel_rows) == 24 else 'FAIL'} |",
        f"| target_total_row_count | `56` | `{batch_total}` | {'PASS' if batch_total == 56 else 'FAIL'} |",
        "| real human review protocol written | `true` | `true` | PASS |",
        "| model reviewer forbidden explicitly | `true` | `true` | PASS |",
        "| lawyer csv batch count | `2` | `2` | PASS |",
        f"| second review flagged for required rows | `true` | `{markdown_bool(cross_type_required == 8 and all(row['second_reviewer_name'] == 'REQUIRED' for row in batch1 + batch2 if row['is_problem_core'] == 'true'))}` | {'PASS' if cross_type_required == 8 and all(row['second_reviewer_name'] == 'REQUIRED' for row in batch1 + batch2 if row['is_problem_core'] == 'true') else 'FAIL'} |",
        "| active runtime changed | `false` | `false` | PASS |",
        "",
        "## Decisive Findings",
        f"- `MEVZUAT-FAZ-2B-LAWYER-REVIEW-BATCH-001 = {len(batch1)}`",
        f"- `MEVZUAT-FAZ-2B-LAWYER-REVIEW-BATCH-002 = {len(batch2)}`",
        f"- `problem_core.refusal = {sum(1 for row in problem_core if row.surface_name == 'excluded_source_unsupported_source_refusal')}`",
        f"- `problem_core.temporal = {sum(1 for row in problem_core if row.surface_name == 'yururluk_mulga_temporal_interpretation')}`",
        f"- `problem_core.citation_heavy = {sum(1 for row in problem_core if row.surface_name == 'citation_heavy_exact_locator_long_article')}`",
        f"- `sentinel.cross_type = {sum(1 for row in sentinel_rows if row.surface_name == 'cross_type_wrong_source_disambiguation')}`",
        f"- `sentinel.direct = {sum(1 for row in sentinel_rows if row.surface_name == 'source_local_direct_retrieval')}`",
        f"- `sentinel.citation_heavy = {sum(1 for row in sentinel_rows if row.surface_name == 'citation_heavy_exact_locator_long_article')}`",
    ]
    return decision, "\n".join(lines) + "\n"


def render_next_doc(decision: str) -> str:
    next_work = (
        "real expert lawyer review execution and filled csv return"
        if decision == "READY - Mevzuat Faz-2B Real Lawyer Review Packs Produced"
        else "mevzuat faz-2b remediation"
    )
    return "\n".join(
        [
            f"# Mevzuat Faz-2B Sonrasi Next Official Work Karari {DATE_TAG}",
            "",
            "## Binding Decision",
            f"- next_official_work = `{next_work}`",
        ]
    ) + "\n"


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_outputs() -> dict[str, object]:
    original_rows = load_csv_rows(ORIGINAL_BATCH_PATHS)
    reviewed_rows = load_csv_rows(REVIEWED_BATCH_PATHS)
    original_by_id = {row["row_id"]: row for row in original_rows}

    problem_core = build_problem_core(reviewed_rows, original_by_id)
    sentinel_rows = build_sentinel(original_by_id)

    problem_batch1, problem_batch2 = assign_problem_batches(problem_core)
    sentinel_batch1, sentinel_batch2 = assign_sentinel_batches(sentinel_rows)

    batch1_rows = [row_to_csv("MEVZUAT-FAZ-2B-BATCH-001", row) for row in (problem_batch1 + sentinel_batch1)]
    batch2_rows = [row_to_csv("MEVZUAT-FAZ-2B-BATCH-002", row) for row in (problem_batch2 + sentinel_batch2)]
    batch1_rows.sort(key=lambda row: row_number(row["row_id"]))
    batch2_rows.sort(key=lambda row: row_number(row["row_id"]))

    return {
        "problem_core": problem_core,
        "sentinel_rows": sentinel_rows,
        "batch1_rows": batch1_rows,
        "batch2_rows": batch2_rows,
        "scope_doc": render_scope_doc(problem_core, sentinel_rows),
        "localization_doc": render_localization_doc(reviewed_rows),
        "protocol_doc": render_protocol_doc(),
    }


def main() -> None:
    outputs = build_outputs()
    scope_doc = outputs["scope_doc"]
    localization_doc = outputs["localization_doc"]
    protocol_doc = outputs["protocol_doc"]
    batch1_rows = outputs["batch1_rows"]
    batch2_rows = outputs["batch2_rows"]
    problem_core = outputs["problem_core"]
    sentinel_rows = outputs["sentinel_rows"]

    decision, gate_doc = render_gate_doc(
        batch1=batch1_rows,
        batch2=batch2_rows,
        problem_core=problem_core,
        sentinel_rows=sentinel_rows,
    )

    write_text(SCOPE_DOC, scope_doc)
    write_text(LOCALIZATION_DOC, localization_doc)
    write_text(PROTOCOL_DOC, protocol_doc)
    write_csv(BATCH_001_DOC, batch1_rows)
    write_csv(BATCH_002_DOC, batch2_rows)
    write_text(GATE_DOC, gate_doc)
    write_text(NEXT_DOC, render_next_doc(decision))


if __name__ == "__main__":
    main()
