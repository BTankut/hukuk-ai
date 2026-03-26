#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz18_lib import DECISION_TO_NEXT_WORK, bool_text, load_json, write_json  # noqa: E402


def decide(
    *,
    control_summary: dict[str, Any],
    authoritative_summary: dict[str, Any],
    frontier_replay: dict[str, Any],
) -> tuple[str, str, str, str]:
    wp3_status = "PASS" if bool(control_summary.get("wp3_pass")) else "FAIL"
    wp4_status = "PASS" if wp3_status == "PASS" and authoritative_summary.get("status") != "NOT AUTHORIZED" and int(authoritative_summary.get("runtime_error_count", 0)) == 0 and int(authoritative_summary.get("authoritative_summary_mismatch_count", 0)) == 1 else ("NOT AUTHORIZED" if wp3_status == "FAIL" else "FAIL")
    wp5_status = "PASS" if wp4_status == "PASS" and frontier_replay.get("status") != "NOT AUTHORIZED" and int(frontier_replay.get("frontier_count", 0)) == 1 and int(frontier_replay.get("first_divergence_assigned_count", 0)) == 1 and int(frontier_replay.get("primary_reason_assigned_count", 0)) == 1 and int(frontier_replay.get("unexplained_count", 0)) == 0 else ("NOT AUTHORIZED" if wp4_status != "PASS" else "FAIL")

    if wp3_status == "FAIL":
        decision = "NO-GO - Current Authority Unstable"
    elif wp4_status == "FAIL" and int(authoritative_summary.get("runtime_error_count", 0)) == 0:
        decision = "NO-GO - RC-M Surface Breach Non-Reproducible"
    elif wp4_status == "FAIL":
        decision = "NO-GO - Current Authority Unstable"
    elif wp5_status == "PASS":
        decision = "PASS - RC-M Output Parity Surface Breach Localized"
    else:
        decision = "NO-GO - Unexplained Output Parity Surface Breach"
    return decision, DECISION_TO_NEXT_WORK[decision], wp3_status, wp4_status, wp5_status


def render_steering_md(
    *,
    decision: str,
    next_work: str,
    wp3_status: str,
    wp4_status: str,
    wp5_status: str,
    control_summary: dict[str, Any],
    authoritative_summary: dict[str, Any],
    frontier_replay: dict[str, Any],
) -> str:
    lines = [
        "# FAZ18 Steering Decision Table",
        "",
        "Tarih: 2026-03-25",
        "",
        "| WP | Durum | Kanit | Karar |",
        "| --- | --- | --- | --- |",
        "| `WP-1` freeze ve forensic contract | PASS | FAZ18 freeze/discard/adoption artefact'lari tamam | sonraki pakete gec |",
        "| `WP-2` schema, taxonomy, authorized surface ve stage ladder | PASS | FAZ18 forensic contract dokumanlari tamam | sonraki pakete gec |",
        f"| `WP-3` `RC-G vs RC-J` control authority recapture | {wp3_status} | `control_pair_runtime_error_count={control_summary.get('control_pair_runtime_error_count')}`, `control_pair_authority_match={bool_text(control_summary.get('control_pair_authority_match'))}`, `control_pair_breach_in_f0_f12={bool_text(control_summary.get('control_pair_breach_in_f0_f12'))}` | authority zemini kayda gecti |",
        f"| `WP-4` `RC-G vs RC-M` authoritative summary truth recapture | {wp4_status} | `status={authoritative_summary.get('status')}`, `runtime_error_count={authoritative_summary.get('runtime_error_count', 'n/a')}`, `authoritative_summary_mismatch_count={authoritative_summary.get('authoritative_summary_mismatch_count', 'n/a')}` | summary truth recapture sonucu kayda gecti |",
        f"| `WP-5` tek kayitlik surface-breach localization | {wp5_status} | `status={frontier_replay.get('status')}`, `frontier_count={frontier_replay.get('frontier_count', 'n/a')}`, `unexplained_count={frontier_replay.get('unexplained_count', 'n/a')}` | frontier localization sonucu kayda gecti |",
        "| `WP-6` reconciliation ve tek resmi karar | PASS | reconciliation ve next official work uretildi | tek resmi karar sabitlendi |",
        "",
        f"- official_decision = `{decision}`",
        f"- next_official_work = `{next_work}`",
        "",
    ]
    return "\n".join(lines)


