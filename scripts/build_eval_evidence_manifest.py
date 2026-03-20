#!/usr/bin/env python3
"""Freeze an evaluation artifact into a manifest the readiness gate can verify."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def _load_report_meta(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    meta = payload.get("report_meta")
    return meta if isinstance(meta, dict) else {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build eval evidence manifest.")
    parser.add_argument("--report-path", required=True)
    parser.add_argument("--role", required=True, choices=("baseline", "post_train"))
    parser.add_argument("--eval-family", required=True)
    parser.add_argument("--model-ref", required=True)
    parser.add_argument("--checkpoint-ref", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--train-package-sha")
    parser.add_argument("--notes")
    parser.add_argument("--output", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report_path = Path(args.report_path)
    if not report_path.exists():
        raise SystemExit(f"report path not found: {report_path}")

    report_meta = _load_report_meta(report_path)
    manifest = {
        "manifest_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "role": args.role,
        "eval_family": args.eval_family,
        "model_ref": args.model_ref,
        "checkpoint_ref": args.checkpoint_ref,
        "git_commit": args.git_commit,
        "train_package_sha": args.train_package_sha,
        "report_path": str(report_path),
        "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "report_meta": report_meta,
        "notes": args.notes or "",
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
