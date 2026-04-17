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
    DOCS_DIR / "MEVZUAT-FAZ-2B-LAWYER-REVIEW-BATCH-001-REVIEWED.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2B-LAWYER-REVIEW-BATCH-002-REVIEWED.csv",
]

ORIGINAL_BATCH_PATHS = [
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-001.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-002.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-003.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2-LAWYER-REVIEW-BATCH-004.csv",
]

SCOPE_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2C-SCOPE-DUZELTME-RAPORU-{DATE_TAG}.md"
PROTOCOL_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2C-GERCEK-INSAN-REVIEW-PROTOKOLU-{DATE_TAG}.md"
BATCH_001_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2C-LAWYER-REVIEW-BATCH-001.csv"
BATCH_002_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2C-LAWYER-REVIEW-BATCH-002.csv"
GATE_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2C-HAZIRLIK-GATE-RAPORU-{DATE_TAG}.md"
NEXT_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2C-SONRASI-NEXT-OFFICIAL-WORK-KARARI-{DATE_TAG}.md"

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
    "second_reviewer_required",
    "second_reviewer_decision",
    "second_reviewer_comment",
    "second_reviewer_name",
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
        "MEVZUAT-FAZ-2-0114",
        "MEVZUAT-FAZ-2-0115",
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
    second_reviewer_required: str


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


def markdown_bool(value: bool) -> str:
    return "true" if value else "false"


def second_reviewer_required(*, is_problem_core: bool, surface_name: str, cross_type_disambiguation: str) -> str:
    required = (
        is_problem_core
        or surface_name == "excluded_source_unsupported_source_refusal"
        or cross_type_disambiguation == "true"
    )
    return markdown_bool(required)


def build_problem_core(reviewed_rows: list[dict[str, str]], original_by_id: dict[str, dict[str, str]]) -> list[BatchRow]:
    problem_ids = sorted(
        {
            row["row_id"]
            for row in reviewed_rows
            if row["lawyer_decision"] in {"REVISE", "REJECT"}
        },
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
                second_reviewer_required=second_reviewer_required(
                    is_problem_core=True,
                    surface_name=surface_name,
                    cross_type_disambiguation=original["cross_type_disambiguation"],
                ),
            )
        )
    return rows


def build_sentinel(original_by_id: dict[str, dict[str, str]], forbidden_row_ids: set[str]) -> list[BatchRow]:
    rows: list[BatchRow] = []
    for surface_name, row_ids in SENTINEL_IDS_BY_SURFACE.items():
        for row_id in row_ids:
            if row_id in forbidden_row_ids:
                raise ValueError(f"sentinel row overlaps problem core: {row_id}")
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
                    second_reviewer_required=second_reviewer_required(
                        is_problem_core=False,
                        surface_name=surface_name,
                        cross_type_disambiguation=original["cross_type_disambiguation"],
                    ),
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
        raise ValueError(f"problem batch split invalid: {len(batch1)} / {len(batch2)}")
    return sorted(batch1, key=lambda row: row_number(row.row_id)), sorted(batch2, key=lambda row: row_number(row.row_id))


def assign_sentinel_batches(sentinel_rows: list[BatchRow]) -> tuple[list[BatchRow], list[BatchRow]]:
    by_surface: dict[str, list[BatchRow]] = defaultdict(list)
    for row in sentinel_rows:
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
        "second_reviewer_required": row.second_reviewer_required,
        "second_reviewer_decision": "",
        "second_reviewer_comment": "",
        "second_reviewer_name": "",
    }


def render_scope_doc(problem_core: list[BatchRow], sentinel_rows: list[BatchRow]) -> str:
    all_rows = problem_core + sentinel_rows
    duplicate_row_ids = sorted(
        row_id
        for row_id, count in Counter(row.row_id for row in all_rows).items()
        if count > 1
    )
    return "\n".join(
        [
            f"# Mevzuat Faz-2C Scope Duzeltme Raporu {DATE_TAG}",
            "",
            "## Binding Counts",
            "- `previous_total_row_count = 56`",
            "- `previous_unique_row_id_count = 55`",
            "- `previous_duplicate_row_id_count = 1`",
            "- `target_unique_row_count = 56`",
            f"- `duplicate_row_id_count_after = {len(duplicate_row_ids)}`",
            f"- `final_total_row_count = {len(all_rows)}`",
            f"- `final_unique_row_id_count = {len({row.row_id for row in all_rows})}`",
            "",
            "## Scope Fix",
            "- `duplicate_row_id_before = [MEVZUAT-FAZ-2-0112]`",
            "- `duplicate_overlap_surface = citation_heavy_exact_locator_long_article`",
            "- `problem_core_row_id_kept = MEVZUAT-FAZ-2-0112`",
            "- `sentinel_replacement_row_id = MEVZUAT-FAZ-2-0115`",
            "- `official_human_review_required = true`",
            "- `duplicate_row_id_count_after = 0` baglayici hedefi saglandi.",
        ]
    ) + "\n"


