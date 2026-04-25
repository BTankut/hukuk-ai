# Phase 18 Rubric Slot Completion Report

Date: 2026-04-25

Instruction: `reports/benchmark/hukuk_ai_phase18_rubric_slot_completion_brief_after_phase17f.md`

Decision: **FAIL / gate closed**. Phase 18 delivered systemic slot, confidence, synthesis and source-supplement fixes, but the full 100 benchmark missed the required `10/13` target gate. Productization and fine-tuning remain closed.

## 1. Commit SHA List

| Phase | Commit | Scope |
|---|---|---|
| 18A | `8f1fad7` | Required slot matrix |
| 18B | `3c71bb7` | Evidence answer slots |
| 18C | `65a8a56` | Claim confidence calibration |
| 18D | `398915a` | Verified-slot answer synthesis |
| 18E | `887cc88` | Source materialization supplements |
| 18F | Current commit containing this report | Rubric-slot completion stabilization, full rerun, gate decision |

## 2. Changed Files

Code and tests changed in this closure patch:

- `api-gateway/src/rag/source_catalog.py`
- `api-gateway/src/faz2a_hardening.py`
- `api-gateway/src/answer_contract_v2.py`
- `api-gateway/src/routers/chat.py`
- `api-gateway/src/rag/required_slot_matrix.py`
- `api-gateway/tests/test_answer_contract_v2.py`
- `api-gateway/tests/test_faz2a_hardening.py`
- `api-gateway/tests/test_chat_router.py`

Primary report/artifact paths:

- `reports/benchmark/runs/20260425T091503Z_phase18f_smoke_backlog_latest`
- `reports/benchmark/runs/20260425T091702Z_phase18f_full`
- `reports/benchmark/green_lane/20260425T_phase18f_full`

## 3. Test Commands

```bash
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/required_slot_matrix.py \
  api-gateway/src/faz2a_hardening.py \
  api-gateway/src/answer_contract_v2.py

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_faz2a_hardening.py \
  -k "whitelist or citation or slash_numbered or effective_start_alias or target_date" -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "selector_exact_span_priority or sufficiency_question or verified_answer_slot_plan or allowed_source_whitelist" -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_answer_contract_v2.py \
  -k "slot_coverage or slash_numbered or cb_genelge_document_level_body_support or active_cb_genelge" -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_source_catalog.py -q
```

Green lane validation:

```bash
GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/20260425T_phase18f_full \
BENCHMARK_PYTHON=api-gateway/.venv/bin/python \
scripts/benchmark/run_green_lane.sh \
  --run-dir reports/benchmark/runs/20260425T091702Z_phase18f_full
```

Result: `pass`.

## 4. Benchmark Commands

Gateway runtime used for rerun:

```bash
cd api-gateway
DGX_BASE_URL=http://192.168.12.243:30000/v1 \
DGX_MODEL=/models/merged_model_fabric_stage_20260321 \
MILVUS_ENABLED=true \
MILVUS_URI=http://localhost:19530 \
MILVUS_COLLECTION=mevzuat_e5_shadow \
EMBEDDING_BACKEND=remote \
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1 \
GUARDRAILS_ENABLED=false \
PRESIDIO_ENABLED=false \
.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --log-level info
```

Benchmark and scorer:

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --out-dir reports/benchmark/runs/20260425T091702Z_phase18f_full \
  --api-url http://127.0.0.1:8000/v1 \
  --model hukuk-ai-poc

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/20260425T091702Z_phase18f_full/candidate_answers.csv \
  --out-dir reports/benchmark/runs/20260425T091702Z_phase18f_full
