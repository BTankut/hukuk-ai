#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "api-gateway" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "faz3"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "faz4"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "faz5"))

from faz2a_hardening import canonical_norm_key, canonicalize_source_id, extract_law_code_from_source_id  # noqa: E402
from build_citation_family_failure_pack import (  # noqa: E402
    build_failure_pack,
    load_eval_rows as load_phase_eval_rows,
    load_question_maps as load_phase_question_maps,
    normalize_sources,
)

FAMILY_ORDER = ["faz1-50", "v2-95", "v3-170"]
QUESTION_PATHS = {
    "faz1-50": PROJECT_ROOT / "configs" / "evaluation" / "test_questions.json",
    "v2-95": PROJECT_ROOT / "configs" / "evaluation" / "test_questions_v2_95.json",
    "v3-170": PROJECT_ROOT / "configs" / "evaluation" / "test_questions_v3_170.json",
}
RC_A_REPORT_PATHS = {
    "faz1-50": PROJECT_ROOT / "evaluation" / "reports" / "eval_baseline_faz1-50_matched_dgxnode2_base_wave15_20260323.json",
    "v2-95": PROJECT_ROOT / "evaluation" / "reports" / "eval_baseline_v2-95_matched_dgxnode2_base_wave15_r2_20260323.json",
    "v3-170": PROJECT_ROOT / "evaluation" / "reports" / "eval_baseline_v3-170_matched_dgxnode2_base_wave15_20260323.json",
}
RC_C_REPORT_PATHS = {
    "faz1-50": PROJECT_ROOT / "evaluation" / "reports" / "eval_faz2b_rc_c_faz1-50_20260323.json",
    "v2-95": PROJECT_ROOT / "evaluation" / "reports" / "eval_faz2b_rc_c_v2-95_20260323.json",
    "v3-170": PROJECT_ROOT / "evaluation" / "reports" / "eval_faz2b_rc_c_v3-170_20260323.json",
}
RC_D_REPORT_PATHS = {
    "faz1-50": PROJECT_ROOT / "evaluation" / "reports" / "eval_faz3_rc_d_faz1-50_20260323.json",
    "v2-95": PROJECT_ROOT / "evaluation" / "reports" / "eval_faz3_rc_d_v2-95_20260323.json",
    "v3-170": PROJECT_ROOT / "evaluation" / "reports" / "eval_faz3_rc_d_v3-170_20260323.json",
}
RC_F_REPORT_PATHS = {
    "faz1-50": PROJECT_ROOT / "evaluation" / "reports" / "eval_faz5_rc_f_faz1-50_20260323.json",
    "v2-95": PROJECT_ROOT / "evaluation" / "reports" / "eval_faz5_rc_f_v2-95_20260323.json",
    "v3-170": PROJECT_ROOT / "evaluation" / "reports" / "eval_faz5_rc_f_v3-170_20260323.json",
}
FAZ4_PACK_PATH = PROJECT_ROOT / "evaluation" / "reports" / "faz4-citation-family-failure-pack-2026-03-23.jsonl"
FAZ5_DIVERGENCE_PACK_PATH = PROJECT_ROOT / "evaluation" / "reports" / "faz5-source-attribution-divergence-pack-2026-03-23.jsonl"

