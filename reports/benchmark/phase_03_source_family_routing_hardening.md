# Phase 3 Source-Family Routing Hardening

- commit_scope: `family routing and source resolver hardening`
- runtime_component: `api-gateway/src/source_family_resolver.py`
- behavior_change: source-family prior is now resolved before dense retrieval and written to trace.

## Systemic Resolver Signals

- Explicit kanun/madde signals route to `kanun` without increasing top-k for ordinary law lookups.
- `Karar Sayısı`, `Karar No`, `Cumhurbaşkanı Kararı` route to `cb_karar`.
- `Cumhurbaşkanlığı Kararnamesi` and `Kararname Numarası` route to `cb_kararname`.
- `Genelge` and `Cumhurbaşkanlığı Genelgesi` route to `cb_genelge`.
- `Cumhurbaşkanlığı Yönetmeliği` routes to `cb_yonetmelik`.
- University/student/lisansüstü/yatay geçiş signals route to `uy` plus `yonetmelik`.
- Agency/board/ministry signals route to `kky` plus `yonetmelik`.
- `Mülga`, `yürürlükten kaldır`, and historical-source signals route to `mulga_kanun` plus controlled active-law fallback.

## Trace Contract

Runtime traces now expose the resolver output in both `parsed_query` and `query_signals`:

- `predicted_family`
- `family_confidence`
- `family_candidates`
- `source_family_resolution.routing_families`
- `source_family_resolution.query_expansions`

The retrieval block also carries `source_family_resolution` so benchmark forensics can compare predicted family, candidate families, and selected evidence.

## Guardrails Against Question-Specific Tuning

- The resolver contains no QID, benchmark-row, or individual question text rules.
- Routing is based on document-type, institution namespace, temporal state, and explicit law/article signals only.
- Weak-family top-k expansion is limited to non-primary-law families; normal `KANUN` exact-reference lookups keep the prior top-k behavior.

## Live Smoke Verification

- `Karar Sayısı: 3350 olan İthalat Rejimi Kararı hangi belge ailesindedir?`
- result: `predicted_family=cb_karar`, `family_confidence=0.86`, `routing_families=["cb_karar"]`, `top_k_effective=24`, first retrieved family `cb_karar`.
- `TBK m.49 nedir?`
- result: `predicted_family=kanun`, `family_confidence=0.86`, `routing_families=[]`, `top_k_effective=20`.
