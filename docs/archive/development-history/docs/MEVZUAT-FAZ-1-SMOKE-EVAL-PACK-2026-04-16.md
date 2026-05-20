# Mevzuat Faz-1 Smoke Eval Pack 2026-04-16

## Pack Boundary
- `old_eval_reused = false`
- `query_mode = exact citation technical smoke`
- `default_retrieval_filter = mulga = false`

| case_id | belge_turu | query_text | expected_source_id | expected_display_citation | expected_behavior |
| --- | --- | --- | --- | --- | --- |
| `KANUN-A` | `kanun` | `3224 m.1` | `3224:3224:m1:f0:from1985-06-25:to9999-12-31` | `3224 m.1` | `exact-article-retrieval` |
| `YONETMELIK-A` | `yonetmelik` | `8913838 m.1` | `8913838:8913838:m1:f0:from1989-03-15:to9999-12-31` | `8913838 m.1` | `exact-article-retrieval` |
| `CBK-A` | `cb_kararname` | `126 m.1` | `126:126:m1:f0:from2023-02-24:to9999-12-31` | `126 m.1` | `exact-article-retrieval` |
| `CB-YONETMELIK-A` | `cb_yonetmelik` | `9128 m.1` | `9128:9128:m1:f0:from2024-11-14:to9999-12-31` | `9128 m.1` | `exact-article-retrieval` |
| `MULGA-A` | `mulga_kanun` | `7354 m.2` | `7354:7354:m2:f0:from2022-02-14:to1900-01-01` | `7354 m.2` | `mulga-hidden-under-default-filter` |
| `TEBLIG-A` | `teblig` | `24653 m.1` | `24653:24653:m1:f0:from2018-06-07:to9999-12-31` | `24653 m.1` | `exact-article-retrieval` |