ALLOWED_PRIMARY_REASONS = {
    "retrieval_source_absent",
    "assembly_primary_miss",
    "model_primary_selection_miss",
    "post_generation_primary_flip",
    "citation_omission_with_correct_primary_present",
    "citation_omission_with_correct_support_present",
    "canonical_normalization_mismatch",
    "guardrail_mode_drop",
    "guardrail_block_true_positive",
    "unsupported_true_refusal",
    "evaluator_alignment_mismatch",
}
REPAIR_GATE_MAPPING = {
    "citation_omission_with_correct_primary_present": "serializer-only citation recovery",
    "post_generation_primary_flip": "source-selection immutability recovery",
    "model_primary_selection_miss": "generator source-anchoring recovery",
    "assembly_primary_miss": "retrieval/source-locking reopening",
    "retrieval_source_absent": "retrieval/source-locking reopening",
    "guardrail_mode_drop": "guardrail mode-boundary recovery",
    "canonical_normalization_mismatch": "evaluator-normalization closure",
    "evaluator_alignment_mismatch": "evaluator-normalization closure",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def tracked_key(family: str, question_id: str) -> str:
    return f"{family}:{question_id}"


def parse_tracked_key(value: str) -> tuple[str, str]:
    family, question_id = value.split(":", 1)
    return family, question_id


def family_sort_key(family: str) -> tuple[int, str]:
    try:
        return (FAMILY_ORDER.index(family), family)
    except ValueError:
        return (len(FAMILY_ORDER), family)


def current_git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()


def question_maps_by_family() -> dict[str, dict[str, dict[str, Any]]]:
    return load_phase_question_maps([QUESTION_PATHS[family] for family in FAMILY_ORDER])


def eval_rows_by_family(paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    payload = load_phase_eval_rows([paths[family] for family in FAMILY_ORDER])
    return {
        family: {question_id: row.payload for question_id, row in payload[family].items()}
        for family in FAMILY_ORDER
    }


def expected_mode(question: dict[str, Any] | None, row: dict[str, Any] | None = None) -> str:
    if question and question.get("refusal_expected"):
        return "refusal"
    if row and row.get("refusal_expected"):
        return "refusal"
    return "answer"


def question_expected_sources(question: dict[str, Any], row: dict[str, Any]) -> list[str]:
    return normalize_sources(list(row.get("expected_sources") or question.get("expected_sources") or []))


def default_expected_primary_source(question: dict[str, Any], row: dict[str, Any]) -> str | None:
    sources = question_expected_sources(question, row)
    if sources:
        return sources[0]
    return None


def source_id_to_canonical_key(source_id: str | None) -> str | None:
    normalized = canonicalize_source_id(source_id)
    if not normalized:
        return None
    return canonical_norm_key(
        law_short_name=extract_law_code_from_source_id(normalized),
        source_id=normalized,
    )


def build_normalization_map(
    *,
    assembled_evidence: list[dict[str, Any]],
    source_ids: list[str],
) -> dict[str, str]:
    output: dict[str, str] = {}
    for item in assembled_evidence:
        source_id = canonicalize_source_id(item.get("source_id") or item.get("citation"))
        if not source_id:
            continue
        output[source_id] = canonical_norm_key(
            source_type=item.get("source_type"),
            kanun_no=item.get("law_no") or item.get("kanun_no"),
            law_short_name=item.get("law_short_name") or item.get("kanun_kisa_adi"),
            source_id=source_id,
            madde_no=item.get("madde_no"),
            fikra_no=item.get("fikra_no"),
            yururluk_baslangic=item.get("yururluk_baslangic"),
            yururluk_bitis=item.get("yururluk_bitis"),
            mulga=item.get("mulga"),
        )
    for source_id in source_ids:
        normalized = canonicalize_source_id(source_id)
        if not normalized or normalized in output:
            continue
        key = source_id_to_canonical_key(normalized)
        if key:
            output[normalized] = key
    return output


def row_changed_between(rc_d_row: dict[str, Any], rc_f_row: dict[str, Any]) -> bool:
    return any(
        [
            rc_d_row.get("final_mode") != rc_f_row.get("final_mode"),
            str(rc_d_row.get("answer_text") or "") != str(rc_f_row.get("answer_text") or ""),
            list(rc_d_row.get("cited_sources") or []) != list(rc_f_row.get("cited_sources") or []),
        ]
    )


def build_tracked_pack_data() -> dict[str, Any]:
    question_maps = question_maps_by_family()
    rc_a_reports = load_phase_eval_rows([RC_A_REPORT_PATHS[family] for family in FAMILY_ORDER])
    rc_d_reports = load_phase_eval_rows([RC_D_REPORT_PATHS[family] for family in FAMILY_ORDER])
    rc_f_reports = load_phase_eval_rows([RC_F_REPORT_PATHS[family] for family in FAMILY_ORDER])

    faz3_rows, faz3_summary = build_failure_pack(
        question_maps=question_maps,
        rc_a_reports=rc_a_reports,
        rc_d_reports=rc_d_reports,
    )
    faz4_rows = load_jsonl_rows(FAZ4_PACK_PATH)
    faz5_divergence_rows = load_jsonl_rows(FAZ5_DIVERGENCE_PACK_PATH)
    faz5_legacy_rows, faz5_legacy_summary = build_failure_pack(
        question_maps=question_maps,
        rc_a_reports=rc_a_reports,
        rc_d_reports=rc_f_reports,
    )

    rc_d_raw = eval_rows_by_family(RC_D_REPORT_PATHS)
    rc_f_raw = eval_rows_by_family(RC_F_REPORT_PATHS)

    faz3_by_key = {tracked_key(row["family"], row["question_id"]): row for row in faz3_rows}
    faz4_by_key = {tracked_key(row["family"], row["question_id"]): row for row in faz4_rows}
    faz5_div_by_key = {tracked_key(row["family"], row["question_id"]): row for row in faz5_divergence_rows}
    faz5_legacy_by_key = {tracked_key(row["family"], row["question_id"]): row for row in faz5_legacy_rows}

    union_keys = set(faz3_by_key) | set(faz4_by_key) | set(faz5_div_by_key) | set(faz5_legacy_by_key)
    faz5_delta_changed_keys: set[str] = set()
    for key in union_keys:
        family, question_id = parse_tracked_key(key)
        rc_d_row = rc_d_raw[family][question_id]
        rc_f_row = rc_f_raw[family][question_id]
        if row_changed_between(rc_d_row, rc_f_row):
            faz5_delta_changed_keys.add(key)

    rows: list[dict[str, Any]] = []
    for key in sorted(union_keys, key=lambda item: (family_sort_key(parse_tracked_key(item)[0]), item)):
        family, question_id = parse_tracked_key(key)
        question = question_maps[family][question_id]
        rc_d_row = rc_d_raw[family][question_id]
        expected_sources = question_expected_sources(question, rc_d_row)
        reference_origin = "faz5_divergence" if key in faz5_div_by_key else "faz4_pack" if key in faz4_by_key else "faz3_family_fail"
        reference_row = faz5_div_by_key.get(key) or faz4_by_key.get(key) or faz3_by_key.get(key) or {}

        rows.append(
            {
                "tracked_key": key,
                "family": family,
                "question_id": question_id,
                "question_text": str(question.get("question") or rc_d_row.get("question_text") or ""),
                "expected_mode": expected_mode(question, rc_d_row),
                "expected_primary_source_id": reference_row.get("expected_primary_source_id")
                or reference_row.get("expected_source_id")
                or default_expected_primary_source(question, rc_d_row),
                "expected_sources": expected_sources,
                "reference_origin": reference_origin,
                "source_origins": {
                    "faz3_family_quality_fail": key in faz3_by_key,
                    "faz4_citation_failure_pack": key in faz4_by_key,
                    "faz5_divergence_fail": key in faz5_div_by_key,
                    "faz5_legacy_fail": key in faz5_legacy_by_key,
                    "faz5_delta_changed": key in faz5_delta_changed_keys,
                },
                "source_details": {
                    "faz3_quality_loss_reasons": list(faz3_by_key.get(key, {}).get("quality_loss_reasons") or []),
                    "faz4_failure_class": faz4_by_key.get(key, {}).get("failure_class"),
                    "faz4_quality_loss_reasons": list(faz4_by_key.get(key, {}).get("quality_loss_reasons") or []),
                    "faz5_divergence_class": faz5_div_by_key.get(key, {}).get("failure_class"),
                    "faz5_legacy_failure_class": faz5_legacy_by_key.get(key, {}).get("failure_class"),
                },
            }
        )

    origin_counts = {
        "faz3_family_quality_fail": sum(1 for row in rows if row["source_origins"]["faz3_family_quality_fail"]),
        "faz4_citation_failure_pack": sum(1 for row in rows if row["source_origins"]["faz4_citation_failure_pack"]),
        "faz5_divergence_fail": sum(1 for row in rows if row["source_origins"]["faz5_divergence_fail"]),
        "faz5_legacy_fail": sum(1 for row in rows if row["source_origins"]["faz5_legacy_fail"]),
        "faz5_delta_changed": sum(1 for row in rows if row["source_origins"]["faz5_delta_changed"]),
    }
    family_counts = Counter(row["family"] for row in rows)
    return {
        "generated_from": {
            "faz3_failure_summary": faz3_summary,
            "faz5_legacy_summary": faz5_legacy_summary,
            "faz4_pack_path": str(FAZ4_PACK_PATH.relative_to(PROJECT_ROOT)),
            "faz5_divergence_pack_path": str(FAZ5_DIVERGENCE_PACK_PATH.relative_to(PROJECT_ROOT)),
        },
        "raw_input_counts": {
            "faz3_family_quality_fail": len(faz3_rows),
            "faz4_citation_failure_pack": len(faz4_rows),
            "faz5_divergence_fail": len(faz5_divergence_rows),
            "faz5_legacy_fail": len(faz5_legacy_rows),
            "faz5_delta_changed": len(faz5_delta_changed_keys),
        },
        "origin_counts": origin_counts,
        "family_counts": dict(family_counts),
        "tracked_count": len(rows),
        "dedupe_rule": "family + question_id",
        "rows": rows,
    }


def render_tracked_pack_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# FAZ 6 Tracked Attribution Pack",
        "",
        f"- tracked_count: `{payload['tracked_count']}`",
        f"- dedupe_rule: `{payload['dedupe_rule']}`",
        "",
        "## Raw Inputs",
        "",
    ]
    for key, value in payload["raw_input_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Origin Coverage", ""])
    for key, value in payload["origin_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Family Counts", ""])
    for family in FAMILY_ORDER:
        lines.append(f"- `{family}`: `{payload['family_counts'].get(family, 0)}`")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| family | question_id | expected_mode | expected_primary_source_id | origins | reference_origin |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        origins = ", ".join(key for key, enabled in row["source_origins"].items() if enabled)
        lines.append(
            f"| {row['family']} | {row['question_id']} | {row['expected_mode']} | "
            f"{row['expected_primary_source_id'] or '-'} | {origins} | {row['reference_origin']} |"
        )
    return "\n".join(lines) + "\n"


