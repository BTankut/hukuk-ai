#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "api-gateway" / "src"))

from faz2a_hardening import canonicalize_source_id, extract_law_code_from_source_id, resolve_target_date  # noqa: E402

from canonical_norm_lib import (  # noqa: E402
    canonical_norm_key,
    canonical_norm_matches_target,
    infer_kanun_no,
    parse_canonical_norm_key,
)

INLINE_CITATION_RE = re.compile(r"\[Kaynak:\s*([^\]]+)\]")
LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;?!])\s+")
DEFAULT_TODAY = date(2026, 3, 24)
FAILURE_CLASSES = {
    "canonical_alias_mismatch",
    "target_law_or_article_priority_miss",
    "citation_projection_gap",
    "mode_drop_on_supported_canonical_source",
}


@dataclass(frozen=True)
class EvalRow:
    family: str
    question_id: str
    payload: dict[str, Any]


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_sources(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        source_id = canonicalize_source_id(value)
        if not source_id or source_id in seen:
            continue
        normalized.append(source_id)
        seen.add(source_id)
    return normalized


def load_question_maps(paths: list[Path]) -> dict[str, dict[str, dict[str, Any]]]:
    output: dict[str, dict[str, dict[str, Any]]] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        questions = payload["questions"] if isinstance(payload, dict) else payload
        family = path.stem.replace("test_questions_", "").replace("test_questions", "faz1-50")
        if family == "v2_95":
            family = "v2-95"
        if family == "v3_170":
            family = "v3-170"
        output[family] = {item["id"]: item for item in questions}
    return output


def report_family(report: dict[str, Any], path: Path) -> str:
    report_meta = report.get("report_meta") or {}
    return str(report_meta.get("eval_family") or path.stem)


def load_eval_rows(paths: list[Path]) -> dict[str, dict[str, EvalRow]]:
    reports: dict[str, dict[str, EvalRow]] = {}
    for path in paths:
        report = json.loads(path.read_text(encoding="utf-8"))
        family = report_family(report, path)
        rows: dict[str, EvalRow] = {}
        for item in report.get("per_question", []):
            rows[item["question_id"]] = EvalRow(family=family, question_id=item["question_id"], payload=item)
        reports[family] = rows
    return reports


def split_claim_units(answer_text: str) -> list[str]:
    raw = str(answer_text or "")
    if not raw.strip():
        return []

    lines = [line.rstrip() for line in raw.splitlines()]
    list_items: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        if LIST_ITEM_RE.match(line):
            item = LIST_ITEM_RE.sub("", line, count=1)
            normalized = normalize_whitespace(item)
            if normalized and not normalized.endswith(":"):
                list_items.append(normalized)
    if list_items:
        return list_items

    flattened = " ".join(line.strip() for line in lines if line.strip())
    parts = [
        normalize_whitespace(part)
        for part in SENTENCE_SPLIT_RE.split(flattened)
        if normalize_whitespace(part)
    ]
    merged_parts: list[str] = []
    for part in parts:
        if part.startswith("[Kaynak:") and merged_parts:
            merged_parts[-1] = normalize_whitespace(f"{merged_parts[-1]} {part}")
            continue
        merged_parts.append(part)
    return [part for part in merged_parts if not part.endswith(":")]


def strip_inline_citations(text: str) -> str:
    return normalize_whitespace(INLINE_CITATION_RE.sub("", text or ""))


def extract_inline_citations(text: str) -> list[str]:
    citations: list[str] = []
    seen: set[str] = set()
    for raw in INLINE_CITATION_RE.findall(text or ""):
        source_id = canonicalize_source_id(raw)
        if not source_id or source_id in seen:
            continue
        citations.append(source_id)
        seen.add(source_id)
    return citations


def _parse_optional_date(value: Any) -> date | None:
    if value in {None, ""}:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _passes_temporal_surface(evidence: dict[str, Any], *, target_date: date) -> bool:
    start = _parse_optional_date(evidence.get("yururluk_baslangic"))
    end = _parse_optional_date(evidence.get("yururluk_bitis"))
    mulga = evidence.get("mulga")
    if mulga is True:
        return False
    if start and target_date < start:
        return False
    if end and target_date > end:
        return False
    return True


def _passes_law_scope_surface(source_id: str, *, law_scope_signal: dict[str, Any]) -> bool:
    scope_class = (law_scope_signal or {}).get("scope_class")
    expected = (law_scope_signal or {}).get("expected_law_scope") or []
    if scope_class != "single_law_high_conf" or not expected:
        return True
    return extract_law_code_from_source_id(source_id) == expected[0]


def _canonical_norm_key_for_evidence(item: dict[str, Any]) -> str:
    return canonical_norm_key(
        source_type=item.get("source_type"),
        kanun_no=item.get("law_no") or item.get("kanun_no"),
        law_short_name=item.get("law_short_name") or item.get("kanun_kisa_adi"),
        source_id=item.get("source_id") or item.get("citation"),
        madde_no=item.get("madde_no"),
        fikra_no=item.get("fikra_no"),
        yururluk_baslangic=item.get("yururluk_baslangic"),
        yururluk_bitis=item.get("yururluk_bitis"),
        mulga=item.get("mulga"),
    )


def _canonical_norm_key_for_source_id(source_id: str | None) -> str | None:
    normalized = canonicalize_source_id(source_id)
    if not normalized:
        return None
    law_short_name = extract_law_code_from_source_id(normalized)
    return canonical_norm_key(
        law_short_name=law_short_name,
        source_id=normalized,
    )


def _source_id_to_evidence_map(
    assembled_evidence: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    mapping: dict[str, list[dict[str, Any]]] = {}
    for item in assembled_evidence:
        source_id = canonicalize_source_id(item.get("source_id") or item.get("citation"))
        if not source_id:
            continue
        mapping.setdefault(source_id, []).append(item)
    return mapping


def _resolve_best_canonical_key_for_source_id(
    source_id: str | None,
    *,
    assembled_evidence: list[dict[str, Any]],
) -> str | None:
    normalized = canonicalize_source_id(source_id)
    if not normalized:
        return None
    mapping = _source_id_to_evidence_map(assembled_evidence)
    candidates = mapping.get(normalized) or []
    if not candidates:
        return _canonical_norm_key_for_source_id(normalized)
    sorted_candidates = sorted(
        candidates,
        key=lambda item: (
            0 if item.get("fikra_no") in {None, ""} else 1,
            str(item.get("fikra_no") or ""),
            _canonical_norm_key_for_evidence(item),
        ),
    )
    return _canonical_norm_key_for_evidence(sorted_candidates[0])


def _normalize_explicit_article_refs(values: list[Any] | None) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for item in values or []:
        if isinstance(item, dict):
            law = item.get("law")
            madde = item.get("madde")
            if law and madde:
                refs.append((str(law), str(madde)))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            refs.append((str(item[0]), str(item[1])))
    return refs


def _build_supported_projection(
    *,
    answer_text: str,
    question_raw: str,
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    law_scope_signal: dict[str, Any],
) -> dict[str, Any]:
    whitelist = {
        canonicalize_source_id(source_id)
        for source_id in allowed_source_whitelist
        if canonicalize_source_id(source_id)
    }
    target_date, _ = resolve_target_date(question_raw, today=DEFAULT_TODAY)
    evidence_by_source = _source_id_to_evidence_map(assembled_evidence)

    kept_claim_units: list[dict[str, Any]] = []
    supported_source_ids: list[str] = []
    supported_canonical_norm_keys: list[str] = []

    for unit_text in split_claim_units(answer_text):
        raw_citations = extract_inline_citations(unit_text)
        supported_for_unit: list[str] = []
        supported_norms_for_unit: list[str] = []
        for source_id in raw_citations:
            if source_id not in whitelist:
                continue
            evidence_items = evidence_by_source.get(source_id) or []
            unit_supported = False
            for evidence in evidence_items:
                if not _passes_temporal_surface(evidence, target_date=target_date):
                    continue
                if not _passes_law_scope_surface(source_id, law_scope_signal=law_scope_signal):
                    continue
                unit_supported = True
                canonical_key = _canonical_norm_key_for_evidence(evidence)
                if canonical_key not in supported_norms_for_unit:
                    supported_norms_for_unit.append(canonical_key)
                if canonical_key not in supported_canonical_norm_keys:
                    supported_canonical_norm_keys.append(canonical_key)
            if unit_supported and source_id not in supported_for_unit:
                supported_for_unit.append(source_id)
                if source_id not in supported_source_ids:
                    supported_source_ids.append(source_id)

        claim_text = strip_inline_citations(unit_text)
        if supported_norms_for_unit:
            kept_claim_units.append(
                {
                    "claim_text": claim_text,
                    "supported_source_ids": supported_for_unit,
                    "supported_canonical_norm_keys": supported_norms_for_unit,
                }
            )

    return {
        "kept_claim_units": kept_claim_units,
        "supported_source_ids": supported_source_ids,
        "supported_canonical_norm_keys": supported_canonical_norm_keys,
    }


def quality_loss_reasons(*, expected_mode: str, row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if expected_mode == "answer":
        if not bool(row.get("has_citation")):
            reasons.append("citation_miss")
        if float(row.get("correct_source_rate") or 0.0) < 1.0:
            reasons.append("correct_source_miss")
    if bool(row.get("refusal_correct")) is False:
        reasons.append("refusal_miss")
    return reasons


def _parser_target(parsed_query: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None]:
    refs = _normalize_explicit_article_refs(parsed_query.get("explicit_article_refs"))
    if not refs:
        return None, None, None, None
    law, madde = refs[0]
    law_short = extract_law_code_from_source_id(f"{law} m.{madde}") or str(law).upper()
    law_no = infer_kanun_no(law_short_name=law_short)
    target_key = canonical_norm_key(
        law_short_name=law_short,
        kanun_no=law_no,
        source_id=f"{law_short} m.{madde}",
        madde_no=madde,
    )
    return law_no, str(madde).lower(), None, target_key


def _canonical_key_compatible(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    left_parts = parse_canonical_norm_key(left)
    right_parts = parse_canonical_norm_key(right)
    if not left_parts or not right_parts:
        return False
    if left_parts.get("source_type") != right_parts.get("source_type"):
        return False
    if left_parts.get("kanun_no") != right_parts.get("kanun_no"):
        return False
    if left_parts.get("madde_no") != right_parts.get("madde_no"):
        return False
    left_fikra = left_parts.get("fikra_no")
    right_fikra = right_parts.get("fikra_no")
    if left_fikra == right_fikra:
        return True
    return left_fikra is None or right_fikra is None


def _count_compatible_overlap(left_values: set[str], right_values: set[str]) -> int:
    matched = 0
    for left in left_values:
        if any(_canonical_key_compatible(left, right) for right in right_values):
            matched += 1
    return matched


def classify_failure(
    *,
    expected_mode: str,
    rc_d_final_mode: str | None,
    expected_primary_key: str | None,
    rc_d_primary_key: str | None,
    rc_d_emitted_source_ids: list[str],
    expected_citation_source_ids: list[str],
    expected_citation_keys: list[str],
    supported_canonical_norm_keys: list[str],
    emitted_canonical_norm_keys: list[str],
    parser_target_law_no: str | None,
    parser_target_article_no: str | None,
    parser_target_paragraph_no: str | None,
    kept_claim_units: list[dict[str, Any]],
) -> str:
    supported_keys = set(supported_canonical_norm_keys)
    emitted_keys = set(emitted_canonical_norm_keys)
    raw_expected = set(normalize_sources(expected_citation_source_ids))
    raw_emitted = set(normalize_sources(rc_d_emitted_source_ids))
    expected_key_set = set(expected_citation_keys)
    covered_key_set: set[str] = set()
    for unit in kept_claim_units:
        covered_key_set.update(unit.get("supported_canonical_norm_keys") or [])

    parser_target_supported = bool(
        parser_target_law_no
        and parser_target_article_no
        and any(
            canonical_norm_matches_target(
                key,
                law_no=parser_target_law_no,
                article_no=parser_target_article_no,
                paragraph_no=parser_target_paragraph_no,
            )
            for key in supported_keys
        )
    )
    primary_matches_parser_target = bool(
        rc_d_primary_key
        and parser_target_law_no
        and parser_target_article_no
        and canonical_norm_matches_target(
            rc_d_primary_key,
            law_no=parser_target_law_no,
            article_no=parser_target_article_no,
            paragraph_no=parser_target_paragraph_no,
        )
    )

    if parser_target_supported and not primary_matches_parser_target:
        return "target_law_or_article_priority_miss"
    if expected_key_set & supported_keys:
        raw_overlap = len(raw_expected & raw_emitted)
        canonical_overlap = _count_compatible_overlap(expected_key_set, emitted_keys)
        if canonical_overlap > raw_overlap and _canonical_key_compatible(rc_d_primary_key, expected_primary_key):
            return "canonical_alias_mismatch"
    if covered_key_set and not emitted_keys.issuperset(covered_key_set):
        return "citation_projection_gap"
    if expected_mode == "answer" and rc_d_final_mode == "refusal" and supported_keys:
        return "mode_drop_on_supported_canonical_source"
    if expected_mode == "answer" and rc_d_final_mode == "partial" and supported_keys:
        return "mode_drop_on_supported_canonical_source"
    return "citation_projection_gap"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ5 source-attribution divergence pack.")
    parser.add_argument("--faz1-questions", required=True, type=Path)
    parser.add_argument("--v2-questions", required=True, type=Path)
    parser.add_argument("--v3-questions", required=True, type=Path)
    parser.add_argument("--faz1-rc-d", required=True, type=Path)
    parser.add_argument("--v2-rc-d", required=True, type=Path)
    parser.add_argument("--v3-rc-d", required=True, type=Path)
    parser.add_argument("--faz1-rc-e", required=True, type=Path)
    parser.add_argument("--v2-rc-e", required=True, type=Path)
    parser.add_argument("--v3-rc-e", required=True, type=Path)
    parser.add_argument("--output-jsonl", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser.parse_args()


def render_markdown(*, rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ 5 Source Attribution Divergence Pack",
        "",
        f"- total_records: `{summary['total_records']}`",
        "",
        "## By Family",
        "",
    ]
    for family, count in summary["by_family"].items():
        lines.append(f"- {family}: `{count}`")
    lines.extend(["", "## By Class", ""])
    for failure_class, count in summary["by_class"].items():
        lines.append(f"- {failure_class}: `{count}`")
    lines.extend(["", "## By Origin", ""])
    for origin, count in summary["by_origin"].items():
        lines.append(f"- {origin}: `{count}`")
    lines.extend(["", "## Sample", ""])
    for row in rows[:10]:
        lines.append(
            f"- {row['family']} {row['question_id']} -> `{row['failure_class']}` "
            f"(origin `{row['quality_loss_origin']}`)"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    question_maps = load_question_maps([args.faz1_questions, args.v2_questions, args.v3_questions])
    rc_d_reports = load_eval_rows([args.faz1_rc_d, args.v2_rc_d, args.v3_rc_d])
    rc_e_reports = load_eval_rows([args.faz1_rc_e, args.v2_rc_e, args.v3_rc_e])

    rows: list[dict[str, Any]] = []
    by_family = Counter()
    by_class = Counter()
    by_origin = Counter()

    for family, question_map in question_maps.items():
        for question_id, question in question_map.items():
            rc_d_row = rc_d_reports[family][question_id].payload
            rc_e_row = rc_e_reports[family][question_id].payload
            expected_mode = "refusal" if question.get("refusal_expected") else "answer"
            rc_d_reasons = quality_loss_reasons(expected_mode=expected_mode, row=rc_d_row)
            rc_e_reasons = quality_loss_reasons(expected_mode=expected_mode, row=rc_e_row)
            if not rc_d_reasons and not rc_e_reasons:
                continue

            quality_loss_origin = "shared"
            if rc_d_reasons and not rc_e_reasons:
                quality_loss_origin = "rc_d_only"
            elif rc_e_reasons and not rc_d_reasons:
                quality_loss_origin = "rc_e_only"

            trace = rc_d_row.get("trace") or {}
            parsed_query = trace.get("parsed_query") or {}
            question_raw = str(trace.get("question_raw") or rc_d_row.get("question_text") or question.get("question") or "")
            assembled_evidence = list(
                trace.get("assembled_evidence")
                or ((trace.get("context_assembly") or {}).get("assembled_evidence"))
                or []
            )
            allowed_source_whitelist = list(
                trace.get("allowed_source_whitelist")
                or ((trace.get("context_assembly") or {}).get("allowed_source_whitelist"))
                or []
            )
            projection_answer_text = (
                rc_d_row.get("answer_text")
                if rc_d_row.get("final_mode") in {"answer", "partial"}
                else rc_e_row.get("answer_text") or rc_d_row.get("answer_text")
            )
            projection = _build_supported_projection(
                answer_text=str(projection_answer_text or ""),
                question_raw=question_raw,
                assembled_evidence=assembled_evidence,
                allowed_source_whitelist=allowed_source_whitelist,
                law_scope_signal=trace.get("law_scope_signal") or {},
            )

            expected_citation_source_ids = normalize_sources(question.get("expected_sources"))
            expected_citation_keys = [
                canonical_norm_key(source_id=source_id, law_short_name=extract_law_code_from_source_id(source_id))
                for source_id in expected_citation_source_ids
            ]
            expected_primary_source_id = expected_citation_source_ids[0] if expected_citation_source_ids else None
            expected_primary_key = expected_citation_keys[0] if expected_citation_keys else None
            rc_d_primary_source_id = canonicalize_source_id(
                ((rc_d_row.get("answer_contract") or {}).get("primary_source_id"))
                or (rc_d_row.get("cited_sources") or [None])[0]
            )
            rc_d_primary_key = _resolve_best_canonical_key_for_source_id(
                rc_d_primary_source_id,
                assembled_evidence=assembled_evidence,
            )
            rc_d_emitted_source_ids = normalize_sources(rc_d_row.get("cited_sources"))
            rc_d_emitted_keys = [
                key
                for key in (
                    _resolve_best_canonical_key_for_source_id(source_id, assembled_evidence=assembled_evidence)
                    for source_id in rc_d_emitted_source_ids
                )
                if key
            ]
            parser_target_law_no, parser_target_article_no, parser_target_paragraph_no, _ = _parser_target(parsed_query)

            failure_class = classify_failure(
                expected_mode=expected_mode,
                rc_d_final_mode=rc_d_row.get("final_mode"),
                expected_primary_key=expected_primary_key,
                rc_d_primary_key=rc_d_primary_key,
                rc_d_emitted_source_ids=rc_d_emitted_source_ids,
                expected_citation_source_ids=expected_citation_source_ids,
                expected_citation_keys=expected_citation_keys,
                supported_canonical_norm_keys=projection["supported_canonical_norm_keys"],
                emitted_canonical_norm_keys=rc_d_emitted_keys,
                parser_target_law_no=parser_target_law_no,
                parser_target_article_no=parser_target_article_no,
                parser_target_paragraph_no=parser_target_paragraph_no,
                kept_claim_units=projection["kept_claim_units"],
            )
            if failure_class not in FAILURE_CLASSES:
                raise RuntimeError(f"Unexpected failure class {failure_class}")

            row = {
                "question_id": question_id,
                "family": family,
                "expected_mode": expected_mode,
                "expected_primary_source_id": expected_primary_source_id,
                "expected_primary_canonical_norm_key": expected_primary_key,
                "expected_citation_source_ids": expected_citation_source_ids,
                "expected_citation_canonical_norm_keys": expected_citation_keys,
                "parser_target_law_no": parser_target_law_no,
                "parser_target_article_no": parser_target_article_no,
                "parser_target_paragraph_no": parser_target_paragraph_no,
                "rc_d_final_mode": rc_d_row.get("final_mode"),
                "rc_d_primary_source_id": rc_d_primary_source_id,
                "rc_d_primary_canonical_norm_key": rc_d_primary_key,
                "rc_d_emitted_source_ids": rc_d_emitted_source_ids,
                "rc_d_emitted_canonical_norm_keys": rc_d_emitted_keys,
                "rc_d_supported_source_ids": projection["supported_source_ids"],
                "rc_d_supported_canonical_norm_keys": projection["supported_canonical_norm_keys"],
                "rc_d_kept_claim_units": projection["kept_claim_units"],
                "quality_loss_origin": quality_loss_origin,
                "failure_class": failure_class,
            }
            rows.append(row)
            by_family[family] += 1
            by_class[failure_class] += 1
            by_origin[quality_loss_origin] += 1

    rows.sort(key=lambda item: (item["family"], item["question_id"]))
    summary = {
        "total_records": len(rows),
        "by_family": dict(sorted(by_family.items())),
        "by_class": dict(sorted(by_class.items())),
        "by_origin": dict(sorted(by_origin.items())),
    }

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    with args.output_jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    args.output_md.write_text(render_markdown(rows=rows, summary=summary), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
