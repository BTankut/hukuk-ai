# Phase 25A Internal Eval Readiness Reframe

Generated: 2026-05-08

## Reframe

Internal eval readiness is no longer determined by benchmark score alone. The relevant decision is whether residual legal risk, trace exposure, access control, guardrails, verification, manual review, and rollback are controlled enough for a defined evaluator population.

Current baseline is useful for benchmark-only comparison, but it is not sufficient for broad internal eval.

## Decision Options

| option | name | requirement | current fit |
| --- | --- | --- | --- |
| A | Internal eval ready with restrictions | Residual matrix accepted for internal eval, manual review workflow exists, trace exposure controlled, access restricted, rollback documented | Not met |
| B | Limited reviewer-only eval | Legal/product reviewers inspect selected rows under manual-review workflow, with no serving candidate and no broad evaluator pool | Future possible after access-control and reviewer queue artifacts |
| C | Not ready | Controls or residual acceptance are insufficient | Selected for Phase25A |

## Phase25A Decision

Decision: `Option C - not ready`.

Rationale:

- Live runtime reports `guardrails=disabled`.
- Live runtime reports `verification=disabled`.
- Privacy/PII runtime enforcement is not evidenced.
- Audit logging runtime enforcement is not evidenced.
- Access-control and monitoring/metrics policy artifacts are still missing.
- Residual matrix blocks serving and productization for all rows.
- Highest-risk residual classes still include `wrong_document`, `hallucinated_identifier`, `wrong_family`, and `current_law_uncertainty`.
- Phase24HY stopped runtime recovery and did not produce a serving candidate.

## Reviewer-Only Path

Reviewer-only eval can be prepared as a later, explicitly approved workstream if all conditions below are met:

- reviewer identities and access limits are documented
- review packet excludes raw traces unless necessary and redacted
- residual rows are mapped to review questions and owner decisions
- no production endpoint, public endpoint, or serving-candidate traffic is involved
- guardrail/verification disabled state is clearly visible in every review packet
- rollback and incident paths are documented even for reviewer-only experiments

Until those conditions are met, reviewer-only eval remains `not_opened`.

## Decisions

Productization decision: `closed`.

Serving candidate decision: `closed`.

Broad internal eval decision: `closed`.

Reviewer-only eval decision: `not_opened; prepare only after access-control and manual-review queue artifacts`.

Fine-tuning decision: `closed`; fine-tuning is not an acceptable substitute for missing controls or residual acceptance.