def extract_retrieved_source_ids(trace: dict[str, Any], assembled_source_ids: list[str]) -> list[str]:
    retrieved: list[str] = []
    retrieval = trace.get("retrieval") or {}
    for chunk in retrieval.get("post_rerank_chunks") or []:
        source_id = canonicalize_source_id(chunk.get("source_id") or chunk.get("citation"))
        if source_id and source_id not in retrieved:
            retrieved.append(source_id)
    if retrieved:
        return retrieved
    return list(assembled_source_ids)


def build_attribution_trace_row(
    *,
    tracked_row: dict[str, Any],
    question: dict[str, Any],
    rc_a_row: dict[str, Any],
    replay_row: dict[str, Any],
) -> dict[str, Any]:
    trace = replay_row.get("trace") or {}
    assembled_evidence = list(
        trace.get("assembled_evidence")
        or ((trace.get("context_assembly") or {}).get("assembled_evidence"))
        or []
    )
    assembled_source_ids = normalize_sources(
        [
            item.get("source_id") or item.get("citation")
            for item in assembled_evidence
            if item.get("source_id") or item.get("citation")
        ]
    )
    retrieved_source_ids = extract_retrieved_source_ids(trace, assembled_source_ids)
    kept_claim_units = list((replay_row.get("answer_contract") or {}).get("claim_units") or [])
    kept_claims = [str(item.get("claim_text") or "") for item in kept_claim_units]
    kept_claim_source_ids = normalize_sources([item.get("source_id") for item in kept_claim_units if item.get("source_id")])
    primary_source_id = canonicalize_source_id((replay_row.get("answer_contract") or {}).get("primary_source_id"))
    kept_claim_support_modes = [
        "primary_source"
        if canonicalize_source_id(item.get("source_id")) == primary_source_id
        else "secondary_source"
        for item in kept_claim_units
    ]
    model_emitted_sources = normalize_sources(list(rc_a_row.get("cited_sources") or []))
    final_citations = normalize_sources(list(replay_row.get("cited_sources") or []))
    all_source_ids = list(
        {
            *tracked_row.get("expected_sources", []),
            *retrieved_source_ids,
            *assembled_source_ids,
            *model_emitted_sources,
            *kept_claim_source_ids,
            *final_citations,
        }
    )
    normalization_map = build_normalization_map(
        assembled_evidence=assembled_evidence,
        source_ids=all_source_ids,
    )
    block_reasons = []
    final_reason = trace.get("final_reason") or replay_row.get("final_reason")
    if final_reason:
        block_reasons.append(str(final_reason))
    generation_outcome = trace.get("generation_outcome") or {}
    for reason in generation_outcome.get("guardrails_reasons") or []:
        reason_value = str(reason)
        if reason_value and reason_value not in block_reasons:
            block_reasons.append(reason_value)

    normalized_trace = {
        "question_id": tracked_row["question_id"],
        "family": tracked_row["family"],
        "question_text": str(question.get("question") or tracked_row["question_text"]),
        "gold_sources": list(tracked_row.get("expected_sources") or []),
        "retrieved_source_ids": retrieved_source_ids,
        "assembled_source_ids": assembled_source_ids,
        "assembled_source_order": assembled_source_ids,
        "assembled_primary_candidate": assembled_source_ids[0] if assembled_source_ids else None,
        "model_answer_text": str(rc_a_row.get("answer_text") or ""),
        "model_emitted_sources": model_emitted_sources,
        "kept_claims": kept_claims,
        "kept_claim_support_modes": kept_claim_support_modes,
        "kept_claim_source_ids": kept_claim_source_ids,
        "final_answer_text": str(replay_row.get("answer_text") or ""),
        "final_citations": final_citations,
        "final_mode": str(replay_row.get("final_mode") or ""),
        "block_reasons": block_reasons,
        "canonical_norm_keys": sorted({value for value in normalization_map.values() if value}),
        "normalization_map": normalization_map,
        "trace_complete": True,
    }
    return normalized_trace


