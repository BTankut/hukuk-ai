# FAZ 2A Category Breakdown

**Date:** 2026-03-23  
**Scope:** matched baseline vs promoted candidate after FAZ 2A re-qualification

## faz1-50

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| Citation | 0.8800 | 0.8800 | +0.0000 |
| Correct Source | 0.7667 | 0.7767 | +0.0100 |
| Hallucination | 0.1000 | 0.1000 | +0.0000 |
| Refusal | 1.0000 | 1.0000 | +0.0000 |
| Avg Response ms | 9374.8 | 10264.2 | +889.4 |
| Error Count | 0 | 0 | +0 |

| Category | n | Baseline Src | Candidate Src | Baseline Hal | Candidate Hal |
| --- | ---: | ---: | ---: | ---: | ---: |
| out_of_scope | 2 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_ceza_sarti | 1 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| tbk_eser | 2 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_genel | 23 | 0.8913 | 0.9130 | 0.0435 | 0.0435 |
| tbk_haksiz_fiil | 5 | 0.6000 | 0.6000 | 0.4000 | 0.4000 |
| tbk_hizmet | 2 | 0.7500 | 0.7500 | 0.0000 | 0.0000 |
| tbk_kefalet | 2 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_kira | 5 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_satis | 2 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_vekaletname | 2 | 0.1666 | 0.1666 | 0.5000 | 0.5000 |
| tmk_aile | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| tmk_esya | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| tmk_genel | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

### Focus Categories

- `out_of_scope`: n=2, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_ceza_sarti`: n=1, src 0.0000 -> 0.0000, hal 1.0000 -> 1.0000
- `tbk_kefalet`: n=2, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_kira`: n=5, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_satis`: n=2, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_vekaletname`: n=2, src 0.1666 -> 0.1666, hal 0.5000 -> 0.5000

### Candidate Error Taxonomy

- `wrong source despite retrieved evidence`: 9 sample=['TBK-003', 'TBK-006', 'TBK-007', 'TBK-008', 'TBK-009']
- `retrieval miss`: 4 sample=['TBK-047', 'TBK-048', 'TBK-049', 'TBK-050']

## v2-95

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| Citation | 0.9474 | 0.9474 | +0.0000 |
| Correct Source | 0.8211 | 0.8281 | +0.0070 |
| Hallucination | 0.0947 | 0.0842 | -0.0105 |
| Refusal | 0.9368 | 0.9263 | -0.0105 |
| Avg Response ms | 14752.2 | 22825.2 | +8073.0 |
| Error Count | 0 | 0 | +0 |

| Category | n | Baseline Src | Candidate Src | Baseline Hal | Candidate Hal |
| --- | ---: | ---: | ---: | ---: | ---: |
| hal_prone | 10 | 0.9000 | 0.8667 | 0.1000 | 0.1000 |
| out_of_scope | 10 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_ceza_sarti | 3 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_eser | 5 | 0.9000 | 0.9000 | 0.0000 | 0.0000 |
| tbk_genel | 15 | 0.3889 | 0.3889 | 0.4667 | 0.4667 |
| tbk_haksiz_fiil | 5 | 0.9000 | 0.9000 | 0.0000 | 0.0000 |
| tbk_hizmet | 9 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_kefalet | 5 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_kira | 8 | 0.8125 | 0.8125 | 0.0000 | 0.0000 |
| tbk_satis | 5 | 0.6000 | 0.8000 | 0.2000 | 0.0000 |
| tbk_vekaletname | 10 | 0.9500 | 0.9500 | 0.0000 | 0.0000 |
| tmk_cross_law | 10 | 0.8167 | 0.8167 | 0.0000 | 0.0000 |

### Focus Categories

- `tmk_cross_law`: n=10, src 0.8167 -> 0.8167, hal 0.0000 -> 0.0000
- `hal_prone`: n=10, src 0.9000 -> 0.8667, hal 0.1000 -> 0.1000
- `out_of_scope`: n=10, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_ceza_sarti`: n=3, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_kefalet`: n=5, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_kira`: n=8, src 0.8125 -> 0.8125, hal 0.0000 -> 0.0000
- `tbk_satis`: n=5, src 0.6000 -> 0.8000, hal 0.2000 -> 0.0000
- `tbk_vekaletname`: n=10, src 0.9500 -> 0.9500, hal 0.0000 -> 0.0000

### Candidate Error Taxonomy

- `wrong source despite retrieved evidence`: 20 sample=['TBK-051', 'TBK-052', 'TBK-054', 'TBK-055', 'TBK-057']
- `unsupported question answered`: 5 sample=['OOS-002', 'OOS-004', 'OOS-006', 'OOS-008', 'OOS-010']
- `cross-law confusion`: 4 sample=['TMK-CL-003', 'TMK-CL-004', 'TMK-CL-007', 'TMK-CL-009']
- `over-refusal`: 2 sample=['TBK-065', 'TBK-093']

## v3-170

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| Citation | 0.9647 | 0.9647 | +0.0000 |
| Correct Source | 0.8441 | 0.8382 | -0.0059 |
| Hallucination | 0.0529 | 0.0471 | -0.0058 |
| Refusal | 0.9471 | 0.9412 | -0.0059 |
| Avg Response ms | 11657.8 | 16337.7 | +4679.9 |
| Error Count | 0 | 0 | +0 |

| Category | n | Baseline Src | Candidate Src | Baseline Hal | Candidate Hal |
| --- | ---: | ---: | ---: | ---: | ---: |
| hal_prone | 12 | 0.8889 | 0.8611 | 0.0833 | 0.0833 |
| out_of_scope | 12 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_ceza_sarti | 11 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_eser | 5 | 0.9000 | 0.9000 | 0.0000 | 0.0000 |
| tbk_genel | 30 | 0.5083 | 0.4917 | 0.2333 | 0.2333 |
| tbk_haksiz_fiil | 6 | 0.9167 | 0.8333 | 0.0000 | 0.0000 |
| tbk_hizmet | 19 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_kefalet | 13 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_kira | 9 | 0.7778 | 0.7778 | 0.0000 | 0.0000 |
| tbk_satis | 5 | 0.7000 | 0.7000 | 0.0000 | 0.0000 |
| tbk_vekaletname | 18 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tmk_cross_law | 30 | 0.8028 | 0.8139 | 0.0333 | 0.0000 |

### Focus Categories

- `tmk_cross_law`: n=30, src 0.8028 -> 0.8139, hal 0.0333 -> 0.0000
- `hal_prone`: n=12, src 0.8889 -> 0.8611, hal 0.0833 -> 0.0833
- `out_of_scope`: n=12, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_ceza_sarti`: n=11, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_kefalet`: n=13, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_kira`: n=9, src 0.7778 -> 0.7778, hal 0.0000 -> 0.0000
- `tbk_satis`: n=5, src 0.7000 -> 0.7000, hal 0.0000 -> 0.0000
- `tbk_vekaletname`: n=18, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000

### Candidate Error Taxonomy

- `wrong source despite retrieved evidence`: 34 sample=['TBK-051', 'TBK-052', 'TBK-054', 'TBK-055', 'TBK-057']
- `cross-law confusion`: 9 sample=['TMK-CL-003', 'TMK-CL-004', 'TMK-CL-007', 'TMK-CL-014', 'TMK-CL-015']
- `unsupported question answered`: 6 sample=['OOS-002', 'OOS-004', 'OOS-006', 'OOS-008', 'OOS-010']
- `over-refusal`: 4 sample=['TBK-065', 'TBK-093', 'HAL-002', 'TBK-119']
