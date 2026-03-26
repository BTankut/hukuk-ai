from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE_TAG = "2026-03-26"
COMPACT_DATE_TAG = "20260326"

FAMILY_SEQUENCE = ("faz1-50", "v2-95", "v3-170")
FAMILY_ORDER = {family_id: index for index, family_id in enumerate(FAMILY_SEQUENCE)}
REFERENCE_SEQUENCE = ("faz13", "faz18", "faz19")
REPLAY_SEQUENCE = ("faz13", "faz18", "faz19")
PAIR_NAME = "rc_g_vs_rc_j"

QUESTIONS_PATH_BY_FAMILY = {
    "faz1-50": "configs/evaluation/test_questions.json",
    "v2-95": "configs/evaluation/test_questions_v2_95.json",
    "v3-170": "configs/evaluation/test_questions_v3_170.json",
}

H_STAGE_SEQUENCE = (
    "H0",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "H7",
    "H8",
    "H9",
    "H10",
    "H11",
)

H_STAGE_LABELS = {
    "H0": "candidate_freeze_manifest_hash",
    "H1": "model_bundle_hash",
    "H2": "prompt_guardrail_bundle_hash",
    "H3": "projection_surface_bundle_hash",
    "H4": "runtime_image_digest",
    "H5": "dependency_lock_hash",
    "H6": "evaluator_bundle_hash",
    "H7": "family_pack_hash",
    "H8": "run_contract_hash",
    "H9": "clean_lane_contract_hash",
    "H10": "per_ordinal_fingerprint_set_hash",
    "H11": "authoritative_summary_hash",
}

SURFACE_BREACH_STAGES = H_STAGE_SEQUENCE[:10]
RECORDING_ONLY_STAGES = H_STAGE_SEQUENCE[10:]

PRIMARY_REASONS = (
    "historical_reference_artifact_drift",
    "candidate_freeze_identity_rotation",
    "runtime_dependency_surface_rotation",
    "evaluator_surface_rotation",
    "family_pack_identity_rotation",
    "run_contract_surface_rotation",
    "projection_surface_rotation",
    "authority_summary_materialization_delta",
    "stable_current_truth_canonical",
    "unexplained_authority_history_conflict",
)

DECISION_TO_NEXT_WORK = {
    "PASS - Current Authority Canonicalization Authorized": "current authority canonicalization gate",
    "NO-GO - Historical Reference Artifact Drift": "historical reference artifact reconciliation",
    "NO-GO - Candidate Freeze Identity Drift": "candidate freeze identity forensics",
    "NO-GO - Runtime Or Evaluator Surface Drift": "runtime-evaluator surface drift forensics",
    "NO-GO - Unexplained Authority History Conflict": "authority history conflict forensics",
}


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_file_bundle(paths: list[Path]) -> str:
    payload = [
        {
            "path": str(path),
            "sha256": file_sha256(path),
        }
        for path in sorted(paths, key=lambda item: str(item))
    ]
    return stable_hash(payload)


def bool_text(value: Any) -> str:
    return str(bool(value)).lower()


def markdown_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return [header, divider, *body]


def family_sort_key(family_id: str) -> tuple[int, str]:
    return (FAMILY_ORDER.get(family_id, 999), family_id)


def family_slug(family_id: str) -> str:
    return family_id.replace("-", "_")


def list_dict(value: Any) -> list[dict[str, Any]]:
    return [item for item in (value or []) if isinstance(item, dict)]


def histogram_from_rows(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    histogram: Counter[str] = Counter()
    for row in rows:
        raw = row.get(key)
        if isinstance(raw, str) and raw:
            histogram[raw] += 1
    return dict(sorted(histogram.items()))


def unique_strings(rows: list[dict[str, Any]], key: str) -> list[str]:
    return sorted({str(row.get(key)) for row in rows if isinstance(row.get(key), str) and str(row.get(key))})


def mismatch_question_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row["question_id"]) for row in rows if row.get("question_id")]


def mismatch_ordinals(rows: list[dict[str, Any]]) -> list[int]:
    return [int(row["ordinal_index"]) for row in rows if row.get("ordinal_index") is not None]


def reference_pack_hash(payload: dict[str, Any]) -> str:
    return stable_hash(
        {
            "reference_name": payload["reference_name"],
            "candidate_pair": payload["candidate_pair"],
            "families": [
                {
                    key: value
                    for key, value in row.items()
                    if key != "reference_pack_hash"
                }
                for row in payload["families"]
            ],
        }
    )


