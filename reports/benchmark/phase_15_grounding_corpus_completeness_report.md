# Phase 15 Grounding / Corpus Completeness Report

## 1. Commit SHA Listesi
- `c0c89cb` Phase 15A harden confidence policy
- `c5abf35` Phase 15B trace answer slot grounding
- `deeed15` Phase 15B guide synthesis by answer slots
- `ebca91a` Phase 15C classify corpus materialization backlog
- `3218d61` Phase 15D harden MULGA temporal routing

## 2. Değişen Dosyalar
- Runtime: `api-gateway/src/answer_contract_v2.py`, `api-gateway/src/routers/chat.py`, `api-gateway/src/source_family_resolver.py`
- Tests: `api-gateway/tests/test_answer_contract_v2.py`, `api-gateway/tests/test_chat_router.py`
- Benchmark/scoring: `scripts/benchmark/run_hukuk_ai_100.py`, `scripts/benchmark/score_hukuk_ai_100.py`
- Phase reports/scripts: `scripts/benchmark/phase15_unsupported_confident_audit.py`, `scripts/benchmark/phase15_corpus_materialization_backlog.py`, `scripts/benchmark/phase15_mulga_temporal_audit.py`

## 3. Çalıştırılan Testler
- `python3 -m py_compile api-gateway/src/answer_contract_v2.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py scripts/benchmark/phase15_unsupported_confident_audit.py`
- `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/src/source_family_resolver.py scripts/benchmark/phase15_mulga_temporal_audit.py`
- `cd api-gateway && .venv/bin/python -m pytest tests/test_answer_contract_v2.py -q`
- `cd api-gateway && .venv/bin/python -m pytest tests/test_chat_router.py -k "completeness_synthesis or answer_slot_synthesis_hint" -q`
- Targeted source-family tests for MULGA temporal/risk routing passed.
- Full `source_family_prior` subset has one pre-existing dirty-worktree expectation conflict from unstaged `cb_karar_relation_prefers_primary_decision`; it was not staged into Phase 15D.

## 4. Full Benchmark Komutları
- Run: `python3 scripts/benchmark/run_hukuk_ai_100.py --out-dir reports/benchmark/runs/20260424T081121Z_phase15_full --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --timeout 420 --retries 0 --sleep 0.2`
- Score: `python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260424T081121Z_phase15_full/candidate_answers.csv --out-dir reports/benchmark/runs/20260424T081121Z_phase15_full`
- Green lane: `GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/20260424T091553Z_phase15_full bash scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260424T081121Z_phase15_full`

## 5. Phase 14'e Göre Delta
| Metric | Phase 14 | Phase 15 | Delta |
|---|---:|---:|---:|
| raw_score_proxy | 729.32 | 707.47 | -21.85 |
| pass_proxy | 70 | 67 | -3 |
| wrong_family | 15 | 12 | -3 |
| wrong_document | 13 | 18 | +5 |
| hallucinated_identifier | 21 | 22 | +1 |
| unsupported_confident_claim | 25 | 6 | -19 |
| right_document_wrong_article_or_span | 70 | 72 | +2 |
| missing_required_content_signal | 96 | 99 | +3 |
| partial_grounding_only | 96 | 99 | +3 |
| corpus_materialization_required_count | 13 | 13 | 0 |
| canonical_span_materialized_count | 87 | 86 | -1 |
| MULGA pass | 0/5 | 0/5 | 0 |

## 6. Unsupported Confident Audit
- Phase15E audit: `reports/benchmark/phase_15e_unsupported_confident_audit.md`
- `unsupported_confident_claim_rows = 6`, below target `<=10`.
- Remaining rows: `CBK-06`, `CBY-04`, `KANUN-18`, `TEB-05`, `YON-03`, `YON-05`.
- Runtime confidence policy improved materially, but scorer still finds six fully-grounded/high-confidence answers whose gold must-include coverage is weak.

## 7. Evidence-To-Answer Grounding Audit
- `avg_answer_slot_coverage_score = 0.721`
- `minimum_answer_facts_present_count = 69`
- `runtime_rubric_aligned_completeness_class.rubric_sufficient = 69`
- Scorer-level `missing_required_content_signal = 99` and `partial_grounding_only = 99` did not improve. This means runtime slot coverage is still too surface-level versus gold must-include content.

## 8. Corpus Materialization Backlog
- Phase15E backlog: `reports/benchmark/phase_15e_corpus_materialization_backlog.md`
- `corpus_materialization_required_rows = 13`
- Families: `CB_GENELGE=4`, `TEBLIGLER=3`, `CB_KARAR=2`, plus one each in `KANUN`, `KHK`, `TUZUK`, `YONETMELIK`.
- This backlog did not shrink in Phase 15 because Phase 15C classified and planned it but did not rebuild corpus/index materialization.

## 9. Source-Key Collision Remediation Plan
- Phase15E plan: `reports/benchmark/phase_15e_source_key_collision_remediation_plan.md`
- Permanent fix remains family-qualified canonical source keys: `{source_family}:{canonical_identifier}:{canonical_title_hash_or_doc_uuid}` plus article/span ids.
- Numeric `belge_no` must stay alias-only; it must not be the sole cross-family materialization key.

## 10. MULGA Temporal/Rubric Audit
- Phase15E audit: `reports/benchmark/phase_15e_mulga_temporal_rubric_audit.md`
- `active_state_claims` improved from `3` to `0`.
- `wrong_family_claims` improved from `5` to `1`.
- `MULGA pass` remains `0/5`; remaining blocker is rubric/content completeness, not active-vs-repealed state.

## 11. Family-Level Score Table
| Family | Rows | Pass | Avg | Wrong family | Wrong doc | Corpus required | Unsupported |
|---|---:|---:|---:|---:|---:|---:|---:|
| CB_GENELGE | 4 | 0 | 3.06 | 0 | 4 | 4 | 0 |
| CB_KARAR | 8 | 6 | 8.06 | 1 | 0 | 2 | 0 |
| CB_KARARNAME | 6 | 6 | 9.09 | 0 | 0 | 0 | 1 |
| CB_YONETMELIK | 6 | 4 | 7.62 | 2 | 0 | 0 | 1 |
| KANUN | 21 | 14 | 6.88 | 3 | 4 | 1 | 1 |
| KHK | 6 | 5 | 7.20 | 0 | 0 | 1 | 0 |
| KKY | 11 | 9 | 8.50 | 2 | 0 | 0 | 0 |
| MULGA | 5 | 0 | 3.56 | 0 | 4 | 0 | 0 |
| TEBLIGLER | 8 | 6 | 7.04 | 0 | 2 | 3 | 1 |
| TUZUK | 5 | 2 | 4.43 | 1 | 2 | 1 | 0 |
| UY | 10 | 9 | 8.52 | 0 | 1 | 0 | 0 |
| YONETMELIK | 10 | 6 | 6.77 | 3 | 1 | 1 | 2 |

## 12. Gate Kararı
- Green lane: `pass`
- Contract validity: `100/100`
- Phase 15 target success: `2/12`
- Productization gate: `closed`
- Fine-tuning gate: `closed`

Phase 15 succeeded only on confidence safety and wrong-family reduction. It failed the grounding/corpus completeness gate. Next work should not be fine-tuning; it should be corpus materialization remediation plus source-key/body-span reindex, especially `CB_GENELGE`, `TEBLIGLER`, `CB_KARAR`, and MULGA content-slot completion.