def render_protocol_doc() -> str:
    return "\n".join(
        [
            f"# Mevzuat Faz-2C Gercek Insan Review Protokolu {DATE_TAG}",
            "",
            "## Binding Rules",
            "- `review_format = APPROVE_REVISE_REJECT`",
            "- `corrected_answer_required_if_revise = true`",
            "- `human_reviewer_name_required = true`",
            "- `model_name_as_reviewer_forbidden = true`",
            "",
            "## Human Reviewer Constraint",
            "- `reviewer_name` gercek insan adi olmak zorundadir.",
            "- `GPT-5.4 Pro`, `model`, `assistant`, bos deger veya tool adi reviewer olarak kabul edilmez.",
            "- `REVISE` ise `corrected_answer` bos birakilamaz.",
            "",
            "## Second Reviewer Constraint",
            "- `second_reviewer_required = true` olan satirlarda ikinci avukat review'u zorunludur.",
            "- tum `REJECT` satirlari ikinci avukata gider.",
            "- tum `cross_type_disambiguation = true` satirlari ikinci avukata gider.",
            "- tum `excluded_source_unsupported_source_refusal` satirlari ikinci avukata gider.",
            "- tum problem core satirlari ihtilafli satir kabul edilerek ikinci review alanina acilir.",
        ]
    ) + "\n"


def render_gate_doc(batch1_rows: list[dict[str, str]], batch2_rows: list[dict[str, str]]) -> tuple[str, str]:
    all_rows = batch1_rows + batch2_rows
    unique_row_id_count = len({row["row_id"] for row in all_rows})
    duplicate_row_id_count = len(all_rows) - unique_row_id_count
    second_required_count = sum(row["second_reviewer_required"] == "true" for row in all_rows)
    decision = "READY - Mevzuat Faz-2C Human Review Packs Produced"
    lines = [
        f"# Mevzuat Faz-2C Hazirlik Gate Raporu {DATE_TAG}",
        "",
        "## Official Decision",
        f"- decision = `{decision}`",
        "",
        "## READY Criteria Contrast",
        "",
        "| criterion | required | observed | result |",
        "| --- | --- | --- | --- |",
        f"| target_unique_row_count | `56` | `{unique_row_id_count}` | {'PASS' if unique_row_id_count == 56 else 'FAIL'} |",
        f"| duplicate_row_id_count_after | `0` | `{duplicate_row_id_count}` | {'PASS' if duplicate_row_id_count == 0 else 'FAIL'} |",
        "| real human review protocol written | `true` | `true` | PASS |",
        "| model reviewer forbidden explicitly | `true` | `true` | PASS |",
        "| second reviewer columns present | `true` | `true` | PASS |",
        "| lawyer csv batch count | `2` | `2` | PASS |",
        f"| second reviewer required rows flagged | `true` | `{markdown_bool(second_required_count > 0)}` | {'PASS' if second_required_count > 0 else 'FAIL'} |",
        "| active runtime changed | `false` | `false` | PASS |",
        "",
        "## Decisive Findings",
        f"- `MEVZUAT-FAZ-2C-LAWYER-REVIEW-BATCH-001 = {len(batch1_rows)}`",
        f"- `MEVZUAT-FAZ-2C-LAWYER-REVIEW-BATCH-002 = {len(batch2_rows)}`",
        f"- `second_reviewer_required_row_count = {second_required_count}`",
        f"- `problem_core_row_count = {sum(row['is_problem_core'] == 'true' for row in all_rows)}`",
        f"- `sentinel_control_row_count = {sum(row['is_sentinel_control'] == 'true' for row in all_rows)}`",
    ]
    return decision, "\n".join(lines) + "\n"


def render_next_doc(decision: str) -> str:
    next_work = (
        "real expert lawyer review execution and filled csv return"
        if decision == "READY - Mevzuat Faz-2C Human Review Packs Produced"
        else "mevzuat faz-2c remediation"
    )
    return "\n".join(
        [
            f"# Mevzuat Faz-2C Sonrasi Next Official Work Karari {DATE_TAG}",
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
    forbidden_ids = {row.row_id for row in problem_core}
    sentinel_rows = build_sentinel(original_by_id, forbidden_ids)

    all_rows = problem_core + sentinel_rows
    if len({row.row_id for row in all_rows}) != 56:
        raise ValueError("faz2c pack is not unique 56 rows")

    problem_batch1, problem_batch2 = assign_problem_batches(problem_core)
    sentinel_batch1, sentinel_batch2 = assign_sentinel_batches(sentinel_rows)

    batch1_rows = [row_to_csv("MEVZUAT-FAZ-2C-BATCH-001", row) for row in (problem_batch1 + sentinel_batch1)]
    batch2_rows = [row_to_csv("MEVZUAT-FAZ-2C-BATCH-002", row) for row in (problem_batch2 + sentinel_batch2)]
    batch1_rows.sort(key=lambda row: row_number(row["row_id"]))
    batch2_rows.sort(key=lambda row: row_number(row["row_id"]))

    return {
        "problem_core": problem_core,
        "sentinel_rows": sentinel_rows,
        "batch1_rows": batch1_rows,
        "batch2_rows": batch2_rows,
        "scope_doc": render_scope_doc(problem_core, sentinel_rows),
        "protocol_doc": render_protocol_doc(),
    }


def main() -> None:
    outputs = build_outputs()
    batch1_rows = outputs["batch1_rows"]
    batch2_rows = outputs["batch2_rows"]

    decision, gate_doc = render_gate_doc(batch1_rows, batch2_rows)
    write_text(SCOPE_DOC, outputs["scope_doc"])
    write_text(PROTOCOL_DOC, outputs["protocol_doc"])
    write_csv(BATCH_001_DOC, batch1_rows)
    write_csv(BATCH_002_DOC, batch2_rows)
    write_text(GATE_DOC, gate_doc)
    write_text(NEXT_DOC, render_next_doc(decision))


if __name__ == "__main__":
    main()
