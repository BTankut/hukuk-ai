# FAZ 1.5 Category Breakdown

**Date:** 2026-03-22  
**Scope:** matched baseline vs promoted candidate across `faz1-50`, `v2-95`, `v3-170`

## faz1-50

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| Citation | 0.8800 | 0.8600 | -0.0200 |
| Correct Source | 0.8667 | 0.8467 | -0.0200 |
| Hallucination | 0.0000 | 0.0000 | +0.0000 |
| Refusal | 1.0000 | 1.0000 | +0.0000 |
| Avg Response ms | 9073.1 | 9833.3 | +760.2 |
| Error Count | 0 | 0 | +0 |

| Category | n | Baseline Src | Candidate Src | Baseline Hal | Candidate Hal |
| --- | ---: | ---: | ---: | ---: | ---: |
| out_of_scope | 2 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_ceza_sarti | 1 | 0.6667 | 0.6667 | 0.0000 | 0.0000 |
| tbk_eser | 2 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_genel | 23 | 0.9783 | 0.9565 | 0.0000 | 0.0000 |
| tbk_haksiz_fiil | 5 | 0.9000 | 0.9000 | 0.0000 | 0.0000 |
| tbk_hizmet | 2 | 0.7500 | 0.5000 | 0.0000 | 0.0000 |
| tbk_kefalet | 2 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_kira | 5 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_satis | 2 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_vekaletname | 2 | 0.5834 | 0.5834 | 0.0000 | 0.0000 |
| tmk_aile | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| tmk_esya | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| tmk_genel | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

### Focus Categories

- `out_of_scope`: n=2, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_ceza_sarti`: n=1, src 0.6667 -> 0.6667, hal 0.0000 -> 0.0000
- `tbk_kefalet`: n=2, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_kira`: n=5, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_satis`: n=2, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_vekaletname`: n=2, src 0.5834 -> 0.5834, hal 0.0000 -> 0.0000

### Candidate Error Taxonomy

- `wrong source despite retrieved evidence`: 6 sample=['TBK-003', 'TBK-006', 'TBK-007', 'TBK-016', 'TBK-033']
- `retrieval miss`: 5 sample=['TBK-008', 'TBK-047', 'TBK-048', 'TBK-049', 'TBK-050']

## v2-95

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| Citation | 0.8421 | 0.8632 | +0.0211 |
| Correct Source | 0.7491 | 0.7281 | -0.0210 |
| Hallucination | 0.0526 | 0.0842 | +0.0316 |
| Refusal | 0.8737 | 0.9263 | +0.0526 |
| Avg Response ms | 17378.3 | 21436.9 | +4058.6 |
| Error Count | 0 | 0 | +0 |

| Category | n | Baseline Src | Candidate Src | Baseline Hal | Candidate Hal |
| --- | ---: | ---: | ---: | ---: | ---: |
| hal_prone | 10 | 0.7500 | 0.7167 | 0.0000 | 0.0000 |
| out_of_scope | 10 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_ceza_sarti | 3 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_eser | 5 | 0.9000 | 0.9000 | 0.0000 | 0.0000 |
| tbk_genel | 15 | 0.5889 | 0.6444 | 0.1333 | 0.2000 |
| tbk_haksiz_fiil | 5 | 0.9000 | 0.9000 | 0.0000 | 0.0000 |
| tbk_hizmet | 9 | 0.6852 | 0.6852 | 0.1111 | 0.1111 |
| tbk_kefalet | 5 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_kira | 8 | 0.8125 | 0.8125 | 0.0000 | 0.0000 |
| tbk_satis | 5 | 0.6000 | 0.5000 | 0.0000 | 0.0000 |
| tbk_vekaletname | 10 | 0.8000 | 0.6500 | 0.1000 | 0.2000 |
| tmk_cross_law | 10 | 0.4167 | 0.3667 | 0.1000 | 0.2000 |

### Focus Categories

