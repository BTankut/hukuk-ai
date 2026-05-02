# Phase 22F-S7M MULGA Current-Law Contract Policy Design

## Objective

Represent `MULGA` currentness answers as dual-role answers:

- primary historical/repealed source remains `MULGA`
- current-law basis is represented separately as supporting `KANUN`

This design targets contract/surface policy only. It must not change source retrieval, global top-k, prompts, model, or live `8000`.

## S6 Starting Point

`MULGA-05` currently has both relevant evidence roles:

- historical source: `6570 m.GEC1/f.0`
- current-law basis: `TBK m.344/f.0`

But the contract collapses the roles:

- contract claims `KANUN / TBK m.344`
- scorer expects primary family `MULGA`
- final answer mentions historical/repealed status but does not explicitly surface `TBK m.344`

Root causes:

- `contract_policy_needs_current_law_exception`
- `answer_surface_wrong_role`
- `identifier_surface_mismatch`
- `scorer_rubric_mismatch`

## Design

For `MULGA` currentness questions with a verified current-law support span, the answer contract should expose a dual-role surface:

- `source_family_claimed=MULGA`
- `source_identifier_claimed=<historical source identifier>`
- `current_law_basis_family=KANUN`
- `current_law_basis_identifier=TBK m.344` or the detected current-law support identifier
- `effective_state_claimed=repealed` or historical, never active for the historical source

The final answer must explicitly state the current-law basis when the question is about currentness. For the rent-cap pattern, the surface must say that the temporary 25 percent cap is not an automatically applicable 2026 general rule and that current analysis must be made under `TBK m.344`.

This is a role separation rule, not a `MULGA-05` branch.

## Implementation Surface

Primary files:

- `api-gateway/src/rag/answer_synthesis.py`
- `api-gateway/src/rag/answer_slots.py` if slot naming is needed
- `api-gateway/src/rag/evidence_bundle.py` if current-law support extraction is needed
- runtime trace fields as needed

Avoid:

- `source_identity.py`
- `retrieval_orchestration.py`
- `article_span_selection.py`

## Diagnostics

Add or surface trace fields:

- `mulga_dual_role_contract_applied`
- `mulga_primary_historical_source_key`
- `mulga_current_law_basis_source_key`
- `mulga_current_law_basis_identifier`
- `mulga_historical_claim_identifier`
- `mulga_current_law_statement_required`
- `mulga_current_law_statement_present`

## Guardrails

The implementation must not:

- claim a repealed source is active
- overwrite current-law basis with historical source
- use benchmark answer key
- branch on `MULGA-05`
- change retrieval behavior

## Targeted Gate

Run `MULGA-01` through `MULGA-05`.

Acceptance:

- `MULGA >= 4/5`.
- `MULGA-05` improves or passes.
- `repealed_as_active_count = 0`.
- `unsupported_confident_answer = 0`.
- `answer_contract_invalid = 0`.
- source-key collision and binding collision remain `0`.

Productization, fine-tuning, live cutover, source acquisition, and corpus materialization remain closed.
