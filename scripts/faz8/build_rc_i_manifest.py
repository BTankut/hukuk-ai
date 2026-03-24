#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from faz8_lib import load_json, write_json


def build_manifest(
    *,
    reference_manifest: dict,
    candidate_id: str,
    checkpoint_ref: str,
    git_commit: str,
    output_path: Path,
    allowed_diff_files: list[str],
    answer_path_delta: list[str],
) -> dict:
    answer_identity = reference_manifest.get("answer_path_identity") or {
        "claim_binding_version": reference_manifest.get("claim_binding_version"),
        "final_mode_mapping_version": reference_manifest.get("final_mode_mapping_version"),
        "source_locking_version": reference_manifest.get("source_locking_version"),
        "citation_normalization_version": reference_manifest.get("citation_normalization_version"),
        "law_scope_gate_version": reference_manifest.get("law_scope_gate_version"),
        "trace_contract_version": reference_manifest.get("trace_contract_version"),
        "schema_contract_version": reference_manifest.get("schema_contract_version"),
    }
    manifest = {
        "candidate_id": candidate_id,
        "status": "release_candidate",
        "inherits_from": reference_manifest.get("candidate_id"),
        "base_model_id": reference_manifest.get("base_model_id"),
        "adapter_id": reference_manifest.get("adapter_id"),
        "checkpoint_ref": checkpoint_ref,
        "git_commit": git_commit,
        "runner_mode": "rc_i_runtime_release_controls_parity_safe",
        "answer_path_identity": answer_identity,
        "family_reports_reference": reference_manifest.get("family_reports_reference")
        or reference_manifest.get("family_reports", []),
        "allowed_diff_surface": allowed_diff_files,
        "answer_path_delta": answer_path_delta,
    }
    write_json(output_path, manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ8 RC-I manifest from RC-G reference.")
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--checkpoint-ref", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--allowed-diff-file", action="append", default=[])
    parser.add_argument("--answer-path-delta", action="append", default=[])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    reference_manifest = load_json(args.reference_manifest)
    build_manifest(
        reference_manifest=reference_manifest,
        candidate_id=args.candidate_id,
        checkpoint_ref=args.checkpoint_ref,
        git_commit=args.git_commit,
        output_path=args.output_path,
        allowed_diff_files=args.allowed_diff_file,
        answer_path_delta=args.answer_path_delta,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
