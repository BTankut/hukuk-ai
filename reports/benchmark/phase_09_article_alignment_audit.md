# Phase 8 Article Alignment Audit

- source_run_dir: `reports/benchmark/runs/20260422T153521Z_phase9_full`
- rows: 100
- selected_article_equals_claimed_article: 75/100

## Article Alignment Distribution
- exact: 62
- neighbor: 4
- title_only: 13
- clause_only: 0
- none: 21
- unknown: 0

## Query Article Alignment Distribution
- exact: 0
- neighbor: 0
- title_only: 13
- clause_only: 0
- none: 0
- unknown: 87

## Audit Buckets
- clearly_wrong: 21
- exact: 62
- neighbor: 4
- title_only_or_weak: 13

## wrong_article by Article Alignment
- exact: 3

## 20-QID Mini Audit
- TUZUK-01: bucket=exact; alignment=exact; selected=7; claimed=madde:7; wrong_article=false; note=selected evidence article and claimed article match
- KHK-01: bucket=exact; alignment=exact; selected=2; claimed=madde:2; wrong_article=false; note=selected evidence article and claimed article match
- KKY-11: bucket=exact; alignment=exact; selected=22; claimed=madde:22; wrong_article=false; note=selected evidence article and claimed article match
- KKY-09: bucket=exact; alignment=exact; selected=5; claimed=madde:5; wrong_article=false; note=selected evidence article and claimed article match
- KANUN-12: bucket=exact; alignment=exact; selected=6; claimed=madde:6; wrong_article=false; note=selected evidence article and claimed article match
- KKY-07: bucket=neighbor; alignment=neighbor; selected=49; claimed=madde:48; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- UY-09: bucket=neighbor; alignment=neighbor; selected=33; claimed=madde:32; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KANUN-19: bucket=neighbor; alignment=neighbor; selected=4; claimed=madde:5; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KKY-02: bucket=neighbor; alignment=neighbor; selected=4; claimed=madde:3; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- CBY-05: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-04: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- TEB-04: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-01: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-02: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- KKY-10: bucket=clearly_wrong; alignment=none; selected=4; claimed=madde:14; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- TUZUK-04: bucket=clearly_wrong; alignment=none; selected=6; claimed=madde:3; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- KANUN-02: bucket=clearly_wrong; alignment=none; selected=8; claimed=madde:13; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- YON-03: bucket=clearly_wrong; alignment=none; selected=12; claimed=madde:7; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- UY-08: bucket=clearly_wrong; alignment=none; selected=14; claimed=madde:4; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
