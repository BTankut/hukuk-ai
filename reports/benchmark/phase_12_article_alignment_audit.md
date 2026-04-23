# Phase 8 Article Alignment Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T065717Z_phase12_full`
- rows: 100
- selected_article_equals_claimed_article: 65/100

## Article Alignment Distribution
- exact: 54
- neighbor: 5
- title_only: 15
- clause_only: 0
- none: 25
- unknown: 1

## Query Article Alignment Distribution
- exact: 0
- neighbor: 0
- title_only: 14
- clause_only: 0
- none: 0
- unknown: 86

## Audit Buckets
- clearly_wrong: 25
- exact: 54
- neighbor: 5
- title_only_or_weak: 16

## wrong_article by Article Alignment
- exact: 3

## 20-QID Mini Audit
- TUZUK-01: bucket=exact; alignment=exact; selected=7; claimed=madde:7; wrong_article=false; note=selected evidence article and claimed article match
- KHK-01: bucket=exact; alignment=exact; selected=2; claimed=madde:2; wrong_article=false; note=selected evidence article and claimed article match
- TEB-06: bucket=exact; alignment=exact; selected=1; claimed=madde:1; wrong_article=false; note=selected evidence article and claimed article match
- KKY-11: bucket=exact; alignment=exact; selected=22; claimed=madde:22; wrong_article=false; note=selected evidence article and claimed article match
- CBK-05: bucket=exact; alignment=exact; selected=3; claimed=madde:3; wrong_article=false; note=selected evidence article and claimed article match
- KANUN-14: bucket=neighbor; alignment=neighbor; selected=10; claimed=madde:11; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KKY-08: bucket=neighbor; alignment=neighbor; selected=8; claimed=madde:7; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KKY-01: bucket=neighbor; alignment=neighbor; selected=3; claimed=madde:4; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- YON-10: bucket=neighbor; alignment=neighbor; selected=6; claimed=madde:5; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- YON-06: bucket=neighbor; alignment=neighbor; selected=6; claimed=madde:7; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- CBY-05: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:1; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- KANUN-02: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-04: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- TEB-04: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:3; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- UY-07: bucket=title_only_or_weak; alignment=unknown; selected=none; claimed=none; wrong_article=false; note=no comparable selected/claimed article signal
- CBG-03: bucket=clearly_wrong; alignment=none; selected=3; claimed=madde:1; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- KKY-03: bucket=clearly_wrong; alignment=none; selected=3; claimed=madde:20; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- KKY-10: bucket=clearly_wrong; alignment=none; selected=4; claimed=madde:14; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- TUZUK-04: bucket=clearly_wrong; alignment=none; selected=6; claimed=madde:18; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- YON-08: bucket=clearly_wrong; alignment=none; selected=27; claimed=madde:14; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
