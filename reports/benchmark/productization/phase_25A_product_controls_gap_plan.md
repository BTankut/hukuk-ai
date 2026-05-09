# Phase 25A Product Controls Gap Closure Plan

Generated: 2026-05-08

## Gate Rule

Internal eval may not open unless all of the following are completed and signed off:

- guardrails policy exists and is mapped to runtime enforcement
- verification policy exists and is mapped to runtime enforcement
- trace exposure policy exists
- manual review workflow exists
- rollback plan exists
- residual acceptance matrix is completed

Serving candidate may not open unless runtime enforcement is evidenced or an explicit written waiver exists for each missing control.

Current live state remains benchmark-only: `guardrails=disabled`, `verification=disabled`, `presidio=false`, lane `phase22f_s7_full_shadow`.

## Control Matrix

| control_area | current_status | required_for_internal_eval | required_for_serving_candidate | required_for_productization | implementation_needed | policy_artifact | runtime_artifact | owner | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| guardrails | Policy artifact exists; live health reports disabled | yes | yes | yes | Enable or gate runtime guardrails; define block/downgrade states for hallucinated citations, unsupported evidence, source unavailable, current-law uncertainty | `reports/benchmark/productization/guardrails_policy.md` | Not evidenced; live `guardrails=disabled` | runtime owner + product policy owner | Produce non-live enforcement smoke, then candidate enforcement evidence before any eval opening |
| claim-level verification | Policy artifact exists; live health reports disabled | yes | yes | yes | Claim-to-evidence map, citation consistency, source-family checks, temporal/effective-state checks, unsupported claim detector | `reports/benchmark/productization/verification_policy.md` | Not evidenced; live `verification=disabled` | verification owner | Implement verification contract and fail-closed report before serving-candidate consideration |
| privacy / PII | Policy artifact exists; runtime PII enforcement not evidenced | yes | yes | yes | Query/log redaction, reviewer packet minimization, retention/deletion rules, secrets scan for committed artifacts | `reports/benchmark/productization/privacy_pii_policy.md` | Not evidenced; `PRESIDIO_ENABLED=false` in observed runtime env | privacy owner + release owner | Define reviewer/export redaction checklist and runtime log-retention owner |
| audit logging | Policy artifact exists; production-grade audit logging not evidenced | yes | yes | yes | Append-only or tamper-evident answer/block records with request id, source keys, model, collection, guardrail/verification result | `reports/benchmark/productization/audit_logging_policy.md` | Not evidenced | platform owner | Create audit-log schema smoke and retention location before reviewer-only eval expansion |
| trace exposure | Policy artifact exists; summary-only practice used; full traces not staged | yes | yes | yes | Enforce no large trace commit, redaction before sharing, secure storage for raw traces, retention window | `reports/benchmark/productization/trace_exposure_policy.md` | Partially evidenced by current commit practice; no automated gate evidenced | release owner | Add release checklist item and optional pre-commit/CI size guard for trace files |
| manual review workflow | Workflow artifact exists; residual acceptance matrix now created | yes | yes | yes | Queue states, reviewer roles, evidence path/SHA fields, legal/scorer owner decisions, closure criteria | `reports/benchmark/productization/manual_review_workflow.md`; `reports/benchmark/productization/phase_25A_residual_acceptance_matrix.md` | Human packets exist; runtime routing to manual review not evidenced | legal owner + scorer owner + release owner | Convert reviewer-only residual rows into controlled queue before any internal evaluator access |
| confidence / abstention UX | Policy artifact exists; live enforcement not evidenced | yes | yes | yes | Confidence bands, insufficient evidence UX, manual-review-required UX, current-law uncertainty messaging, source unavailable messaging | `reports/benchmark/productization/confidence_ux_policy.md` | Not evidenced as live enforced | product UX owner + runtime owner | Build answer-contract examples and verifier-gated abstention smoke |
| rollback / incident runbook | Runbook exists; no rehearsal evidenced in Phase25A | yes | yes | yes | Rehearsed rollback path, captured baseline config, owner escalation, post-rollback smoke | `reports/benchmark/productization/rollback_incident_runbook.md` | Documentation only | release owner + infra owner | Run non-live rollback rehearsal packet before candidate switch request |
| access control | Not yet a dedicated artifact in productization folder | yes | yes | yes | Named reviewer access, endpoint/network restriction, API-key policy, role separation for reviewer-only eval | Missing dedicated `access_control_policy.md` | Not evidenced | security/release owner | Create access-control policy and bind reviewer-only eval to named users only |
| monitoring / metrics | Not yet a dedicated artifact in productization folder | yes | yes | yes | Runtime metrics for contract invalid, unsupported confident answer, hallucinated citation, source-family mismatch, latency, errors, manual-review rate | Missing dedicated `monitoring_metrics_policy.md` | Not evidenced | platform owner | Define metrics schema and dashboard acceptance criteria before serving candidate |

## Minimum Closure Sequence

1. Keep live `8000` frozen as benchmark-only.
2. Complete access-control and monitoring/metrics policy artifacts.
3. Convert residual matrix into reviewer-only queue decisions.
4. Implement non-live guardrail and verification enforcement smokes.
5. Rehearse rollback without changing live routing.
6. Only then request explicit owner decision for reviewer-only internal eval.

## Current Decision

Product controls status: `not_closed`.

Internal eval status: `closed`.

Serving candidate status: `closed`.

Productization status: `closed`.
