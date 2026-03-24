#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz10_lib import load_json, write_json


def build_manifest(
    *,
    reference_manifest: dict[str, Any],
    diagnostic_manifest: dict[str, Any],
    candidate_id: str,
    checkpoint_ref: str,
    git_commit: str,
    output_path: Path,
    allowed_diff_surface: list[str],
    allowed_diff_surface_notes: list[str],
) -> dict[str, Any]:
    answer_identity = diagnostic_manifest.get("answer_path_identity") or {
        "claim_binding_version": reference_manifest.get("claim_binding_version"),
        "final_mode_mapping_version": reference_manifest.get("final_mode_mapping_version"),
        "source_locking_version": reference_manifest.get("source_locking_version"),
        "citation_normalization_version": reference_manifest.get("citation_normalization_version"),
        "law_scope_gate_version": reference_manifest.get("law_scope_gate_version"),
        "trace_contract_version": "faz10-v3-runtime-parity-trace-schema-v1",
        "schema_contract_version": reference_manifest.get("schema_contract_version"),
    }
    manifest = {
        "candidate_id": candidate_id,
        "status": "release_candidate",
        "inherits_from": reference_manifest.get("candidate_id"),
        "diagnostic_source_candidate_id": diagnostic_manifest.get("candidate_id"),
        "base_model_id": reference_manifest.get("base_model_id"),
        "adapter_id": reference_manifest.get("adapter_id"),
        "checkpoint_ref": checkpoint_ref,
        "git_commit": git_commit,
        "runner_mode": "rc_k_v3_preprojection_parity_safe",
        "answer_path_identity": answer_identity,
        "family_reports_reference": reference_manifest.get("family_reports")
        or reference_manifest.get("family_reports_reference", []),
        "allowed_diff_surface": allowed_diff_surface,
        "allowed_diff_surface_notes": allowed_diff_surface_notes,
        "answer_path_delta": [],
    }
    write_json(output_path, manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ10 RC-K manifest from RC-G reference and RC-J diagnostic.")
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--diagnostic-manifest", type=Path, required=True)
    parser.add_argument("--candidate-id", default="rc-k-20260324")
    parser.add_argument("--checkpoint-ref", default="rc-k-2026-03-24")
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--allowed-diff-surface", action="append", default=[])
    parser.add_argument("--allowed-diff-note", action="append", default=[])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    build_manifest(
        reference_manifest=load_json(args.reference_manifest),
        diagnostic_manifest=load_json(args.diagnostic_manifest),
        candidate_id=args.candidate_id,
        checkpoint_ref=args.checkpoint_ref,
        git_commit=args.git_commit,
        output_path=args.output_path,
        allowed_diff_surface=args.allowed_diff_surface,
        allowed_diff_surface_notes=args.allowed_diff_note,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
