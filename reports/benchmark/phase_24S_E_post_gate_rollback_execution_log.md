# Phase 24S-E Post-Gate Rollback Execution Log

Generated at UTC: `2026-05-05T08:22:31Z`  
Git HEAD before rollback commit: `fbcb42da899e77e73252b15174ce0808dc6d1a8e`  
Live API: `http://127.0.0.1:8000/v1`  
Live PID after rollback: `46587`  
Process manager: `tmux session hukuk_ai_live_8000`

## Rollback Reason

Phase 24S-E full benchmark failed the mandatory minimum gate:

- raw_score_proxy: `727.18 < 816.86`
- pass_proxy: `73 < 91`
- wrong_family: `8 > 6`
- wrong_document: `21 > 4`
- hallucinated_identifier: `25 > 4`

## Rollback Target

- Collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Expected row count: `349403`
- Lane: `phase22f_s7_full_shadow`
- API version: `2026-05-03-phase23R-E-benchmark-only-cutover`
- Model id: `hukuk-ai-poc`
- DGX model: `/models/merged_model_fabric_stage_20260321`

## Verification Checks

- health_ok: `True`
- lane_match: `True`
- api_version_match: `True`
- collection_match: `True`
- row_count_match: `True`
- model_contract_match: `True`
- dgx_model_match: `True`

## Result

Rollback verification: `PASS`.

Live `8000` is no longer serving the Phase24S CBY candidate collection.
