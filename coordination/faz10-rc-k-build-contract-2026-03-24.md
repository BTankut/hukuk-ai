# FAZ10 RC-K Build Contract

Tarih: 2026-03-24

## Tanim

`RC-K = RC-G answer-path truth + RC-J model-visible isolation package + runtime isolation repair`

## Build Rule

- `RC-K`, `RC-G` tabanindan kurulur.
- `RC-J` ustune patch atilmaz.
- `RC-J` icindeki kapanmis model-visible isolation paketi aynen tasinir.
- `RC-K answer_path_delta = []`

## Allowed Diff Surface

- `api-gateway/src/config.py`
- `api-gateway/src/llm/client.py`
- `api-gateway/src/release_controls.py`
- `api-gateway/src/routers/chat.py`
- `api-gateway/src/token_accounting.py`
- `evaluation/eval_runner.py`
- `scripts/faz10/*`

## Izinli Teknik Yuzey

- generation worker affinity / worker count
- generation process reuse / request-local state reset
- generation cache namespace / cache policy
- post-payload auth/session/audit/observability context shadow isolation
- request ordering / serial execution policy
- deterministic retry / fallback / streaming closure
- raw token stream capture noktasi
- raw answer object capture boundary
- parity replay instrumentation
- cutover parity topology sabitlemesi

## Yasak

- retrieval mantigi degisikligi yok
- query parsing degisikligi yok
- prompt / context assembly semantics degisikligi yok
- citation / source election / primary source election mantigi degisikligi yok
- refusal / guardrail answer logic degisikligi yok
- model / adapter / merge / corpus / metadata / eval family degisikligi yok

## Kabul

- `RC-K` varsayilan serving lane olmayacak
- `allowed_diff_surface` bu listeyle sinirli kalacak
- `RC-K` yalniz FAZ10 talimatindaki runtime isolation repair yuzeyini tasiyacak
