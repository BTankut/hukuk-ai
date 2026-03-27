#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz22_lib import DECISION_TO_NEXT_WORK, bool_text, load_json, markdown_table, write_json


def decide(
    *,
    control_summary: dict[str, Any],
    authoritative_summary: dict[str, Any] | None,
    frontier_replay: dict[str, Any] | None,
) -> tuple[str, str, str, str]:
    wp3_status = "PASS" if bool(control_summary.get("wp3_pass")) else "FAIL"
    wp4_status = "NOT AUTHORIZED"
    wp5_status = "NOT AUTHORIZED"
    if wp3_status == "PASS":
        if authoritative_summary is not None:
            wp4_status = "PASS" if bool(authoritative_summary.get("wp4_pass")) else "FAIL"
            if wp4_status == "PASS" and frontier_replay is not None:
                wp5_status = "PASS" if bool(frontier_replay.get("wp5_pass")) else "FAIL"

    if wp3_status == "FAIL":
        decision = "NO-GO - Canonical Current Authority Contract Breach"
    elif wp4_status == "FAIL" and int((authoritative_summary or {}).get("runtime_error_count", 0)) == 0:
        decision = "NO-GO - RC-M Surface Breach Non-Reproducible Under Canonical Current Authority"
    elif wp4_status == "FAIL":
        decision = "NO-GO - Canonical Current Authority Contract Breach"
    elif wp5_status == "PASS":
        decision = "PASS - RC-M Output Parity Surface Breach Localized Under Canonical Current Authority"
    else:
        decision = "NO-GO - Unexplained Output Parity Surface Breach Under Canonical Current Authority"

    return decision, DECISION_TO_NEXT_WORK[decision], wp3_status, wp4_status, wp5_status


def render_steering(
    *,
    decision: str,
    next_work: str,
    wp3_status: str,
    wp4_status: str,
    wp5_status: str,
    control_summary: dict[str, Any],
    authoritative_summary: dict[str, Any] | None,
    frontier_replay: dict[str, Any] | None,
) -> str:
    rows = [
        {
            "wp": "WP-1",
            "status": "PASS",
            "evidence": "canonical current authority adopted, rc-g/rc-j/rc-m roles frozen",
            "decision": "wp2",
        },
        {
            "wp": "WP-2",
            "status": "PASS",
            "evidence": "forensics schema/taxonomy/authorized surface/stage ladder contracts written",
            "decision": "wp3",
        },
        {
            "wp": "WP-3",
            "status": wp3_status,
            "evidence": (
                f"runtime_error_count={control_summary.get('control_pair_runtime_error_count')}, "
                f"authority_match={bool_text(control_summary.get('control_pair_authority_match'))}"
            ),
            "decision": "wp4" if wp3_status == "PASS" else "wp6",
        },
        {
            "wp": "WP-4",
            "status": wp4_status,
            "evidence": (
                "not authorized"
                if authoritative_summary is None
                else (
                    f"runtime_error_count={authoritative_summary.get('runtime_error_count')}, "
                    f"mismatch_count={authoritative_summary.get('authoritative_summary_mismatch_count')}, "
                    f"frontier_candidate_count={authoritative_summary.get('frontier_candidate_count')}"
                )
            ),
            "decision": "wp5" if wp4_status == "PASS" else "wp6",
        },
        {
            "wp": "WP-5",
            "status": wp5_status,
            "evidence": (
                "not authorized"
                if frontier_replay is None
                else (
                    f"frontier_count={frontier_replay.get('frontier_count')}, "
                    f"unexplained_count={frontier_replay.get('unexplained_count')}, "
                    f"rc_j_vs_rc_m_runtime_error_count={frontier_replay.get('rc_j_vs_rc_m_runtime_error_count')}"
                )
            ),
            "decision": "wp6",
        },
        {
            "wp": "WP-6",
            "status": "PASS",
            "evidence": decision,
            "decision": next_work,
        },
    ]
    lines = ["# FAZ22 Steering Decision Table", ""]
    lines.extend(markdown_table([("wp", "WP"), ("status", "Durum"), ("evidence", "Kanit"), ("decision", "Karar")], rows))
    lines.extend(["", f"- official_decision = `{decision}`", f"- next_official_work = `{next_work}`", ""])
    return "\n".join(lines)


