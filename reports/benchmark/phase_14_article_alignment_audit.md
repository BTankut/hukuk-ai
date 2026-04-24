# Phase 8 Article Alignment Audit

- source_run_dir: `reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic`
- rows: 100
- selected_article_equals_claimed_article: 80/100

## Article Alignment Distribution
- exact: 70
- neighbor: 2
- title_only: 12
- clause_only: 0
- none: 16
- unknown: 0

## Query Article Alignment Distribution
- exact: 0
- neighbor: 0
- title_only: 12
- clause_only: 0
- none: 0
- unknown: 88

## Audit Buckets
- clearly_wrong: 16
- exact: 70
- neighbor: 2
- title_only_or_weak: 12

## wrong_article by Article Alignment
- exact: 2

## 20-QID Mini Audit
- KKY-11: bucket=exact; alignment=exact; selected=22; claimed=madde:22; wrong_article=false; note=selected evidence article and claimed article match
- KKY-09: bucket=exact; alignment=exact; selected=2; claimed=madde:2; wrong_article=false; note=selected evidence article and claimed article match
- TEB-08: bucket=exact; alignment=exact; selected=1; claimed=madde:1; wrong_article=false; note=selected evidence article and claimed article match
- KKY-08: bucket=exact; alignment=exact; selected=5; claimed=madde:5; wrong_article=false; note=selected evidence article and claimed article match
- KKY-02: bucket=exact; alignment=exact; selected=1; claimed=madde:1; wrong_article=false; note=selected evidence article and claimed article match
- UY-10: bucket=neighbor; alignment=neighbor; selected=5; claimed=madde:6; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KANUN-03: bucket=neighbor; alignment=neighbor; selected=3; claimed=madde:4; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- CBG-04: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- TEB-01: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-01: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-02: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-03: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- YON-08: bucket=clearly_wrong; alignment=none; selected=21; claimed=madde:10; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- KANUN-19: bucket=clearly_wrong; alignment=none; selected=60; claimed=madde:1; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- KKY-01: bucket=clearly_wrong; alignment=none; selected=4; claimed=madde:29; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- KANUN-06: bucket=clearly_wrong; alignment=none; selected=511; claimed=madde:587; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- CBKAR-05: bucket=clearly_wrong; alignment=none; selected=8; claimed=madde:1; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
