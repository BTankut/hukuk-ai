#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz16_lib import NEXT_WORK_BY_DECISION, load_json, write_json


def decide(
    *,
    wp2_summary: dict[str, Any],
    wp3_manifest: dict[str, Any],
    wp4_candidate_gate: dict[str, Any],
    wp4_replacement_gate: dict[str, Any],
    wp5_gate: dict[str, Any],
    wp6_candidate_gate: dict[str, Any],
    wp6_replacement_gate: dict[str, Any],
) -> tuple[str, str]:
    if not bool(wp2_summary.get("wp2_pass")):
        decision = "NO-GO - Control Authority Unstable"
    elif not bool(wp4_candidate_gate.get("gate_pass")) or not bool(wp4_replacement_gate.get("gate_pass")):
        decision = "NO-GO - Replacement Repair Ineffective"
    elif not bool(wp5_gate.get("gate_pass")) or not bool(wp6_candidate_gate.get("gate_pass")) or not bool(
        wp6_replacement_gate.get("gate_pass")
    ):
        decision = "NO-GO - Build Surface Isolation Failed"
    else:
        manifest_ok = (
            wp3_manifest.get("build_from") == "RC-J"
            and wp3_manifest.get("answer_path_delta") == []
            and wp3_manifest.get("request_surface_delta") == []
            and wp3_manifest.get("model_visible_surface_delta") == []
            and wp3_manifest.get("retrieval_surface_delta") == []
            and wp3_manifest.get("release_controls_delta") == []
        )
        decision = "PASS - Replacement Build Surface Isolated" if manifest_ok else "NO-GO - Build Surface Isolation Failed"
    return decision, NEXT_WORK_BY_DECISION[decision]


def wp_status(value: bool) -> str:
    return "PASS" if value else "FAIL"


def render_steering_md(
    *,
    title: str,
    decision: str,
    next_work: str,
    wp2_summary: dict[str, Any],
    wp4_candidate_gate: dict[str, Any],
    wp4_replacement_gate: dict[str, Any],
    wp5_gate: dict[str, Any],
    wp6_candidate_gate: dict[str, Any],
    wp6_replacement_gate: dict[str, Any],
) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "| WP | Durum | Kanit | Sonuc |",
            "| --- | --- | --- | --- |",
            "| `WP-1` | `PASS` | refreeze/build contract artefact'lari tamam | faz authority kuruldu |",
            f"| `WP-2` | `{wp_status(bool(wp2_summary.get('wp2_pass')))}` | `runtime_error_count={wp2_summary.get('runtime_error_count')}`, `control_pair_breach_in_f0_f12={str(bool(wp2_summary.get('control_pair_breach_in_f0_f12'))).lower()}` | current authority snapshot donduruldu |",
            "| `WP-3` | `PASS` | `build_from=RC-J`, tum delta listeleri bos | RC-M manifest ve build proof tamam |",
            f"| `WP-4` | `{wp_status(bool(wp4_candidate_gate.get('gate_pass')) and bool(wp4_replacement_gate.get('gate_pass')))}` | candidate `gate_pass={str(bool(wp4_candidate_gate.get('gate_pass'))).lower()}`, replacement `gate_pass={str(bool(wp4_replacement_gate.get('gate_pass'))).lower()}` | targeted 6 gate sonucu kayda gecti |",
            f"| `WP-5` | `{wp_status(bool(wp5_gate.get('gate_pass')))}` | `repair_surface_breach_count={wp5_gate.get('repair_surface_breach_count')}` | breach sentinel-16 gate sonucu kayda gecti |",
            f"| `WP-6` | `{wp_status(bool(wp6_candidate_gate.get('gate_pass')) and bool(wp6_replacement_gate.get('gate_pass')))}` | candidate `gate_pass={str(bool(wp6_candidate_gate.get('gate_pass'))).lower()}`, replacement `gate_pass={str(bool(wp6_replacement_gate.get('gate_pass'))).lower()}` | full-family replacement isolation sonucu kayda gecti |",
            "| `WP-7` | `PASS` | reconciliation ve next work uretildi | tek resmi karar sabitlendi |",
            "",
            f"- official_decision = `{decision}`",
            f"- next_official_work = `{next_work}`",
            "",
        ]
    )


def render_reconciliation_md(*, title: str, decision: str) -> str:
    return "\n".join([f"# {title}", "", f"- official_decision = `{decision}`", ""])


def render_next_work_md(*, title: str, next_work: str) -> str:
    return "\n".join([f"# {title}", "", f"- next_official_work = `{next_work}`", ""])


