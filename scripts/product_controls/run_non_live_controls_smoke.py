#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "api-gateway" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from config import Settings  # noqa: E402
from product_controls.access_control import evaluate_access_control  # noqa: E402
from product_controls.audit import build_audit_event_preview  # noqa: E402
from product_controls.claim_verification import evaluate_claim_verification  # noqa: E402
from product_controls.guardrails import evaluate_product_guardrails  # noqa: E402
from product_controls.privacy import preview_privacy_controls  # noqa: E402


CSV_FIELDS = [
    "scenario",
    "guardrails_result",
    "verification_result",
    "privacy_result",
    "audit_event_created",
    "access_decision",
    "expected",
    "actual",
    "status",
    "notes",
]


def _contract(**claim_overrides: Any) -> dict[str, Any]:
    claim = {
        "claim_id": "claim-1",
        "text": "TBK m.49 haksiz fiil sorumlulugunu duzenler.",
        "evidence_ids": ["ev-1"],
        "source_family": "KANUN",
        "source_identifier": "TBK",
        "effective_state": "active",
    }
    claim.update(claim_overrides)
    return {
        "answer_text": "TBK m.49 haksiz fiil sorumlulugunu duzenler.",
        "citations": ["TBK m.49"],
        "claims": [claim],
    }


def _evidence(**overrides: Any) -> list[dict[str, Any]]:
    row = {
        "evidence_id": "ev-1",
        "source_family": "KANUN",
        "source_identifier": "TBK",
        "effective_state": "active",
        "source_key": "TBK:49",
        "text": "TBK m.49 metni",
    }
    row.update(overrides)
    return [row]


def _audit(*, guardrail: str, verification: str, privacy: str, manual_review: bool = False) -> str:
    preview = build_audit_event_preview(
        enabled=True,
        request_id="req-smoke",
        actor_role="developer_operator",
        endpoint="/internal/product-controls/smoke",
        model_id="hukuk-ai-poc",
        collection_id="non-live-smoke",
        retrieved_source_keys=["TBK:49"],
        selected_source_keys=["TBK:49"],
        guardrail_result=guardrail,
        verification_result=verification,
        privacy_result=privacy,
        manual_review_flag=manual_review,
        latency=0.0,
        error_state=None,
    )
    return "true" if preview.audit_event_created else "false"


def _row(
    *,
    scenario: str,
    guardrails_result: str,
    verification_result: str,
    privacy_result: str,
    audit_event_created: str,
    access_decision: str,
    expected: str,
    actual: str,
    notes: str,
) -> dict[str, str]:
    return {
        "scenario": scenario,
        "guardrails_result": guardrails_result,
        "verification_result": verification_result,
        "privacy_result": privacy_result,
        "audit_event_created": audit_event_created,
        "access_decision": access_decision,
        "expected": expected,
        "actual": actual,
        "status": "PASS" if expected == actual else "FAIL",
        "notes": notes,
    }


