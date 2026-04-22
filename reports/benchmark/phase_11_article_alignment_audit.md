# Phase 8 Article Alignment Audit

- source_run_dir: `reports/benchmark/runs/20260422T204628Z_phase11_full`
- rows: 100
- selected_article_equals_claimed_article: 63/100

## Article Alignment Distribution
- exact: 53
- neighbor: 5
- title_only: 14
- clause_only: 0
- none: 28
- unknown: 0

## Query Article Alignment Distribution
- exact: 0
- neighbor: 0
- title_only: 13
- clause_only: 0
- none: 0
- unknown: 87

## Audit Buckets
- clearly_wrong: 28
- exact: 53
- neighbor: 5
- title_only_or_weak: 14

## wrong_article by Article Alignment
- exact: 2
- none: 1

## 20-QID Mini Audit
- TUZUK-01: bucket=exact; alignment=exact; selected=7; claimed=madde:7; wrong_article=false; note=selected evidence article and claimed article match
- KHK-01: bucket=exact; alignment=exact; selected=2; claimed=madde:2; wrong_article=false; note=selected evidence article and claimed article match
- TEB-06: bucket=exact; alignment=exact; selected=1; claimed=madde:1; wrong_article=false; note=selected evidence article and claimed article match
- KKY-11: bucket=exact; alignment=exact; selected=22; claimed=madde:22; wrong_article=false; note=selected evidence article and claimed article match
- CBK-05: bucket=exact; alignment=exact; selected=3; claimed=madde:3; wrong_article=false; note=selected evidence article and claimed article match
- KANUN-14: bucket=neighbor; alignment=neighbor; selected=10; claimed=madde:11; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KKY-08: bucket=neighbor; alignment=neighbor; selected=8; claimed=madde:7; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KANUN-19: bucket=neighbor; alignment=neighbor; selected=4; claimed=madde:5; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- YON-10: bucket=neighbor; alignment=neighbor; selected=6; claimed=madde:5; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- YON-06: bucket=neighbor; alignment=neighbor; selected=6; claimed=madde:7; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- CBY-05: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:1; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-04: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- TEB-04: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:3; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-01: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-02: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- UY-07: bucket=clearly_wrong; alignment=none; selected=9; claimed=madde:15; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- KKY-02: bucket=clearly_wrong; alignment=none; selected=4; claimed=madde:1; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- KKY-10: bucket=clearly_wrong; alignment=none; selected=4; claimed=madde:14; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
- MULGA-01: bucket=clearly_wrong; alignment=none; selected=36; claimed=madde:33; wrong_article=true; note=scorer also marks wrong_article against gold
- TUZUK-04: bucket=clearly_wrong; alignment=none; selected=6; claimed=madde:18; wrong_article=false; note=natural-language query had no explicit article; selection and claimed article diverge
