# Phase 17B Article-Zero Materialization Report

- execution_brief: `reports/benchmark/hukuk_ai_phase17_sourcekey_slots_mulga_cbgenelge_brief_after_phase16.md`
- smoke_run_dir: `reports/benchmark/runs/20260424T_phase17b_article_zero_smoke`
- audited_qids: `KANUN-06`, `KHK-05`, `TUZUK-05`, `YON-04`, `CBG-04`, `CBKAR-08`
- decision: **accepted for Phase 17B smoke**

## What Changed

Added systemic article-zero body materialization for selected `m.0` chunks when:
- the source family is a regulation-like family (`khk`, `kky`, `tuzuk`, `uy`, `yonetmelik`, `cb_yonetmelik`);
- the selected `m.0` chunk has readable legal body text;
- the user did not request a specific non-zero article.

New trace fields:
- `selected_document_has_article_zero_body_span`
- `article_zero_body_extracted`
- `article_zero_materialization_reason`
- `body_extraction_source`
- `materialized_from_m0`

This is not a qid-specific fix. It does not force unreadable `m.0` chunks to materialize and does not override explicit article requests.

## Smoke Result

| QID | Before Reason | Phase 17B Reason | Corpus Required | Materialized |
|---|---|---|---:|---:|
| `KHK-05` | `body_span_available_but_title_or_article_zero` | `article_zero_body_extracted_from_m0` | false | true |
| `TUZUK-05` | `body_span_available_but_title_or_article_zero` | `article_zero_body_extracted_from_m0` | false | true |
| `YON-04` | `body_span_available_but_title_or_article_zero` | `article_zero_body_extracted_from_m0` | false | true |
| `KANUN-06` | `title_only_or_unreadable_body` | `title_only_or_unreadable_body` | true | false |
| `CBG-04` | source-key blocker before 17A | `title_only_or_unreadable_body` | true | false |
| `CBKAR-08` | source-key blocker before 17A | `title_only_or_unreadable_body` | true | false |

Aggregate smoke metrics:
- `canonical_span_materialized_count=3/6`
- `corpus_materialization_required_count=3/6`
- `article_zero_body_extracted_count=3/6`
- `title_only_answer_degraded_count=3/6`
- `binding_source_key_collision_detected_count=0/6`

## Remaining Corpus Backlog

After Phase 17B smoke, the remaining explicit corpus/materialization rows are:
- `KANUN-06`: selected body text is not readable enough; text extraction/corpus ingestion backlog.
- `CBG-04`: v2 source-key binding is clean, but selected body remains unreadable/title-only.
- `CBKAR-08`: v2 source-key binding is clean, but selected body remains unreadable/title-only.

These should not be hidden by prompt or selector changes. They need corpus extraction or source acquisition remediation.

## Verification

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py scripts/benchmark/phase16_corpus_materialization_remediation.py`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "article_zero_body_extraction or canonical_span_materialization or document_level_body_span"`
- `api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --out-dir reports/benchmark/runs/20260424T_phase17b_article_zero_smoke --qids KANUN-06 KHK-05 TUZUK-05 YON-04 CBG-04 CBKAR-08 --allow-missing-trace`
- `api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260424T_phase17b_article_zero_smoke/candidate_answers.csv --out-dir reports/benchmark/runs/20260424T_phase17b_article_zero_smoke`
- `api-gateway/.venv/bin/python scripts/benchmark/phase16_corpus_materialization_remediation.py --run-dir reports/benchmark/runs/20260424T_phase17b_article_zero_smoke`
- `api-gateway/.venv/bin/python scripts/benchmark/phase17_sourcekey_binding_audit.py --run-dir reports/benchmark/runs/20260424T_phase17b_article_zero_smoke --qids CBG-04 CBKAR-08`
