# Phase 22F-S6 Split Decision Report

## Commit List

Phase 22F-S6 commits pushed to `origin/bt/hukuk-ai-100-benchmark-hardening`:

- `cbcde5f` - `Audit TEB-04 KDV teblig source pool`
- `83f28de` - `Design TEB-04 KDV teblig remediation`
- `b82cf01` - `Audit MULGA-05 current-law exception policy`
- Decision report commit: this report is committed with subject `Report Phase 22F-S6 split remediation decision`

Reference S5 run:

- `reports/benchmark/runs/20260502T1126Z_phase22F_S5_targeted_fix_smoke_final2`
- Runtime candidate API: `http://127.0.0.1:8018/v1`
- Live `8000` untouched: `true`
- Model: `hukuk-ai-poc`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`

## TEB-04 Decision

Audit result:

- The correct KDV General Application Communique source exists in the catalog and Milvus as source key `19631`.
- It is absent from runtime `retrieval_top_k=24`, source identity `top_scores`, and the S5 `rerank_list`.
- Raw dense search first finds `19631` at rank `130`, outside the runtime candidate horizon.
- `metadata_lookup_hit=false`.
- Current selected source is the wrong tebliğ: `ELEKTRONİK TEBLİGAT SİSTEMİ GENEL TEBLİĞİ (SIRA NO: 1)` / `24345 m.1`.

Root cause:

- `kdv_source_present_not_retrieved`
- `kdv_source_title_alias_missing`
- `teblig_identifier_disambiguation_gap`
- `body_materialization_gap`

Decision:

- Open Option B: narrow TEB source identity fix.
- Include a limited Option C component: source identity/rerank must be able to promote a recovered `19631` candidate.
- Do not open source acquisition for this item, because the source exists.

Next phase:

- `Phase 22F-S7 TEB source identity fix`

Allowed future scope:

- KDV title aliases for source `19631`
- KDV signal extraction: `kdv`, `katma deger vergisi`, `tevkifat`, `iade`, `konsolide`, `ana teblig`
- Metadata-guided candidate injection for `19631`
- Targeted TEB smoke only

## MULGA-05 Decision

Audit result:

- Historical/repealed selected source is present: `6570 m.GEC1/f.0`.
- Current-law basis is present in evidence: `TBK m.344/f.0`.
- Contract currently claims `KANUN / TBK m.344`.
- Scorer expects primary family `MULGA`.
- Final answer text mentions historical/repealed status but does not explicitly mention `TBK m.344`.
- `relation_query_detected=false`; no explicit relation-chain metadata explains the primary historical/current-law split.

Root cause:

- `contract_policy_needs_current_law_exception`
- `answer_surface_wrong_role`
- `identifier_surface_mismatch`
- `scorer_rubric_mismatch`

Decision:

- Open Option C: `Phase 22F-S7M MULGA current-law contract policy`.
- The contract/scorer must support dual-role currentness answers instead of treating the current-law basis as a replacement primary source.

Expected policy shape:

- Primary historical source family: `MULGA`
- Primary historical source identifier: expired/historical rent-cap source
- Current-law basis family: `KANUN`
- Current-law basis identifier: `TBK m.344`
- Final answer must explicitly state that the temporary 25 percent cap ended and that 2026 current-law analysis uses `TBK m.344`.

## Recommended Next Phase

Run two separated remediation tracks before any full benchmark:

1. `Phase 22F-S7 TEB source identity fix`
2. `Phase 22F-S7M MULGA current-law contract policy`

Required gates before S5-E/S5-F or any full shadow benchmark:

- TEB targeted smoke recovers `TEB-04` source identity without drifting adjacent TEB rows to `19631`.
- MULGA targeted smoke preserves primary historical `MULGA` identity while exposing current-law basis separately.
- No QID-specific runtime branches.
- No answer-key driven runtime logic.
- No broad top-k change.

## Gate Decisions

Productization:

- Closed.
- Reason: S5-D failed and residuals are source identity plus contract/scorer policy issues.

Fine-tuning:

- Closed.
- Reason: remaining failures are not model capability issues.

Cutover:

- No cutover.
- Keep live `8000` baseline untouched.
- Do not switch live/base collection.

Full benchmark:

- Do not run S5-E/S5-F or a full shadow benchmark until S7 and S7M targeted gates pass.