def render_reconciliation(
    *,
    decision: str,
    next_work: str,
    wp3_status: str,
    wp4_status: str,
    wp5_status: str,
    control_summary: dict[str, Any],
    authoritative_summary: dict[str, Any] | None,
    frontier_replay: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "wp1_status": "PASS",
        "wp2_status": "PASS",
        "wp3_status": wp3_status,
        "wp4_status": wp4_status,
        "wp5_status": wp5_status,
        "control_pair_runtime_error_count": int(control_summary.get("control_pair_runtime_error_count", 0)),
        "control_pair_authority_match": bool(control_summary.get("control_pair_authority_match")),
        "current_authority_contract_breach": bool(control_summary.get("current_authority_contract_breach")),
        "control_pair_breach_in_f0_f12": bool(control_summary.get("control_pair_breach_in_f0_f12")),
        "authoritative_summary_runtime_error_count": int((authoritative_summary or {}).get("runtime_error_count", 0)),
        "authoritative_summary_mismatch_count": int(
            (authoritative_summary or {}).get("authoritative_summary_mismatch_count", 0)
        ),
        "output_parity_surface_breach_count": int(
            (authoritative_summary or {}).get("output_parity_surface_breach_count", 0)
        ),
        "localized_authorized_downstream_drift_count": int(
            (authoritative_summary or {}).get("localized_authorized_downstream_drift_count", 0)
        ),
        "frontier_candidate_count": int((authoritative_summary or {}).get("frontier_candidate_count", 0)),
        "frontier_count": int((frontier_replay or {}).get("frontier_count", 0)),
        "first_divergence_assigned_count": int((frontier_replay or {}).get("first_divergence_assigned_count", 0)),
        "primary_reason_assigned_count": int((frontier_replay or {}).get("primary_reason_assigned_count", 0)),
        "root_cause_class_assigned_count": int((frontier_replay or {}).get("root_cause_class_assigned_count", 0)),
        "unexplained_count": int((frontier_replay or {}).get("unexplained_count", 0)),
        "rc_j_vs_rc_m_runtime_error_count": int((frontier_replay or {}).get("rc_j_vs_rc_m_runtime_error_count", 0)),
        "official_decision": decision,
        "next_official_work": next_work,
    }


