#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz14_lib import IMMUTABLE_BREACH_STAGES, load_json, write_json  # noqa: E402


def build_localization(frontier_pack: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    replay = {
        "frontier_count": int(frontier_pack.get("frontier_count", 0)),
        "first_divergence_assigned_count": int(frontier_pack.get("first_divergence_assigned_count", 0)),
        "primary_reason_assigned_count": int(frontier_pack.get("primary_reason_assigned_count", 0)),
        "unexplained_count": int(frontier_pack.get("unexplained_count", 0)),
        "stage_histogram": dict(frontier_pack.get("stage_histogram") or {}),
        "reason_histogram": dict(frontier_pack.get("reason_histogram") or {}),
        "repair_surface_breach_count": sum(
            1
            for row in frontier_pack.get("rows", [])
            if row.get("first_divergence_stage") in IMMUTABLE_BREACH_STAGES
        ),
    }
    reconciliation = {
        "frontier_count": replay["frontier_count"],
        "first_divergence_assigned_count": replay["first_divergence_assigned_count"],
        "primary_reason_assigned_count": replay["primary_reason_assigned_count"],
        "unexplained_count": replay["unexplained_count"],
        "stage_histogram_total": sum(int(value) for value in replay["stage_histogram"].values()),
        "reason_histogram_total": sum(int(value) for value in replay["reason_histogram"].values()),
        "repair_surface_breach_count": replay["repair_surface_breach_count"],
    }
    reconciliation["localization_pass"] = (
        reconciliation["frontier_count"] == reconciliation["first_divergence_assigned_count"]
        and reconciliation["frontier_count"] == reconciliation["primary_reason_assigned_count"]
        and reconciliation["frontier_count"] == reconciliation["stage_histogram_total"]
        and reconciliation["frontier_count"] == reconciliation["reason_histogram_total"]
        and reconciliation["unexplained_count"] == 0
    )
    return replay, reconciliation


def render_replay_markdown(replay: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{replay['frontier_count']}`",
        f"- first_divergence_assigned_count = `{replay['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{replay['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{replay['unexplained_count']}`",
        f"- repair_surface_breach_count = `{replay['repair_surface_breach_count']}`",
        "",
        "## Stage Histogram",
        "",
    ]
    for key, value in sorted(replay["stage_histogram"].items()):
        lines.append(f"- `{key}` = `{value}`")
    lines.extend(["", "## Reason Histogram", ""])
    for key, value in sorted(replay["reason_histogram"].items()):
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
        f"- stage_histogram_total = `{reconciliation['stage_histogram_total']}`",
        f"- reason_histogram_total = `{reconciliation['reason_histogram_total']}`",
        f"- repair_surface_breach_count = `{reconciliation['repair_surface_breach_count']}`",
        f"- localization_pass = `{str(reconciliation['localization_pass']).lower()}`",
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ14 output parity repair localization outputs.")
    parser.add_argument("--frontier-pack-json", type=Path, required=True)
    parser.add_argument("--replay-output-json", type=Path, required=True)
    parser.add_argument("--replay-output-md", type=Path, required=True)
    parser.add_argument("--reconciliation-output-json", type=Path, required=True)
    parser.add_argument("--reconciliation-output-md", type=Path, required=True)
    parser.add_argument("--replay-title", required=True)
    parser.add_argument("--reconciliation-title", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    replay, reconciliation = build_localization(load_json(args.frontier_pack_json))
    write_json(args.replay_output_json, replay)
    write_json(args.reconciliation_output_json, reconciliation)
    args.replay_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.replay_output_md.write_text(render_replay_markdown(replay, title=args.replay_title), encoding="utf-8")
    args.reconciliation_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.reconciliation_output_md.write_text(
        render_reconciliation_markdown(reconciliation, title=args.reconciliation_title),
        encoding="utf-8",
    )
    return 0 if reconciliation["localization_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
