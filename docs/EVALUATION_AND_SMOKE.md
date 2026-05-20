# Evaluation And Smoke

Validation should exercise current runtime behavior, not historical evaluation lanes.

## Readiness

```bash
python3 scripts/check_legal_advisor_readiness.py
```

This command requires `DGX_BASE_URL` and `DGX_MODEL`. If judicial runtime is enabled, it also requires readable processed judicial indexes.

## Closed runtime gates

Judicial disabled gate:

```bash
python3 scripts/ci/check_closed_runtime_state.py
```

Judicial enabled gate:

```bash
JUDICIAL_RUNTIME_ENABLED=true python3 scripts/ci/check_closed_runtime_state.py
```

These gates check mevzuat closed state and judicial fail-closed behavior.

## Focused API tests

```bash
api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_legal_rag_runtime_integration.py -q
api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_legal_advisor_application_e2e.py -q
```

If feasible, run the broader API gateway test set:

```bash
api-gateway/.venv/bin/python -m pytest api-gateway/tests -q -k 'not reranker'
```

Legacy root-level tests may still collect old historical test modules. Treat those as legacy until explicitly modernized.

## Real-index final smoke

Run only with a reachable fine-tuned LLM endpoint, Milvus mevzuat collection, embedding service, and real processed judicial indexes:

```bash
python3 scripts/run_final_legal_advisor_smoke.py
```

The smoke battery covers mevzuat-only, judicial exact lookup, judicial issue retrieval, mixed mevzuat and judicial evidence, unsupported exact decisions, fabrication refusal, single-decision boundary behavior, and streaming/non-streaming parity.

## External benchmark workflow

External benchmarks measure quality but do not define product truth alone. Run them against the current API, record metrics outside the repo unless a small reviewed artifact is intentionally committed, and compare source-card and verification failures to runtime traces.

Do not patch individual benchmark questions. Fix the generic runtime, retrieval, evidence, or verifier cause.

## Failure triage categories

- routing miss
- mevzuat retrieval miss
- judicial exact lookup miss
- judicial lexical retrieval miss
- evidence packet defect
- LLM drift
- verifier miss
- citation/source-card mismatch
- readiness/config issue
