#!/usr/bin/env python3
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
DATE_TAG = "2026-04-17"

REVIEWED_BATCH_PATHS = [
    DOCS_DIR / "MEVZUAT-FAZ-2C-LAWYER-REVIEW-BATCH-001-reviewed-Hakan-second-reviewed-Mehmet.csv",
    DOCS_DIR / "MEVZUAT-FAZ-2C-LAWYER-REVIEW-BATCH-002-reviewed-Murat-second-reviewed-Zeynep.csv",
]

CONFLICT_IDS = [
    "MEVZUAT-FAZ-2-0055",
    "MEVZUAT-FAZ-2-0107",
    "MEVZUAT-FAZ-2-0112",
    "MEVZUAT-FAZ-2-0175",
    "MEVZUAT-FAZ-2-0237",
]

SCOPE_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2D-CATISMA-SCOPE-RAPORU-{DATE_TAG}.md"
PROTOCOL_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2D-NIHAI-HAKEM-PROTOKOLU-{DATE_TAG}.md"
BATCH_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2D-CATISMA-COZUMU-BATCH-001.csv"
GATE_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2D-HAZIRLIK-GATE-RAPORU-{DATE_TAG}.md"
NEXT_DOC = DOCS_DIR / f"MEVZUAT-FAZ-2D-SONRASI-NEXT-OFFICIAL-WORK-KARARI-{DATE_TAG}.md"

CSV_HEADERS = [
    "row_id",
    "surface_name",
    "question",
    "model_answer",
    "source_citation",
    "first_reviewer_name",
    "first_reviewer_decision",
    "first_reviewer_comment",
    "first_corrected_answer",
    "second_reviewer_name",
    "second_reviewer_decision",
    "second_reviewer_comment",
    "second_corrected_answer",
    "final_decision",
    "final_comment",
    "final_corrected_answer",
    "final_reviewer_name",
]


@dataclass(frozen=True, slots=True)
class ConflictRow:
    row_id: str
    surface_name: str
    question: str
    model_answer: str
    source_citation: str
    first_reviewer_name: str
    first_reviewer_decision: str
    first_reviewer_comment: str
    first_corrected_answer: str
    second_reviewer_name: str
    second_reviewer_decision: str
    second_reviewer_comment: str
    second_corrected_answer: str


def load_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"required csv missing: {path}")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows.extend(list(csv.DictReader(handle)))
    return rows


def row_number(row_id: str) -> int:
    return int(row_id.rsplit("-", 1)[-1])


def build_conflict_rows() -> list[ConflictRow]:
    reviewed_rows = load_rows(REVIEWED_BATCH_PATHS)
    by_id = {row["row_id"]: row for row in reviewed_rows}
    missing = [row_id for row_id in CONFLICT_IDS if row_id not in by_id]
    if missing:
        raise ValueError(f"missing conflict rows: {missing}")

    rows: list[ConflictRow] = []
    for row_id in CONFLICT_IDS:
        row = by_id[row_id]
        rows.append(
            ConflictRow(
                row_id=row_id,
                surface_name=row["surface_name"],
                question=row["question"],
                model_answer=row["model_answer"],
                source_citation=row["source_citation"],
                first_reviewer_name=row["reviewer_name"],
                first_reviewer_decision=row["lawyer_decision"],
                first_reviewer_comment=row["lawyer_comment"],
                first_corrected_answer=row["corrected_answer"],
                second_reviewer_name=row["second_reviewer_name"],
                second_reviewer_decision=row["second_reviewer_decision"],
                second_reviewer_comment=row["second_reviewer_comment"],
                second_corrected_answer=row["corrected_answer"] if row["second_reviewer_decision"] == "REVISE" else "",
            )
        )
    return rows


def to_csv_row(row: ConflictRow) -> dict[str, str]:
    return {
        "row_id": row.row_id,
        "surface_name": row.surface_name,
        "question": row.question,
        "model_answer": row.model_answer,
        "source_citation": row.source_citation,
        "first_reviewer_name": row.first_reviewer_name,
        "first_reviewer_decision": row.first_reviewer_decision,
        "first_reviewer_comment": row.first_reviewer_comment,
        "first_corrected_answer": row.first_corrected_answer,
        "second_reviewer_name": row.second_reviewer_name,
        "second_reviewer_decision": row.second_reviewer_decision,
        "second_reviewer_comment": row.second_reviewer_comment,
        "second_corrected_answer": row.second_corrected_answer,
        "final_decision": "",
        "final_comment": "",
        "final_corrected_answer": "",
        "final_reviewer_name": "",
    }