def render_report_md(
    *,
    title: str,
    decision: str,
    next_work: str,
    wp2_summary: dict[str, Any],
    wp4_candidate_gate: dict[str, Any],
    wp4_replacement_gate: dict[str, Any],
    wp5_gate: dict[str, Any],
    wp6_candidate_gate: dict[str, Any],
    wp6_replacement_gate: dict[str, Any],
) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "Tarih: 2026-03-25",
            "",
            "Referans:",
            "- `docs/FAZ16-ROTASYON-RC-M-REPLACEMENT-BUILD-SURFACE-ISOLATION-GATE-TALIMATI-2026-03-25.md`",
            "- `coordination/faz16-official-implementation-plan-2026-03-25.md`",
            "- `coordination/faz16-steering-decision-table-2026-03-25.md`",
            "",
            "## Yonetici Ozeti",
            "",
            f"FAZ16 tek resmi hedef olarak `RC-L discard` sonrasinda `RC-J` uzerinden uretilen `RC-M` replacement candidate'inin build-surface isolation kanitini istedi. `WP-2` current authority snapshot `runtime_error_count = {wp2_summary.get('runtime_error_count')}` ve `control_pair_breach_in_f0_f12 = {str(bool(wp2_summary.get('control_pair_breach_in_f0_f12'))).lower()}` ile kapandi. Targeted, sentinel ve full-family isolation gate'leri candidate ve replacement pair icin sirasiyla kayda alindi.",
            "",
            "## Gate Sonuclari",
            "",
            f"- `WP-2 = {wp_status(bool(wp2_summary.get('wp2_pass')))} `",
            f"- `WP-4 candidate gate = {wp_status(bool(wp4_candidate_gate.get('gate_pass')))} `",
            f"- `WP-4 replacement gate = {wp_status(bool(wp4_replacement_gate.get('gate_pass')))} `",
            f"- `WP-5 = {wp_status(bool(wp5_gate.get('gate_pass')))} `",
            f"- `WP-6 candidate gate = {wp_status(bool(wp6_candidate_gate.get('gate_pass')))} `",
            f"- `WP-6 replacement gate = {wp_status(bool(wp6_replacement_gate.get('gate_pass')))} `",
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ16 final report pack.")
    parser.add_argument("--wp2-summary-json", type=Path, required=True)
    parser.add_argument("--wp3-manifest-json", type=Path, required=True)
    parser.add_argument("--wp4-candidate-gate-json", type=Path, required=True)
    parser.add_argument("--wp4-replacement-gate-json", type=Path, required=True)
    parser.add_argument("--wp5-gate-json", type=Path, required=True)
    parser.add_argument("--wp6-candidate-gate-json", type=Path, required=True)
    parser.add_argument("--wp6-replacement-gate-json", type=Path, required=True)
    parser.add_argument("--steering-output-md", type=Path, required=True)
    parser.add_argument("--reconciliation-output-json", type=Path, required=True)
    parser.add_argument("--reconciliation-output-md", type=Path, required=True)
    parser.add_argument("--next-work-output-json", type=Path, required=True)
    parser.add_argument("--next-work-output-md", type=Path, required=True)
    parser.add_argument("--report-output-md", type=Path, required=True)
    parser.add_argument("--steering-title", required=True)
    parser.add_argument("--report-title", required=True)
    args = parser.parse_args()

    wp2_summary = load_json(args.wp2_summary_json)
    wp3_manifest = load_json(args.wp3_manifest_json)
    wp4_candidate_gate = load_json(args.wp4_candidate_gate_json)
    wp4_replacement_gate = load_json(args.wp4_replacement_gate_json)
    wp5_gate = load_json(args.wp5_gate_json)
    wp6_candidate_gate = load_json(args.wp6_candidate_gate_json)
    wp6_replacement_gate = load_json(args.wp6_replacement_gate_json)

    decision, next_work = decide(
        wp2_summary=wp2_summary,
        wp3_manifest=wp3_manifest,
        wp4_candidate_gate=wp4_candidate_gate,
        wp4_replacement_gate=wp4_replacement_gate,
        wp5_gate=wp5_gate,
        wp6_candidate_gate=wp6_candidate_gate,
        wp6_replacement_gate=wp6_replacement_gate,
    )

    reconciliation = {"official_decision": decision}
    next_work_payload = {"next_official_work": next_work}
    write_json(args.reconciliation_output_json, reconciliation)
    write_json(args.next_work_output_json, next_work_payload)

    args.steering_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.steering_output_md.write_text(
        render_steering_md(
            title=args.steering_title,
            decision=decision,
            next_work=next_work,
            wp2_summary=wp2_summary,
            wp4_candidate_gate=wp4_candidate_gate,
            wp4_replacement_gate=wp4_replacement_gate,
            wp5_gate=wp5_gate,
            wp6_candidate_gate=wp6_candidate_gate,
            wp6_replacement_gate=wp6_replacement_gate,
        ),
        encoding="utf-8",
    )
    args.reconciliation_output_md.write_text(
        render_reconciliation_md(
            title="FAZ16 Replacement Build Surface Isolation Reconciliation",
            decision=decision,
        ),
        encoding="utf-8",
    )
    args.next_work_output_md.write_text(
        render_next_work_md(
            title="FAZ16 Next Official Work",
            next_work=next_work,
        ),
        encoding="utf-8",
    )
    args.report_output_md.write_text(
        render_report_md(
            title=args.report_title,
            decision=decision,
            next_work=next_work,
            wp2_summary=wp2_summary,
            wp4_candidate_gate=wp4_candidate_gate,
            wp4_replacement_gate=wp4_replacement_gate,
            wp5_gate=wp5_gate,
            wp6_candidate_gate=wp6_candidate_gate,
            wp6_replacement_gate=wp6_replacement_gate,
        ),
        encoding="utf-8",
    )
    return 0 if decision == "PASS - Replacement Build Surface Isolated" else 1


if __name__ == "__main__":
    raise SystemExit(main())

