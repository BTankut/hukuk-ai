from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


_FAIL_RESPONSE = (
    "Bu yanıt için seçilen kaynaklarla yeterli doğrulama kuramadım. "
    "Kaynak kapsamı netleştirilmeden güvenilir cevap veremem."
)


@dataclass(slots=True)
class ProductClaimVerificationResult:
    enabled: bool
    verification_status: str
    verification_failures: list[str] = field(default_factory=list)
    claim_to_evidence_map: list[dict[str, Any]] = field(default_factory=list)
    unsupported_claim_count: int = 0
    source_consistency_result: str = "not_evaluated"
    effective_state_result: str = "not_evaluated"
    answer_contract_validity: str = "not_evaluated"
    verification_fail_response: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "verification_status": self.verification_status,
            "verification_failures": self.verification_failures,
            "claim_to_evidence_map": self.claim_to_evidence_map,
            "unsupported_claim_count": self.unsupported_claim_count,
            "source_consistency_result": self.source_consistency_result,
            "effective_state_result": self.effective_state_result,
            "answer_contract_validity": self.answer_contract_validity,
            "verification_fail_response": self.verification_fail_response,
        }


def _evidence_by_id(selected_evidence: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for index, evidence in enumerate(selected_evidence, start=1):
        evidence_id = str(evidence.get("evidence_id") or evidence.get("id") or f"evidence-{index}")
        rows[evidence_id] = evidence
    return rows


def _answer_contract_valid(answer_contract: dict[str, Any]) -> bool:
    answer_text = answer_contract.get("answer_text")
    citations = answer_contract.get("citations")
    return isinstance(answer_text, str) and bool(answer_text.strip()) and isinstance(citations, list)


def _claims_from_contract(answer_contract: dict[str, Any]) -> list[dict[str, Any]]:
    claims = answer_contract.get("claims")
    if isinstance(claims, list):
        return [claim for claim in claims if isinstance(claim, dict)]
    answer_text = str(answer_contract.get("answer_text") or "").strip()
    if not answer_text:
        return []
    return [{"claim_id": "claim-1", "text": answer_text, "evidence_ids": []}]


def evaluate_claim_verification(
    *,
    answer_contract: dict[str, Any],
    selected_evidence: list[dict[str, Any]] | None = None,
    enabled: bool = False,
) -> ProductClaimVerificationResult:
    """Preview product claim verification without repairing sources or answers."""

    if not enabled:
        return ProductClaimVerificationResult(enabled=False, verification_status="disabled")

    evidence_rows = _evidence_by_id(selected_evidence or [])
    claims = _claims_from_contract(answer_contract)
    failures: list[str] = []
    claim_map: list[dict[str, Any]] = []
    unsupported_count = 0
    source_mismatch = False
    effective_state_mismatch = False

    answer_contract_validity = "pass" if _answer_contract_valid(answer_contract) else "fail"
    if answer_contract_validity == "fail":
        failures.append("answer_contract_invalid")

    for index, claim in enumerate(claims, start=1):
        claim_id = str(claim.get("claim_id") or f"claim-{index}")
        evidence_ids = [str(item) for item in claim.get("evidence_ids", []) if item]
        mapped_evidence = [evidence_rows[item] for item in evidence_ids if item in evidence_rows]
        claim_failures: list[str] = []

        if not mapped_evidence:
            unsupported_count += 1
            claim_failures.append("unsupported_claim")

        for evidence in mapped_evidence:
            if claim.get("source_family") and evidence.get("source_family"):
                if str(claim["source_family"]).casefold() != str(evidence["source_family"]).casefold():
                    source_mismatch = True
                    claim_failures.append("source_family_mismatch")
            if claim.get("source_identifier") and evidence.get("source_identifier"):
                if str(claim["source_identifier"]).casefold() != str(evidence["source_identifier"]).casefold():
                    source_mismatch = True
                    claim_failures.append("source_identifier_mismatch")
            if claim.get("effective_state") and evidence.get("effective_state"):
                if str(claim["effective_state"]).casefold() != str(evidence["effective_state"]).casefold():
                    effective_state_mismatch = True
                    claim_failures.append("effective_state_mismatch")

        claim_map.append(
            {
                "claim_id": claim_id,
                "claim_text": str(claim.get("text") or ""),
                "supporting_evidence_ids": evidence_ids,
                "verification_result": "fail" if claim_failures else "pass",
                "failure_reasons": sorted(set(claim_failures)),
            }
        )

    if unsupported_count:
        failures.append("unsupported_claim")
    if source_mismatch:
        failures.append("source_consistency_failed")
    if effective_state_mismatch:
        failures.append("effective_state_failed")

    failures = sorted(set(failures))
    status = "pass" if not failures else "fail"

    return ProductClaimVerificationResult(
        enabled=True,
        verification_status=status,
        verification_failures=failures,
        claim_to_evidence_map=claim_map,
        unsupported_claim_count=unsupported_count,
        source_consistency_result="fail" if source_mismatch else "pass",
        effective_state_result="fail" if effective_state_mismatch else "pass",
        answer_contract_validity=answer_contract_validity,
        verification_fail_response=_FAIL_RESPONSE if failures else None,
    )
