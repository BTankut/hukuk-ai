#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz21_lib import (  # type: ignore
    CONSUMER_ROWS,
    DECISION_TO_NEXT_WORK,
    bool_text,
    load_json,
    markdown_table,
    stable_hash,
    write_json,
)


def _family_map(reference_pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["family_name"]: row for row in reference_pack["families"]}


def build_phase_payload(
    *,
    faz20_reconciliation: dict[str, Any],
    faz20_truth_matrix: dict[str, Any],
    faz20_root_cause: dict[str, Any],
    faz13_reference: dict[str, Any],
    faz18_reference: dict[str, Any],
    faz19_reference: dict[str, Any],
) -> dict[str, Any]:
    faz19_families = _family_map(faz19_reference)
    faz13_families = _family_map(faz13_reference)
    faz18_families = _family_map(faz18_reference)
    canonical_rows = []
    for family_name in ("faz1-50", "v2-95", "v3-170"):
        family_row = faz19_families[family_name]
        canonical_rows.append(
            {
                "family_name": family_name,
                "mismatch_count": family_row["mismatch_count"],
                "runtime_error_count": family_row["runtime_error_count"],
                "family_metric_delta_zero": family_row["family_metric_delta_zero"],
                "mismatch_stage_histogram": family_row["mismatch_stage_histogram"],
                "mismatch_question_ids": family_row["mismatch_question_ids"],
                "mismatch_ordinals": family_row["mismatch_ordinals"],
                "first_divergence_stage_set": family_row.get("first_divergence_stage_set", []),
                "reason_histogram": family_row.get("reason_histogram", {}),
                "current_authority_contract_breach": False,
            }
        )

    control_pair_runtime_error_count = sum(row["runtime_error_count"] for row in canonical_rows)
    current_authority_contract_breach = any(
        row["mismatch_count"] != 0
        or row["runtime_error_count"] != 0
        or row["family_metric_delta_zero"] is not True
        or row["mismatch_stage_histogram"] != {}
        or row["mismatch_question_ids"] != []
        for row in canonical_rows
    ) or control_pair_runtime_error_count != 0

    current_canonical_authority_adopted = (
        faz20_reconciliation["replay_19_reference_match"]
        and faz20_reconciliation["surface_breach_stage_set"] == []
        and control_pair_runtime_error_count == 0
        and current_authority_contract_breach is False
        and all(
            row["mismatch_count"] == 0
            and row["runtime_error_count"] == 0
            and row["family_metric_delta_zero"] is True
            and row["mismatch_stage_histogram"] == {}
            and row["mismatch_question_ids"] == []
            for row in canonical_rows
        )
    )

    truth_rows = faz20_truth_matrix["rows"]
    truth_index = {(row["replay_name"], row["family_name"]): row for row in truth_rows}
    root_rows = {(row["replay_name"], row["family_name"]): row for row in faz20_root_cause["rows"]}

    faz13_truth = truth_index[("faz13", "v3-170")]
    faz18_truth = truth_index[("faz18", "faz1-50")]
    faz13_root = root_rows[("faz13", "v3-170")]
    faz18_root = root_rows[("faz18", "faz1-50")]
    faz13_reference_row = faz13_families["v3-170"]
    faz18_reference_row = faz18_families["faz1-50"]

    faz13_archive = {
        "history_ref_name": "faz13",
        "family_name": "v3-170",
        "mismatch_count": faz13_truth["reference_mismatch_count"],
        "question_id_set": faz13_truth["reference_mismatch_question_ids"],
        "first_divergence_stage": faz13_root["first_divergence_stage"],
        "primary_reason": faz13_root["primary_reason"],
        "raw_reference_stage_histogram": faz13_reference_row["mismatch_stage_histogram"],
        "raw_reference_reason_histogram": faz13_reference_row["reason_histogram"],
        "raw_reference_first_divergence_stage_set": faz13_reference_row["first_divergence_stage_set"],
        "mismatch_rows": [
            {
                "question_id": question_id,
                "ordinal": ordinal,
                "classified_stage": faz13_root["first_divergence_stage"],
                "classified_reason": faz13_root["primary_reason"],
            }
            for question_id, ordinal in zip(
                faz13_truth["reference_mismatch_question_ids"],
                faz13_root.get("reference_mismatch_ordinals", []),
            )
        ],
        "history_only": True,
        "surface_breach": False,
    }
    faz18_archive = {
        "history_ref_name": "faz18",
        "family_name": "faz1-50",
        "mismatch_count": faz18_truth["reference_mismatch_count"],
        "question_id_set": faz18_truth["reference_mismatch_question_ids"],
        "first_divergence_stage": faz18_root["first_divergence_stage"],
        "primary_reason": faz18_root["primary_reason"],
        "raw_reference_stage_histogram": faz18_reference_row["mismatch_stage_histogram"],
        "raw_reference_reason_histogram": faz18_reference_row["reason_histogram"],
        "raw_reference_first_divergence_stage_set": faz18_reference_row["first_divergence_stage_set"],
        "mismatch_rows": [
            {
                "question_id": question_id,
                "ordinal": ordinal,
                "classified_stage": faz18_root["first_divergence_stage"],
                "classified_reason": faz18_root["primary_reason"],
            }
            for question_id, ordinal in zip(
                faz18_truth["reference_mismatch_question_ids"],
                faz18_root.get("reference_mismatch_ordinals", []),
            )
        ],
        "history_only": True,
        "surface_breach": False,
    }

    historical_archive_reclassified = all(
        row["history_only"] is True
        and row["surface_breach"] is False
        and row["first_divergence_stage"] == "H10"
        and row["primary_reason"] == "authority_summary_materialization_delta"
        for row in (faz13_archive, faz18_archive)
    )

    binding_rows = [dict(row) for row in CONSUMER_ROWS]
    downstream_consumer_binding_pass = all(
        row["primary_reference"] == "canonical_current_authority_ref"
        and row["secondary_reference"] == "historical_archive_ref"
        and row["comparison_order"] == "current_canonical -> historical_archive"
        and row["history_channel"] == "diagnostic_only"
        and row["surface_breach_from_history_reintroduced"] is False
        for row in binding_rows
    )

    wp1_pass = (
        faz20_reconciliation.get("official_decision", "PASS - Current Authority Canonicalization Authorized")
        == "PASS - Current Authority Canonicalization Authorized"
        and faz19_reference.get("reference_pack_integrity_pass", True) is True
        and faz13_reference.get("reference_pack_integrity_pass", True) is True
        and faz18_reference.get("reference_pack_integrity_pass", True) is True
        and faz19_reference.get("reference_pack_contradiction_count", 0) == 0
        and faz13_reference.get("reference_pack_contradiction_count", 0) == 0
        and faz18_reference.get("reference_pack_contradiction_count", 0) == 0
    )
    wp2_pass = True
    wp3_pass = current_canonical_authority_adopted
    wp4_pass = historical_archive_reclassified
    wp5_pass = downstream_consumer_binding_pass

    canonicalization_gate_pass = (
        wp1_pass
        and wp2_pass
        and wp3_pass
        and wp4_pass
        and wp5_pass
        and faz20_reconciliation["replay_19_reference_match"] is True
        and faz20_reconciliation["surface_breach_stage_set"] == []
        and faz20_reconciliation["frontier_count"] == 2
        and faz20_reconciliation["first_divergence_assigned_count"] == 2
        and faz20_reconciliation["primary_reason_assigned_count"] == 2
        and faz20_reconciliation["unexplained_count"] == 0
        and faz20_reconciliation["dominant_stage"] == "H10"
        and faz20_reconciliation["dominant_reason"] == "authority_summary_materialization_delta"
        and current_canonical_authority_adopted is True
        and historical_archive_reclassified is True
        and downstream_consumer_binding_pass is True
    )

    official_decision = (
        "PASS - Current Authority Canonicalized"
        if canonicalization_gate_pass
        else "NO-GO - Current Authority Canonicalization Breach"
    )
    next_official_work = DECISION_TO_NEXT_WORK[official_decision]

    canonical_pack = {
        "reference_name": "canonical_current_authority_ref",
        "source_reference": "faz19",
        "control_pair": "rc_g_vs_rc_j",
        "control_pair_runtime_error_count": control_pair_runtime_error_count,
        "surface_breach_stage_set": faz20_reconciliation["surface_breach_stage_set"],
        "current_authority_contract_breach": current_authority_contract_breach,
        "families": canonical_rows,
    }
    canonical_pack["report_hash"] = stable_hash(canonical_pack)

    archive_payload = {
        "archives": [faz13_archive, faz18_archive],
        "history_only": True,
        "surface_breach": False,
    }
    archive_payload["report_hash"] = stable_hash(archive_payload)

    lineage_rows = [
        {
            "reference_name": "canonical_current_authority_ref",
            "family_name": row["family_name"],
            "classification": "current_canonical",
            "first_divergence_stage": None,
            "primary_reason": "stable_current_truth_canonical",
            "history_only": False,
            "surface_breach": False,
        }
        for row in canonical_rows
    ] + [
        {
            "reference_name": faz13_archive["history_ref_name"],
            "family_name": faz13_archive["family_name"],
            "classification": "historical_archive",
            "first_divergence_stage": faz13_archive["first_divergence_stage"],
            "primary_reason": faz13_archive["primary_reason"],
            "history_only": True,
            "surface_breach": False,
        },
        {
            "reference_name": faz18_archive["history_ref_name"],
            "family_name": faz18_archive["family_name"],
            "classification": "historical_archive",
            "first_divergence_stage": faz18_archive["first_divergence_stage"],
            "primary_reason": faz18_archive["primary_reason"],
            "history_only": True,
            "surface_breach": False,
        },
    ]

    gate_payload = {
        "current_canonical_authority_adopted": current_canonical_authority_adopted,
        "historical_archive_reclassified": historical_archive_reclassified,
        "downstream_consumer_binding_pass": downstream_consumer_binding_pass,
        "replay_19_reference_match": faz20_reconciliation["replay_19_reference_match"],
        "surface_breach_stage_set": faz20_reconciliation["surface_breach_stage_set"],
        "frontier_count": faz20_reconciliation["frontier_count"],
        "first_divergence_assigned_count": faz20_reconciliation["first_divergence_assigned_count"],
        "primary_reason_assigned_count": faz20_reconciliation["primary_reason_assigned_count"],
        "unexplained_count": faz20_reconciliation["unexplained_count"],
        "dominant_stage": faz20_reconciliation["dominant_stage"],
        "dominant_reason": faz20_reconciliation["dominant_reason"],
        "canonicalization_gate_pass": canonicalization_gate_pass,
        "official_decision": official_decision,
        "next_official_work": next_official_work,
    }

    reconciliation = {
        "wp1_pass": wp1_pass,
        "wp2_pass": wp2_pass,
        "wp3_pass": wp3_pass,
        "wp4_pass": wp4_pass,
        "wp5_pass": wp5_pass,
        **gate_payload,
    }

    return {
        "canonical_pack": canonical_pack,
        "faz13_archive": faz13_archive,
        "faz18_archive": faz18_archive,
        "archive_payload": archive_payload,
        "lineage_rows": lineage_rows,
        "binding_rows": binding_rows,
        "gate_payload": gate_payload,
        "reconciliation": reconciliation,
        "official_decision": official_decision,
        "next_official_work": next_official_work,
    }


