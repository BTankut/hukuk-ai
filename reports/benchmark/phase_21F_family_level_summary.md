# Phase 21F Family Level Summary

Run: `reports/benchmark/runs/20260429T174747Z_phase21F_full`

| Family | Pass/Total | Raw | Phase20F Pass/Total | Phase20F Raw | Pass Delta | Raw Delta | Wrong Family | Wrong Document | Hallucinated | Insufficient Span | Avg Slot Coverage | Target | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CB_GENELGE | 4/4 | 35.20 | 4/4 | 35.20 | +0 | +0.00 | 0 | 0 | 0 | 1 | 0.856 | >=4/4 (hard) | PASS |
| CB_KARAR | 8/8 | 68.14 | 6/8 | 63.69 | +2 | +4.45 | 1 | 0 | 1 | 0 | 0.89 | >=7/8 (preferred 8/8) | PASS |
| CB_KARARNAME | 6/6 | 52.07 | 6/6 | 52.07 | +0 | +0.00 | 0 | 0 | 0 | 0 | 0.869 | >=6/6 (target) | PASS |
| CB_YONETMELIK | 4/6 | 46.85 | 3/6 | 39.10 | +1 | +7.75 | 2 | 0 | 2 | 0 | 0.89 | not specified | - |
| KANUN | 19/21 | 165.28 | 19/21 | 164.18 | +0 | +1.10 | 1 | 1 | 0 | 0 | 0.888 | >=19/21 (target) | PASS |
| KHK | 6/6 | 53.15 | 6/6 | 53.15 | +0 | +0.00 | 0 | 0 | 0 | 0 | 0.874 | >=6/6 (target) | PASS |
| KKY | 9/11 | 89.61 | 9/11 | 90.03 | +0 | -0.42 | 2 | 1 | 1 | 0 | 0.89 | >=9/11 (target) | PASS |
| MULGA | 4/5 | 32.12 | 3/5 | 24.87 | +1 | +7.25 | 0 | 0 | 0 | 1 | 0.89 | >=4/5 (target) | PASS |
| TEBLIGLER | 7/8 | 62.01 | 4/8 | 44.49 | +3 | +17.52 | 0 | 1 | 1 | 1 | 0.89 | >=6/8 (preferred 7/8) | PASS |
| TUZUK | 3/5 | 31.15 | 3/5 | 37.58 | +0 | -6.43 | 0 | 1 | 0 | 0 | 0.89 | not specified | - |
| UY | 10/10 | 88.32 | 10/10 | 90.23 | +0 | -1.91 | 0 | 0 | 0 | 0 | 0.872 | >=9/10 (hard/preferred 10/10) | PASS |
| YONETMELIK | 9/10 | 76.65 | 6/10 | 61.01 | +3 | +15.64 | 0 | 1 | 0 | 0 | 0.89 | >=7/10 (preferred 9/10) | PASS |

## Notes

- Phase 21 remediation gains are preserved for `TEBLIGLER`, `YONETMELIK`, `MULGA`, and `CB_KARAR` versus Phase20F.
- `CB_YONETMELIK` and `TUZUK` are reported because they are present in the 100-question set, even though they are not explicit Phase21F target families.
