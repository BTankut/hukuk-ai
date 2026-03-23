# FAZ 4 RC-E Build

Tarih: 2026-03-23

Referans:
- [faz4-official-implementation-plan-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz4-official-implementation-plan-2026-03-23.md)
- [faz4-citation-fidelity-controller-v1-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz4-citation-fidelity-controller-v1-spec-2026-03-23.md)
- [faz4-primary-source-anchor-v1-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz4-primary-source-anchor-v1-spec-2026-03-23.md)
- [faz4-kept-claim-citation-projection-v1-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz4-kept-claim-citation-projection-v1-spec-2026-03-23.md)
- [faz4-final-mode-boundary-v4-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz4-final-mode-boundary-v4-spec-2026-03-23.md)

## Ozet

`RC-E`, working tree uzerinde `RC-D` tabani uzerine kuruldu.

Formul:

`RC-E = RC-D + citation fidelity controller v1 + primary source anchor v1 + kept-claim citation projection v1 + final-mode boundary v4`

## Degisen Yuzey

- citation fidelity controller v1
- primary source anchor v1
- kept-claim citation projection v1
- final-mode boundary v4

## Degismeyen Yuzey

- model
- adapter
- retrieval
- reranker
- corpus
- prompt
- query parser
- source-locking
- canonical citation normalization
- whitelist gate
- temporal gate
- law-scope gate v2
- trace/schema contract

## Kod Dokunusu

- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)
- [test_faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/tests/test_faz2a_hardening.py)
- [build_citation_family_failure_pack.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/build_citation_family_failure_pack.py)
- [rc_e_offline_lib.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/rc_e_offline_lib.py)
- [run_rc_e_family_eval.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/run_rc_e_family_eval.py)
- [build_citation_family_failure_pack_rerun.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/build_citation_family_failure_pack_rerun.py)
- [build_blocker_invariance_rerun.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/build_blocker_invariance_rerun.py)
- [build_rc_e_family_eval_summary.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/build_rc_e_family_eval_summary.py)

## Focused Verification

Gecen:

- `python3 -m py_compile api-gateway/src/faz2a_hardening.py api-gateway/tests/test_faz2a_hardening.py scripts/faz4/rc_e_offline_lib.py scripts/faz4/run_rc_e_family_eval.py scripts/faz4/build_citation_family_failure_pack_rerun.py scripts/faz4/build_blocker_invariance_rerun.py scripts/faz4/build_rc_e_family_eval_summary.py`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_faz2a_hardening.py -q`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`

## Sonraki Adim

Resmi sira geregi build sonrasi:

1. quality-loss pack rerun
2. blocker invariance rerun
3. full-family matched eval
4. steering sonucu

