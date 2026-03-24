#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_manifest(
    *,
    reference_manifest: dict,
    candidate_id: str,
    checkpoint_ref: str,
    git_commit: str,
    output_path: Path,
    allowed_diff_files: list[str],
) -> dict:
    manifest = {
        "candidate_id": candidate_id,
        "status": "release_candidate",
        "inherits_from": reference_manifest.get("candidate_id"),
        "base_model_id": reference_manifest.get("base_model_id"),
        "adapter_id": reference_manifest.get("adapter_id"),
        "checkpoint_ref": checkpoint_ref,
        "git_commit": git_commit,
        "runner_mode": "rc_h_runtime_release_controls",
        "answer_path_identity": {
            "claim_binding_version": reference_manifest.get("claim_binding_version"),
            "final_mode_mapping_version": reference_manifest.get("final_mode_mapping_version"),
            "source_locking_version": reference_manifest.get("source_locking_version"),
            "citation_normalization_version": reference_manifest.get("citation_normalization_version"),
            "law_scope_gate_version": reference_manifest.get("law_scope_gate_version"),
            "trace_contract_version": reference_manifest.get("trace_contract_version"),
            "schema_contract_version": reference_manifest.get("schema_contract_version"),
        },
        "family_reports_reference": reference_manifest.get("family_reports", []),
        "allowed_diff_surface": allowed_diff_files,
        "answer_path_delta": [],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ7 RC-H manifest from RC-G reference.")
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--checkpoint-ref", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--allowed-diff-file", action="append", default=[])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    reference_manifest = json.loads(args.reference_manifest.read_text(encoding="utf-8"))
    build_manifest(
        reference_manifest=reference_manifest,
        candidate_id=args.candidate_id,
        checkpoint_ref=args.checkpoint_ref,
        git_commit=args.git_commit,
        output_path=args.output_path,
        allowed_diff_files=args.allowed_diff_file,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
