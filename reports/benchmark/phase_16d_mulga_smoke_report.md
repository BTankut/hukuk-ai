# Phase 16D MULGA Temporal/Rubric Smoke Report

- run_dir: `reports/benchmark/runs/20260424T121323Z_phase16d_mulga_smoke_final`
- qids: `MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05`
- gateway: `http://127.0.0.1:8000/v1`
- model: `hukuk-ai-poc`
- errors: 0
- missing_trace: 0
- contract_valid: 5/5

## Runtime Slot Result

- pass_proxy: 0/5
- raw_score_proxy: 18.68 / 50
- minimum_answer_facts_present_count: 4/5
- avg_required_fact_coverage_score: 0.907
- rubric_sufficient_count: 4/5
- complete_enough_count: 4/5
- repealed_as_active_count: 0
- unsupported_confident_answer_count: 0
- answer_mode: `repealed_transition_answer` for 5/5

## Row Snapshot

- MULGA-01: score=6.43, runtime=`complete_enough`, rubric=`rubric_sufficient`, remaining=`wrong_article | missing_required_content_signal | partial_grounding_only`
- MULGA-02: score=3.25, runtime=`complete_enough`, rubric=`rubric_sufficient`, remaining=`wrong_document | hallucinated_identifier | missing_gold_document_signal`
- MULGA-03: score=3.25, runtime=`complete_enough`, rubric=`rubric_sufficient`, remaining=`wrong_document | hallucinated_identifier | missing_gold_document_signal`
- MULGA-04: score=3.25, runtime=`no_retrieved_evidence`, rubric=`insufficient_both`, remaining=`wrong_document | missing_gold_document_signal`
- MULGA-05: score=2.50, runtime=`complete_enough`, rubric=`rubric_sufficient`, remaining=`wrong_document | wrong_article | hallucinated_identifier`

## Decision

- Phase 16D content-slot objective is materially improved: the old `no_answer`/empty-slot failure is closed for 4/5 rows.
- Phase 16D acceptance target `MULGA pass >= 2/5` is not met.
- Remaining blocker is not answer-mode wording; it is historical document/source identity selection against the private gold documents.
- Next remediation should target explicit historical title/source binding for old regulation/tuzuk/KHK queries before another full-run acceptance decision.
