# Phase 8 Article Alignment Audit

- source_run_dir: `reports/benchmark/runs/20260422T101818Z_phase8a_semantics`
- rows: 100
- selected_article_equals_claimed_article: 34/100

## Article Alignment Distribution
- exact: 27
- neighbor: 9
- title_only: 16
- clause_only: 0
- none: 48
- unknown: 0

## Query Article Alignment Distribution
- exact: 0
- neighbor: 0
- title_only: 0
- clause_only: 0
- none: 0
- unknown: 100

## Audit Buckets
- clearly_wrong: 48
- exact: 27
- neighbor: 9
- title_only_or_weak: 16

## wrong_article by Article Alignment
- exact: 1
- none: 2

## 20-QID Mini Audit
- KKY-11: bucket=exact; alignment=exact; selected=22; claimed=madde:22; wrong_article=false; note=selected evidence article and claimed article match
- KANUN-12: bucket=exact; alignment=exact; selected=6; claimed=madde:6; wrong_article=false; note=selected evidence article and claimed article match
- UY-01: bucket=exact; alignment=exact; selected=25; claimed=madde:25; wrong_article=false; note=selected evidence article and claimed article match
- CBKAR-06: bucket=exact; alignment=exact; selected=2; claimed=madde:2; wrong_article=false; note=selected evidence article and claimed article match
- UY-03: bucket=exact; alignment=exact; selected=9; claimed=madde:9; wrong_article=false; note=selected evidence article and claimed article match
- KHK-01: bucket=neighbor; alignment=neighbor; selected=2; claimed=madde:1; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KANUN-17: bucket=neighbor; alignment=neighbor; selected=290; claimed=madde:289; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- KANUN-08: bucket=neighbor; alignment=neighbor; selected=14; claimed=madde:13; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- CBKAR-02: bucket=neighbor; alignment=neighbor; selected=17; claimed=madde:18; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- CBKAR-03: bucket=neighbor; alignment=neighbor; selected=9; claimed=madde:10; wrong_article=false; note=selected evidence is adjacent to the claimed article; treat as neighbor support
- CBY-05: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:1; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-04: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- TEB-04: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:3; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-01: bucket=title_only_or_weak; alignment=title_only; selected=7; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- CBG-02: bucket=title_only_or_weak; alignment=title_only; selected=0; claimed=madde:0; wrong_article=false; note=article identity is title-level or article 0; not exact span support
- MULGA-04: bucket=clearly_wrong; alignment=none; selected=174; claimed=madde:103; wrong_article=false; note=selected evidence article and claimed article diverge
- UY-07: bucket=clearly_wrong; alignment=none; selected=9; claimed=madde:15; wrong_article=false; note=selected evidence article and claimed article diverge
- KANUN-02: bucket=clearly_wrong; alignment=none; selected=14; claimed=madde:398; wrong_article=false; note=selected evidence article and claimed article diverge
- KANUN-06: bucket=clearly_wrong; alignment=none; selected=511; claimed=madde:23; wrong_article=false; note=selected evidence article and claimed article diverge
- KKY-02: bucket=clearly_wrong; alignment=none; selected=4; claimed=madde:6; wrong_article=false; note=selected evidence article and claimed article diverge
