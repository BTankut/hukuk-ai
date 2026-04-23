# Phase 8 Article Alignment Audit

- source_run_dir: `reports/benchmark/runs/20260423T124900Z_phase13_full`
- rows: 100
- selected_article_equals_claimed_article: 55/100

## Article Alignment Distribution
- exact: 45
- neighbor: 5
- title_only: 16
- clause_only: 0
- none: 34
- unknown: 0

## Query Article Alignment Distribution
- exact: 0
- neighbor: 0
- title_only: 14
- clause_only: 0
- none: 0
- unknown: 86

## Audit Buckets
- clearly_wrong: 34
- exact: 45
- neighbor: 5
- title_only_or_weak: 16

## wrong_article by Article Alignment
- exact: 1
- none: 1

## 20-QID Mini Audit
- UY-01: bucket=exact; alignment=exact; selected=25; claimed=madde:25; wrong_article=false; note=selected evidence article and claimed article match
- TUZUK-01: bucket=exact; alignment=exact; selected=7; claimed=madde:7; wrong_article=false; note=selected evidence article and claimed article match
- KHK-05: bucket=exact; alignment=exact; selected=25; claimed=madde:25; wrong_article=false; note=selected evidence article and claimed article match
- TUZUK-02: bucket=exact; alignment=exact; selected=12; claimed=madde:12; wrong_article=false; note=selected evidence article and claimed article match
- TEB-07: bucket=exact; alignment=exact; selected=11; claimed=madde:11; wrong_article=false; note=selected evidence article and claimed article match
- KANUN-12: bucket=neighbor; alignment=neighbor; selected=2; claimed=madde:3; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- CBKAR-03: bucket=neighbor; alignment=neighbor; selected=9; claimed=madde:10; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KANUN-03: bucket=neighbor; alignment=neighbor; selected=3; claimed=madde:4; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- YON-02: bucket=neighbor; alignment=neighbor; selected=5; claimed=madde:6; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KKY-09: bucket=neighbor; alignment=neighbor; selected=9; claimed=madde:8; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- TEB-04: bucket=title_only_or_weak; alignment=title_only; selected=60; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBKAR-08: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:4; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBKAR-06: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- KKY-02: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBKAR-04: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- MULGA-01: bucket=clearly_wrong; alignment=none; selected=31; claimed=madde:24; wrong_article=true; note=scorer also marks wrong_article against gold
- YON-07: bucket=clearly_wrong; alignment=none; selected=2; claimed=madde:9; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- CBY-03: bucket=clearly_wrong; alignment=none; selected=8; claimed=madde:18; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- TEB-06: bucket=clearly_wrong; alignment=none; selected=11; claimed=madde:9; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- YON-08: bucket=clearly_wrong; alignment=none; selected=21; claimed=madde:10; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
