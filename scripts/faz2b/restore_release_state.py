#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path


def restore_backup_bundle(*, manifest_path: Path, restore_dir: Path) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundle_dir = Path(manifest.get("bundle_dir")) if manifest.get("bundle_dir") else manifest_path.parent
    restore_dir.mkdir(parents=True, exist_ok=True)

    restore_env_path = restore_dir / "restore.env.sh"
    env_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    for key, value in manifest.get("env", {}).items():
        if value is None:
            continue
        env_lines.append(f"export {key}={shlex.quote(str(value))}")
    restore_env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    verification = []
    for file_info in manifest.get("files", []):
        backup_path = bundle_dir / file_info["backup_path"]
        verification.append(
            {
                "source_path": file_info["source_path"],
                "backup_path": str(backup_path),
                "exists": backup_path.exists(),
                "sha256": file_info["sha256"],
            }
        )

    summary_path = restore_dir / "restore_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "manifest_path": str(manifest_path),
                "restore_env_path": str(restore_env_path),
                "files": verification,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Restore a bounded release-lane backup bundle.")
    parser.add_argument("--manifest-path", type=Path, required=True)
    parser.add_argument("--restore-dir", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary_path = restore_backup_bundle(
        manifest_path=args.manifest_path,
        restore_dir=args.restore_dir,
    )
    print(str(summary_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
