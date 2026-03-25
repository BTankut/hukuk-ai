#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz14_lib import load_json, write_json


def build_manifest(
    *,
    diagnostic_manifest: dict[str, Any],
    candidate_id: str,
    checkpoint_ref: str,
    git_commit: str,
    output_path: Path,
    allowed_diff_surface: list[str],
    allowed_diff_surface_notes: list[str],
) -> dict[str, Any]:
    answer_identity = diagnostic_manifest.get("answer_path_identity") or {
        "claim_binding_version": diagnostic_manifest.get("claim_binding_version"),
        "final_mode_mapping_version": diagnostic_manifest.get("final_mode_mapping_version"),
        "source_locking_version": diagnostic_manifest.get("source_locking_version"),
        "citation_normalization_version": diagnostic_manifest.get("citation_normalization_version"),
        "law_scope_gate_version": diagnostic_manifest.get("law_scope_gate_version"),
        "trace_contract_version": "faz14-authoritative-output-repair-schema-v1",
        "schema_contract_version": diagnostic_manifest.get("schema_contract_version"),
    }
    manifest = {
        "candidate_id": candidate_id,
        "status": "repair_candidate",
        "inherits_from": diagnostic_manifest.get("candidate_id"),
        "base_model_id": diagnostic_manifest.get("base_model_id"),
        "adapter_id": diagnostic_manifest.get("adapter_id"),
        "checkpoint_ref": checkpoint_ref,
        "git_commit": git_commit,
        "runner_mode": "rc_l_authoritative_output_repair_gate",
        "answer_path_identity": answer_identity,
        "family_reports_reference": diagnostic_manifest.get("family_reports_reference")
        or diagnostic_manifest.get("family_reports", []),
        "allowed_diff_surface": allowed_diff_surface,
        "allowed_diff_surface_notes": allowed_diff_surface_notes,
        "answer_path_delta": [],
    }
    write_json(output_path, manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ14 RC-L manifest from RC-J diagnostic manifest.")
    parser.add_argument("--diagnostic-manifest", type=Path, required=True)
    parser.add_argument("--candidate-id", default="rc-l-20260325")
    parser.add_argument("--checkpoint-ref", default="rc-l-2026-03-25")
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--allowed-diff-surface", action="append", default=[])
    parser.add_argument("--allowed-diff-note", action="append", default=[])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    build_manifest(
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