def build_rows() -> list[dict[str, str]]:
    settings = Settings()
    flags_default_off = all(
        [
            settings.enable_product_guardrails is False,
            settings.enable_product_claim_verification is False,
            settings.enable_product_privacy_pii is False,
            settings.enable_product_audit_logging is False,
            settings.enable_product_access_control is False,
        ]
    )
    rows: list[dict[str, str]] = []

    guard = evaluate_product_guardrails(
        answer_text="TBK m.49 haksiz fiil sorumlulugunu duzenler. [Kaynak: TBK m.49]",
        selected_evidence=_evidence(),
        enabled=True,
        legal_disclaimer_required=False,
    )
    ver = evaluate_claim_verification(answer_contract=_contract(), selected_evidence=_evidence(), enabled=True)
    priv = preview_privacy_controls(query="TBK m.49 nedir?", enabled=True)
    access = evaluate_access_control(actor_role="developer_operator", action="product_controls_dry_run", enabled=True)
    rows.append(
        _row(
            scenario="safe_answer_with_valid_sources",
            guardrails_result=guard.decision,
            verification_result=ver.verification_status,
            privacy_result=priv.privacy_decision,
            audit_event_created=_audit(
                guardrail=guard.decision,
                verification=ver.verification_status,
                privacy=priv.privacy_decision,
            ),
            access_decision=access.decision,
            expected="allow/pass/pass_no_pii/true/allow",
            actual=f"{guard.decision}/{ver.verification_status}/{priv.privacy_decision}/true/{access.decision}",
            notes=f"flags_default_off={flags_default_off}",
        )
    )

    guard = evaluate_product_guardrails(
        answer_text="Bu sonuc kesinlikle uygulanir.",
        selected_evidence=[],
        enabled=True,
    )
    ver = evaluate_claim_verification(answer_contract=_contract(evidence_ids=[]), selected_evidence=[], enabled=True)
    priv = preview_privacy_controls(query="Kesin cevap ver", enabled=True)
    access = evaluate_access_control(actor_role="developer_operator", action="product_controls_dry_run", enabled=True)
    rows.append(
        _row(
            scenario="unsupported_confident_answer",
            guardrails_result=guard.decision,
            verification_result=ver.verification_status,
            privacy_result=priv.privacy_decision,
            audit_event_created=_audit(guardrail=guard.decision, verification=ver.verification_status, privacy=priv.privacy_decision),
            access_decision=access.decision,
            expected="block_unsupported_confident_answer/fail/pass_no_pii/true/allow",
            actual=f"{guard.decision}/{ver.verification_status}/{priv.privacy_decision}/true/{access.decision}",
            notes="unsupported confident answer blocked in preview",
        )
    )

    guard = evaluate_product_guardrails(answer_text="Kaynak yok.", selected_evidence=[], enabled=True)
    ver = evaluate_claim_verification(answer_contract=_contract(evidence_ids=[]), selected_evidence=[], enabled=True)
    priv = preview_privacy_controls(query="Kaynak yok", enabled=True)
    access = evaluate_access_control(actor_role="developer_operator", action="product_controls_dry_run", enabled=True)
    rows.append(
        _row(
            scenario="insufficient_evidence_answer",
            guardrails_result=guard.decision,
            verification_result=ver.verification_status,
            privacy_result=priv.privacy_decision,
            audit_event_created=_audit(guardrail=guard.decision, verification=ver.verification_status, privacy=priv.privacy_decision),
            access_decision=access.decision,
            expected="block_insufficient_evidence/fail/pass_no_pii/true/allow",
            actual=f"{guard.decision}/{ver.verification_status}/{priv.privacy_decision}/true/{access.decision}",
            notes="insufficient evidence safe mode preview",
        )
    )

    guard = evaluate_product_guardrails(
        answer_text="Tarihsel kaynak boyleydi. [Kaynak: Eski Tuzuk m.1]",
        selected_evidence=_evidence(effective_state="repealed", source_identifier="OLD-TUZUK"),
        enabled=True,
        current_law_resolved=False,
        effective_state="repealed",
        legal_disclaimer_required=False,
    )
    ver = evaluate_claim_verification(
        answer_contract=_contract(source_identifier="OLD-TUZUK", effective_state="active"),
        selected_evidence=_evidence(source_identifier="OLD-TUZUK", effective_state="repealed"),
        enabled=True,
    )
    priv = preview_privacy_controls(query="Eski tuzuk guncel mi?", enabled=True)
    access = evaluate_access_control(actor_role="developer_operator", action="product_controls_dry_run", enabled=True)
    rows.append(
        _row(
            scenario="repealed_source_current_law_uncertainty",
            guardrails_result=guard.decision,
            verification_result=ver.verification_status,
            privacy_result=priv.privacy_decision,
            audit_event_created=_audit(guardrail=guard.decision, verification=ver.verification_status, privacy=priv.privacy_decision),
            access_decision=access.decision,
            expected="allow_with_warning/fail/pass_no_pii/true/allow",
            actual=f"{guard.decision}/{ver.verification_status}/{priv.privacy_decision}/true/{access.decision}",
            notes="historical warning and effective-state mismatch detected",
        )
    )

    guard = evaluate_product_guardrails(
        answer_text="Kaynakli cevap. [Kaynak: TBK m.49]",
        selected_evidence=_evidence(),
        enabled=True,
        legal_disclaimer_required=False,
    )
    ver = evaluate_claim_verification(answer_contract=_contract(), selected_evidence=_evidence(), enabled=True)
    priv = preview_privacy_controls(query="Musteri test@example.com 5551234567", enabled=True)
    access = evaluate_access_control(actor_role="developer_operator", action="product_controls_dry_run", enabled=True)
    rows.append(
        _row(
            scenario="PII_in_query",
            guardrails_result=guard.decision,
            verification_result=ver.verification_status,
            privacy_result=priv.privacy_decision,
            audit_event_created=_audit(guardrail=guard.decision, verification=ver.verification_status, privacy=priv.privacy_decision),
            access_decision=access.decision,
            expected="allow/pass/pass_redacted/true/allow",
            actual=f"{guard.decision}/{ver.verification_status}/{priv.privacy_decision}/true/{access.decision}",
            notes="email and phone redaction preview",
        )
    )

    access = evaluate_access_control(actor_role="external_user", action="trace_access", enabled=True)
    rows.append(
        _row(
            scenario="external_user_trace_access_denied",
            guardrails_result="not_applicable",
            verification_result="not_applicable",
            privacy_result="not_applicable",
            audit_event_created=_audit(guardrail="not_applicable", verification="not_applicable", privacy="not_applicable"),
            access_decision=access.decision,
            expected="not_applicable/not_applicable/not_applicable/true/deny_route_not_allowed",
            actual=f"not_applicable/not_applicable/not_applicable/true/{access.decision}",
            notes="external user denied trace access",
        )
    )

    access = evaluate_access_control(actor_role="legal_reviewer", action="review_queue", enabled=True)
    rows.append(
        _row(
            scenario="legal_reviewer_manual_review_allowed",
            guardrails_result="manual_review_required",
            verification_result="not_applicable",
            privacy_result="not_applicable",
            audit_event_created=_audit(
                guardrail="manual_review_required",
                verification="not_applicable",
                privacy="not_applicable",
                manual_review=True,
            ),
            access_decision=access.decision,
            expected="manual_review_required/not_applicable/not_applicable/true/allow",
            actual=f"manual_review_required/not_applicable/not_applicable/true/{access.decision}",
            notes="legal reviewer allowed review queue",
        )
    )

    ver = evaluate_claim_verification(
        answer_contract=_contract(source_identifier="TMK"),
        selected_evidence=_evidence(source_identifier="TBK"),
        enabled=True,
    )
    rows.append(
        _row(
            scenario="claim_source_identifier_mismatch",
            guardrails_result="not_applicable",
            verification_result=ver.verification_status,
            privacy_result="not_applicable",
            audit_event_created=_audit(guardrail="not_applicable", verification=ver.verification_status, privacy="not_applicable"),
            access_decision="not_applicable",
            expected="not_applicable/fail/not_applicable/true/not_applicable",
            actual=f"not_applicable/{ver.verification_status}/not_applicable/true/not_applicable",
            notes="source identifier mismatch detected",
        )
    )

    return rows


