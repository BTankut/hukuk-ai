# FAZ 5 RC-F Build

Tarih: 2026-03-23

Referans:
- [faz5-official-implementation-plan-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz5-official-implementation-plan-2026-03-23.md)
- [faz5-candidate-manifests-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz5-candidate-manifests-2026-03-23.json)

## Build Formulu

`RC-F = RC-D + canonical_norm_identity_v1 + target_primary_source_election_v2 + claim_to_norm_projection_v2 + citation_closure_controller_v2 + canonical_support_mode_recovery_v1`

## Kod Yuzeyi

- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)
- [rc_f_offline_lib.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz5/rc_f_offline_lib.py)
- [run_rc_f_family_eval.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz5/run_rc_f_family_eval.py)

## Bilincli Olarak Degistirilmeyenler

- retrieval config
- reranker config
- model / adapter
- corpus
- query parser
- source-locking
- whitelist / temporal / law-scope / schema hard-fail cizgisi

## Test Kaniti

- `python3 -m py_compile api-gateway/src/faz2a_hardening.py`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_faz5_rc_f_hardening.py api-gateway/tests/test_faz2a_hardening.py -q`
- `python3 -m py_compile scripts/faz5/*.py`

## Sonuc

RC-F code surface, replay ve evaluation builder zinciri resmi FAZ5 talimatina uygun sekilde uretildi.
