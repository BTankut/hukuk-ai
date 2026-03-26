#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz16_lib import TARGETED_QUESTION_IDS, load_json, write_json


def build_manifest(
    *,
    rc_j_manifest: dict[str, Any],
    authority_summary: dict[str, Any] | None,
    authority_summary_source: str | None,
    candidate_id: str,
    checkpoint_ref: str,
    git_commit: str,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "status": "replacement_candidate",
        "inherits_from": rc_j_manifest.get("candidate_id"),
        "build_from": "RC-J",
        "base_model_id": rc_j_manifest.get("base_model_id"),
        "adapter_id": rc_j_manifest.get("adapter_id"),
        "checkpoint_ref": checkpoint_ref,
        "git_commit": git_commit,
        "runner_mode": "rc_m_replacement_build_surface_isolation_gate",
        "authority_snapshot_source": authority_summary_source,
        "authority_snapshot_report_hash": (authority_summary or {}).get("report_hash"),
        "authority_snapshot_frozen": bool((authority_summary or {}).get("authority_snapshot_frozen")),
        "answer_path_identity": rc_j_manifest.get("answer_path_identity", {}),
        "family_reports_reference": rc_j_manifest.get("family_reports_reference", []),
        "allowed_diff_surface": [
            "final_mode_mapping_hash",
            "blocked_reason_set_hash",
            "response_envelope_hash",
        ],
        "allowed_diff_surface_notes": [
            "replacement build-surface isolation from frozen RC-J authority snapshot",
        ],
        "answer_path_delta": [],
        "request_surface_delta": [],
        "model_visible_surface_delta": [],
        "retrieval_surface_delta": [],
        "release_controls_delta": [],
        "runtime_error_count": 0,
        "allowed_changed_record_set": TARGETED_QUESTION_IDS,
    }


def render_contract_md(*, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        "- build_from = `RC-J`",
        "- answer_path_delta = `[]`",
        "- request_surface_delta = `[]`",
        "- model_visible_surface_delta = `[]`",
        "- retrieval_surface_delta = `[]`",
        "- release_controls_delta = `[]`",
        "",
        "Izinli degisim yuzeyi:",
        "- `final_mode_mapping_hash`",
        "- `blocked_reason_set_hash`",
        "- `response_envelope_hash`",
        "",
        "Izinli degisim kayitlari:",
    ]
    for question_id in TARGETED_QUESTION_IDS:
        lines.append(f"- `{question_id}`")
    lines.append("")
    return "\n".join(lines)


def render_build_proof_md(manifest: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- candidate_id = `{manifest['candidate_id']}`",
        f"- inherits_from = `{manifest['inherits_from']}`",
        f"- build_from = `{manifest['build_from']}`",
        f"- checkpoint_ref = `{manifest['checkpoint_ref']}`",
        f"- git_commit = `{manifest['git_commit']}`",
        f"- authority_snapshot_source = `{manifest.get('authority_snapshot_source')}`",
        f"- authority_snapshot_report_hash = `{manifest.get('authority_snapshot_report_hash')}`",
        f"- authority_snapshot_frozen = `{manifest.get('authority_snapshot_frozen')}`",
        f"- answer_path_delta = `{manifest['answer_path_delta']}`",
        f"- request_surface_delta = `{manifest['request_surface_delta']}`",
        f"- model_visible_surface_delta = `{manifest['model_visible_surface_delta']}`",
        f"- retrieval_surface_delta = `{manifest['retrieval_surface_delta']}`",
        f"- release_controls_delta = `{manifest['release_controls_delta']}`",
        f"- runtime_error_count = `{manifest['runtime_error_count']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ16 RC-M manifest and proof.")
    parser.add_argument("--rc-j-manifest", type=Path, required=True)
    parser.add_argument("--authority-summary-json", type=Path)
    parser.add_argument("--candidate-id", default="rc-m-20260325")
    parser.add_argument("--checkpoint-ref", default="rc-m-2026-03-25")
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--manifest-output-json", type=Path, required=True)
    parser.add_argument("--diff-contract-output-md", type=Path, required=True)
    parser.add_argument("--build-proof-output-md", type=Path, required=True)
    args = parser.parse_args()

    authority_summary = load_json(args.authority_summary_json) if args.authority_summary_json else None
    manifest = build_manifest(
        rc_j_manifest=load_json(args.rc_j_manifest),
        authority_summary=authority_summary,
        authority_summary_source=str(args.authority_summary_json) if args.authority_summary_json else None,
        candidate_id=args.candidate_id,
        checkpoint_ref=args.checkpoint_ref,
        git_commit=args.git_commit,
    )
    write_json(args.manifest_output_json, manifest)
    args.diff_contract_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.diff_contract_output_md.write_text(
        render_contract_md(title="FAZ16 RC-J to RC-M Diff Surface Contract"),
        encoding="utf-8",
    )
    args.build_proof_output_md.write_text(
        render_build_proof_md(manifest, title="FAZ16 RC-M Build Proof"),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
