# Reviewer-Only Eval Form Template

Generated: 2026-05-09

## Scope

This template is for controlled reviewer-only evaluation preparation. It does not open reviewer-only eval, broad internal eval, serving candidate, productization, or public access.

CSV template: `reports/benchmark/productization/reviewer_only_eval_form_template.csv`

## Fields

| field | meaning |
| --- | --- |
| `review_id` | Stable review row id. |
| `reviewer_name` | Named reviewer completing the row. |
| `query` | Redacted user/query text under review. |
| `answer` | Redacted answer text or answer summary. |
| `selected_sources` | Sources selected or cited by the system. |
| `source_roles` | Roles such as `primary_rule`, `current_law_basis`, `historical_source`, `precedent`, or `interpretation`. |
| `legal_correctness` | Reviewer assessment of legal correctness. |
| `citation_correctness` | Reviewer assessment of citation/source correctness. |
| `current_law_validity` | Reviewer assessment of current-law/effective-state correctness. |
| `missing_context` | Missing source, facts, caveat, temporal status, or review context. |
| `risk_level` | `low`, `medium`, `high`, or `critical`. |
| `decision` | One of the decision enums below. |
| `required_action` | Required follow-up action before closure. |
| `notes` | Reviewer notes. |

## Decision Enums

```text
accept
accept_with_caveat
needs_source_review
needs_legal_review
reject_wrong_source
reject_hallucination
reject_current_law_risk
manual_escalation
```

## Usage Rules

- Use redacted prompts and answers by default.
- Do not include real client facts or personal data.
- Do not attach raw traces unless privacy owner and release owner approve.
- A row marked `reject_wrong_source`, `reject_hallucination`, or `reject_current_law_risk` blocks productization and serving-candidate use until resolved.
- `accept` does not open internal eval or productization by itself.
- Reviewer-only eval can open only after explicit owner approval and access-control completion.

## Current State

Template status: `prepared`.

Reviewer-only eval status: `not_opened`.

Internal eval status: `closed`.

Serving candidate status: `closed`.

Productization status: `closed`.
