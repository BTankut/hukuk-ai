# Phase 24O-A Source Identity / Selector Audit

Run used for final targeted evidence:

```text
reports/benchmark/runs/phase_24O_targeted_shadow_smoke_20260504T094600Z
```

Candidate runtime:

```text
api_url = http://127.0.0.1:8031/v1
model = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
MILVUS_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24n
EMBEDDING_BACKEND = remote
EMBEDDING_BASE_URL = http://127.0.0.1:8081/v1
```

## Result

The original Phase 24N residual was not raw-source absence. In the final valid Phase 24O candidate run, source identity selection improved materially:

- `KANUN-12`: selected source is `5651`, metadata rank 1, answer score `8.99`, PASS.
- `YON-04`: selected source is KVKK imha regulation supplement / `30224`, metadata rank 1, answer score `8.22`, PASS.
- `KKY-03`: selected document is now `34360`, metadata rank 1, but answer remains `insufficient_grounding` because the selected source identifier is not carried into the final answer contract strongly enough.

## Implemented Systemic Fixes

- Added internet-law domain hints for 5651-style hosting, traffic data, provider and BTK obligation queries.
- Added 5651 source supplement key mapping so `5651` can be materialized without relying only on dense recall.
- Loaded Phase24N official source spans as source supplements, gated by `ENABLE_PHASE24N_SOURCE_SUPPLEMENTS` and overridable via `PHASE24N_SOURCE_SUPPLEMENT_SPANS_PATH`.
- Added title/focus-key source supplement lookup, so old/new source-key splits such as `24038`, `30224`, and `KVKK_IMHA_YONETMELIGI` can converge without QID-specific branching.
- Re-applied selected-source focus after domain-law supporting source prepend to prevent supporting sources from pushing the primary selected source out of the evidence bundle.

## Residual

`KKY-03` is not safe to patch by relabeling `YONETMELIK` as `KKY`. The legal source family remains yönetmelik. The residual is answer-contract/source-identifier materialization for selected `34360 m.11`, not source identity selection.

CSV details:

```text
reports/benchmark/phase_24O_A_source_identity_selector_audit.csv
```