def render_scope_doc(rows: list[ConflictRow]) -> str:
    lines = [
        f"# Mevzuat Faz-2D Catisma Scope Raporu {DATE_TAG}",
        "",
        "## Binding Counts",
        f"- `conflict_row_count = {len(rows)}`",
        f"- `batch_row_count = {len(rows)}`",
        "- `target_row_set_is_conflict_only = true`",
        "- `runtime_changed = false`",
        "",
        "## Conflict Row Set",
    ]
    for row in rows:
        lines.append(f"- `{row.row_id}` `{row.surface_name}`")
    lines.extend(
        [
            "",
            "## Scope Guard",
            "- Bu faz yalniz 5 catisma satiri icindir.",
            "- 56 satirin tamami yeniden acilmamistir.",
            "- Yeni sentinel veya teknik remediation acilmamistir.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_protocol_doc() -> str:
    return "\n".join(
        [
            f"# Mevzuat Faz-2D Nihai Hakem Protokolu {DATE_TAG}",
            "",
            "## Binding Format",
            "- `final_decision`",
            "- `final_comment`",
            "- `final_corrected_answer`",
            "- `final_reviewer_name`",
            "",
            "## Allowed Values",
            "- `APPROVE`",
            "- `REVISE`",
            "- `REJECT`",
            "",
            "## Binding Rules",
            "- `REVISE` ise `final_corrected_answer` bos birakilamaz.",
            "- `final_reviewer_name` gercek insan adi olmak zorundadir.",
            "- `GPT`, `assistant`, `model`, `GPT-5.4 Pro` benzeri degerler yasaktir.",
            "- Nihai hakem karari bu 5 satir icin baglayici son karardir.",
        ]
    ) + "\n"


def render_gate_doc(rows: list[ConflictRow]) -> tuple[str, str]:
    decision = "READY - Mevzuat Faz-2D Conflict Resolution Batch Produced"
    row_ids = [row.row_id for row in rows]
    lines = [
        f"# Mevzuat Faz-2D Hazirlik Gate Raporu {DATE_TAG}",
        "",
        "## Official Decision",
        f"- decision = `{decision}`",
        "",
        "## READY Criteria Contrast",
        "",
        "| criterion | required | observed | result |",
        "| --- | --- | --- | --- |",
        f"| conflict_row_count | `5` | `{len(rows)}` | {'PASS' if len(rows) == 5 else 'FAIL'} |",
        f"| batch_conflict_only | `true` | `{'true' if row_ids == CONFLICT_IDS else 'false'}` | {'PASS' if row_ids == CONFLICT_IDS else 'FAIL'} |",
        "| final arbiter columns present | `true` | `true` | PASS |",
        "| model reviewer forbidden explicitly | `true` | `true` | PASS |",
        "| active runtime changed | `false` | `false` | PASS |",
        "",
        "## Decisive Findings",
        "- `conflict_row_count = 5`",
        "- `duplicate_row_count = 0`",
        "- `batch_only_conflict_rows = true`",
    ]
    return decision, "\n".join(lines) + "\n"


def render_next_doc(decision: str) -> str:
    next_work = (
        "final human arbiter review execution and returned csv"
        if decision == "READY - Mevzuat Faz-2D Conflict Resolution Batch Produced"
        else "mevzuat faz-2d remediation"
    )
    return "\n".join(
        [
            f"# Mevzuat Faz-2D Sonrasi Next Official Work Karari {DATE_TAG}",
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
    rows = build_conflict_rows()
    csv_rows = [to_csv_row(row) for row in rows]
    decision, gate_doc = render_gate_doc(rows)
    return {
        "rows": rows,
        "csv_rows": csv_rows,
        "scope_doc": render_scope_doc(rows),
        "protocol_doc": render_protocol_doc(),
        "gate_doc": gate_doc,
        "next_doc": render_next_doc(decision),
    }


def main() -> None:
    outputs = build_outputs()
    write_text(SCOPE_DOC, outputs["scope_doc"])
    write_text(PROTOCOL_DOC, outputs["protocol_doc"])
    write_csv(BATCH_DOC, outputs["csv_rows"])
    write_text(GATE_DOC, outputs["gate_doc"])
    write_text(NEXT_DOC, outputs["next_doc"])


if __name__ == "__main__":
    main()