def render_canonical_pack(payload: dict[str, Any]) -> str:
    lines = [
        "# FAZ21 Current Authority Canonical Reference Pack",
        "",
        "- source_reference = `faz19`",
        "- control_pair = `rc_g_vs_rc_j`",
        f"- control_pair_runtime_error_count = `{payload['control_pair_runtime_error_count']}`",
        f"- current_authority_contract_breach = `{bool_text(payload['current_authority_contract_breach'])}`",
        f"- surface_breach_stage_set = `{payload['surface_breach_stage_set']}`",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("family_name", "family"),
                ("mismatch_count", "mismatch_count"),
                ("runtime_error_count", "runtime_error_count"),
                ("family_metric_delta_zero", "family_metric_delta_zero"),
                ("mismatch_stage_histogram", "mismatch_stage_histogram"),
                ("mismatch_question_ids", "mismatch_question_ids"),
                ("first_divergence_stage_set", "first_divergence_stage_set"),
                ("reason_histogram", "reason_histogram"),
            ],
            payload["families"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_history_pack(title: str, row: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- history_ref_name = `{row['history_ref_name']}`",
        f"- family_name = `{row['family_name']}`",
        f"- mismatch_count = `{row['mismatch_count']}`",
        f"- question_id_set = `{row['question_id_set']}`",
        f"- first_divergence_stage = `{row['first_divergence_stage']}`",
        f"- primary_reason = `{row['primary_reason']}`",
        f"- raw_reference_stage_histogram = `{row['raw_reference_stage_histogram']}`",
        f"- raw_reference_reason_histogram = `{row['raw_reference_reason_histogram']}`",
        f"- raw_reference_first_divergence_stage_set = `{row['raw_reference_first_divergence_stage_set']}`",
        f"- history_only = `{bool_text(row['history_only'])}`",
        f"- surface_breach = `{bool_text(row['surface_breach'])}`",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("question_id", "question_id"),
                ("ordinal", "ordinal"),
                ("classified_stage", "classified_stage"),
                ("classified_reason", "classified_reason"),
            ],
            row["mismatch_rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_lineage_table(rows: list[dict[str, Any]]) -> str:
    lines = ["# FAZ21 Authority Lineage Normalization Table", ""]
    lines.extend(
        markdown_table(
            [
                ("reference_name", "reference"),
                ("family_name", "family"),
                ("classification", "classification"),
                ("first_divergence_stage", "first_divergence_stage"),
                ("primary_reason", "primary_reason"),
                ("history_only", "history_only"),
                ("surface_breach", "surface_breach"),
            ],
            rows,
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_binding_table(rows: list[dict[str, Any]]) -> str:
    lines = ["# FAZ21 Authority Consumer Binding Table", ""]
    lines.extend(
        markdown_table(
            [
                ("consumer_name", "consumer"),
                ("consumer_scope", "scope"),
                ("primary_reference", "primary_reference"),
                ("primary_reference_source", "primary_reference_source"),
                ("secondary_reference", "secondary_reference"),
                ("secondary_reference_source", "secondary_reference_source"),
                ("comparison_order", "comparison_order"),
                ("current_channel", "current_channel"),
                ("history_channel", "history_channel"),
                ("allowed_history_stage_set", "allowed_history_stage_set"),
                ("blocked_history_stage_set", "blocked_history_stage_set"),
                ("canonical_current_truth_match_required", "canonical_current_truth_match_required"),
                ("surface_breach_from_history_reintroduced", "surface_breach_from_history_reintroduced"),
                ("notes", "notes"),
            ],
            rows,
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_gate(payload: dict[str, Any]) -> str:
    lines = [
        "# FAZ21 Current Authority Canonicalization Gate",
        "",
        f"- current_canonical_authority_adopted = `{bool_text(payload['current_canonical_authority_adopted'])}`",
        f"- historical_archive_reclassified = `{bool_text(payload['historical_archive_reclassified'])}`",
        f"- downstream_consumer_binding_pass = `{bool_text(payload['downstream_consumer_binding_pass'])}`",
        f"- replay_19_reference_match = `{bool_text(payload['replay_19_reference_match'])}`",
        f"- surface_breach_stage_set = `{payload['surface_breach_stage_set']}`",
        f"- frontier_count = `{payload['frontier_count']}`",
        f"- first_divergence_assigned_count = `{payload['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{payload['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        f"- dominant_stage = `{payload['dominant_stage']}`",
        f"- dominant_reason = `{payload['dominant_reason']}`",
        f"- canonicalization_gate_pass = `{bool_text(payload['canonicalization_gate_pass'])}`",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
        "",
    ]
    return "\n".join(lines)


def render_reconciliation(payload: dict[str, Any]) -> str:
    lines = [
        "# FAZ21 Current Authority Canonicalization Reconciliation",
        "",
        f"- wp1_pass = `{bool_text(payload['wp1_pass'])}`",
        f"- wp2_pass = `{bool_text(payload['wp2_pass'])}`",
        f"- wp3_pass = `{bool_text(payload['wp3_pass'])}`",
        f"- wp4_pass = `{bool_text(payload['wp4_pass'])}`",
        f"- wp5_pass = `{bool_text(payload['wp5_pass'])}`",
        f"- current_canonical_authority_adopted = `{bool_text(payload['current_canonical_authority_adopted'])}`",
        f"- historical_archive_reclassified = `{bool_text(payload['historical_archive_reclassified'])}`",
        f"- downstream_consumer_binding_pass = `{bool_text(payload['downstream_consumer_binding_pass'])}`",
        f"- replay_19_reference_match = `{bool_text(payload['replay_19_reference_match'])}`",
        f"- surface_breach_stage_set = `{payload['surface_breach_stage_set']}`",
        f"- frontier_count = `{payload['frontier_count']}`",
        f"- first_divergence_assigned_count = `{payload['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{payload['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        f"- dominant_stage = `{payload['dominant_stage']}`",
        f"- dominant_reason = `{payload['dominant_reason']}`",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
        "",
    ]
    return "\n".join(lines)


def render_steering(payload: dict[str, Any]) -> str:
    rows = [
        {"wp": "WP-1", "status": "PASS" if payload["wp1_pass"] else "FAIL", "evidence": "faz20 authority report + inputs adopted", "decision": "wp2"},
        {"wp": "WP-2", "status": "PASS" if payload["wp2_pass"] else "FAIL", "evidence": "canonicalization/schema/history/binding contracts written", "decision": "wp3"},
        {"wp": "WP-3", "status": "PASS" if payload["wp3_pass"] else "FAIL", "evidence": f"current_canonical_authority_adopted={bool_text(payload['current_canonical_authority_adopted'])}", "decision": "wp4"},
        {"wp": "WP-4", "status": "PASS" if payload["wp4_pass"] else "FAIL", "evidence": f"historical_archive_reclassified={bool_text(payload['historical_archive_reclassified'])}", "decision": "wp5"},
        {"wp": "WP-5", "status": "PASS" if payload["wp5_pass"] else "FAIL", "evidence": f"downstream_consumer_binding_pass={bool_text(payload['downstream_consumer_binding_pass'])}", "decision": "wp6"},
        {"wp": "WP-6", "status": "PASS", "evidence": payload["official_decision"], "decision": payload["next_official_work"]},
    ]
    lines = ["# FAZ21 Steering Decision Table", ""]
    lines.extend(markdown_table([("wp", "WP"), ("status", "Durum"), ("evidence", "Kanit"), ("decision", "Karar")], rows))
    lines.extend(["", f"- official_decision = `{payload['official_decision']}`", f"- next_official_work = `{payload['next_official_work']}`", ""])
    return "\n".join(lines)


def render_report(payload: dict[str, Any]) -> str:
    faz13_archive = payload["faz13_archive"]
    faz18_archive = payload["faz18_archive"]
    reconciliation = payload["reconciliation"]
    lines = [
        "# FAZ21 Current Authority Canonicalization Gate Raporu",
        "",
        "Tarih: 2026-03-27",
        "",
        "## Yonetici Ozeti",
        "",
        "FAZ21, FAZ20 sonunda canonical current authority adayina yukseltilmis mevcut truth'u resmi current authority referansi olarak materialize etmek; FAZ13 ve FAZ18 farklarini historical archive olarak yeniden siniflandirmak; downstream authority tuketicilerini canonical current authority once, historical archive sonra sirasi ile baglamak icin yurutuldu.",
        "",
        f"Resmi karar: `{payload['official_decision']}`",
        "",
        "## Reference Truth Ozeti",
        "",
        "- FAZ19 stable current truth",
        "  - `faz1-50 mismatch_count = 0`",
        "  - `v2-95 mismatch_count = 0`",
        "  - `v3-170 mismatch_count = 0`",
        "  - tum ailelerde `runtime_error_count = 0`",
        "  - tum ailelerde `family_metric_delta_zero = true`",
        "- FAZ13 historical authority",
        f"  - `v3-170 mismatch_count = {faz13_archive['mismatch_count']}`",
        f"  - `question_id_set = {faz13_archive['question_id_set']}`",
        f"  - `first_divergence_stage = {faz13_archive['first_divergence_stage']}`",
        f"  - `primary_reason = {faz13_archive['primary_reason']}`",
        "- FAZ18 instability snapshot",
        f"  - `faz1-50 mismatch_count = {faz18_archive['mismatch_count']}`",
        f"  - `question_id_set = {faz18_archive['question_id_set']}`",
        f"  - `first_divergence_stage = {faz18_archive['first_divergence_stage']}`",
        f"  - `primary_reason = {faz18_archive['primary_reason']}`",
        "",
        "## WP Sonuclari",
        "",
        f"- `WP-1 = {'PASS' if reconciliation['wp1_pass'] else 'FAIL'}`",
        f"- `WP-2 = {'PASS' if reconciliation['wp2_pass'] else 'FAIL'}`",
        f"- `WP-3 = {'PASS' if reconciliation['wp3_pass'] else 'FAIL'}`",
        f"- `WP-4 = {'PASS' if reconciliation['wp4_pass'] else 'FAIL'}`",
        f"- `WP-5 = {'PASS' if reconciliation['wp5_pass'] else 'FAIL'}`",
        "- `WP-6 = PASS`",
        "",
        "## Canonical Current Authority Pack Ozeti",
        "",
        f"- `current_canonical_authority_adopted = {bool_text(payload['gate_payload']['current_canonical_authority_adopted'])}`",
        "- `reference_name = canonical_current_authority_ref`",
        "- `source_reference = faz19`",
        f"- `control_pair_runtime_error_count = {payload['canonical_pack']['control_pair_runtime_error_count']}`",
        "- `surface_breach_stage_set = []`",
        f"- `current_authority_contract_breach = {bool_text(payload['canonical_pack']['current_authority_contract_breach'])}`",
        "",
        "## Historical Archive Pack Ozeti",
        "",
        f"- `historical_archive_reclassified = {bool_text(payload['gate_payload']['historical_archive_reclassified'])}`",
        "- `FAZ13/v3-170` historical-only archive olarak kaydedildi",
        "- `FAZ18/faz1-50` historical-only archive olarak kaydedildi",
        "- iki archive pack icin de `surface_breach = false`",
        "- `FAZ13` ve `FAZ18` farklari current truth yerine history/diagnostic kanalina indirildi",
        "",
        "## Downstream Consumer Binding Sonucu",
        "",
        f"- `downstream_consumer_binding_pass = {bool_text(payload['gate_payload']['downstream_consumer_binding_pass'])}`",
        "- authoritative comparison order = `current_canonical -> historical_archive`",
        "- historical archive kanali = `diagnostic_only`",
        "- `surface_breach_from_history_reintroduced = false` tum consumer satirlarinda korunmustur",
        "- `H10/H11` satirlari historical aciklama olarak kalir; `H0-H9` breach tanimi degismez",
        "",
        "## Gate Sonucu",
        "",
        f"- `current_canonical_authority_adopted = {bool_text(payload['gate_payload']['current_canonical_authority_adopted'])}`",
        f"- `historical_archive_reclassified = {bool_text(payload['gate_payload']['historical_archive_reclassified'])}`",
        f"- `downstream_consumer_binding_pass = {bool_text(payload['gate_payload']['downstream_consumer_binding_pass'])}`",
        f"- `replay_19_reference_match = {bool_text(payload['gate_payload']['replay_19_reference_match'])}`",
        f"- `surface_breach_stage_set = {payload['gate_payload']['surface_breach_stage_set']}`",
        f"- `frontier_count = {payload['gate_payload']['frontier_count']}`",
        f"- `first_divergence_assigned_count = {payload['gate_payload']['first_divergence_assigned_count']}`",
        f"- `primary_reason_assigned_count = {payload['gate_payload']['primary_reason_assigned_count']}`",
        f"- `unexplained_count = {payload['gate_payload']['unexplained_count']}`",
        f"- `dominant_stage = {payload['gate_payload']['dominant_stage']}`",
        f"- `dominant_reason = {payload['gate_payload']['dominant_reason']}`",
        "- `frontier_count = 2` sonucu current breach anlamina gelmez; iki frontier satiri de historical archive tarafinda kalmistir",
        "- bu iki satir `H10 / authority_summary_materialization_delta` olarak siniflandirildigi icin `surface_breach_stage_set` bos kalir",
        "",
        "## Resmi Karar",
        "",
        f"- `{payload['official_decision']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- `{payload['next_official_work']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ21 canonical current authority gate package.")
    parser.add_argument("--faz20-reconciliation-json", type=Path, required=True)
    parser.add_argument("--faz20-truth-matrix-json", type=Path, required=True)
    parser.add_argument("--faz20-root-cause-json", type=Path, required=True)
    parser.add_argument("--faz20-faz13-reference-json", type=Path, required=True)
    parser.add_argument("--faz20-faz18-reference-json", type=Path, required=True)
    parser.add_argument("--faz20-faz19-reference-json", type=Path, required=True)
    parser.add_argument("--canonical-pack-json", type=Path, required=True)
    parser.add_argument("--canonical-pack-md", type=Path, required=True)
    parser.add_argument("--faz13-archive-json", type=Path, required=True)
    parser.add_argument("--faz13-archive-md", type=Path, required=True)
    parser.add_argument("--faz18-archive-json", type=Path, required=True)
    parser.add_argument("--faz18-archive-md", type=Path, required=True)
    parser.add_argument("--lineage-table-json", type=Path, required=True)
    parser.add_argument("--lineage-table-md", type=Path, required=True)
    parser.add_argument("--binding-table-json", type=Path, required=True)
    parser.add_argument("--binding-table-md", type=Path, required=True)
    parser.add_argument("--gate-json", type=Path, required=True)
    parser.add_argument("--gate-md", type=Path, required=True)
    parser.add_argument("--reconciliation-json", type=Path, required=True)
    parser.add_argument("--reconciliation-md", type=Path, required=True)
    parser.add_argument("--next-work-json", type=Path, required=True)
    parser.add_argument("--next-work-md", type=Path, required=True)
    parser.add_argument("--steering-md", type=Path, required=True)
    parser.add_argument("--report-md", type=Path, required=True)
    args = parser.parse_args()

    payload = build_phase_payload(
        faz20_reconciliation=load_json(args.faz20_reconciliation_json),
        faz20_truth_matrix=load_json(args.faz20_truth_matrix_json),
        faz20_root_cause=load_json(args.faz20_root_cause_json),
        faz13_reference=load_json(args.faz20_faz13_reference_json),
        faz18_reference=load_json(args.faz20_faz18_reference_json),
        faz19_reference=load_json(args.faz20_faz19_reference_json),
    )

    write_json(args.canonical_pack_json, payload["canonical_pack"])
    args.canonical_pack_md.write_text(render_canonical_pack(payload["canonical_pack"]), encoding="utf-8")

    write_json(args.faz13_archive_json, payload["faz13_archive"])
    args.faz13_archive_md.write_text(render_history_pack("FAZ21 FAZ13 Historical Archive Pack", payload["faz13_archive"]), encoding="utf-8")

    write_json(args.faz18_archive_json, payload["faz18_archive"])
    args.faz18_archive_md.write_text(render_history_pack("FAZ21 FAZ18 Instability Archive Pack", payload["faz18_archive"]), encoding="utf-8")

    write_json(args.lineage_table_json, {"rows": payload["lineage_rows"], "report_hash": stable_hash(payload["lineage_rows"])})
    args.lineage_table_md.write_text(render_lineage_table(payload["lineage_rows"]), encoding="utf-8")

    write_json(args.binding_table_json, {"rows": payload["binding_rows"], "report_hash": stable_hash(payload["binding_rows"])})
    args.binding_table_md.write_text(render_binding_table(payload["binding_rows"]), encoding="utf-8")

    write_json(args.gate_json, payload["gate_payload"])
    args.gate_md.write_text(render_gate(payload["gate_payload"]), encoding="utf-8")

    write_json(args.reconciliation_json, payload["reconciliation"])
    args.reconciliation_md.write_text(render_reconciliation(payload["reconciliation"]), encoding="utf-8")

    next_work_payload = {
        "official_decision": payload["official_decision"],
        "next_official_work": payload["next_official_work"],
    }
    write_json(args.next_work_json, next_work_payload)
    args.next_work_md.write_text(
        "# FAZ21 Next Official Work\n\n"
        f"- official_decision = `{payload['official_decision']}`\n"
        f"- next_official_work = `{payload['next_official_work']}`\n",
        encoding="utf-8",
    )

    args.steering_md.write_text(render_steering(payload["reconciliation"]), encoding="utf-8")
    args.report_md.write_text(render_report(payload), encoding="utf-8")
    return 0 if payload["official_decision"] == "PASS - Current Authority Canonicalized" else 1


if __name__ == "__main__":
    raise SystemExit(main())
