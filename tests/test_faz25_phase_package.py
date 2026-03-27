from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz25"))

from build_phase_package import build_phase_payload  # type: ignore


def _reference_texts() -> dict[str, str]:
    return {
        "faz6": "PASS - Repair Surface Localized and RC-G Accepted\n",
        "faz7": "NO-GO - Release Controls\nallowed diff surface: release-controls / observability / session / auth / API versioning / eval client\n",
        "faz21": "PASS - Current Authority Canonicalized\ncurrent_canonical_authority_adopted = true\nauthoritative comparison order = `current_canonical -> historical_archive`\n",
        "faz24": "PASS - RC-M Discard Archived Under Canonical Current Authority\npost-rc-m steering re-entry under canonical current authority\ncandidate_status = `discard_archived`\n",
        "faz1_5": "must-close release controls remain open\n",
    }


def _source_texts() -> dict[str, str]:
    return {
        "faz1_5_release_matrix": "auth, audit logging, PII, Redis, token accounting, observability, alerting, versioning, keepalive, backup/restore\n",
        "faz7_release_matrix": "\n".join(
            [
                "mandatory auth",
                "immutable audit logging",
                "persisted PII redaction",
                "Redis session persistence",
                "tokenizer-backed accounting",
                "observability / alerting",
                "API versioning",
                "process supervision",
                "backup / restore",
                "one-command release smoke",
            ]
        ),
    }


def test_faz25_payload_pass_path() -> None:
    payload = build_phase_payload(_reference_texts(), _source_texts())
    assert payload["wp_statuses"] == {
        "WP-1": "PASS",
        "WP-2": "PASS",
        "WP-3": "PASS",
        "WP-4": "PASS",
        "WP-5": "PASS",
    }
    assert payload["reconciliation"]["official_decision"] == "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority"
    assert payload["next_contract"]["next_candidate_id"] == "RC-N"
    assert payload["next_contract"]["must_close_release_controls_count"] == 10


def test_faz25_payload_fails_when_reference_pack_breaks() -> None:
    refs = _reference_texts()
    refs["faz24"] = refs["faz24"].replace("candidate_status = `discard_archived`\n", "")
    payload = build_phase_payload(refs, _source_texts())
    assert payload["reference_pack"]["reference_pack_integrity_pass"] is False
    assert payload["wp_statuses"]["WP-1"] == "FAIL"
    assert payload["reconciliation"]["official_decision"] == "FAIL - Post-RC-M Steering Baseline Not Materialized"


def test_faz25_release_controls_exact_set_is_frozen() -> None:
    payload = build_phase_payload(_reference_texts(), _source_texts())
    assert payload["next_contract"]["must_close_release_controls_exact_set"] == [
        "mandatory auth",
        "immutable audit logging",
        "persisted PII redaction",
        "Redis session persistence",
        "tokenizer-backed accounting",
        "observability / alerting",
        "API versioning",
        "process supervision",
        "backup / restore",
        "one-command release smoke",
    ]
