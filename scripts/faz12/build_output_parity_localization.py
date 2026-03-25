#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz12_lib import PRIMARY_REASONS, load_json, write_json  # noqa: E402


def build_localization(frontier_pack: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = frontier_pack.get("rows") or []
    stage_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    unexplained_rows: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        stage = row.get("first_divergence_stage")
        reason = row.get("primary_reason")
        if isinstance(stage, str) and stage:
            stage_counts[stage] += 1
        if isinstance(reason, str) and reason in PRIMARY_REASONS:
            reason_counts[reason] += 1
        else:
            unexplained_rows.append(row)

    replay = {
        "frontier_count": len(rows),
        "first_divergence_assigned_count": sum(stage_counts.values()),
        "primary_reason_assigned_count": sum(reason_counts.values()),
        "unexplained_count": len(unexplained_rows),
        "stage_counts": dict(stage_counts),
        "reason_counts": dict(reason_counts),
        "unexplained_rows": unexplained_rows,
    }
    reconciliation = {
        "frontier_count": replay["frontier_count"],
        "first_divergence_assigned_count": replay["first_divergence_assigned_count"],
        "primary_reason_assigned_count": replay["primary_reason_assigned_count"],
        "unexplained_count": replay["unexplained_count"],
        "localization_pass": (
            replay["frontier_count"] == replay["first_divergence_assigned_count"]
            and replay["frontier_count"] == replay["primary_reason_assigned_count"]
            and replay["unexplained_count"] == 0
        ),
    }
    return replay, reconciliation


def render_replay_markdown(replay: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{replay['frontier_count']}`",
        f"- first_divergence_assigned_count = `{replay['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{replay['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{replay['unexplained_count']}`",
        "",
        "## Stage Counts",
        "",
    ]
    for key, value in sorted(replay["stage_counts"].items()):
        lines.append(f"- `{key}` = `{value}`")
    lines.extend(["", "## Reason Counts", ""])
    for key, value in sorted(replay["reason_counts"].items()):
        lines.append(f"- `{key}` = `{value}`")
    lines.append("")
    return "\n".join(lines)


def render_reconciliation_markdown(reconciliation: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{reconciliation['frontier_count']}`",
        f"- first_divergence_assigned_count = `{reconciliation['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{reconciliation['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        f"- localization_pass = `{str(reconciliation['localization_pass']).lower()}`",
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ12 first-divergence localization outputs.")
    parser.add_argument("--frontier-pack-json", type=Path, required=True)
    parser.add_argument("--replay-output-json", type=Path)
    parser.add_argument("--replay-output-md", type=Path, required=True)
    parser.add_argument("--reconciliation-output-json", type=Path)
    parser.add_argument("--reconciliation-output-md", type=Path, required=True)
    parser.add_argument("--replay-title", default="FAZ12 Output Parity Frontier Replay")
    parser.add_argument("--reconciliation-title", default="FAZ12 Output Parity Reconciliation")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    replay, reconciliation = build_localization(load_json(args.frontier_pack_json))
    if args.replay_output_json:
        write_json(args.replay_output_json, replay)
    if args.reconciliation_output_json:
        write_json(args.reconciliation_output_json, reconciliation)
    args.replay_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.replay_output_md.write_text(
        render_replay_markdown(replay, title=args.replay_title),
        encoding="utf-8",
    )
    args.reconciliation_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.reconciliation_output_md.write_text(
        render_reconciliation_markdown(reconciliation, title=args.reconciliation_title),
        encoding="utf-8",
    )
    return 0 if reconciliation["localization_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
