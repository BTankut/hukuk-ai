# FAZ 3 RC-D Build

Tarih: 2026-03-23

Referans:
- [faz3-official-implementation-plan-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz3-official-implementation-plan-2026-03-23.md)
- [faz3-selective-claim-binding-v3-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz3-selective-claim-binding-v3-spec-2026-03-23.md)
- [faz3-final-mode-mapping-v3-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz3-final-mode-mapping-v3-spec-2026-03-23.md)

## Ozet

`RC-D` guardrail katmani working tree uzerinde kuruldu.

Bu build yalniz su alanlari degistirir:

- selective claim-binding v3
- final-mode mapping v3

## Degismeyen Yuzey

- model
- adapter
- retrieval
- reranker
- corpus
- source-locking
- canonical citation normalization
- whitelist gate
- temporal gate
- law-scope gate v2

## Kod Dokunusu

- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)
- [test_faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/tests/test_faz2a_hardening.py)

## Focused Verification

Gecen:

- `python3 -m py_compile api-gateway/src/faz2a_hardening.py api-gateway/tests/test_faz2a_hardening.py`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_faz2a_hardening.py -q`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`

## Sonraki Adim

Resmi siradaki adim `WP-6`:

- `77` satirlik blocker pack uzerinde `RC-D` rerun
