# Development

`main` is canonical. Work on scoped branches, push branches before review, and merge back only with fast-forward when requested by the delivery instructions.

## Policy

- Keep changes tied to production runtime quality, tests, operators, or current product docs.
- Do not revive legacy staged-track or narrative status-report loops.
- Do not commit generated data, processed indexes, benchmark outputs, logs, local secrets, or private endpoint values.
- Keep legacy historical material under `docs/archive/` and use `docs/LEGACY_DOCS.md` as the map.
- Prefer generic runtime and evidence fixes over benchmark-specific patches.

## Current runtime tests

```bash
python3 scripts/check_docs_current.py
python3 scripts/ci/check_closed_runtime_state.py
JUDICIAL_RUNTIME_ENABLED=true python3 scripts/ci/check_closed_runtime_state.py
api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_legal_rag_runtime_integration.py -q
api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_legal_advisor_application_e2e.py -q
```

Run `api-gateway/.venv/bin/python -m pytest api-gateway/tests -q -k 'not reranker'` when feasible.

## Web search

Use web search only when current external behavior is uncertain, such as OpenAI-compatible SSE details, FastAPI or Uvicorn behavior, SQLite read-only behavior, Docker Compose behavior, or GitHub Markdown rendering. Prefer official sources.

## Delegation

Subagents may inspect or edit bounded, disjoint areas when explicitly authorized by the active task. They should return files inspected, files changed, classification, commands checked, and blockers only.

## Legacy root tests

Some root-level historical tests may still import old modules. Do not treat them as current runtime gates unless they are modernized and mapped to the current legal advisor behavior.
