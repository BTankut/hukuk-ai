#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from faz6_lib import REPAIR_GATE_MAPPING, compute_repair_gate_decision, current_git_commit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ6 reconciliation table and repair-gate decision.")
    parser.add_argument("--tracked-pack-json", required=True, type=Path)
    parser.add_argument("--decomposition-json", required=True, type=Path)
    parser.add_argument("--reconciliation-json", required=True, type=Path)
    parser.add_argument("--reconciliation-md", required=True, type=Path)
    parser.add_argument("--decision-md", required=True, type=Path)
    return parser.parse_args()


def render_reconciliation_markdown(payload: dict[str, object]) -> str:
    return (
        "# FAZ 6 Reconciliation Table\n\n"
        f"- tracked_count: `{payload['tracked_count']}`\n"
        f"- taxonomy_primary_reason_total: `{payload['taxonomy_primary_reason_total']}`\n"
        f"- stage_first_loss_total: `{payload['stage_first_loss_total']}`\n"
        f"- family_breakdown_total: `{payload['family_breakdown_total']}`\n"
        f"- reconciliation_closed: `{str(payload['reconciliation_closed']).lower()}`\n"
        f"- unexplained_count: `{payload['unexplained_count']}`\n"
    )


def render_decision_markdown(payload: dict[str, object]) -> str:
    decision = payload["decision"]
    mapping_preview = "\n".join(
        f"- `{reason}` -> `{move}`" for reason, move in sorted(REPAIR_GATE_MAPPING.items())
    )
    return (
        "# FAZ 6 Repair Gate Decision Table\n\n"
        f"- trace_complete_rate: `{decision['trace_complete_rate']:.4f}`\n"
        f"- reconciliation_closed: `{str(decision['reconciliation_closed']).lower()}`\n"
        f"- explained_ratio: `{decision['explained_ratio']:.4f}`\n"
        f"- dominant_reason: `{decision['dominant_reason'] or 'none'}`\n"
        f"- dominant_count: `{decision['dominant_count']}`\n"
        f"- repair_gate_open: `{str(decision['repair_gate_open']).lower()}`\n"
        f"- next_official_move: `{decision['next_official_move'] or 'none'}`\n"
        f"- rc_g_permitted: `{str(decision['rc_g_permitted']).lower()}`\n\n"
        "## Mapping\n\n"
        f"{mapping_preview}\n"
    )


def main() -> int:
    args = parse_args()
    tracked_pack = json.loads(args.tracked_pack_json.read_text(encoding="utf-8"))
    decomposition = json.loads(args.decomposition_json.read_text(encoding="utf-8"))

    tracked_count = int(tracked_pack["tracked_count"])
    taxonomy_primary_reason_total = sum(int(value) for value in decomposition["reason_histogram"].values())
    stage_first_loss_total = sum(int(value) for value in decomposition["stage_first_loss_histogram"].values())
    family_breakdown_counter = Counter(row["family"] for row in decomposition["rows"])
    family_breakdown_total = sum(family_breakdown_counter.values())
    unexplained_count = tracked_count - stage_first_loss_total
    reconciliation_closed = (
        tracked_count == taxonomy_primary_reason_total == stage_first_loss_total == family_breakdown_total
        and unexplained_count == 0
    )

    decision = compute_repair_gate_decision(
        tracked_count=tracked_count,
        trace_complete_rate=float(decomposition["trace_complete_rate"]),
        reconciliation_closed=reconciliation_closed,
        reason_histogram={key: int(value) for key, value in decomposition["reason_histogram"].items()},
        stage_histogram={key: int(value) for key, value in decomposition["stage_first_loss_histogram"].items()},
    )

    reconciliation_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": current_git_commit(),
        "tracked_count": tracked_count,
        "taxonomy_primary_reason_total": taxonomy_primary_reason_total,
        "stage_first_loss_total": stage_first_loss_total,
        "family_breakdown_total": family_breakdown_total,
        "family_breakdown": dict(sorted(family_breakdown_counter.items())),
        "unexplained_count": unexplained_count,
        "reconciliation_closed": reconciliation_closed,
    }

    decision_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": current_git_commit(),
        "decision": decision,
    }

    args.reconciliation_json.parent.mkdir(parents=True, exist_ok=True)
    args.reconciliation_json.write_text(
        json.dumps(reconciliation_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.reconciliation_md.write_text(render_reconciliation_markdown(reconciliation_payload), encoding="utf-8")
    args.decision_md.write_text(render_decision_markdown(decision_payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
