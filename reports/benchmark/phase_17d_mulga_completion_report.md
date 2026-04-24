# Phase 17D MULGA Rubric Completion Report

- date: 2026-04-24
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- scope: MULGA temporal/rubric completion slice only
- pre_run: `reports/benchmark/runs/20260424T_phase17d_mulga_smoke_pre`
- post_run: `reports/benchmark/runs/20260424T_phase17d_mulga_smoke_post_v5`

## Decision

Phase 17D is accepted for the narrow MULGA slice.

The acceptance gate was `MULGA pass >= 2/5`, with no increase in repealed-as-active or unsupported-confident answers. The post run reached `3/5` pass proxy and kept the safety counters at zero.

## Systemic Changes

- Added a historical/current counterpart retrieval lane for historical, repealed, and current-applicability questions. The lane retrieves active-law candidates separately from the primary MULGA family lock, so the answer can discuss current applicability without treating the repealed source as current law.
- Marked counterpart chunks with `historical_current_counterpart` trace metadata and allowed them to fill `current_applicability` and `transition_or_replacement_rule` slots.
- Extended historical-transition query detection for old KHK, old regulation, old bylaw, and old arrangement language.
- Re-applied evidence-slot synthesis after controlled fallback/refusal paths when the answer contract is a historical/repealed mode. This fixes the prior case where controlled temporal answers had slot evidence but did not surface it in the final response.
- Fixed the MULGA temporal audit script so `pass_fail_proxy=PASS` is treated as passable instead of being misclassified as an unresolved rubric gap.

No benchmark question id specific rule was added. The selection change is based on source state, retrieval lane identity, title/query term overlap, and a generic non-academic penalty for university-specific active regulations when the query is not academic.

## Pre/Post Metrics

| Metric | Pre | Post |
| --- | ---: | ---: |
| raw_score_proxy | 18.68 / 50 | 33.35 / 50 |
| average_score_0_10_proxy | 3.74 | 6.67 |
| pass_proxy | 0 / 5 | 3 / 5 |
| minimum_answer_facts_present | 4 / 5 | 5 / 5 |
| runtime rubric_sufficient | 4 / 5 | 5 / 5 |
| evidence_slot_synthesis_count | 0 / 5 | 5 / 5 |
| active_candidate_available_count | 0 | 5 |
| repealed_as_active_count | 0 | 0 |
| unsupported_confident_answer_count | 0 | 0 |
| temporal_validity_miss_count | 0 | 0 |

## Post-Run Row State

- `MULGA-01`: fail, score `6.43`, remaining issue `rubric_slot_gap`.
- `MULGA-02`: pass, score `8.65`, candidate passable.
- `MULGA-03`: pass, score `7.55`, candidate passable.
- `MULGA-04`: pass, score `8.22`, candidate passable.
- `MULGA-05`: fail, score `2.50`, remaining issue `rubric_slot_gap`.

## Evidence Slot Result

Post-run slot synthesis was visible in all 5 MULGA answers.

- `minimum_answer_facts_present_count`: `5/5`
- `evidence_slot_synthesis_count`: `5/5`
- `avg_evidence_required_slot_value_count`: `5.0`
- synthesis reasons: `missing_slots_filled_from_selected_evidence=4`, `slot_values_made_visible_from_selected_evidence=1`

## Residual Risks

- `canonical_missing_required_content_signal` and `canonical_partial_grounding_only` remain `5/5`. The narrow MULGA gate is accepted, but the deterministic scorer still flags partial grounding/must-include gaps.
- `MULGA-01` and `MULGA-05` remain failures. The remaining fix should be a general current-law counterpart concept anchoring improvement, not a row-specific patch. Examples: current norm-chain selection and time-limited current-law regimes such as rent-increase caps/TBK 344 style mappings.
- Latency increased materially because the counterpart lane performs an additional active-law recall pass. The observed smoke run had slow rows, so performance must be addressed before a full 100-row rerun or productization gate.

## Verification

Executed targeted gateway tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "mulga_required_slots or mulga_controlled_refusal or mulga_current_counterpart or answer_slot_synthesis_hint_adds_mulga or historical_year_risk or evidence_slot_synthesis"
```

Result: `8 passed`.

## Persistent Artifacts

- `reports/benchmark/phase_17d_mulga_temporal_audit_pre.csv`
- `reports/benchmark/phase_17d_mulga_temporal_audit_pre.md`
- `reports/benchmark/phase_17d_evidence_slot_audit_pre.csv`
- `reports/benchmark/phase_17d_evidence_slot_audit_pre.md`
- `reports/benchmark/phase_17d_mulga_answer_template_pre.md`
- `reports/benchmark/phase_17d_mulga_temporal_audit_post_v5.csv`
- `reports/benchmark/phase_17d_mulga_temporal_audit_post_v5.md`
- `reports/benchmark/phase_17d_evidence_slot_audit_post_v5.csv`
- `reports/benchmark/phase_17d_evidence_slot_audit_post_v5.md`
- `reports/benchmark/phase_17d_mulga_answer_template_post_v5.md`

