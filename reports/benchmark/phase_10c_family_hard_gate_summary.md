# Phase 10C Family Hard Gate Summary

## Change
- Strong family priors now hard-lock the pre-generation candidate pool for `cb_karar`, `cb_genelge`, `cb_yonetmelik`, `yonetmelik`, `uy`, `mulga_kanun`, and `teblig`.
- If a hard-gated family has no preferred-family candidate, the system does not answer from a cross-family fallback pool; it returns an empty candidate set so the normal insufficient-source path can produce a controlled narrow answer.
- Trace and benchmark CSV now expose `pre_filter_family_set`, `reranked_family_set`, `selected_family_source`, and `family_gate_status`.

## Verification
- `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/src/source_family_resolver.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py`
- `api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "source_family_prior or pre_generation_family_pool or retrieval_verification_features_export_phase9" -q`
- `python3 -m pytest tests/test_hukuk_ai_100_scorer.py -q`

## Expected Effect
- Wrong-family answers should fall because hard-family questions can no longer silently use a different family when the preferred pool is absent.
- Some rows may move from wrong-family to insufficient-source or corpus/retrieval visibility gaps; this is preferred over a detailed answer grounded in the wrong family.
- This change is source-family systemic and does not encode any benchmark QID-specific rule.
