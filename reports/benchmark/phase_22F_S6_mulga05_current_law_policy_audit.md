# Phase 22F-S6-C MULGA-05 Current-Law Exception Policy Audit

## Scope

This audit separates runtime source selection from answer-contract and scorer policy for `MULGA-05`. It does not change runtime behavior, live `8000`, prompts, models, retrieval top-k, or scoring.

Reference run:

- `reports/benchmark/runs/20260502T1126Z_phase22F_S5_targeted_fix_smoke_final2`
- API URL: `http://127.0.0.1:8018/v1`
- Model: `hukuk-ai-poc`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Live `8000` untouched: `true`

## Current MULGA-05 Result

`MULGA-05` failed with score `5.45`.

- Selected main document: `GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ`
- Selected main span: `6570 m.GEC1/f.0`
- Selected article: `gec1`
- Supporting spans: `TBK m.344/f.0 | 6570 m.16/f.0 | 6570 m.4/f.0 | 6570 m.15/f.0`
- Claimed family/identifier: `KANUN / TBK m.344`
- Expected family in scorer: `MULGA`
- Failure classes: `missing_required_content_signal | wrong_family | repealed_source_used_as_active | hallucinated_identifier | partial_grounding_only`
- `auto_fail_triggered`: `false`
- `hallucinated_source_penalty`: `0.00`

S5 successfully kept the current-law basis observable in the contract claim, but it did not establish a clean dual-role contract.

## Evidence Findings

Historical source presence:

- `true`
- The selected main source is the historical/repealed `6570` source.
- The selector reason is `legacy_scope_state_binding`.
- The S5 guard is `historical_surface_current_law_basis_exception_guard`.

Current-law basis presence:

- `true`
- The source pool and supporting spans include `TBK m.344/f.0`.
- The answer contract claims `source_family_claimed=KANUN`, `source_identifier_claimed=TBK m.344`, `article_or_section_claimed=madde:344`.

Relation-chain presence:

- `false`
- `relation_query_detected=false`.
- No explicit relation-chain metadata explains the role split between the historical temporary cap surface and the current-law basis.

Question currentness intent:

- `true`
- The question asks why applying the temporary 25 percent rent cap in `2026` is a currentness error.

Final answer surface:

- It mentions the historical/repealed nature of the selected source.
- It gives only a generic warning that current law must be separately verified.
- It does not explicitly surface `TBK m.344`.
- It does not explicitly state that the temporary 25 percent cap has ended and that the 2026 current basis is `TBK m.344`.

## Policy Diagnosis

The current contract collapses two legally distinct roles into one claimed source:

- Primary historical role: the expired or historical temporary rent-cap regime.
- Current-law basis role: `6098` Turkish Code of Obligations / `TBK m.344`.

The scorer still expects the primary family to remain `MULGA`, while S5 lets the contract claim switch to `KANUN / TBK m.344` when a current-law basis is present. That creates:

- `wrong_family`, because the canonical claimed family becomes `KANUN` while expected family is `MULGA`.
- `hallucinated_identifier` in failure classes, because `TBK m.344` is not the selected main historical source even though it exists as a supporting/current-law basis.
- Answer-surface mismatch, because the final answer text does not explicitly expose the current-law basis it claims.

This is not a model/fine-tuning issue. It is a contract and scorer role-model issue.

## Root Cause

Primary root cause:

- `contract_policy_needs_current_law_exception`

Contributing root causes:

- `answer_surface_wrong_role`
- `identifier_surface_mismatch`
- `scorer_rubric_mismatch`

The policy needs to represent dual-source currentness answers. For `MULGA` currentness questions, the answer contract should be able to keep the primary historical source as `MULGA` while separately exposing a verified current-law basis such as `TBK m.344`.

## Safe Action

Open Phase 22F-S7M MULGA current-law contract policy.

The next phase should design and test a dual-role contract shape:

- `primary_historical_source_family=MULGA`
- `primary_historical_identifier=<expired/historical rent cap source>`
- `current_law_basis_family=KANUN`
- `current_law_basis_identifier=TBK m.344`
- final answer must explicitly state the expired cap/current-law distinction

The scorer should then evaluate primary historical identity and current-law basis as separate supported roles instead of treating the current-law basis as a hallucinated replacement for the primary source.

No runtime behavior should be changed in S6. Productization, fine-tuning, and live cutover remain closed.
