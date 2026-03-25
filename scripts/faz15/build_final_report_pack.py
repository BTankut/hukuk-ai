#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz15_lib import load_json  # noqa: E402


def _wp3_status(control_summary: dict[str, Any]) -> str:
    return "PASS" if bool(control_summary.get("control_pair_authority_match")) else "FAIL"


def _wp4_status(context_contrast: dict[str, Any]) -> str:
    return (
        "PASS"
        if int(context_contrast.get("targeted_pack_count", 0)) == 6
        and int(context_contrast.get("full_family_slice_count", 0)) == 6
        and int(context_contrast.get("targeted_first_divergence_assigned_count", 0)) == 6
        and int(context_contrast.get("full_family_slice_first_divergence_assigned_count", 0)) == 6
        and int(context_contrast.get("unexplained_count", 1)) == 0
        else "FAIL"
    )


def _wp5_status(breach_summary: dict[str, Any]) -> str:
    return (
        "PASS"
        if int(breach_summary.get("frontier_count", 0)) == 217
        and int(breach_summary.get("expected_frontier_count", 0)) == 217
        and bool(breach_summary.get("frontier_count_matches_reference"))
        and int(breach_summary.get("rc_g_vs_rc_l_first_divergence_assigned_count", 0)) == 217
        and int(breach_summary.get("rc_j_vs_rc_l_first_divergence_assigned_count", 0)) == 217
        and int(breach_summary.get("primary_reason_assigned_count", 0)) == 217
        and int(breach_summary.get("root_cause_class_assigned_count", 0)) == 217
        and int(breach_summary.get("unexplained_count", 1)) == 0
        else "FAIL"
    )


def _wp6_status(reconciliation: dict[str, Any]) -> str:
    return "PASS" if str(reconciliation.get("official_decision", "")).startswith("PASS") else "FAIL"


def _render_pack_md(*, title: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "Referans artefact'lar:",
            "- `evaluation/reports/faz15-rc-g-vs-rc-j-control-authority-faz1-50-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-g-vs-rc-j-control-authority-v2-95-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-g-vs-rc-j-control-authority-v3-170-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-g-vs-rc-l-breach-forensics-faz1-50-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-g-vs-rc-l-breach-forensics-v2-95-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-g-vs-rc-l-breach-forensics-v3-170-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-j-vs-rc-l-breach-forensics-faz1-50-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-j-vs-rc-l-breach-forensics-v2-95-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-j-vs-rc-l-breach-forensics-v3-170-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-l-repair-surface-breach-summary-2026-03-25.md`",
            "",
        ]
    )


def _render_steering_md(
    *,
    title: str,
    wp3_status: str,
    wp4_status: str,
    wp5_status: str,
    wp6_status: str,
    control_summary: dict[str, Any],
    context_contrast: dict[str, Any],
    breach_summary: dict[str, Any],
    reconciliation: dict[str, Any],
) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "Tarih: 2026-03-25",
            "",
            "Referans:",
            "- `docs/FAZ15-ROTASYON-RC-L-DISCARD-VE-REPAIR-SURFACE-BREACH-FORENSICS-TALIMATI-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-g-vs-rc-j-control-authority-summary-2026-03-25.md`",
            "- `evaluation/reports/faz15-targeted-vs-full-family-context-contrast-2026-03-25.md`",
            "- `evaluation/reports/faz15-rc-l-repair-surface-breach-summary-2026-03-25.md`",
            "- `coordination/faz15-breach-reconciliation-2026-03-25.md`",
            "",
            "| WP | Durum | Kanit | Sonuc |",
            "| --- | --- | --- | --- |",
            "| `WP-1` | `PASS` | freeze/discard/refreeze contract artefact'lari tamam | `RC-G`, `RC-J`, `RC-L` resmi rol dagilimi kilitlendi |",
            "| `WP-2` | `PASS` | schema, taxonomy ve stage ladder tamam | FAZ15 forensic contract'i sabitlendi |",
            f"| `WP-3` | `{wp3_status}` | control summary: `control_pair_authority_match={str(bool(control_summary.get('control_pair_authority_match'))).lower()}`, `control_pair_breach_in_f0_f12={str(bool(control_summary.get('control_pair_breach_in_f0_f12'))).lower()}` | `RC-G vs RC-J` control pair authority durumu kayda gecti |",
            f"| `WP-4` | `{wp4_status}` | context contrast: `targeted_pack_count={context_contrast.get('targeted_pack_count')}`, `stage_shift_count={context_contrast.get('same_question_stage_shift_count')}`, `unexplained_count={context_contrast.get('unexplained_count')}` | targeted vs full-family context contrast localized |",
            f"| `WP-5` | `{wp5_status}` | breach summary: `frontier_count={breach_summary.get('frontier_count')}`, `unexplained_count={breach_summary.get('unexplained_count')}`, `dominant_root_cause_class={breach_summary.get('dominant_root_cause_class')}` | full breach pair-matrix forensics tamamlandi |",
            f"| `WP-6` | `{wp6_status}` | reconciliation: `official_decision={reconciliation.get('official_decision')}` | `{reconciliation.get('official_decision')}` |",
            "",
            "## Sonraki Resmi Is",
            "",
            f"- `{reconciliation.get('next_official_work')}`",
            "",
        ]
    )


