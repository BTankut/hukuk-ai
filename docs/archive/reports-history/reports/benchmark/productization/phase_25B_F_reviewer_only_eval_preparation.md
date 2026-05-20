# Phase25B-F Reviewer-Only Evaluation Preparation

Generated: 2026-05-08

## Decision

Selected decision:

```text
prepared_not_opened
```

Execution status:

```text
blocked_controls_missing
```

This document prepares a controlled reviewer-only evaluation design. It does not open reviewer-only eval, broad internal eval, serving candidate, or productization.

## Reviewer Roles

| role | scope | allowed action |
| --- | --- | --- |
| legal reviewer | source identity, current-law status, legal family, article/span correctness | approve, reject, or request more review on legal/source evidence |
| scorer reviewer | benchmark rubric, expected answer criteria, accepted source family | approve scorer expectation or mark rubric mismatch |
| product reviewer | user-facing risk, confidence UX, manual-review suitability | decide whether residual class can be shown in controlled review context |
| privacy reviewer | PII/redaction/retention review | approve reviewer packet exposure or require redaction |
| release owner | gatekeeper | open/close reviewer queue only after controls are complete |

## Allowed Query Types

- questions from the existing 100-question benchmark set
- residual-class examples from Phase25A/Phase25B matrices
- synthetic legal-information prompts without real personal data
- source-identity and citation-fidelity prompts
- judicial corpus dry-run metadata questions after package inventory exists

## Forbidden Query Types

- real client/legal matter facts
- personal data, party names, addresses, national IDs, phone numbers, emails, or sensitive case facts
- prompts intended to obtain attorney-client advice
- public endpoint testing
- production traffic
- prompt sets that require live yargı retrieval or merging judicial corpus into mevzuat
- prompts intended to tune model behavior or start fine-tuning

## Trace Access Rules

- reviewers receive redacted row-level packets, not raw full traces by default
- raw trace access requires privacy owner approval and a specific review need
- trace excerpts must omit secrets, private tokens, unnecessary host/process details, and unrelated prompt content
- large trace files must not be committed
- reviewer packets must reference compact evidence summaries where possible

## Manual Review Form

Required fields:

```text
review_id
reviewer_name
reviewer_role
qid_or_case_id
query_text_redacted
expected_source_family
expected_source_identifier
expected_article_or_span
actual_source_family
actual_source_identifier
actual_article_or_span
evidence_path
raw_sha256_if_applicable
decision
confidence
requires_runtime_fix
requires_policy_fix
requires_source_review
requires_scorer_review
privacy_issue_detected
notes
reviewed_at
```

## Review Decision Enums

```text
accepted
accepted_with_review_note
conditional_acceptance
needs_more_review
rejected
source_not_acquired
rubric_mismatch
blocks_productization
blocks_internal_eval
blocks_serving_candidate
privacy_redaction_required
```

## Privacy Notice

Reviewer-only eval is for system quality and product-risk assessment. Reviewers must not submit real client facts or personal data. Any accidental PII must be flagged, redacted from shared artifacts, and routed to the privacy owner. Raw traces and raw legal/source packages remain controlled artifacts and are not general review material.

## Data Retention

| artifact | retention rule |
| --- | --- |
| redacted reviewer packet | keep until residual decision is closed, then archive with product governance docs |
| raw traces | keep outside git in controlled local/artifact storage with retention owner |
| raw source files | keep in controlled source-acquisition storage with hash manifest |
| review CSV/forms | commit only if redacted and product-governance relevant |
| accidental PII | delete or redact per privacy owner instruction |

## Rollback / Escalation Path

If reviewer-only eval detects unsafe behavior:

1. Stop the reviewer queue.
2. Mark affected residual class as blocked.
3. Notify release owner, legal owner, and privacy owner if applicable.
4. Preserve compact evidence summary; do not commit raw traces.
5. Confirm live `8000` remains unchanged.
6. Reopen only after owner decision and updated controls.

## Activation Gates

Reviewer-only eval cannot open until:

- access-control policy exists
- trace exposure and privacy redaction process is operational
- manual review form is materialized as a CSV/template
- reviewer list and roles are approved
- rollback/escalation owner is named
- release owner explicitly approves opening

## Current State

Reviewer-only eval plan: `prepared`.

Reviewer-only eval runtime status: `not_opened`.

Broad internal eval: `closed`.

Serving candidate: `closed`.

Productization: `closed`.