def classify_attribution_loss(row: dict[str, Any]) -> dict[str, Any]:
    gold_sources = normalize_sources(list(row.get("gold_sources") or []))
    gold_set = set(gold_sources)
    retrieved_set = set(normalize_sources(list(row.get("retrieved_source_ids") or [])))
    assembled_set = set(normalize_sources(list(row.get("assembled_source_ids") or [])))
    model_set = set(normalize_sources(list(row.get("model_emitted_sources") or [])))
    final_set = set(normalize_sources(list(row.get("final_citations") or [])))
    kept_set = set(normalize_sources(list(row.get("kept_claim_source_ids") or [])))

    assembled_primary = canonicalize_source_id(row.get("assembled_primary_candidate"))
    model_primary = next(iter(normalize_sources(list(row.get("model_emitted_sources") or []))), None)
    final_primary = next(iter(normalize_sources(list(row.get("final_citations") or []))), None)
    final_mode = str(row.get("final_mode") or "")
    expected_mode = str(row.get("expected_mode") or "answer")

    normalization_map = row.get("normalization_map") or {}
    gold_keys = {normalization_map.get(source_id) or source_id_to_canonical_key(source_id) for source_id in gold_sources}
    final_keys = {normalization_map.get(source_id) or source_id_to_canonical_key(source_id) for source_id in final_set}
    model_keys = {normalization_map.get(source_id) or source_id_to_canonical_key(source_id) for source_id in model_set}

    primary_reason: str
    secondary_reason: str | None = None
    first_loss_stage: str

    if expected_mode == "refusal":
        if final_mode == "refusal":
            if row.get("block_reasons"):
                primary_reason = "guardrail_block_true_positive"
            else:
                primary_reason = "unsupported_true_refusal"
        else:
            primary_reason = "evaluator_alignment_mismatch"
        first_loss_stage = "post_generation"
    elif not (gold_set & retrieved_set):
        primary_reason = "retrieval_source_absent"
        first_loss_stage = "retrieval"
    elif not (gold_set & assembled_set):
        primary_reason = "assembly_primary_miss"
        first_loss_stage = "assembly"
    elif assembled_primary and assembled_primary not in gold_set and (model_primary not in gold_set if model_primary else True):
        primary_reason = "assembly_primary_miss"
        first_loss_stage = "assembly"
    elif final_mode in {"refusal", "blocked"} and (gold_set & (assembled_set | model_set)):
        primary_reason = "guardrail_mode_drop"
        first_loss_stage = "post_generation"
    elif final_primary in gold_set and bool(gold_set - final_set):
        primary_reason = "citation_omission_with_correct_primary_present"
        first_loss_stage = "post_generation"
    elif not final_set and (gold_set & (model_set | kept_set | assembled_set)):
        if model_primary in gold_set:
            primary_reason = "citation_omission_with_correct_primary_present"
        else:
            primary_reason = "citation_omission_with_correct_support_present"
        first_loss_stage = "post_generation"
    elif model_primary and model_primary not in gold_set:
        if gold_keys & model_keys:
            primary_reason = "canonical_normalization_mismatch"
        else:
            primary_reason = "model_primary_selection_miss"
        first_loss_stage = "model"
    elif final_primary and final_primary not in gold_set:
        if gold_keys & final_keys:
            primary_reason = "canonical_normalization_mismatch"
        elif model_primary in gold_set:
            primary_reason = "post_generation_primary_flip"
        elif gold_set & kept_set:
            primary_reason = "citation_omission_with_correct_support_present"
        else:
            primary_reason = "model_primary_selection_miss"
        first_loss_stage = "post_generation" if primary_reason in {
            "canonical_normalization_mismatch",
            "post_generation_primary_flip",
            "citation_omission_with_correct_support_present",
        } else "model"
    else:
        primary_reason = "evaluator_alignment_mismatch"
        first_loss_stage = "evaluator"

    if final_mode in {"refusal", "blocked"} and primary_reason not in {
        "guardrail_mode_drop",
        "guardrail_block_true_positive",
        "unsupported_true_refusal",
    }:
        secondary_reason = "guardrail_mode_drop"

    if primary_reason not in ALLOWED_PRIMARY_REASONS:
        raise RuntimeError(f"Unexpected primary_reason: {primary_reason}")
    if secondary_reason == primary_reason:
        secondary_reason = None

    return {
        "primary_reason": primary_reason,
        "secondary_reason": secondary_reason,
        "first_loss_stage": first_loss_stage,
        "gold_in_retrieval": bool(gold_set & retrieved_set),
        "gold_in_assembly": bool(gold_set & assembled_set),
        "assembly_primary_is_gold": assembled_primary in gold_set if assembled_primary else False,
        "model_primary_is_gold": model_primary in gold_set if model_primary else False,
        "final_primary_is_gold": final_primary in gold_set if final_primary else False,
    }