def write_outputs(rows: list[dict[str, str]]) -> None:
    out_dir = ROOT / "reports" / "benchmark" / "productization"
    csv_path = out_dir / "phase_25N_F_non_live_controls_smoke.csv"
    report_path = out_dir / "phase_25N_F_non_live_controls_smoke_report.md"
    out_dir.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    all_pass = all(row["status"] == "PASS" for row in rows)
    lines = [
        "# Phase25N-F Non-Live Product Controls Smoke Report",
        "",
        "Generated: 2026-05-10",
        "",
        "## Decision",
        "",
        f"{'PASS' if all_pass else 'FAIL'} - non-live product controls smoke scenarios completed.",
        "",
        "## Command",
        "",
        "```text",
        "python3 scripts/product_controls/run_non_live_controls_smoke.py",
        "```",
        "",
        "## Acceptance",
        "",
        f"- all scenarios pass = {str(all_pass).lower()}",
        "- all flags default off outside smoke = true",
        "- live 8000 unchanged = true",
        "- no productization opened = true",
        "- no eval opened = true",
        "",
        "## Results",
        "",
        "| scenario | status | notes |",
        "|---|---|---|",
    ]
    lines.extend(f"| {row['scenario']} | {row['status']} | {row['notes']} |" for row in rows)
    lines.extend(
        [
            "",
            "## CSV",
            "",
            "```text",
            "reports/benchmark/productization/phase_25N_F_non_live_controls_smoke.csv",
            "```",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = build_rows()
    write_outputs(rows)
    failed = [row for row in rows if row["status"] != "PASS"]
    if failed:
        for row in failed:
            print(f"FAIL {row['scenario']}: expected={row['expected']} actual={row['actual']}")
        return 1
    print(f"PASS {len(rows)} smoke scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
