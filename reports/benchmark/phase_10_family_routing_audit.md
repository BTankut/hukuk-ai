# Phase 10 Family Routing Audit

- source_run_dir: `reports/benchmark/runs/20260422T180225Z_phase10_full`
- rows_analyzed: 100
- wrong_family: 36
- family_compatibility_incompatible: 3
- family_gate_locked_preferred_family: 42
- avg_selected_family_confidence: 0.57
- selector_preferred_family_hit_rate: 0.9

## By Expected Family
- CB_GENELGE: total=4, wrong_family_rows=0, locked=4, preferred_hit=4, avg_conf=0.860
- CB_KARAR: total=8, wrong_family_rows=4, locked=4, preferred_hit=4, avg_conf=0.590
- CB_KARARNAME: total=6, wrong_family_rows=0, locked=5, preferred_hit=0, avg_conf=0.823
- CB_YONETMELIK: total=6, wrong_family_rows=4, locked=1, preferred_hit=1, avg_conf=0.553
- KANUN: total=21, wrong_family_rows=8, locked=2, preferred_hit=1, avg_conf=0.128
- KHK: total=6, wrong_family_rows=1, locked=5, preferred_hit=0, avg_conf=0.823
- KKY: total=11, wrong_family_rows=2, locked=1, preferred_hit=7, avg_conf=0.599
- MULGA: total=5, wrong_family_rows=4, locked=3, preferred_hit=1, avg_conf=0.516
- TEBLIGLER: total=8, wrong_family_rows=0, locked=8, preferred_hit=8, avg_conf=0.860
- TUZUK: total=5, wrong_family_rows=1, locked=0, preferred_hit=0, avg_conf=0.662
- UY: total=10, wrong_family_rows=2, locked=7, preferred_hit=8, avg_conf=0.757
- YONETMELIK: total=10, wrong_family_rows=10, locked=2, preferred_hit=2, avg_conf=0.600

## Gate Status Counts
- locked_preferred_family: 42
- no_gate: 58

## Family Override Reason Counts
- low_confidence_family_prior: 2
- no_family_prior: 22
- strong_preferred_family_pool: 42
- weak_family_prior_cross_family_allowed: 34

## Worst Rows
- CBKAR-01: expected=CB_KARAR, claimed=TEBLIGLER, prior=, gate=no_gate, selected=kanun, score=5.00
- CBKAR-04: expected=CB_KARAR, claimed=CB_YONETMELIK, prior=cb_genelge, gate=no_gate, selected=cb_yonetmelik, score=1.45
- CBKAR-05: expected=CB_KARAR, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, selected=teblig, score=7.19
- CBKAR-08: expected=CB_KARAR, claimed=MULGA, prior=, gate=no_gate, selected=mulga_kanun, score=5.00
- CBY-01: expected=CB_YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, selected=kky, score=6.85
- CBY-04: expected=CB_YONETMELIK, claimed=CB_KARARNAME, prior=cb_kararname, gate=no_gate, selected=cb_kararname, score=7.12
- CBY-05: expected=CB_YONETMELIK, claimed=CB_GENELGE, prior=cb_genelge, gate=no_gate, selected=cb_genelge, score=1.45
- CBY-06: expected=CB_YONETMELIK, claimed=KANUN, prior=, gate=no_gate, selected=kanun, score=6.10
- KANUN-01: expected=KANUN, claimed=TEBLIGLER, prior=, gate=no_gate, selected=kanun, score=0.00
- KANUN-02: expected=KANUN, claimed=YONETMELIK, prior=, gate=no_gate, selected=yonetmelik, score=5.75
- KANUN-03: expected=KANUN, claimed=TEBLIGLER, prior=, gate=no_gate, selected=kanun, score=6.85
- KANUN-04: expected=KANUN, claimed=KKY, prior=, gate=no_gate, selected=kky, score=5.75
- KANUN-06: expected=KANUN, claimed=MULGA, prior=, gate=no_gate, selected=mulga_kanun, score=1.45
- KANUN-13: expected=KANUN, claimed=KKY, prior=, gate=no_gate, selected=kky, score=6.85
- KANUN-15: expected=KANUN, claimed=KKY, prior=, gate=no_gate, selected=teblig, score=6.85
- KANUN-19: expected=KANUN, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, selected=teblig, score=7.75
- KHK-03: expected=KHK, claimed=CB_KARARNAME, prior=cb_kararname, gate=no_gate, selected=khk, score=6.55
- KKY-04: expected=KKY, claimed=KANUN, prior=kky, gate=no_gate, selected=kanun, score=6.85
- KKY-06: expected=KKY, claimed=UY, prior=uy, gate=locked_preferred_family, selected=uy, score=7.53
- MULGA-01: expected=MULGA, claimed=UY, prior=uy, gate=locked_preferred_family, selected=uy, score=3.43
- MULGA-02: expected=MULGA, claimed=CB_YONETMELIK, prior=cb_yonetmelik, gate=locked_preferred_family, selected=cb_yonetmelik, score=5.00
- MULGA-03: expected=MULGA, claimed=TUZUK, prior=, gate=no_gate, selected=tuzuk, score=0.00
- MULGA-04: expected=MULGA, claimed=KHK, prior=khk, gate=locked_preferred_family, selected=khk, score=6.78
- TUZUK-04: expected=TUZUK, claimed=UY, prior=tuzuk, gate=no_gate, selected=uy, score=4.63
- UY-07: expected=UY, claimed=KANUN, prior=uy, gate=no_gate, selected=kanun, score=1.45
- UY-08: expected=UY, claimed=KKY, prior=uy, gate=no_gate, selected=kky, score=6.55
- YON-01: expected=YONETMELIK, claimed=TEBLIGLER, prior=teblig, gate=locked_preferred_family, selected=teblig, score=5.75
- YON-02: expected=YONETMELIK, claimed=CB_YONETMELIK, prior=kky, gate=no_gate, selected=cb_yonetmelik, score=1.45
- YON-03: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, selected=kky, score=5.75
- YON-04: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, selected=yonetmelik, score=6.85
- YON-05: expected=YONETMELIK, claimed=KANUN, prior=yonetmelik, gate=no_gate, selected=kanun, score=5.75
- YON-06: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, selected=yonetmelik, score=1.45
- YON-07: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, selected=kky, score=6.43
- YON-08: expected=YONETMELIK, claimed=UY, prior=uy, gate=locked_preferred_family, selected=uy, score=5.00
- YON-09: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, selected=kky, score=5.75
- YON-10: expected=YONETMELIK, claimed=KKY, prior=yonetmelik, gate=no_gate, selected=yonetmelik, score=5.75
