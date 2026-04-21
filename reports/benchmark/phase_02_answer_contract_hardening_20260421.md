# Phase 2 Answer Contract Hardening Report

## Scope

Phase 2 implemented gateway-level answer contract repair/validation before
retrieval tuning. The runtime still preserves legacy `final_mode` and hardening
reason semantics; the new contract fields are emitted under `answer_contract`,
top-level `confidence_0_100`, benchmark CSV columns, and trace validation.

## Implementation

- Added `api-gateway/src/answer_contract_v2.py` for required contract fields,
  source claim parsing, confidence policy, validation flags, and controlled
  fallback text when public answer content is empty.
- Integrated contract repair into normal chat finalization and boundary proxy
  finalization.
- Extended benchmark runner/scorer/validator with Phase 2 contract columns:
  `answer_mode`, `grounding_status`, claimed source fields, confidence policy,
  uncertainty, manual review, and unsupported-confident-answer flags.
- Updated source canonicalization to prefer claimed Phase 2 source fields over
  noisy free-text answer surfaces.
- Added unit coverage for grounded contract repair and unsupported fallback
  degradation.

## Acceptance Run

Run artifact:
`reports/benchmark/runs/20260421T134133Z_phase2_answer_contract_rerun`

Runtime:

- API URL: `http://127.0.0.1:8000/v1`
- Model: `hukuk-ai-poc`
- Lane: `current_serving_lane`
- Retriever: `milvus`
- Gateway PID after restart: `32069`

Key run metrics:

- Total: 100
- Answered: 100
- Refused/empty: 0
- Errors: 0
- Missing trace: 0
- Missing `confidence_0_100`: 0
- Missing `final_reason`: 0
- Missing Phase 2 contract fields: 0
- Contract valid: 100/100

Score summary:

- Raw score proxy: 657.5 / 1000
- Average score proxy: 6.58 / 10
- Pass proxy: 55
- Fail proxy: 45
- `avg_answer_contract_score`: 1.0
- `contract_completeness_rate`: 1.0
- `unsupported_confident_answer_count`: 62
- `answer_contract_invalid_count`: 0

Phase 1 comparison:

- Phase 1 `answer_contract_missing`: 100 -> Phase 2: 0
- Phase 1 `avg_answer_contract_score`: 0.0 -> Phase 2: 1.0
- Phase 1 missing confidence/final reason: 100/100 -> Phase 2: 0/100

## Verification

- `api-gateway/.venv/bin/python -m py_compile ...`: pass
- `api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_answer_contract_v2.py ...`: pass
- `scripts/benchmark/validate_hukuk_ai_100_run.py --strict-contract`: pass
- `bash scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260421T134133Z_phase2_answer_contract_rerun`: pass

## Residual Risks

- Content-side quality is not solved by this phase. The scorer still shows
  `missing_required_content_signal=97`, `partial_grounding_only=97`,
  `wrong_family=36`, and `hallucinated_identifier=44`.
- `unsupported_confident_answer_count=62` is now visible; this is a routing,
  retrieval, and answer-quality target for the next phase, not a contract
  completion blocker.
