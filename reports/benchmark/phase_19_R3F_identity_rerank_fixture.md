# Phase 19 R3F Identity Rerank Fixture

Purpose: pre-extraction snapshot for `_rerank_chunks_by_source_identity(...)`.

Baseline commit: `3408e44 Refactor R3E source key binding helpers`

Runtime:

- `api_url`: `http://127.0.0.1:8000/v1`
- `model`: `hukuk-ai-poc`
- `DGX_MODEL`: `/models/merged_model_fabric_stage_20260321`
- `MILVUS_COLLECTION`: `mevzuat_faz1_shadow_20260418_compat1024`
- `MILVUS_ENTITY_COUNT`: `349191`
- `VECTOR_DIMENSION`: `1024`
- `EMBEDDING_BACKEND`: `remote`
- `EMBEDDING_BASE_URL`: `http://127.0.0.1:8081/v1`
- `GUARDRAILS_ENABLED`: `false`
- `PRESIDIO_ENABLED`: `false`

Source runs:

- `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity`
- `reports/benchmark/runs/20260426T_phase19_R3F_fixture_UY07_envparity`

Fixture table:

| QID | Run | Pre Count | Pre Top | First Changed | Input Source | Post Top | Score | Title | Identifier | Lock | Reason |
|---|---|---:|---|---|---|---|---:|---|---|---|---|
| CBG-01 | `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity` | 1 | `2024/7 m.0/f.0 / cb_genelge / Tasarruf Tedbirleri ile Ilgili` | `False` | `metadata_lookup_selector` | `2024/7 m.0/f.0 / cb_genelge / Tasarruf Tedbirleri ile Ilgili` | 198.0 | `medium_overlap` | `not_requested` | `strong` | `metadata_first_match / family_match / title_medium_overlap / title_overlap:2 / year_match / metadata_lane_supported` |
| CBKAR-01 | `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity` | 9 | `3351 m.7/f.0 / cb_karar / ITHALATTA ILAVE GUMRUK VERGISI UYGULANMASINA ILISKIN KARAR (KARAR SAYISI: 3351)` | `True` | `metadata_lookup_selector` | `10395 m.0/f.0 / cb_karar / 2024-2026 YILLARINDA YAPILACAK HAYVANCILIK DESTEKLEMELERI...` | 171.8683 | `weak_overlap` | `not_requested` | `strong` | `metadata_first_match / family_match / title_weak_overlap / title_overlap:3 / year_match / metadata_lane_supported` |
| CBKAR-08 | `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity` | 2 | `9903 gecici m.1/f.0 / cb_karar / Yatirimlarda Devlet Yardimlari Hakkinda Karar (Karar Sayisi: 9903)` | `False` | `metadata_lookup_selector` | `9903 gecici m.1/f.0 / cb_karar / Yatirimlarda Devlet Yardimlari Hakkinda Karar (Karar Sayisi: 9903)` | 378.0 | `medium_overlap` | `exact_identifier` | `strong` | `metadata_first_match / identifier_exact / family_match / title_medium_overlap / title_overlap:2 / year_match / metadata_lane_supported / legacy_query_identifier_anchor / ...` |
| MULGA-02 | `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity` | 14 | `33899 m.32/f.0 / yonetmelik / DEVLET ARSIV HIZMETLERI HAKKINDA YONETMELIK` | `True` | `metadata_lookup_selector` | `33899 m.4/f.0 / kky / DEVLET ARSIV HIZMETLERI HAKKINDA YONETMELIK` | 203.9132 | `medium_overlap` | `not_requested` | `strong` | `metadata_first_match / family_match / family_mapping_bridge_match / title_medium_overlap / title_overlap:3 / year_mismatch_penalty / dual_lane_confirmation` |
| YON-01 | `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity` | 12 | `29033 m.1/f.0 / yonetmelik / ELEKTRONIK TEBLIGAT YONETMELIGI` | `True` | `source_family_prior` | `20631 m.7/f.0 / kky / MALI SUCLARI ARASTIRMA KURULU BASKANLIGI ELEKTRONIK TEBLIGAT SISTEMINE ILISKIN USUL VE ESASLAR HAKKINDA YONETMELIK` | 79.9235 | `weak_overlap` | `not_requested` | `weak` | `family_match / family_mapping_bridge_match / title_weak_overlap / title_overlap:2 / dual_lane_confirmation` |
| TEB-01 | `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity` | 9 | `44999 m.0/f.0 / teblig / KAMU IHALE TEBLIGI (TEBLIG NO: 2026/1)` | `False` | `metadata_lookup_selector` | `44999 m.0/f.0 / teblig / KAMU IHALE TEBLIGI (TEBLIG NO: 2026/1)` | 303.9385 | `strong_overlap` | `not_requested` | `strong` | `metadata_first_match / family_match / title_strong_overlap / title_overlap:4 / year_match / dual_lane_confirmation` |
| KANUN-01 | `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity` | 24 | `TBK m.438/f.0 / kanun / TURK BORCLAR KANUNU` | `True` | `source_family_prior` | `7088 m.2/f.0 / cb_karar / GELIR IDARESI BASKANLIGI ... 657 SAYILI DEVLET MEMURLARI KANUNUNA TABI PERSONELINE FAZLA CALISMA UCRETI ODENMESI...` | 71.9146 | `none` | `not_requested` | `weak` | `family_match / family_mapping_bridge_match / dual_lane_confirmation` |
| UY-07 | `reports/benchmark/runs/20260426T_phase19_R3F_fixture_UY07_envparity` | 24 | `39691 m.23/f.0 / uy / KTO-KARATAY UNIVERSITESI ON LISANS VE LISANS EGITIM-OGRETIM VE SINAV YONETMELIGI` | `True` | `source_family_prior` | `40291 m.27/f.0 / uy / ISTANBUL ATLAS UNIVERSITESI ON LISANS VE LISANS EGITIM-OGRETIM VE SINAV YONETMELIGI` | 59.9253 | `none` | `not_requested` | `weak` | `family_match / dual_lane_confirmation` |

R3F after-extraction gate:

- The same QIDs must preserve `first_changed`, `identity_rerank_input_source`, top post-rerank citation/source family, top `document_identity_score`, match types, lock strength, and reason prefix unless the change is proven to be formatting-only.
- Any source-family or selected-document drift in this fixture is a stop condition for R3F.
