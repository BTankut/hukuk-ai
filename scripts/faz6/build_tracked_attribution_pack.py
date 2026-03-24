#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from faz6_lib import build_tracked_pack_data, current_git_commit, render_tracked_pack_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ6 tracked attribution pack from FAZ3/4/5 failure surfaces.")
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_tracked_pack_data()
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["git_commit"] = current_git_commit()

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_md.write_text(render_tracked_pack_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
