# FAZ 4 Primary Source Anchor Delta

Tarih: 2026-03-23

Referans:
- [faz4-primary-source-anchor-v1-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz4-primary-source-anchor-v1-spec-2026-03-23.md)
- [faz4-citation-family-failure-pack-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz4-citation-family-failure-pack-rerun-2026-03-23.md)

## Ozet

Primary source anchor v1, `primary_source_id` secimini planner sirasina gore deterministic hale getirdi:

1. `supported_claim_count desc`
2. `single_law_high_conf + single_article` tie-break
3. `retrieval_rank asc`
4. `source_id asc`

## Delta

- `wrong_primary_source_with_supported_answer`: `41 -> 43`
- delta: `+2`

## Yorum

- deterministic primary-source secimi kuruldu
- ancak benchmark beklenen primary ile tam hizalanma toparlanmadi
- bu nedenle `WP-4` teknik olarak uygulanmis olsa da kabul etkisi `FAIL` oldu

