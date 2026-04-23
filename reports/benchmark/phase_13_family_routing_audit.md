# Phase 13 Family Routing Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T124900Z_phase13_full`
- rows_analyzed: 100
- wrong_family: 31
- family_compatibility_incompatible: 6
- family_gate_locked_preferred_family: 75
- family_gate_no_gate: 21
- avg_selected_family_confidence: 0.705
- selector_preferred_family_hit_rate: 0.703
- metadata_lookup_hit_count: 42

## By Expected Family
- CB_GENELGE: total=4, wrong_family_rows=0, locked=4, no_gate=0, preferred_hit=4, avg_conf=0.870
- CB_KARAR: total=8, wrong_family_rows=4, locked=8, no_gate=0, preferred_hit=5, avg_conf=0.875
- CB_KARARNAME: total=6, wrong_family_rows=0, locked=6, no_gate=0, preferred_hit=0, avg_conf=0.823
- CB_YONETMELIK: total=6, wrong_family_rows=2, locked=6, no_gate=0, preferred_hit=0, avg_conf=0.796
- KANUN: total=21, wrong_family_rows=5, locked=8, no_gate=13, preferred_hit=0, avg_conf=0.372
- KHK: total=6, wrong_family_rows=1, locked=6, no_gate=0, preferred_hit=0, avg_conf=0.823
- KKY: total=11, wrong_family_rows=8, locked=7, no_gate=1, preferred_hit=0, avg_conf=0.808
- MULGA: total=5, wrong_family_rows=3, locked=5, no_gate=0, preferred_hit=0, avg_conf=0.846
- TEBLIGLER: total=8, wrong_family_rows=1, locked=6, no_gate=2, preferred_hit=7, avg_conf=0.703
- TUZUK: total=5, wrong_family_rows=1, locked=5, no_gate=0, preferred_hit=0, avg_conf=0.662
- UY: total=10, wrong_family_rows=0, locked=8, no_gate=2, preferred_hit=9, avg_conf=0.804
- YONETMELIK: total=10, wrong_family_rows=6, locked=6, no_gate=3, preferred_hit=1, avg_conf=0.747

## Gate Status Counts
- locked_preferred_family: 75
- no_gate: 21
- global_fallback: 4

## Family Gate Reason Counts
- preferred_family_pool_available: 75
- no_family_prior: 13
- weak_family_prior_cross_family_allowed: 6
- global_fallback: 4
- low_confidence_family_prior: 2

## No Gate Reason Counts
- none: 79
- no_preferred_family_prior: 21

## Worst Rows
- TEB-04: expected=TEBLIGLER, claimed=MULGA, prior=none, gate=no_gate, reason=no_family_prior, selected=teblig, score=0.00
- CBKAR-08: expected=CB_KARAR, claimed=CB_KARARNAME, prior=cb_kararname, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=cb_kararname, score=0.70
- KHK-03: expected=KHK, claimed=CB_KARARNAME, prior=cb_kararname, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=cb_kararname, score=0.70
- MULGA-01: expected=MULGA, claimed=UY, prior=uy, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=uy, score=0.70
- CBKAR-06: expected=CB_KARAR, claimed=CB_GENELGE, prior=cb_genelge, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=cb_genelge, score=1.45
- KANUN-04: expected=KANUN, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=teblig, score=1.45
- KKY-02: expected=KKY, claimed=UY, prior=uy, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=uy, score=1.45
- KKY-09: expected=KKY, claimed=UY, prior=uy, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=uy, score=1.45
- YON-07: expected=YONETMELIK, claimed=UY, prior=uy, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=uy, score=1.79
- CBKAR-04: expected=CB_KARAR, claimed=CB_GENELGE, prior=cb_genelge, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=cb_genelge, score=1.90
- KKY-06: expected=KKY, claimed=UY, prior=uy, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=uy, score=2.12
- MULGA-05: expected=MULGA, claimed=KANUN, prior=kanun, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=kanun, score=3.80
- YON-08: expected=YONETMELIK, claimed=UY, prior=uy, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=uy, score=5.45
- YON-02: expected=YONETMELIK, claimed=KKY, prior=kky, gate=global_fallback, reason=global_fallback, selected=yonetmelik, score=5.75
- YON-05: expected=YONETMELIK, claimed=KANUN, prior=yonetmelik, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=kanun, score=5.75
- KANUN-15: expected=KANUN, claimed=MULGA, prior=none, gate=no_gate, reason=no_family_prior, selected=kanun, score=6.02
- YON-03: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=yonetmelik, score=6.02
- KANUN-03: expected=KANUN, claimed=KKY, prior=none, gate=no_gate, reason=no_family_prior, selected=yonetmelik, score=6.09
- KANUN-05: expected=KANUN, claimed=MULGA, prior=kky, gate=no_gate, reason=low_confidence_family_prior, selected=kanun, score=6.10
- MULGA-02: expected=MULGA, claimed=UY, prior=uy, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=uy, score=6.10
- KKY-01: expected=KKY, claimed=YONETMELIK, prior=yonetmelik, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=yonetmelik, score=6.20
- KKY-05: expected=KKY, claimed=YONETMELIK, prior=yonetmelik, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=yonetmelik, score=6.20
- KKY-08: expected=KKY, claimed=YONETMELIK, prior=yonetmelik, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=yonetmelik, score=6.65
- TUZUK-03: expected=TUZUK, claimed=MULGA, prior=tuzuk, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=tuzuk, score=6.78
- CBY-01: expected=CB_YONETMELIK, claimed=YONETMELIK, prior=yonetmelik, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=yonetmelik, score=6.85
- KKY-04: expected=KKY, claimed=KHK, prior=kky, gate=global_fallback, reason=global_fallback, selected=yonetmelik, score=6.85
- YON-10: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=yonetmelik, score=6.85
- KANUN-10: expected=KANUN, claimed=MULGA, prior=none, gate=no_gate, reason=no_family_prior, selected=kanun, score=7.12
- CBKAR-05: expected=CB_KARAR, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=teblig, score=7.19
- CBY-04: expected=CB_YONETMELIK, claimed=CB_KARARNAME, prior=cb_kararname, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=cb_kararname, score=7.66
- KKY-11: expected=KKY, claimed=YONETMELIK, prior=yonetmelik, gate=locked_preferred_family, reason=preferred_family_pool_available, selected=yonetmelik, score=7.86
