#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz17_lib import DECISION_TO_NEXT_WORK, load_json, write_json


def decide(
    *,
    wp3_summary: dict[str, Any],
    wp4_frontier_replay: dict[str, Any] | None,
) -> tuple[str, str]:
    if bool(wp3_summary.get("wp3_pass")):
        decision = "PASS - RC-M Authoritative Output Parity Closed"
    elif int(wp3_summary.get("runtime_error_count", 0)) > 0:
        decision = "NO-GO - RC-M Authority Run Unstable"
    elif wp4_frontier_replay is None:
        decision = "NO-GO - RC-M Authority Run Unstable"
    elif int(wp4_frontier_replay.get("output_parity_surface_breach_count", 0)) == 0:
        decision = "NO-GO - RC-M Authoritative Output Parity Drift Localized"
    else:
        decision = "NO-GO - RC-M Output Parity Surface Breach"
    return decision, DECISION_TO_NEXT_WORK[decision]


def render_steering_md(
    *,
    decision: str,
    next_work: str,
    wp3_summary: dict[str, Any],
    wp4_frontier_replay: dict[str, Any] | None,
) -> str:
    wp4_status = "NOT AUTHORIZED" if bool(wp3_summary.get("wp3_pass")) else "PASS"
    wp4_evidence = (
        "not authorized by WP-3 PASS"
        if wp4_frontier_replay is None
        else (
            f"frontier_count={wp4_frontier_replay.get('frontier_count')}, "
            f"surface_breach_count={wp4_frontier_replay.get('output_parity_surface_breach_count')}"
        )
    )
    lines = [
        "# FAZ17 Steering Decision Table",
        "",
        "| WP | Durum | Kanit | Sonuc |",
        "| --- | --- | --- | --- |",
        "| `WP-1` | `PASS` | freeze ve authority contract artefact'lari tamam | faz authority/referans yuzeyi sabitlendi |",
        "| `WP-2` | `PASS` | schema/taxonomy/equivalence/classification contract artefact'lari tamam | parity yorum contract'i sabitlendi |",
        f"| `WP-3` | `{'PASS' if bool(wp3_summary.get('wp3_pass')) else 'FAIL'}` | `runtime_error_count={wp3_summary.get('runtime_error_count')}`, `authoritative_summary_mismatch_count={wp3_summary.get('authoritative_summary_mismatch_count')}` | full-family authoritative parity sonucu kayda gecti |",
        f"| `WP-4` | `{wp4_status}` | `{wp4_evidence}` | frontier localization / diagnostic containment sonucu kayda gecti |",
        "| `WP-5` | `PASS` | reconciliation ve next work uretildi | tek resmi karar sabitlendi |",
        "",
        f"- official_decision = `{decision}`",
        f"- next_official_work = `{next_work}`",
        "",
    ]
    return "\n".join(lines)


def render_reconciliation_md(*, decision: str) -> str:
    return "\n".join(
        [
            "# FAZ17 Output Parity Authoritative Reconciliation",
            "",
            f"- official_decision = `{decision}`",
            "",
        ]
    )


def render_next_work_md(*, next_work: str) -> str:
    return "\n".join(["# FAZ17 Next Official Work", "", f"- next_official_work = `{next_work}`", ""])


def render_report_md(
    *,
    decision: str,
    next_work: str,
    wp3_summary: dict[str, Any],
    wp4_frontier_replay: dict[str, Any] | None,
) -> str:
    lines = [
        "# FAZ17 RC-M Authoritative Output Parity Reopen Raporu",
        "",
        "Tarih: 2026-03-25",
        "",
        "Referans:",
        "- `docs/FAZ17-ROTASYON-RC-M-AUTHORITATIVE-OUTPUT-PARITY-REOPEN-TALIMATI-2026-03-25.md`",
        "- `coordination/faz17-official-implementation-plan-2026-03-25.md`",
        "- `coordination/faz17-steering-decision-table-2026-03-25.md`",
        "",
        "## Yonetici Ozeti",
        "",
        f"FAZ17, FAZ16 sonunda `PASS - Replacement Build Surface Isolated` ile frozen kalan `RC-M` icin full-family authoritative output parity reopen istedi. `WP-3` sonunda `runtime_error_count = {wp3_summary.get('runtime_error_count')}` ve `authoritative_summary_mismatch_count = {wp3_summary.get('authoritative_summary_mismatch_count')}` kayda gecti.",
        "",
        "## Gate Sonuclari",
        "",
        f"- `WP-3 = {'PASS' if bool(wp3_summary.get('wp3_pass')) else 'FAIL'} `",
    ]
    if wp4_frontier_replay is None:
        lines.append("- `WP-4 = NOT AUTHORIZED `")
    else:
        lines.append("- `WP-4 = PASS `")
        lines.append(
            f"- `output_parity_surface_breach_count = {wp4_frontier_replay.get('output_parity_surface_breach_count')} `"
        )
        lines.append(
            f"- `localized_authorized_downstream_drift_count = {wp4_frontier_replay.get('localized_authorized_downstream_drift_count')} `"
        )
    lines.extend(
        [
            "",
            "## Resmi Karar",
            "",
            f"- `{decision}`",
            "",
            "## Sonraki Resmi Is",
            "",
            f"- `{next_work}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ17 final report pack.")
    parser.add_argument("--wp3-summary-json", type=Path, required=True)
    parser.add_argument("--wp4-frontier-replay-json", type=Path)
    parser.add_argument("--steering-output-md", type=Path, required=True)
    parser.add_argument("--reconciliation-output-json", type=Path, required=True)
    parser.add_argument("--reconciliation-output-md", type=Path, required=True)
    parser.add_argument("--next-work-output-json", type=Path, required=True)
    parser.add_argument("--next-work-output-md", type=Path, required=True)
    parser.add_argument("--report-output-md", type=Path, required=True)
    args = parser.parse_args()

    wp3_summary = load_json(args.wp3_summary_json)
    wp4_frontier_replay = load_json(args.wp4_frontier_replay_json) if args.wp4_frontier_replay_json else None
    decision, next_work = decide(wp3_summary=wp3_summary, wp4_frontier_replay=wp4_frontier_replay)

    write_json(args.reconciliation_output_json, {"official_decision": decision})
    write_json(args.next_work_output_json, {"next_official_work": next_work})
    args.steering_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.steering_output_md.write_text(
        render_steering_md(
            decision=decision,
            next_work=next_work,
            wp3_summary=wp3_summary,
            wp4_frontier_replay=wp4_frontier_replay,
        ),
        encoding="utf-8",
    )
    args.reconciliation_output_md.write_text(render_reconciliation_md(decision=decision), encoding="utf-8")
    args.next_work_output_md.write_text(render_next_work_md(next_work=next_work), encoding="utf-8")
    args.report_output_md.write_text(
        render_report_md(
            decision=decision,
            next_work=next_work,
            wp3_summary=wp3_summary,
            wp4_frontier_replay=wp4_frontier_replay,
        ),
        encoding="utf-8",
    )
    return 0 if decision == "PASS - RC-M Authoritative Output Parity Closed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
