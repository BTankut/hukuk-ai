# Phase25L-C Claim-Level Verification Enforcement Design

Generated: 2026-05-10

## Decision

Design only. Do not enable verification on live `8000`.

Recommended product flag:

```text
ENABLE_PRODUCT_CLAIM_VERIFICATION=false
```

Existing `USE_VERIFICATION` and `VerificationEngine` are useful building blocks, but product enforcement needs a stricter answer-contract boundary with explicit claim-to-evidence mapping, source identity checks, and effective-state checks.

## Runtime Position

Proposed insertion point for Phase25M:

```text
selected evidence -> draft answer -> answer contract -> claim verification -> guardrails decision -> response envelope
```

Verification must run before product guardrails so guardrails can consume verification failures and select the correct fallback mode.

## Required Checks

| Check | Requirement | Failure result |
|---|---|---|
| claim_to_evidence mapping | every legal claim maps to at least one selected evidence span | unsupported_claim |
| citation/source consistency | cited source must exist in selected evidence | citation_source_mismatch |
| source_family consistency | answer family must match selected source family | source_family_mismatch |
| source_identifier consistency | answer source identifier must match selected source identifier/source key | source_identifier_mismatch |
| effective_state consistency | current/historical/repealed statement must match selected source metadata | effective_state_mismatch |
| unsupported claim detector | legal conclusion without evidence is counted and blocked above threshold | unsupported_claim |
| answer contract validation | public answer, citations, selected evidence, and final_mode must be schema-valid | answer_contract_invalid |
| verification fail response | fail response must be deterministic and non-confident | fallback_verification_failed |

## Verification Status Enum

```text
disabled
pass
warn_manual_review
fail_insufficient_evidence
fail_source_consistency
fail_effective_state
fail_answer_contract
error_fail_closed
```

## Trace Fields

```text
verification_status
verification_failures
claim_evidence_map
unsupported_claim_count
source_consistency_result
effective_state_result
answer_contract_validation_result
claim_count
evidence_span_count
selected_source_keys
selected_source_families
selected_source_identifiers
```

## Claim Evidence Map Shape

```json
{
  "claim_id": "claim-001",
  "claim_text": "short normalized claim",
  "claim_type": "definition|condition|procedure|exception|temporal|consequence",
  "supporting_evidence_ids": ["evidence-001"],
  "supporting_source_keys": ["..."],
  "supporting_article_refs": ["..."],
  "verification_result": "pass|warn|fail",
  "failure_reasons": []
}
```

## Source Consistency Rules

The verification module must compare the answer contract against selected evidence using normalized fields:

```text
source_family
source_identifier
source_key
source_title
article_no
clause_no
effective_state
effective_start_date
effective_end_date
```

The module must not repair retrieval, rerank sources, or select a different source. It only verifies the already selected evidence.

## Verification Fail Response

For product routes in a future phase:

```text
Bu soruya güvenilir cevap vermek için seçilen kaynaklarla yanıt arasında yeterli doğrulama kuramadım. Lütfen kaynak kapsamı netleştirildikten sonra tekrar deneyin.
```

The fail response must include no fabricated citation and must set:

```text
final_mode=blocked_verification_failed
manual_review_flag=true
```

## Non-Live Test Route

Phase25M should add a dry-run route only:

```text
POST /internal/product-controls/verification/dry-run
```

The route should accept a prepared answer contract and selected evidence bundle, then return verification trace fields without changing public chat behavior.

## Gate Result

Reviewer-only eval, internal eval, and serving candidate remain blocked until product claim verification exists behind `ENABLE_PRODUCT_CLAIM_VERIFICATION=false`, passes non-live tests, and can fail closed on non-live product-review routes.
