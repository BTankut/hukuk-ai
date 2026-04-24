# Phase 17E CB_GENELGE Recovery Slice Completion Report

- date: 2026-04-24
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- scope: CB_GENELGE recovery slice only
- pre_run: `reports/benchmark/runs/20260424T_phase17e_cbgenelge_smoke_pre`
- post_run: `reports/benchmark/runs/20260424T_phase17e_cbgenelge_smoke_post5`
- template_check_run: `reports/benchmark/runs/20260424T_phase17e_cbgenelge_template_check_post6`

## Decision

Phase 17E is accepted for the narrow CB_GENELGE slice.

The acceptance gate was `CB_GENELGE pass >= 2/4`, CBG-04 blocker closure or explicit corpus blocker separation, and a reduction in CB_GENELGE corpus materialization gaps. The post run reached `2/4` pass proxy, reduced `corpus_materialization_required_count` from `1` to `0`, and kept safety counters at zero.

Productization and fine-tuning gates remain closed pending Phase 17F full benchmark rerun.

## Systemic Changes

- Preserved slash-numbered source identifiers such as `2025/3`; these are no longer collapsed to a year-only alias.
- Added CB_GENELGE topic scoring so metadata selection can prefer a specific circular topic over generic year matches.
- Promoted strong metadata-first source locks into retrieval/source-selection focus keys.
- Added an official-source supplement path for source key `3`, family `cb_genelge`, identifier `2025/3`, based on the Resmi Gazete PDF at `https://www.resmigazete.gov.tr/eskiler/2025/03/20250306-5.pdf`.
- Materialized official supplement text as document-level body evidence with `official_source_supplement` lane metadata.
- Narrowed CB_GENELGE body-gap unsuppression to the official supplement lane only.
- Added a CB_GENELGE document-level answer template that extracts numbered clauses from the selected official text.
- Prevented active CB_* sources from being forced into legacy/mülga fallback merely because the query contrasts old and current arrangements.

No benchmark question id specific rule was added. The recovery is source-family, metadata identity, official-source supplement, and selected-evidence based.

## Pre/Post Metrics

| Metric | Pre | Post |
| --- | ---: | ---: |
| raw_score_proxy | 17.65 / 40 | 23.50 / 40 |
| average_score_0_10_proxy | 4.41 | 5.88 |
| pass_proxy | 1 / 4 | 2 / 4 |
| minimum_answer_facts_present | 0 / 4 | 2 / 4 |
| evidence_slot_synthesis_count | 1 / 4 | 3 / 4 |
| canonical_span_materialized_count | 3 / 4 | 4 / 4 |
| corpus_materialization_required_count | 1 | 0 |
| insufficient_canonical_span_evidence_count | 1 | 0 |
| answer_suppressed_due_to_evidence_gap_count | 4 | 2 |
| hallucinated_source_count | 3 | 2 |
| unsupported_confident_answer_count | 0 | 0 |
| repealed_as_active_count | 0 | 0 |
| source_key_v2_collision_detected_count | 0 | 0 |

## Row Outcomes

- `CBG-01`: still fails. The system selected `14 m.0` instead of the expected `2024/7` Tasarruf Tedbirleri source. It remains safely suppressed as an acquisition/index/metadata backlog item rather than producing a confident unsupported answer.
- `CBG-02`: still fails. The system selected `14 m.0` instead of the expected `2019/12` Bilgi ve İletişim Güvenliği source. It remains safely suppressed as an acquisition/index/metadata backlog item.
- `CBG-03`: fixed through official source supplement materialization for `2025/3` Mobbing Genelgesi. The template check score is `9.10`, with no hallucinated source and no evidence-gap suppression.
- `CBG-04`: fixed. The active `2025/3` source is retained as active/current, while the old `2011/2` Genelge repeal clause is kept separate. The template check score is `8.35`.

## Template Check

The post5 full 4-row smoke is the acceptance run. The post6 template check is a targeted verification for the two rows affected by the official supplement/template path.

| Metric | Template Check |
| --- | ---: |
| total | 2 |
| raw_score_proxy | 17.45 / 20 |
| average_score_0_10_proxy | 8.72 |
| pass_proxy | 2 / 2 |
| hallucinated_source_count | 0 |
| unsupported_confident_answer_count | 0 |
| answer_suppressed_due_to_evidence_gap_count | 0 |

## Safety

- `unsupported_confident_answer_count` stayed `0`.
- `repealed_as_active_count` stayed `0`.
- `source_key_v2_collision_detected_count` stayed `0`.
- `CBG-01` and `CBG-02` remain suppressed instead of wrong-confident, which is the correct safety posture until the missing official source rows are acquired/materialized.

## Verification

Executed targeted gateway checks:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/answer_contract_v2.py api-gateway/src/rag/source_supplements.py
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "metadata_lookup_parser_preserves_slash_numbered_genelge_identifier or metadata_first_selector_uses_genelge_topic_anchor_over_generic_year_match or article_selector_uses_metadata_topic_lock_over_slash_year_fragment or source_supplement_materializes_cb_genelge_document_body or cb_genelge_document_level_template"
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_answer_contract_v2.py -k "active_cb_genelge_legacy_contrast_does_not_use_mulga_fallback or cb_genelge_document_level_body_support_is_not_suppressed_as_span_gap or legacy_suppressed_answer_keeps_temporal_answer_mode or repair_preserves_explicit_legacy_khk_family_when_query_is_bound_to_khk or repair_uses_mapped_evidence_family"
```

Results:

- chat router targeted tests: `5 passed`
- answer contract targeted tests: `5 passed`

## Persistent Artifacts

- `reports/benchmark/phase_17e_cbgenelge_evidence_slot_audit_pre.csv`
- `reports/benchmark/phase_17e_cbgenelge_evidence_slot_audit_pre.md`
- `reports/benchmark/phase_17e_cbgenelge_evidence_slot_audit_post.csv`
- `reports/benchmark/phase_17e_cbgenelge_evidence_slot_audit_post.md`
- `reports/benchmark/runs/20260424T_phase17e_cbgenelge_smoke_pre/score_summary.md`
- `reports/benchmark/runs/20260424T_phase17e_cbgenelge_smoke_post5/score_summary.md`
- `reports/benchmark/runs/20260424T_phase17e_cbgenelge_template_check_post6/score_summary.md`

## Remaining Backlog

- Acquire/materialize the correct official source for `CBG-01` (`2024/7` Tasarruf Tedbirleri) or repair catalog metadata so it can be selected.
- Acquire/materialize the correct official source for `CBG-02` (`2019/12` Bilgi ve İletişim Güvenliği) or repair catalog metadata so it can be selected.
- Run Phase 17F full benchmark rerun before any productization or fine-tuning gate decision.
