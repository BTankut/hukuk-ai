#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_name(path: Path) -> str:
    return str(path).strip("/").replace("/", "__") or path.name


def create_backup_bundle(
    *,
    output_dir: Path,
    label: str,
    env_keys: list[str],
    include_paths: list[Path],
) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = output_dir / f"{label}_{timestamp}"
    files_dir = bundle_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    env_values = {key: os.getenv(key) for key in env_keys}
    copied_files: list[dict[str, str | int]] = []
    for source in include_paths:
        resolved = source.resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Include path not found: {resolved}")
        target = files_dir / _safe_name(source)
        shutil.copy2(resolved, target)
        copied_files.append(
            {
                "source_path": str(source),
                "backup_path": str(target.relative_to(bundle_dir)),
                "sha256": sha256_file(target),
                "size_bytes": target.stat().st_size,
            }
        )

    manifest = {
        "label": label,
        "created_at": timestamp,
        "env": env_values,
        "files": copied_files,
    }
    manifest_path = bundle_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a bounded release-lane backup bundle.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--env-key", action="append", default=[])
    parser.add_argument("--include-path", type=Path, action="append", default=[])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest_path = create_backup_bundle(
        output_dir=args.output_dir,
        label=args.label,
        env_keys=args.env_key,
        include_paths=args.include_path,
    )
    print(str(manifest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