def _render_report_md(
    *,
    title: str,
    wp3_status: str,
    wp4_status: str,
    wp5_status: str,
    wp6_status: str,
    control_summary: dict[str, Any],
    context_contrast: dict[str, Any],
    breach_summary: dict[str, Any],
    reconciliation: dict[str, Any],
) -> str:
    lines = [
        f"# {title}",
        "",
        "Tarih: 2026-03-25",
        "",
        "Referans:",
        "- `docs/FAZ15-ROTASYON-RC-L-DISCARD-VE-REPAIR-SURFACE-BREACH-FORENSICS-TALIMATI-2026-03-25.md`",
        "- `coordination/faz15-official-implementation-plan-2026-03-25.md`",
        "- `coordination/faz15-steering-decision-table-2026-03-25.md`",
        "- `evaluation/reports/faz15-rc-g-vs-rc-j-control-authority-summary-2026-03-25.md`",
        "- `evaluation/reports/faz15-targeted-vs-full-family-context-contrast-2026-03-25.md`",
        "- `evaluation/reports/faz15-rc-l-repair-surface-breach-summary-2026-03-25.md`",
        "- `coordination/faz15-breach-first-divergence-table-2026-03-25.md`",
        "- `coordination/faz15-breach-root-cause-mapping-2026-03-25.md`",
        "- `coordination/faz15-breach-reconciliation-2026-03-25.md`",
        "",
        "## Yonetici Ozeti",
        "",
        "FAZ15 resmi talimata gore yalniz `RC-L discard` ve `repair-surface breach forensics` amaciyla yurutuldu. Yeni candidate build acilmadi, `RC-L` uzerine patch atilmadi ve serving/cutover/pilot yolu acilmadi. `RC-G` kalite referansi, `RC-J` authoritative diagnostic referans ve `RC-L` forensic-only discard candidate olarak korundu.",
        "",
        f"Control pair authority sonucu `control_pair_authority_match = {str(bool(control_summary.get('control_pair_authority_match'))).lower()}` ve `control_pair_breach_in_f0_f12 = {str(bool(control_summary.get('control_pair_breach_in_f0_f12'))).lower()}` olarak kapandi. Targeted vs full-family context contrast `unexplained_count = {context_contrast.get('unexplained_count')}` ve `stage_shift_count = {context_contrast.get('same_question_stage_shift_count')}` ile kapandi. Full breach pair-matrix `frontier_count = {breach_summary.get('frontier_count')}`, `unexplained_count = {breach_summary.get('unexplained_count')}`, `dominant_root_cause_class = {breach_summary.get('dominant_root_cause_class')}` sonucunu verdi.",
        "",
        "Bu nedenle resmi karar:",
        "",
        f"> `{reconciliation.get('official_decision')}`",
        "",
        "## WP-1 Sonucu",
        "",
        "- `WP-1 = PASS`",
        "",
        "## WP-2 Sonucu",
        "",
        "- `WP-2 = PASS`",
        "",
        "## WP-3 Control Pair Authority",
        "",
        f"- `WP-3 = {wp3_status}`",
        f"- `control_pair_authority_match = {str(bool(control_summary.get('control_pair_authority_match'))).lower()}`",
        f"- `control_pair_breach_in_f0_f12 = {str(bool(control_summary.get('control_pair_breach_in_f0_f12'))).lower()}`",
        f"- `control_pair_downstream_only = {str((not bool(control_summary.get('control_pair_authority_match'))) and (not bool(control_summary.get('control_pair_breach_in_f0_f12')))).lower()}`",
        "",
        "Per-family control ozeti:",
        "",
    ]
    for row in control_summary.get("families", []):
        lines.append(
            f"- `{row['family_id']}` -> `pass={str(bool(row['pass'])).lower()}`, "
            f"`mismatch_count={row['mismatch_count']}`, "
            f"`family_metric_delta_zero={str(bool(row['family_metric_delta_zero'])).lower()}`"
        )
        for failure in row.get("failures", []):
            lines.append(f"  not: `{failure}`")
    lines.extend(
        [
            "",
            "## WP-4 Targeted vs Full-Family Context Contrast",
            "",
            f"- `WP-4 = {wp4_status}`",
            f"- `targeted_pack_count = {context_contrast.get('targeted_pack_count')}`",
            f"- `full_family_slice_count = {context_contrast.get('full_family_slice_count')}`",
            f"- `targeted_mismatch_count = {context_contrast.get('targeted_mismatch_count')}`",
            f"- `full_family_slice_mismatch_count = {context_contrast.get('full_family_slice_mismatch_count')}`",
            f"- `stage_relocation_count = {context_contrast.get('stage_relocation_count')}`",
            f"- `unexplained_count = {context_contrast.get('unexplained_count')}`",
            "",
            "## WP-5 Full Breach Pair-Matrix Forensics",
            "",
            f"- `WP-5 = {wp5_status}`",
            f"- `frontier_count = {breach_summary.get('frontier_count')}`",
            f"- `expected_frontier_count = {breach_summary.get('expected_frontier_count')}`",
            f"- `frontier_count_matches_reference = {str(bool(breach_summary.get('frontier_count_matches_reference'))).lower()}`",
            f"- `rc_g_vs_rc_l_first_divergence_assigned_count = {breach_summary.get('rc_g_vs_rc_l_first_divergence_assigned_count')}`",
            f"- `rc_j_vs_rc_l_first_divergence_assigned_count = {breach_summary.get('rc_j_vs_rc_l_first_divergence_assigned_count')}`",
            f"- `primary_reason_assigned_count = {breach_summary.get('primary_reason_assigned_count')}`",
            f"- `root_cause_class_assigned_count = {breach_summary.get('root_cause_class_assigned_count')}`",
            f"- `pair_symmetry_count = {breach_summary.get('pair_symmetry_count')}`",
            f"- `pair_asymmetry_count = {breach_summary.get('pair_asymmetry_count')}`",
            f"- `unexplained_count = {breach_summary.get('unexplained_count')}`",
            f"- `dominant_root_cause_class = {breach_summary.get('dominant_root_cause_class')}`",
            "",
            "## WP-6 Reconciliation",
            "",
            f"- `WP-6 = {wp6_status}`",
            f"- `official_decision = {reconciliation.get('official_decision')}`",
            f"- `next_official_work = {reconciliation.get('next_official_work')}`",
            "",
            "## Resmi Karar",
            "",
            f"- `{reconciliation.get('official_decision')}`",
            "",
            "## Sonraki Resmi Is",
            "",
            f"- `{reconciliation.get('next_official_work')}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ15 steering and final report pack.")
    parser.add_argument("--control-summary-json", type=Path, required=True)
    parser.add_argument("--context-contrast-json", type=Path, required=True)
    parser.add_argument("--breach-summary-json", type=Path, required=True)
    parser.add_argument("--breach-reconciliation-json", type=Path, required=True)
    parser.add_argument("--pack-output-md", type=Path, required=True)
    parser.add_argument("--steering-output-md", type=Path, required=True)
    parser.add_argument("--report-output-md", type=Path, required=True)
    parser.add_argument("--pack-title", required=True)
    parser.add_argument("--steering-title", required=True)
    parser.add_argument("--report-title", required=True)
    args = parser.parse_args()

    control_summary = load_json(args.control_summary_json)
    context_contrast = load_json(args.context_contrast_json)
    breach_summary = load_json(args.breach_summary_json)
    reconciliation = load_json(args.breach_reconciliation_json)

    wp3_status = _wp3_status(control_summary)
    wp4_status = _wp4_status(context_contrast)
    wp5_status = _wp5_status(breach_summary)
    wp6_status = _wp6_status(reconciliation)

    args.pack_output_md.write_text(_render_pack_md(title=args.pack_title), encoding="utf-8")
    args.steering_output_md.write_text(
        _render_steering_md(
            title=args.steering_title,
            wp3_status=wp3_status,
            wp4_status=wp4_status,
            wp5_status=wp5_status,
            wp6_status=wp6_status,
            control_summary=control_summary,
            context_contrast=context_contrast,
            breach_summary=breach_summary,
            reconciliation=reconciliation,
        ),
        encoding="utf-8",
    )
    args.report_output_md.write_text(
        _render_report_md(
            title=args.report_title,
            wp3_status=wp3_status,
            wp4_status=wp4_status,
            wp5_status=wp5_status,
            wp6_status=wp6_status,
            control_summary=control_summary,
            context_contrast=context_contrast,
            breach_summary=breach_summary,
            reconciliation=reconciliation,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
