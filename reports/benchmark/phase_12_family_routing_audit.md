# Phase 12 Family Routing Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T065717Z_phase12_full`
- rows_analyzed: 100
- wrong_family: 35
- family_compatibility_incompatible: 3
- family_gate_locked_preferred_family: 63
- family_gate_no_gate: 35
- avg_selected_family_confidence: 0.682
- selector_preferred_family_hit_rate: 0.825
- metadata_lookup_hit_count: 54

## By Expected Family
- CB_GENELGE: total=4, wrong_family_rows=1, locked=4, no_gate=0, preferred_hit=3, avg_conf=0.860
- CB_KARAR: total=8, wrong_family_rows=2, locked=8, no_gate=0, preferred_hit=4, avg_conf=0.897
- CB_KARARNAME: total=6, wrong_family_rows=0, locked=5, no_gate=1, preferred_hit=0, avg_conf=0.823
- CB_YONETMELIK: total=6, wrong_family_rows=4, locked=2, no_gate=3, preferred_hit=1, avg_conf=0.677
- KANUN: total=21, wrong_family_rows=8, locked=5, no_gate=16, preferred_hit=1, avg_conf=0.247
- KHK: total=6, wrong_family_rows=1, locked=6, no_gate=0, preferred_hit=0, avg_conf=0.882
- KKY: total=11, wrong_family_rows=4, locked=10, no_gate=1, preferred_hit=5, avg_conf=0.908
- MULGA: total=5, wrong_family_rows=4, locked=3, no_gate=2, preferred_hit=0, avg_conf=0.542
- TEBLIGLER: total=8, wrong_family_rows=0, locked=8, no_gate=0, preferred_hit=8, avg_conf=0.860
- TUZUK: total=5, wrong_family_rows=1, locked=0, no_gate=5, preferred_hit=0, avg_conf=0.662
- UY: total=10, wrong_family_rows=0, locked=9, no_gate=0, preferred_hit=9, avg_conf=0.881
- YONETMELIK: total=10, wrong_family_rows=10, locked=3, no_gate=7, preferred_hit=2, avg_conf=0.644

## Gate Status Counts
- global_fallback: 1
- hard_gate_no_preferred_candidates: 1
- locked_preferred_family: 63
- no_gate: 35

## Family Gate Reason Counts
- global_fallback: 1
- hard_family_gate_no_preferred_candidates: 1
- low_confidence_family_prior: 2
- no_family_prior: 17
- preferred_family_pool_available: 63
- weak_family_prior_cross_family_allowed: 16

## Worst Rows
- KANUN-01: expected=KANUN, claimed=TEBLIGLER, prior=, gate=no_gate, reason=no_family_prior, selected=kanun, score=0.00
- MULGA-03: expected=MULGA, claimed=TUZUK, prior=, gate=no_gate, reason=no_family_prior, selected=tuzuk, score=0.00
- MULGA-04: expected=MULGA, claimed=KHK, prior=khk, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=khk, score=0.00
- CBG-03: expected=CB_GENELGE, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=teblig, score=1.45
- CBY-05: expected=CB_YONETMELIK, claimed=CB_GENELGE, prior=cb_genelge, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=cb_genelge, score=1.45
- KANUN-02: expected=KANUN, claimed=CB_KARAR, prior=cb_karar, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=cb_karar, score=1.45
- KANUN-06: expected=KANUN, claimed=MULGA, prior=, gate=no_gate, reason=no_family_prior, selected=mulga_kanun, score=1.45
- KKY-02: expected=KKY, claimed=UY, prior=uy, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=uy, score=1.45
- YON-02: expected=YONETMELIK, claimed=CB_YONETMELIK, prior=kky, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=cb_yonetmelik, score=1.45
- YON-06: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=yonetmelik, score=1.45
- MULGA-01: expected=MULGA, claimed=KKY, prior=kky, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=kky, score=4.17
- TUZUK-04: expected=TUZUK, claimed=UY, prior=tuzuk, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=uy, score=4.63
- CBKAR-01: expected=CB_KARAR, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=teblig, score=5.00
- KHK-03: expected=KHK, claimed=CB_KARARNAME, prior=cb_kararname, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=cb_kararname, score=5.00
- YON-08: expected=YONETMELIK, claimed=UY, prior=uy, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=uy, score=5.00
- KANUN-03: expected=KANUN, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=teblig, score=5.75
- KANUN-04: expected=KANUN, claimed=KKY, prior=, gate=no_gate, reason=no_family_prior, selected=kky, score=5.75
- YON-01: expected=YONETMELIK, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=teblig, score=5.75
- YON-03: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=kky, score=5.75
- YON-05: expected=YONETMELIK, claimed=KANUN, prior=yonetmelik, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=kanun, score=5.75
- YON-09: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=kky, score=5.75
- YON-10: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=yonetmelik, score=5.75
- CBY-06: expected=CB_YONETMELIK, claimed=KANUN, prior=, gate=no_gate, reason=no_family_prior, selected=kanun, score=6.10
- MULGA-02: expected=MULGA, claimed=KKY, prior=kky, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=kky, score=6.10
- KKY-09: expected=KKY, claimed=UY, prior=uy, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=uy, score=6.43
- KANUN-19: expected=KANUN, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=teblig, score=6.65
- CBY-01: expected=CB_YONETMELIK, claimed=KKY, prior=kky, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=kky, score=6.85
- KANUN-13: expected=KANUN, claimed=KKY, prior=, gate=no_gate, reason=no_family_prior, selected=kky, score=6.85
- KANUN-15: expected=KANUN, claimed=KKY, prior=, gate=no_gate, reason=no_family_prior, selected=teblig, score=6.85
- KKY-04: expected=KKY, claimed=KANUN, prior=kanun, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=kanun, score=6.85
- YON-04: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=yonetmelik, score=6.85
- CBY-04: expected=CB_YONETMELIK, claimed=CB_KARARNAME, prior=cb_kararname, gate=no_gate, reason=weak_family_prior_cross_family_allowed, selected=cb_kararname, score=7.12
- CBKAR-05: expected=CB_KARAR, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=teblig, score=7.19
- KKY-06: expected=KKY, claimed=UY, prior=uy, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=uy, score=7.53
- YON-07: expected=YONETMELIK, claimed=KKY, prior=kky, gate=locked_preferred_family, reason=strong_preferred_family_pool, selected=kky, score=7.53