```

Operational caveat: guardrails were disabled for this benchmark lane because the current NeMoGuardrails path blocks synchronous generation and creates benchmark-time false failures. This report evaluates retrieval, contract, slot and answer synthesis behavior without that external guardrail bottleneck.

## 5. Phase 17F Delta

| Metric | Phase 17F | Phase 18F full | Delta | Target met |
|---|---:|---:|---:|---|
| raw_score_proxy | 767.91 | 324.59 | -443.32 | no |
| pass_proxy | 77/100 | 12/100 | -65 | no |
| wrong_family | 12 | 44 | +32 | no |
| wrong_document | 10 | 82 | +72 | no |
| hallucinated_identifier | 18 | 32 | +14 | no |
| unsupported_confident_claim/answer | 8 | 0 | -8 | yes |
| missing_required_content_signal | 98 | 100 | +2 | no |
| partial_grounding_only | 98 | 100 | +2 | no |
| runtime rubric_sufficient | 88/100 | 65/100 | -23 | no |
| MULGA pass | 3/5 | 0/5 | -3 | no |
| CB_GENELGE pass | 2/4 | 4/4 | +2 | yes |
| corpus_materialization_required_count | 2 | 0 | -2 | yes |
| canonical_span_materialized_count | 98 | 64 | -34 | no |

Target gate result: **3/13**, required **10/13**.

## 6. Required Slot Matrix Summary

Implemented/retained systemic slot controls:

- Task/family slot matrix is emitted into trace and candidate CSV.
- Query-level additions distinguish procedure/sufficiency questions from hierarchy-conflict questions.
- `yeterli midir` is no longer treated as hierarchy conflict unless the query also contains explicit norm-family conflict language.
- `procedure`, `facts_applied`, `result_or_holding`, `current_applicability`, `temporal_validity`, identity and document-selection slots are exposed through answer slot maps.

Full run result:

- `avg_answer_slot_coverage_score = 0.614`
- `avg_evidence_required_slot_value_count = 3.39`
- `evidence_required_slot_value_count_total = 339`
- `minimum_answer_facts_present_count = 65`

## 7. Evidence-to-Slot Extraction Audit

Implemented/retained systemic extraction changes:

- Slash-numbered identifiers are preserved, including `2024/7` and `2019/12`.
- Year-only parsing no longer misreads slash-numbered circular identifiers as dates.
- `effective_start` / `effective_end` aliases participate in temporal validity policy.
- Selector exact spans receive priority for slot extraction.
- Source whitelist now accepts canonical source id, citation, chunk source, resolved source identifier, canonical display and display citation aliases.

Full run result:

- `evidence_slot_synthesis_count = 55`
- `evidence_slot_synthesis_reason.slot_values_made_visible_from_selected_evidence = 55`
- `selector_exact_article_hit_rate = 0.31`
- `selected_article_equals_claimed_article_rate = 0.56`
- `selector_preferred_family_hit_rate = 0.2857`

The extraction layer works for rows with a usable selected source, but it cannot compensate when the selected source family/document is wrong or absent.

## 8. Claim-Level Confidence Calibration Audit

Implemented/retained systemic confidence changes:

- Confidence is capped by critical missing required slots, temporal uncertainty, source identity uncertainty and low answer-slot evidence coverage.
- Partially slot-grounded answers are degraded instead of being emitted as confident unsupported answers.
- Controlled verified-slot replacement is allowed only when verified slots provide enough direct basis/rule support and no evidence gap is present.

Full run result:

- `unsupported_confident_answer_count = 0`
- `avg_confidence_policy_consistency_score = 1.0`
- `avg_groundedness_confidence_consistency_score = 1.0`
- `confidence_policy_adjusted_count = 69`
- `answer_contract_invalid_count = 0`
- `contract_completeness_rate = 1.0`

This is the clearest successful part of Phase 18F.

## 9. Verified-Slot Answer Synthesis Audit

Implemented/retained synthesis changes:

- Verified answer plans carry direct answer, legal basis, temporal validity, scenario application, procedure/consequence and missing-slot data.
- Finalization can replace unsupported or blocked generated text with a controlled verified-slot answer when required evidence is available.
- Missing-slot pressure now lowers confidence instead of silently overclaiming.

Smoke result after the latest synthesis and whitelist fixes:

- Run: `reports/benchmark/runs/20260425T091503Z_phase18f_smoke_backlog_latest`
- `raw_score_proxy = 33.99/40`
- `pass_proxy = 3/4`
- `unsupported_confident_answer_count = 0`
- `CBG-01 PASS 8.65`
- `CBG-02 PASS 9.55`
- `KANUN-06 PASS 8.99`
- `CBKAR-08 FAIL 6.80`

Full run result:

- `raw_score_proxy = 324.59/1000`
- `pass_proxy = 12/100`
- `fail_proxy = 88/100`
- `canonical_missing_required_content_signal = 100`
- `canonical_partial_grounding_only = 100`

Conclusion: synthesis is now safer, but not enough to solve family/source selection gaps.

## 10. CB_GENELGE Side Backlog Result

CB_GENELGE is the main successful side backlog:

| Metric | Value |
|---|---:|
| pass | 4/4 |
| average score | 9.03 |
| canonical span materialized | 4/4 in selected rows |
| corpus materialization required | 0 |

The slash-numbered identifier and document-level body supplement work resolved the previous CB_GENELGE blocker.

## 11. MULGA Result

MULGA regressed materially:

| Metric | Value |
|---|---:|
| pass | 0/5 |
| average score | 1.78 |
| repealed_source_used_as_active | 5 |

Representative failure: `MULGA-01` selected active `HUKUK MUHAKEMELERİ KANUNU m.42` under `pre_filter_family_set=kanun`, while expected family was `mulga_kanun`. The gate reported `hard_gate_no_preferred_candidates`, which means the preferred historical family was detected but no usable preferred candidate was available.

## 12. Family-Level Score Table

| Family | Count | Pass | Fail | Avg score |
|---|---:|---:|---:|---:|
| CB_GENELGE | 4 | 4 | 0 | 9.03 |
| KANUN | 21 | 6 | 15 | 4.67 |
| UY | 10 | 1 | 9 | 3.53 |
| CB_KARAR | 8 | 0 | 8 | 2.87 |
| KKY | 11 | 0 | 11 | 2.82 |
| KHK | 6 | 0 | 6 | 2.78 |
| CB_KARARNAME | 6 | 1 | 5 | 2.38 |
| YONETMELIK | 10 | 0 | 10 | 2.36 |
| CB_YONETMELIK | 6 | 0 | 6 | 2.18 |
| TEBLIGLER | 8 | 0 | 8 | 2.16 |
| MULGA | 5 | 0 | 5 | 1.78 |
| TUZUK | 5 | 0 | 5 | 1.49 |

Main failure classes:

- `missing_required_content_signal = 100`
- `partial_grounding_only = 100`
- `missing_gold_document_signal = 82`
- `wrong_document = 82`
- `wrong_family = 44`
- `hallucinated_identifier = 32`
- `claimed_source_parse_failed = 31`

## 13. Productization / Fine-Tuning Gate Decision

Productization gate: **closed**.

Fine-tuning gate: **closed**.

Reason: Phase 18F did not pass the minimum acceptance gate. The blocker is not an LLM fine-tuning problem yet. The dominant error is that non-KANUN families often do not reach a materialized, selectable source/body candidate before answer synthesis.

Do not fine-tune on this benchmark state. It would train around retrieval/source-selection failure and hide the real system defect.

## 14. Remaining Risks and Next Systemic Work

Primary diagnosis:

- Dense/runtime retrieval still collapses many non-KANUN questions into `kanun` pre-filter pools.
- When preferred family candidates are absent, the hard gate either refuses/UNKNOWN or global fallback selects the wrong Kanun document.
- Metadata lookup can identify candidate titles but does not consistently materialize a usable source/body fallback for non-KANUN families.
- CB_GENELGE passes because source supplements now exist; the same materialized-source path is missing for several CB_KARAR, CB_KARARNAME, YONETMELIK, TEBLIGLER, TUZUK, KHK, KKY and MULGA rows.

Representative rows:

- `CBK-01`: expected `cb_kararname`; selected `İCRA VE İFLAS KANUNU m.1`; `pre_filter_family_set=kanun`; `global_fallback`.
- `YON-01`: expected `yonetmelik`; `pre_filter_family_set=kanun`; `hard_gate_no_preferred_candidates`.
- `TEB-01`: expected `teblig`; `pre_filter_family_set=kanun`; `hard_gate_no_preferred_candidates`.
- `MULGA-01`: expected `mulga_kanun`; selected active HMK; `repealed_source_used_as_active`.

Recommended next phase:

- Build metadata-backed family materialization/stub recall for non-KANUN source families.
- Ensure preferred-family metadata hits produce selectable body/stub candidates before dense global fallback.
- Add family-level smoke packs for `YONETMELIK`, `TEBLIGLER`, `TUZUK`, `KHK`, `KKY`, `CB_KARAR`, `CB_KARARNAME`, `CB_YONETMELIK`, and `MULGA`.
- Keep the no-QID-specific rule. The fix must be family/source materialization and selection, not benchmark-question patching.
