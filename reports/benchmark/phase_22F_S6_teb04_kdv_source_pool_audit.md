# Phase 22F-S6-A TEB-04 KDV Teblig Source Pool Audit

## Scope

This audit investigates why `TEB-04` does not select the KDV General Application Communique source in the S5 targeted smoke run. It does not change runtime behavior, live `8000`, prompts, models, retrieval top-k, or scoring.

Reference run:

- `reports/benchmark/runs/20260502T1126Z_phase22F_S5_targeted_fix_smoke_final2`
- API URL: `http://127.0.0.1:8018/v1`
- Model: `hukuk-ai-poc`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Live `8000` untouched: `true`

## Current TEB-04 Result

`TEB-04` failed with score `0.00`.

- Selected source: `ELEKTRONİK TEBLİGAT SİSTEMİ GENEL TEBLİĞİ (SIRA NO: 1)`
- Claimed family/identifier: `TEBLIGLER / 24345 m.1`
- Failure classes: `auto_fail_triggered | missing_required_content_signal | partial_grounding_only`
- S5 guard type: `active_non_mulga_claim_preservation`
- Runtime selected pool: `24345`, `6115`, `10674`, plus related tax-law spans; it did not contain source `19631`.

The failure is not a family rewrite problem anymore. It is a source identity and retrieval pool problem inside the `TEBLIGLER` lane.

## Corpus Findings

The expected source is present in the canonical catalog:

- Catalog: `reports/benchmark/phase_05_canonical_source_catalog.csv`
- `source_key`: `19631`
- `source_family_canonical`: `teblig`
- `canonical_title`: `KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ`
- `canonical_identifier_display`: `19631 m.0`
- Official Gazette: `28983`, `2014-04-26`
- Effective state: `active`

The source is also present in Milvus:

- Collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Query: `metadata["belge_no"] == "19631"`
- Rows found: `3`
- Example IDs:
  - `19631:19631:m0:f0:from2014-04-26:to9999-12-31::row:207586`
  - `19631:19631:m0:f0:from2014-04-26:to9999-12-31::row:207587`
  - `19631:19631:m0:f0:from2014-04-26:to9999-12-31::row:207588`

However, the Milvus metadata does not carry the canonical KDV title. It carries `belge_no=19631`, `belge_kisa_adi=19631`, `kanun_kisa_adi=19631`, and `display_citation=19631 m.0`. This blocks title/alias based identity selection for a natural-language KDV query.

## Retrieval Findings

Using the S5 provenance embedding service (`intfloat/multilingual-e5-large-instruct` at `http://127.0.0.1:8081/v1`) and the same collection:

- Runtime retrieval top-k: `24`
- Raw dense top-24: no `19631`
- Raw dense top-100: no `19631`
- Raw dense top-500: `19631` first appears at rank `130`
- Runtime `rerank_list`: no `19631`
- Runtime source identity `top_scores`: no `19631`
- `metadata_lookup_hit`: `false`

Top dense candidates are tax and tax-procedure items such as `18937` VUK Genel Tebliği, `KDVK m.36`, several Gelir Vergisi Genel Tebliği rows, and restructuring tebliğ rows. The KDV General Application Communique exists but is below the runtime candidate horizon.

## Root Cause

Primary root cause:

- `kdv_source_present_not_retrieved`

Contributing root causes:

- `kdv_source_title_alias_missing`
- `teblig_identifier_disambiguation_gap`
- `body_materialization_gap`

The source is not missing from the corpus. The problem is that the source is indexed as identifier-only/document-level `19631 m.0`, lacks the canonical KDV title in Milvus metadata, and appears below top-k in raw dense retrieval. The selector therefore has no strong title/alias anchor to promote it for the natural-language query.

## Safe Action

Open a narrow `TEBLIGLER` source identity remediation phase:

- Add KDV General Application Communique aliases and title normalization for source `19631`.
- Preserve the existing runtime top-k policy; do not broaden top-k as a global fix.
- Add a targeted TEB smoke gate for `TEB-04` and adjacent KDV/tebliğ rows.
- Do not apply a QID-specific branch.
- Do not cut over live `8000`.

Productization and fine-tuning remain closed.