def normalized_family_row(
    *,
    family_name: str,
    mismatch_count: int,
    runtime_error_count: int,
    family_metric_delta_zero: bool,
    mismatch_stage_histogram: dict[str, int],
    mismatch_question_ids_value: list[str],
    mismatch_ordinals_value: list[int],
    first_divergence_stage_set: list[str],
    reason_histogram: dict[str, int],
    authoritative_summary_hash: str,
) -> dict[str, Any]:
    return {
        "family_name": family_name,
        "candidate_pair": PAIR_NAME,
        "mismatch_count": int(mismatch_count),
        "runtime_error_count": int(runtime_error_count),
        "family_metric_delta_zero": bool(family_metric_delta_zero),
        "mismatch_stage_histogram": dict(mismatch_stage_histogram),
        "mismatch_question_ids": list(mismatch_question_ids_value),
        "mismatch_ordinals": list(mismatch_ordinals_value),
        "first_divergence_stage_set": list(first_divergence_stage_set),
        "reason_histogram": dict(reason_histogram),
        "authoritative_summary_hash": authoritative_summary_hash,
    }


def current_h0_h7_hashes(repo_root: Path) -> dict[str, str]:
    return {
        "H0": stable_hash(
            {
                "pair": PAIR_NAME,
                "rc_g_role": "accepted quality and authority reference",
                "rc_j_role": "frozen diagnostic control reference",
                "current_serving_lane": "unchanged",
            }
        ),
        "H1": hash_file_bundle(
            [
                repo_root / "scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh",
            ]
        ),
        "H2": hash_file_bundle(
            [
                repo_root / "api-gateway/src/faz2a_hardening.py",
                repo_root / "api-gateway/src/guardrails/pipeline.py",
                repo_root / "api-gateway/src/guardrails/actions.py",
            ]
        ),
        "H3": hash_file_bundle(
            [
                repo_root / "api-gateway/src/routers/chat.py",
                repo_root / "api-gateway/src/llm/client.py",
                repo_root / "api-gateway/src/rag/orchestrator.py",
                repo_root / "api-gateway/src/rag/verification_engine.py",
            ]
        ),
        "H4": hash_file_bundle(
            [
                repo_root / "scripts/faz7/launch_local_rc_g_reference_gateway.sh",
                repo_root / "scripts/faz9/launch_local_rc_j_candidate_gateway.sh",
                repo_root / "scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh",
            ]
        ),
        "H5": hash_file_bundle(
            [
                repo_root / "api-gateway/pyproject.toml",
                repo_root / "api-gateway/uv.lock",
            ]
        ),
        "H6": hash_file_bundle(
            [
                repo_root / "evaluation/eval_runner.py",
                repo_root / "scripts/faz13/build_authoritative_output_parity_report.py",
                repo_root / "scripts/faz20/build_replay_report.py",
            ]
        ),
        "H7": hash_file_bundle(
            [
                repo_root / QUESTIONS_PATH_BY_FAMILY["faz1-50"],
                repo_root / QUESTIONS_PATH_BY_FAMILY["v2-95"],
                repo_root / QUESTIONS_PATH_BY_FAMILY["v3-170"],
            ]
        ),
    }


def replay_contract_hashes(repo_root: Path, replay_kind: str) -> dict[str, str]:
    contract_paths: dict[str, tuple[Path, Path]] = {
        "faz13": (
            repo_root / "coordination/faz13-output-parity-authority-run-contract-2026-03-25.md",
            repo_root / "coordination/faz13-authoritative-runtime-lane-contract-2026-03-25.md",
        ),
        "faz18": (
            repo_root / "coordination/faz18-authoritative-output-parity-surface-run-contract-2026-03-25.md",
            repo_root / "coordination/faz18-runtime-lane-contract-2026-03-25.md",
        ),
        "faz19": (
            repo_root / "coordination/faz19-current-authority-run-contract-2026-03-25.md",
            repo_root / "coordination/faz19-clean-lane-isolation-contract-2026-03-25.md",
        ),
    }
    run_contract_path, clean_lane_path = contract_paths[replay_kind]
    return {
        "H8": hash_file_bundle([run_contract_path]),
        "H9": hash_file_bundle([clean_lane_path]),
    }


def per_ordinal_fingerprint_set_hash(report: dict[str, Any]) -> str:
    mismatch_rows = list_dict(report.get("mismatch_rows"))
    rows = [
        {
            "question_id": row.get("question_id"),
            "ordinal_index": row.get("ordinal_index"),
            "first_divergence_stage": row.get("first_divergence_stage"),
            "primary_reason": row.get("primary_reason"),
        }
        for row in mismatch_rows
    ]
    rows.sort(key=lambda item: int(item.get("ordinal_index") or 0))
    return stable_hash(rows)