- `tmk_cross_law`: n=10, src 0.4167 -> 0.3667, hal 0.1000 -> 0.2000
- `hal_prone`: n=10, src 0.7500 -> 0.7167, hal 0.0000 -> 0.0000
- `out_of_scope`: n=10, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_ceza_sarti`: n=3, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_kefalet`: n=5, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_kira`: n=8, src 0.8125 -> 0.8125, hal 0.0000 -> 0.0000
- `tbk_satis`: n=5, src 0.6000 -> 0.5000, hal 0.0000 -> 0.0000
- `tbk_vekaletname`: n=10, src 0.8000 -> 0.6500, hal 0.1000 -> 0.2000

### Candidate Error Taxonomy

- `wrong source despite retrieved evidence`: 25 sample=['TBK-051', 'TBK-052', 'TBK-054', 'TBK-055', 'TBK-057']
- `cross-law confusion`: 7 sample=['TMK-CL-002', 'TMK-CL-003', 'TMK-CL-005', 'TMK-CL-006', 'TMK-CL-008']
- `unsupported question answered`: 5 sample=['OOS-002', 'OOS-004', 'OOS-006', 'OOS-008', 'OOS-010']
- `retrieval miss`: 4 sample=['TBK-081', 'TBK-083', 'HAL-002', 'HAL-003']
- `over-refusal`: 2 sample=['TBK-065', 'TBK-093']

## v3-170

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| Citation | 0.8471 | 0.8909 | +0.0438 |
| Correct Source | 0.6558 | 0.6507 | -0.0051 |
| Hallucination | 0.0706 | 0.0788 | +0.0082 |
| Refusal | 0.9118 | 0.9152 | +0.0034 |
| Avg Response ms | 17687.6 | 27119.7 | +9432.1 |
| Error Count | 0 | 5 | +5 |

| Category | n | Baseline Src | Candidate Src | Baseline Hal | Candidate Hal |
| --- | ---: | ---: | ---: | ---: | ---: |
| hal_prone | 11 | 0.8472 | 0.9394 | 0.0000 | 0.0000 |
| out_of_scope | 12 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| tbk_ceza_sarti | 10 | 0.6970 | 0.6000 | 0.0909 | 0.1000 |
| tbk_eser | 5 | 0.9000 | 0.9000 | 0.0000 | 0.0000 |
| tbk_genel | 28 | 0.6356 | 0.6143 | 0.0333 | 0.0714 |
| tbk_haksiz_fiil | 6 | 0.8333 | 0.9167 | 0.0000 | 0.0000 |
| tbk_hizmet | 19 | 0.6404 | 0.5877 | 0.1579 | 0.1579 |
| tbk_kefalet | 13 | 0.6538 | 0.6154 | 0.1538 | 0.0000 |
| tbk_kira | 9 | 0.7778 | 0.7778 | 0.0000 | 0.0000 |
| tbk_satis | 5 | 0.7000 | 0.7000 | 0.0000 | 0.0000 |
| tbk_vekaletname | 17 | 0.6759 | 0.6275 | 0.1111 | 0.1176 |
| tmk_cross_law | 30 | 0.3250 | 0.3833 | 0.1000 | 0.1667 |

### Focus Categories

- `tmk_cross_law`: n=30, src 0.3250 -> 0.3833, hal 0.1000 -> 0.1667
- `hal_prone`: n=11, src 0.8472 -> 0.9394, hal 0.0000 -> 0.0000
- `out_of_scope`: n=12, src 1.0000 -> 1.0000, hal 0.0000 -> 0.0000
- `tbk_ceza_sarti`: n=10, src 0.6970 -> 0.6000, hal 0.0909 -> 0.1000
- `tbk_kefalet`: n=13, src 0.6538 -> 0.6154, hal 0.1538 -> 0.0000
- `tbk_kira`: n=9, src 0.7778 -> 0.7778, hal 0.0000 -> 0.0000
- `tbk_satis`: n=5, src 0.7000 -> 0.7000, hal 0.0000 -> 0.0000
- `tbk_vekaletname`: n=17, src 0.6759 -> 0.6275, hal 0.1111 -> 0.1176

### Candidate Error Taxonomy

- `wrong source despite retrieved evidence`: 56 sample=['TBK-052', 'TBK-054', 'TBK-055', 'TBK-057', 'TBK-059']
- `cross-law confusion`: 20 sample=['TMK-CL-001', 'TMK-CL-002', 'TMK-CL-003', 'TMK-CL-006', 'TMK-CL-008']
- `over-refusal`: 9 sample=['TBK-093', 'TMK-CL-005', 'HAL-002', 'TMK-CL-016', 'TMK-CL-024']
- `infrastructure / timeout / serving error`: 5 sample=['TBK-058', 'TBK-114', 'HAL-009', 'TBK-120', 'TBK-163']
- `retrieval miss`: 5 sample=['TBK-083', 'TBK-133', 'TBK-150', 'TBK-152', 'TBK-159']
- `unsupported question answered`: 5 sample=['OOS-002', 'OOS-004', 'OOS-006', 'OOS-010', 'OOS-011']
