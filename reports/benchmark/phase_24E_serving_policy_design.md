# Phase 24E Serving Policy Design

Generated: 2026-05-03T10:53:00Z

Scope: define the policy boundary between current benchmark-only runtime, possible internal-eval access, serving-candidate, and public serving. This phase is design-only and does not change live `8000`.

## Runtime Class Policy

| Runtime Class | Policy |
|---|---|
| benchmark_only | Current approved state. Live `8000` may be used only for controlled benchmark/reproducibility work. No public use. |
| internal_eval | Limited reviewer access only after Phase 24F approval. No public use. Traces controlled. Residual blockers must be fixed or explicitly accepted. |
| serving_candidate | Requires guardrails, verification, privacy/Presidio policy, audit logs, rollback runbook, manual review workflow, and restricted exposure. Not open now. |
| public_serving | Out of scope. Requires separate approval after serving-candidate evidence and product/legal signoff. |

## Required Policies

| Policy Area | benchmark_only Current State | internal_eval Requirement | serving_candidate Requirement |
|---|---|---|---|
| Guardrails policy | Disabled; acceptable only because benchmark-only and controlled. | Either enabled in non-blocking review mode or explicitly waived with reviewer-only access. | Enabled and validated; failure modes tested. |
| Verification policy | Disabled. | Decision must be documented; verifier may be disabled only if legal reviewers understand limitation. | Verification required or formally replaced by equivalent evidence gate. |
| Presidio/privacy policy | Disabled. | Internal reviewers must not submit personal/sensitive/private client data; privacy disclaimer required. | Privacy/PII handling required before any user-facing access. |
| Audit logging policy | Disabled. | Minimal access log and failure report log required before opening. | Audit logs required with retention and incident process. |
| Trace exposure policy | Benchmark traces are controlled artifacts. | Traces must be stored in restricted repo/run directories; no external sharing without redaction. | Trace redaction, retention, and access controls required. |
| Manual review policy | Residual register exists; no closure yet. | Legal/scorer/corpus review queue must be active; blockers must be fixed or explicitly accepted. | Manual review SLAs, escalation, and acceptance criteria required. |
| Confidence threshold policy | Benchmark scorer checks confidence policy; no user UX policy. | Low-confidence or insufficient evidence answers must be tagged for reviewer attention. | UX must expose uncertainty and block unsupported confident answers. |
| Refusal / insufficient evidence policy | Active via answer contract; benchmark accepts insufficient-grounding answers when honest. | Reviewers may test insufficiency behavior; no pressure to answer without evidence. | Must preserve refusal/insufficient-evidence behavior and avoid unsupported confident answers. |
| Rate limit / abuse policy | Not applicable for local benchmark. | Access list and manual rate limits sufficient for named reviewers. | Formal rate limit, abuse prevention, and API key management required. |
| Rollback policy | E1 rollback command documented for live `8000`. | Rollback command must be revalidated before opening any internal_eval lane. | Automated or operator-run rollback playbook required. |

## Access Policy

| Access Group | benchmark_only | internal_eval | serving_candidate | public_serving |
|---|---|---|---|---|
| Code/operator assistant | allowed | allowed if approved | allowed if approved | not approved |
| Named legal reviewers | not applicable | allowed only after Phase 24F approval | not allowed by default | not approved |
| Internal product users | not applicable | not allowed unless named in approval | restricted only after separate gate | not approved |
| External users/customers | not allowed | not allowed | not allowed | not approved |

## Operational Policy

1. No live `8000` runtime mutation without a backup and rollback command.
2. No model, prompt strategy, broad retrieval/top-k, or QID-specific runtime branch changes in policy-only phases.
3. Internal-eval access, if later approved, must use a named lane and a written runtime provenance artifact.
4. Any internal-eval smoke must use non-private test prompts and must not use the private answer key.
5. Productization requires a new gate after residual closure and policy implementation.

## Decision

Phase 24E serving policy design: complete.

The current runtime remains `benchmark_only`. This policy does not open internal_eval, serving_candidate, public serving, or productization.