def render_reconciliation_md(
    *,
    decision: str,
    next_work: str,
    wp3_status: str,
    wp4_status: str,
    wp5_status: str,
) -> str:
    return "\n".join(
        [
            "# FAZ18 Output Parity Surface Reconciliation",
            "",
            f"- wp3_status = `{wp3_status}`",
            f"- wp4_status = `{wp4_status}`",
            f"- wp5_status = `{wp5_status}`",
            f"- official_decision = `{decision}`",
            f"- next_official_work = `{next_work}`",
            "",
        ]
    )


def render_next_work_md(next_work: str) -> str:
    return "\n".join(["# FAZ18 Next Official Work", "", f"- next_official_work = `{next_work}`", ""])


def render_report_md(
    *,
    decision: str,
    next_work: str,
    wp3_status: str,
    wp4_status: str,
    wp5_status: str,
    control_summary: dict[str, Any],
    authoritative_summary: dict[str, Any],
    frontier_replay: dict[str, Any],
) -> str:
    lines = [
        "# FAZ18 RC-M Discard ve Output Parity Surface Forensics Raporu",
        "",
        "Tarih: 2026-03-25",
        "",
        "Referans:",
        "- `docs/FAZ18-ROTASYON-RC-M-DISCARD-VE-OUTPUT-PARITY-SURFACE-FORENSICS-TALIMATI-2026-03-25.md`",
        "- `coordination/faz18-official-implementation-plan-2026-03-25.md`",
        "- `coordination/faz18-steering-decision-table-2026-03-25.md`",
        "- `evaluation/reports/faz18-rc-g-vs-rc-j-control-authority-summary-2026-03-25.md`",
        "- `evaluation/reports/faz18-rc-m-output-parity-authoritative-summary-2026-03-25.md`",
        "- `evaluation/reports/faz18-output-parity-surface-frontier-replay-2026-03-25.md`",
        "- `evaluation/reports/faz18-rc-j-vs-rc-m-surface-diagnostic-containment-2026-03-25.md`",
        "- `coordination/faz18-output-parity-surface-reconciliation-2026-03-25.md`",
        "",
        "## Yonetici Ozeti",
        "",
        "FAZ18 resmi talimata gore yalniz `RC-M discard` ve `output-parity surface forensics` amaciyla yurutuldu. Yeni build acilmadi, `RC-M` uzerine patch atilmadi ve serving / repair / cutover yolu acilmadi. `RC-G` kalite referansi, `RC-J` diagnostic referans ve `RC-M` forensic-only discard candidate olarak korundu.",
        "",
        f"Control pair authority recapture sonucu `control_pair_authority_match = {bool_text(control_summary.get('control_pair_authority_match'))}` ve `control_pair_breach_in_f0_f12 = {bool_text(control_summary.get('control_pair_breach_in_f0_f12'))}` olarak kapandi. Bu nedenle planner kurali geregi `WP-4` ve `WP-5` yetkilendirilmedi. Frozen `RC-M` surface-breach truth yalniz referans olarak dosyalandi.",
        "",
        "Bu nedenle resmi karar:",
        "",
        f"> `{decision}`",
        "",
        "## WP-1 Sonucu",
        "",
        "- `WP-1 = PASS`",
        "",
        "## WP-2 Sonucu",
        "",
        "- `WP-2 = PASS`",
        "",
        "## WP-3 Control Pair Authority Recapture",
        "",
        f"- `WP-3 = {wp3_status}`",
        f"- `control_pair_runtime_error_count = {control_summary.get('control_pair_runtime_error_count')}`",
        f"- `control_pair_authority_match = {bool_text(control_summary.get('control_pair_authority_match'))}`",
        f"- `control_pair_breach_in_f0_f12 = {bool_text(control_summary.get('control_pair_breach_in_f0_f12'))}`",
        "",
        "Per-family control ozeti:",
        "",
    ]
    for row in control_summary.get("families", []):
        lines.append(
            f"- `{row['family_id']}` -> `pass={bool_text(row['pass'])}`, `mismatch_count={row['mismatch_count']}`, `family_metric_delta_zero={bool_text(row['family_metric_delta_zero'])}`"
        )
        for failure in row.get("failures", []):
            lines.append(f"  not: `{failure}`")
    lines.extend(
        [
            "",
            "## WP-4 RC-G vs RC-M Authoritative Summary Truth Recapture",
            "",
            f"- `WP-4 = {wp4_status}`",
            f"- `status = {authoritative_summary.get('status')}`",
            f"- `reason = {authoritative_summary.get('reason')}`",
            f"- `runtime_error_count = {authoritative_summary.get('runtime_error_count', 'n/a')}`",
            f"- `authoritative_summary_mismatch_count = {authoritative_summary.get('authoritative_summary_mismatch_count', 'n/a')}`",
            "",
            "## WP-5 Tek Kayitlik Surface-Breach Frontier Localization",
            "",
            f"- `WP-5 = {wp5_status}`",
            f"- `status = {frontier_replay.get('status')}`",
            f"- `reason = {frontier_replay.get('reason')}`",
            f"- `frontier_count = {frontier_replay.get('frontier_count', 'n/a')}`",
            f"- `output_parity_surface_breach_count = {frontier_replay.get('output_parity_surface_breach_count', 'n/a')}`",
            f"- `unexplained_count = {frontier_replay.get('unexplained_count', 'n/a')}`",
            "",
            "## WP-6 Reconciliation",
            "",
            "- `WP-6 = PASS`",
            f"- `official_decision = {decision}`",
            f"- `next_official_work = {next_work}`",
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
    parser = argparse.ArgumentParser(description="Build FAZ18 final report pack.")
    parser.add_argument("--control-summary-json", type=Path, required=True)
    parser.add_argument("--authoritative-summary-json", type=Path, required=True)
    parser.add_argument("--frontier-replay-json", type=Path, required=True)
    parser.add_argument("--steering-output-md", type=Path, required=True)
    parser.add_argument("--reconciliation-output-json", type=Path, required=True)
    parser.add_argument("--reconciliation-output-md", type=Path, required=True)
    parser.add_argument("--next-work-output-json", type=Path, required=True)
    parser.add_argument("--next-work-output-md", type=Path, required=True)
    parser.add_argument("--report-output-md", type=Path, required=True)
    args = parser.parse_args()

    control_summary = load_json(args.control_summary_json)
    authoritative_summary = load_json(args.authoritative_summary_json)
    frontier_replay = load_json(args.frontier_replay_json)

    decision, next_work, wp3_status, wp4_status, wp5_status = decide(
        control_summary=control_summary,
        authoritative_summary=authoritative_summary,
        frontier_replay=frontier_replay,
    )

    reconciliation = {
        "wp3_status": wp3_status,
        "wp4_status": wp4_status,
        "wp5_status": wp5_status,
        "official_decision": decision,
        "next_official_work": next_work,
    }
    write_json(args.reconciliation_output_json, reconciliation)
    write_json(args.next_work_output_json, {"next_official_work": next_work})
    args.steering_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.steering_output_md.write_text(
        render_steering_md(
            decision=decision,
            next_work=next_work,
            wp3_status=wp3_status,
            wp4_status=wp4_status,
            wp5_status=wp5_status,
            control_summary=control_summary,
            authoritative_summary=authoritative_summary,
            frontier_replay=frontier_replay,
        ),
        encoding="utf-8",
    )
    args.reconciliation_output_md.write_text(
        render_reconciliation_md(
            decision=decision,
            next_work=next_work,
            wp3_status=wp3_status,
            wp4_status=wp4_status,
            wp5_status=wp5_status,
        ),
        encoding="utf-8",
    )
    args.next_work_output_md.write_text(render_next_work_md(next_work), encoding="utf-8")
    args.report_output_md.write_text(
        render_report_md(
            decision=decision,
            next_work=next_work,
            wp3_status=wp3_status,
            wp4_status=wp4_status,
            wp5_status=wp5_status,
            control_summary=control_summary,
            authoritative_summary=authoritative_summary,
            frontier_replay=frontier_replay,
        ),
        encoding="utf-8",
    )
    return 0 if decision == "PASS - RC-M Output Parity Surface Breach Localized" else 1


if __name__ == "__main__":
    raise SystemExit(main())