def render_report(
    *,
    decision: str,
    next_work: str,
    wp3_status: str,
    wp4_status: str,
    wp5_status: str,
    control_summary: dict[str, Any],
    authoritative_summary: dict[str, Any] | None,
    frontier_replay: dict[str, Any] | None,
) -> str:
    frontier_row = ((frontier_replay or {}).get("rows") or [{}])[0]
    lines = [
        "# FAZ22 RC-M Discard ve Output-Parity Surface Forensics Reopen Under Canonical Current Authority Raporu",
        "",
        "Tarih: 2026-03-27",
        "",
        "## Yonetici Ozeti",
        "",
        "FAZ22, FAZ21 ile canonical current authority resmen benimsendikten sonra RC-M discard candidate icin output-parity surface truth'unu ayni canonical authority zemini altinda yeniden acmak amaciyla yurutuldu. Bu fazda yeni build, patch veya repair acilmadi; yalniz canonical current authority dogrulandi, RC-G vs RC-M authoritative summary yeniden toplandi ve varsa tek frontier kaydi stage-level lokalize edildi.",
        "",
        "## Reference Truth Ozeti",
        "",
        "- canonical_current_authority_ref = `faz19 stable current truth`",
        "- FAZ16 truth = `runtime_error_count = 0`, `control_pair_breach_in_f0_f12 = false`",
        "- FAZ17 truth = `runtime_error_count = 0`, `authoritative_summary_mismatch_count = 1`, `output_parity_surface_breach_count = 1`, `localized_authorized_downstream_drift_count = 0`, `frontier_candidate_count = 1`",
        "",
        "## WP Sonuclari",
        "",
        "- `WP-1 = PASS`",
        "- `WP-2 = PASS`",
        f"- `WP-3 = {wp3_status}`",
        f"- `WP-4 = {wp4_status}`",
        f"- `WP-5 = {wp5_status}`",
        "- `WP-6 = PASS`",
        "",
        "## Canonical Current Authority Check Ozeti",
        "",
        f"- `control_pair_runtime_error_count = {control_summary.get('control_pair_runtime_error_count')}`",
        f"- `control_pair_authority_match = {bool_text(control_summary.get('control_pair_authority_match'))}`",
        f"- `current_authority_contract_breach = {bool_text(control_summary.get('current_authority_contract_breach'))}`",
        f"- `control_pair_breach_in_f0_f12 = {bool_text(control_summary.get('control_pair_breach_in_f0_f12'))}`",
        "",
        "## RC-G vs RC-M Authoritative Summary Ozeti",
        "",
        f"- `runtime_error_count = {(authoritative_summary or {}).get('runtime_error_count', 0)}`",
        f"- `authoritative_summary_mismatch_count = {(authoritative_summary or {}).get('authoritative_summary_mismatch_count', 0)}`",
        f"- `output_parity_surface_breach_count = {(authoritative_summary or {}).get('output_parity_surface_breach_count', 0)}`",
        f"- `localized_authorized_downstream_drift_count = {(authoritative_summary or {}).get('localized_authorized_downstream_drift_count', 0)}`",
        f"- `frontier_candidate_count = {(authoritative_summary or {}).get('frontier_candidate_count', 0)}`",
        (
            "- yorum = `canonical current authority altinda RC-M authoritative mismatch yeniden uretilemedi; "
            "historical tek-kayitlik breach truth bu authority zemini altinda non-reproducible kaldigi icin WP-5 acilmadi`"
            if wp4_status == "FAIL"
            else "- yorum = `authoritative mismatch yeniden uretildi`"
        ),
        "",
        "## Frontier / Localization Ozeti",
        "",
        (
            f"- `status = {(frontier_replay or {}).get('status')}`"
            if frontier_replay and frontier_replay.get("status")
            else "- `status = AUTHORIZED`"
        ),
        (
            f"- `reason = {(frontier_replay or {}).get('reason')}`"
            if frontier_replay and frontier_replay.get("reason")
            else "- `reason = n/a`"
        ),
        f"- `frontier_count = {(frontier_replay or {}).get('frontier_count', 0)}`",
        f"- `first_divergence_assigned_count = {(frontier_replay or {}).get('first_divergence_assigned_count', 0)}`",
        f"- `primary_reason_assigned_count = {(frontier_replay or {}).get('primary_reason_assigned_count', 0)}`",
        f"- `root_cause_class_assigned_count = {(frontier_replay or {}).get('root_cause_class_assigned_count', 0)}`",
        f"- `unexplained_count = {(frontier_replay or {}).get('unexplained_count', 0)}`",
        f"- `rc_j_vs_rc_m_runtime_error_count = {(frontier_replay or {}).get('rc_j_vs_rc_m_runtime_error_count', 0)}`",
    ]
    if frontier_row and frontier_row != {}:
        lines.extend(
            [
                f"- `frontier_record_id = {frontier_row.get('frontier_record_id')}`",
                f"- `frontier_family = {frontier_row.get('frontier_family')}`",
                f"- `frontier_ordinal = {frontier_row.get('frontier_ordinal')}`",
                f"- `first_divergence_stage_f = {frontier_row.get('first_divergence_stage_f')}`",
                f"- `first_divergence_stage_o = {frontier_row.get('first_divergence_stage_o')}`",
                f"- `primary_reason = {frontier_row.get('primary_reason')}`",
                f"- `root_cause_class = {frontier_row.get('root_cause_class')}`",
            ]
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
    parser = argparse.ArgumentParser(description="Build FAZ22 final report pack.")
    parser.add_argument("--control-summary-json", type=Path, required=True)
    parser.add_argument("--authoritative-summary-json", type=Path)
    parser.add_argument("--frontier-replay-json", type=Path)
    parser.add_argument("--steering-output-md", type=Path, required=True)
    parser.add_argument("--reconciliation-output-json", type=Path, required=True)
    parser.add_argument("--reconciliation-output-md", type=Path, required=True)
    parser.add_argument("--next-work-output-json", type=Path, required=True)
    parser.add_argument("--next-work-output-md", type=Path, required=True)
    parser.add_argument("--report-output-md", type=Path, required=True)
    args = parser.parse_args()

    control_summary = load_json(args.control_summary_json)
    authoritative_summary = load_json(args.authoritative_summary_json) if args.authoritative_summary_json else None
    frontier_replay = load_json(args.frontier_replay_json) if args.frontier_replay_json else None
    decision, next_work, wp3_status, wp4_status, wp5_status = decide(
        control_summary=control_summary,
        authoritative_summary=authoritative_summary,
        frontier_replay=frontier_replay,
    )

    reconciliation = render_reconciliation(
        decision=decision,
        next_work=next_work,
        wp3_status=wp3_status,
        wp4_status=wp4_status,
        wp5_status=wp5_status,
        control_summary=control_summary,
        authoritative_summary=authoritative_summary,
        frontier_replay=frontier_replay,
    )
    write_json(args.reconciliation_output_json, reconciliation)
    write_json(args.next_work_output_json, {"next_official_work": next_work, "official_decision": decision})

    args.steering_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.steering_output_md.write_text(
        render_steering(
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
        "# FAZ22 Output Parity Surface Reconciliation\n\n"
        + "\n".join(f"- {key} = `{value}`" for key, value in reconciliation.items())
        + "\n",
        encoding="utf-8",
    )
    args.next_work_output_md.write_text(
        "# FAZ22 Next Official Work\n\n"
        f"- official_decision = `{decision}`\n"
        f"- next_official_work = `{next_work}`\n",
        encoding="utf-8",
    )
    args.report_output_md.write_text(
        render_report(
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
    return 0 if decision == "PASS - RC-M Output Parity Surface Breach Localized Under Canonical Current Authority" else 1


if __name__ == "__main__":
    raise SystemExit(main())