def replay_family_row(report: dict[str, Any]) -> dict[str, Any]:
    mismatch_rows = list_dict(report.get("mismatch_rows"))
    mismatch_stage_histogram = histogram_from_rows(mismatch_rows, "first_divergence_stage")
    reason_histogram = histogram_from_rows(mismatch_rows, "primary_reason")
    family_row = normalized_family_row(
        family_name=str(report["family_id"]),
        mismatch_count=int(report.get("mismatch_count", 0)),
        runtime_error_count=int(report.get("reference_runtime_error_count", 0))
        + int(report.get("candidate_runtime_error_count", 0)),
        family_metric_delta_zero=bool(report.get("family_metric_delta_zero")),
        mismatch_stage_histogram=mismatch_stage_histogram,
        mismatch_question_ids_value=mismatch_question_ids(mismatch_rows),
        mismatch_ordinals_value=mismatch_ordinals(mismatch_rows),
        first_divergence_stage_set=unique_strings(mismatch_rows, "first_divergence_stage"),
        reason_histogram=reason_histogram,
        authoritative_summary_hash=stable_hash(
            {
                "family_id": report["family_id"],
                "mismatch_count": report.get("mismatch_count", 0),
                "runtime_error_count": int(report.get("reference_runtime_error_count", 0))
                + int(report.get("candidate_runtime_error_count", 0)),
                "family_metric_delta_zero": bool(report.get("family_metric_delta_zero")),
                "mismatch_stage_histogram": mismatch_stage_histogram,
                "mismatch_question_ids": mismatch_question_ids(mismatch_rows),
                "mismatch_ordinals": mismatch_ordinals(mismatch_rows),
                "first_divergence_stage_set": unique_strings(mismatch_rows, "first_divergence_stage"),
                "reason_histogram": reason_histogram,
            }
        ),
    )
    family_row["per_ordinal_fingerprint_set_hash"] = per_ordinal_fingerprint_set_hash(report)
    return family_row


def normalize_reason_for_stage(stage_name: str | None) -> str:
    if stage_name in {"H0", "H1", "H2"}:
        return "candidate_freeze_identity_rotation"
    if stage_name == "H3":
        return "projection_surface_rotation"
    if stage_name in {"H4", "H5"}:
        return "runtime_dependency_surface_rotation"
    if stage_name == "H6":
        return "evaluator_surface_rotation"
    if stage_name == "H7":
        return "family_pack_identity_rotation"
    if stage_name in {"H8", "H9"}:
        return "run_contract_surface_rotation"
    if stage_name in {"H10", "H11"}:
        return "authority_summary_materialization_delta"
    return "unexplained_authority_history_conflict"


def first_h_stage(stage_set: list[str]) -> str | None:
    for stage in H_STAGE_SEQUENCE:
        if stage in stage_set:
            return stage
    return None


def first_truth_divergence(
    *,
    breach_in_h0_h9: list[str],
    breach_in_h10_h11: list[str],
    reference_match: bool,
) -> str | None:
    if breach_in_h0_h9:
        return first_h_stage(breach_in_h0_h9)
    if breach_in_h10_h11:
        return first_h_stage(breach_in_h10_h11)
    if reference_match:
        return None
    return "H11"


def build_reference_match_row(
    replay_row: dict[str, Any],
    reference_row: dict[str, Any],
    *,
    h10_match: bool,
    h11_match: bool,
) -> dict[str, Any]:
    replay_core = {
        key: replay_row[key]
        for key in (
            "mismatch_count",
            "runtime_error_count",
            "family_metric_delta_zero",
            "mismatch_stage_histogram",
            "mismatch_question_ids",
            "mismatch_ordinals",
            "first_divergence_stage_set",
            "reason_histogram",
        )
    }
    reference_core = {
        key: reference_row[key]
        for key in (
            "mismatch_count",
            "runtime_error_count",
            "family_metric_delta_zero",
            "mismatch_stage_histogram",
            "mismatch_question_ids",
            "mismatch_ordinals",
            "first_divergence_stage_set",
            "reason_histogram",
        )
    }
    mismatched_fields = sorted(key for key in replay_core if replay_core[key] != reference_core[key])
    h10_h11_breaches = []
    if not h10_match:
        h10_h11_breaches.append("H10")
    if not h11_match:
        h10_h11_breaches.append("H11")
    return {
        "family_name": replay_row["family_name"],
        "match": not mismatched_fields,
        "mismatched_fields": mismatched_fields,
        "replay": replay_core,
        "reference": reference_core,
        "breach_in_h10_h11": h10_h11_breaches,
    }


def render_family_summary_table(rows: list[dict[str, Any]]) -> list[str]:
    return markdown_table(
        [
            ("family_name", "family"),
            ("mismatch_count", "mismatch_count"),
            ("runtime_error_count", "runtime_error_count"),
            ("family_metric_delta_zero", "family_metric_delta_zero"),
            ("mismatch_stage_histogram", "mismatch_stage_histogram"),
            ("mismatch_question_ids", "mismatch_question_ids"),
        ],
        rows,
    )
