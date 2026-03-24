# FAZ9 RC-J Build Contract

Tarih: 2026-03-24

## Tanim

`RC-J = RC-G answer-path + retained release controls + model-visible surface parity isolation`

## Allowed Diff Surface

- `api-gateway/src/config.py`
- `api-gateway/src/release_controls.py`
- `api-gateway/src/session_store.py`
- `api-gateway/src/token_accounting.py`
- `api-gateway/src/main.py`
- `api-gateway/src/api/openai.py`
- `api-gateway/src/routers/chat.py`
- `api-gateway/src/llm/client.py`
- `api-gateway/src/observability.py`
- `evaluation/eval_runner.py`
- `scripts/faz9/*`

## Izinli Teknik Yuzey

- normalized request hizasi
- auth/session/trace bilgisinin model-visible surface disina alinmasi
- deterministic middleware ordering
- retrieval input payload hizasi
- assembly payload hizasi
- generation contract esitligi
- model request payload canonicalization
- projection-oncesi raw answer capture
- response envelope / eval-client boundary hizasi
- deterministic null / empty / omitted davranisi

## Yasak

- retrieval mantigi degisikligi yok
- prompt veya context assembly semantics degisikligi yok
- claim binding / source election / citation semantics degisikligi yok
- guardrail answer logic gevsetme yok
- model / adapter / corpus / eval family degisikligi yok

## Kabul

- `RC-J answer_path_delta = []`
- `allowed_diff_surface` yalniz bu liste olacak
- `RC-J` varsayilan lane olmayacak