def compute_repair_gate_decision(
    *,
    tracked_count: int,
    trace_complete_rate: float,
    reconciliation_closed: bool,
    reason_histogram: dict[str, int],
    stage_histogram: dict[str, int],
) -> dict[str, Any]:
    explained_count = sum(stage_histogram.values())
    explained_ratio = explained_count / tracked_count if tracked_count else 0.0
    dominant_reason = None
    dominant_count = 0
    if reason_histogram:
        ordered = sorted(reason_histogram.items(), key=lambda item: (-item[1], item[0]))
        dominant_reason, dominant_count = ordered[0]
        if len(ordered) > 1 and ordered[1][1] == dominant_count:
            dominant_reason = None
            dominant_count = 0

    repair_gate_open = bool(
        trace_complete_rate == 1.0
        and reconciliation_closed
        and explained_ratio >= 0.8
        and dominant_reason is not None
    )
    next_official_move = REPAIR_GATE_MAPPING.get(dominant_reason) if dominant_reason else None
    rc_g_permitted = bool(
        repair_gate_open
        and dominant_reason in {
            "citation_omission_with_correct_primary_present",
            "post_generation_primary_flip",
        }
    )
    return {
        "tracked_count": tracked_count,
        "explained_count": explained_count,
        "explained_ratio": explained_ratio,
        "dominant_reason": dominant_reason,
        "dominant_count": dominant_count,
        "trace_complete_rate": trace_complete_rate,
        "reconciliation_closed": reconciliation_closed,
        "repair_gate_open": repair_gate_open,
        "next_official_move": next_official_move,
        "rc_g_permitted": rc_g_permitted,
    }
