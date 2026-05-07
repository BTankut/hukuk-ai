# Phase 24HT-A KANUN-08 Same-Family Candidate Audit

## Scope

Input run: `reports/benchmark/runs/phase_24HS_focused_non_live_candidate_smoke_final_v6`.

Target row: `KANUN-08`.

Question: internetten kişiye özel ölçüye göre üretilen mobilyada 14 günlük cayma hakkı ve kişiye özel üretim istisnası.

## Findings

- Phase24HS selected `TÜRK BORÇLAR KANUNU / TBK m.255`.
- Source identity reranker did not prefer TBK. It ranked `TÜKETİCİNİN KORUNMASI HAKKINDA KANUN / TKHK m.18` first with document identity score `59.9158`.
- The same TKHK document also appeared at rank 2 via `TKHK m.43` with score `59.9087`.
- TBK candidates were ranks 3-10 in source identity with scores around `17.88`.
- Article selector then re-locked to TBK because selected-source lock gave TBK candidates `selected_source_match=True`, `+55`, plus local support bonus, while TKHK had `selected_source_match=False`.
- This is not a dense recall absence. The domain-specific KANUN candidate is already in the pool and is already top-ranked by source identity.

## Answers To Required Questions

- Why did TBK m.255 win? Because article span selector applied `selected_source_lock` to `tbk m.1`; this made TBK article-level scores `104-132`, while TKHK stayed around `53-56`.
- Is expected/domain-specific KANUN in the pool? Yes. `TKHK m.18` is source-identity rank 1; `TKHK m.43` is rank 2.
- Is this a metadata/dense retrieval miss? No for the KANUN document. TKHK came from both `metadata_guided_recall` and `semantic_dense_recall`.
- Is this same-family domain compatibility? Yes. A generic/private-law KANUN source was allowed to override a stronger consumer-law KANUN source after source identity had already identified the domain source.

## Safe Systemic Fix

A safe fix exists: when no explicit law/article identifier appears in the user query, and source identity has a strong same-family dual-lane document signal, article selector should allow that document identity to override a weaker selected-source lock.

This remains systemic because it uses only query/source metadata and trace scores. It does not use `KANUN-08`, answer key content, or hardcoded expected titles.

Detailed candidate rows: `reports/benchmark/phase_24HT_A_kanun08_same_family_candidate_audit.csv`.
