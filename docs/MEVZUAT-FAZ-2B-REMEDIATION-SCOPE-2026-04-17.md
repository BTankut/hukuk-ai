# Mevzuat Faz-2B Remediation Scope 2026-04-17

## Binding Counts
- `problem_core_row_count = 32`
- `sentinel_control_row_count = 24`
- `target_total_row_count = 56`
- `official_human_review_required = true`

## Scope Rules
- `problem_core` yalniz Faz-2 reviewed sonucunda `REVISE` veya `REJECT` donen satirlardan olusur.
- `sentinel_control` yalniz onceden `APPROVE` donen ve regresyon kontrolu icin yeniden acilan satirlardan olusur.
- Bu fazda resmi insan review zorunludur; model adi reviewer olarak kullanilamaz.

## Surface Split
- `problem_core.surface.excluded_source_unsupported_source_refusal = 12`
- `problem_core.surface.yururluk_mulga_temporal_interpretation = 13`
- `problem_core.surface.citation_heavy_exact_locator_long_article = 7`
- `sentinel_control.surface.cross_type_wrong_source_disambiguation = 8`
- `sentinel_control.surface.source_local_direct_retrieval = 8`
- `sentinel_control.surface.citation_heavy_exact_locator_long_article = 8`
