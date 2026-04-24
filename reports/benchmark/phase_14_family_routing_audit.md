# Phase 14 Family Routing Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic`
- rows_analyzed: 100
- wrong_family: 15
- family_compatibility_incompatible: 5
- family_gate_locked_preferred_family: 73
- family_gate_no_gate: 22
- avg_selected_family_confidence: 0.706
- selector_preferred_family_hit_rate: 0.703

## By Expected Family
- CB_GENELGE: total=4, wrong_family_rows=0, locked=4, no_gate=0, avg_score=3.062
- CB_KARAR: total=8, wrong_family_rows=1, locked=8, no_gate=0, avg_score=7.961
- CB_KARARNAME: total=6, wrong_family_rows=0, locked=6, no_gate=0, avg_score=9.050
- CB_YONETMELIK: total=6, wrong_family_rows=2, locked=6, no_gate=0, avg_score=7.775
- KANUN: total=21, wrong_family_rows=2, locked=8, no_gate=13, avg_score=7.189
- KHK: total=6, wrong_family_rows=0, locked=6, no_gate=0, avg_score=8.745
- KKY: total=11, wrong_family_rows=2, locked=6, no_gate=1, avg_score=8.438
- MULGA: total=5, wrong_family_rows=5, locked=5, no_gate=0, avg_score=2.120
- TEBLIGLER: total=8, wrong_family_rows=0, locked=6, no_gate=2, avg_score=6.776
- TUZUK: total=5, wrong_family_rows=0, locked=5, no_gate=0, avg_score=6.154
- UY: total=10, wrong_family_rows=0, locked=7, no_gate=3, avg_score=9.162
- YONETMELIK: total=10, wrong_family_rows=3, locked=6, no_gate=3, avg_score=6.898

## Gate Status Counts
- locked_preferred_family: 73
- no_gate: 22
- global_fallback: 5

## Family Gate Reason Counts
- preferred_family_pool_available: 73
- no_family_prior: 13
- weak_family_prior_cross_family_allowed: 7
- global_fallback: 5
- low_confidence_family_prior: 2

## No Gate Reason Counts
- none: 78
- no_preferred_family_prior: 22

## Worst Rows
- MULGA-02: expected=MULGA, claimed=YONETMELIK, prior=yonetmelik, gate=locked_preferred_family, reason=preferred_family_pool_available, score=0.00
- MULGA-03: expected=MULGA, claimed=TUZUK, prior=tuzuk, gate=locked_preferred_family, reason=preferred_family_pool_available, score=0.00
- KANUN-04: expected=KANUN, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=preferred_family_pool_available, score=1.45
- MULGA-04: expected=MULGA, claimed=KHK, prior=khk, gate=locked_preferred_family, reason=preferred_family_pool_available, score=1.45
- CBG-04: expected=CB_GENELGE, claimed=CB_GENELGE, prior=cb_genelge, gate=locked_preferred_family, reason=preferred_family_pool_available, score=2.50
- TUZUK-04: expected=TUZUK, claimed=TUZUK, prior=tuzuk, gate=locked_preferred_family, reason=preferred_family_pool_available, score=2.50
- TEB-01: expected=TEBLIGLER, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=preferred_family_pool_available, score=2.95
- CBG-01: expected=CB_GENELGE, claimed=CB_GENELGE, prior=cb_genelge, gate=locked_preferred_family, reason=preferred_family_pool_available, score=3.25
- CBG-02: expected=CB_GENELGE, claimed=CB_GENELGE, prior=cb_genelge, gate=locked_preferred_family, reason=preferred_family_pool_available, score=3.25
- CBG-03: expected=CB_GENELGE, claimed=CB_GENELGE, prior=cb_genelge, gate=locked_preferred_family, reason=preferred_family_pool_available, score=3.25
- KANUN-18: expected=KANUN, claimed=KANUN, prior=none, gate=no_gate, reason=no_family_prior, score=3.25
- TEB-06: expected=TEBLIGLER, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=preferred_family_pool_available, score=3.25
- TUZUK-05: expected=TUZUK, claimed=TUZUK, prior=tuzuk, gate=locked_preferred_family, reason=preferred_family_pool_available, score=3.25
- KANUN-02: expected=KANUN, claimed=KANUN, prior=none, gate=no_gate, reason=no_family_prior, score=3.59
- YON-06: expected=YONETMELIK, claimed=YONETMELIK, prior=yonetmelik, gate=locked_preferred_family, reason=preferred_family_pool_available, score=3.59
- MULGA-05: expected=MULGA, claimed=KANUN, prior=kanun, gate=locked_preferred_family, reason=preferred_family_pool_available, score=4.25
- MULGA-01: expected=MULGA, claimed=UY, prior=uy, gate=locked_preferred_family, reason=preferred_family_pool_available, score=4.90
- YON-08: expected=YONETMELIK, claimed=UY, prior=uy, gate=locked_preferred_family, reason=preferred_family_pool_available, score=5.45
- CBY-04: expected=CB_YONETMELIK, claimed=CB_KARARNAME, prior=cb_kararname, gate=locked_preferred_family, reason=preferred_family_pool_available, score=5.75
- YON-05: expected=YONETMELIK, claimed=KANUN, prior=yonetmelik, gate=no_gate, reason=weak_family_prior_cross_family_allowed, score=5.75
- KANUN-15: expected=KANUN, claimed=KANUN, prior=none, gate=no_gate, reason=no_family_prior, score=6.05
- KANUN-19: expected=KANUN, claimed=KANUN, prior=kanun, gate=locked_preferred_family, reason=preferred_family_pool_available, score=6.05
- KANUN-03: expected=KANUN, claimed=YONETMELIK, prior=none, gate=no_gate, reason=no_family_prior, score=6.09
- KKY-01: expected=KKY, claimed=YONETMELIK, prior=yonetmelik, gate=locked_preferred_family, reason=preferred_family_pool_available, score=6.20
- CBKAR-03: expected=CB_KARAR, claimed=CB_KARAR, prior=cb_karar, gate=locked_preferred_family, reason=preferred_family_pool_available, score=6.80
- CBKAR-08: expected=CB_KARAR, claimed=CB_KARAR, prior=cb_karar, gate=locked_preferred_family, reason=preferred_family_pool_available, score=6.80
- CBY-06: expected=CB_YONETMELIK, claimed=CB_YONETMELIK, prior=cb_yonetmelik, gate=locked_preferred_family, reason=preferred_family_pool_available, score=6.80
- TUZUK-03: expected=TUZUK, claimed=TUZUK, prior=tuzuk, gate=locked_preferred_family, reason=preferred_family_pool_available, score=6.80
- KKY-04: expected=KKY, claimed=KHK, prior=kky, gate=global_fallback, reason=global_fallback, score=6.85
- YON-02: expected=YONETMELIK, claimed=KANUN, prior=kky, gate=global_fallback, reason=global_fallback, score=6.85
- KANUN-06: expected=KANUN, claimed=KANUN, prior=kanun, gate=locked_preferred_family, reason=preferred_family_pool_available, score=7.15
- TEB-03: expected=TEBLIGLER, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=preferred_family_pool_available, score=7.15
- CBKAR-05: expected=CB_KARAR, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=preferred_family_pool_available, score=7.19
- CBKAR-02: expected=CB_KARAR, claimed=CB_KARAR, prior=cb_karar, gate=locked_preferred_family, reason=preferred_family_pool_available, score=7.25
- KHK-03: expected=KHK, claimed=KHK, prior=khk, gate=locked_preferred_family, reason=preferred_family_pool_available, score=7.25
