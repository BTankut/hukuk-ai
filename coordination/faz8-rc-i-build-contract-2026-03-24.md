# FAZ8 RC-I Build Contract

Tarih: 2026-03-24

## Tanim

`RC-I = RC-G answer-path + retained release controls + transparent request/response boundary isolation`

## Allowed Diff Surface

- `api-gateway/src/release_controls.py`
- `api-gateway/src/session_store.py`
- `api-gateway/src/token_accounting.py`
- `api-gateway/src/main.py`
- `api-gateway/src/api/openai.py`
- `api-gateway/src/routers/chat.py`
- `api-gateway/src/observability.py`
- `evaluation/eval_runner.py`
- `scripts/faz8/*`

## Yasak

- retrieval / reranker / prompt / hardening logic / model / corpus degisikligi yok
- answer-path icinde citation/source election degisikligi yok
- must-close release controls gevsetme yok

## Kabul

- `RC-I answer_path_delta = []`
- `allowed_diff_surface` yalniz bu liste olacak
