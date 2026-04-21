# hukuk-ai 100 proxy calibration

- calibration_mode: `phase1_label_only_subset_no_private_answer_key`
- label_source: `phase1_proxy_seed_pending_human_judge_confirmation`
- total: 20
- exact_band_accuracy: 1.0
- adjacent_or_exact_band_accuracy: 1.0
- low_band_recall: 1.0
- critical_flag_any_match_rate: 1.0

## Band Confusion
- high->high: 5
- low->low: 10
- medium->medium: 5

## Calibration Rows

| QID | Expected | Proxy | Score | Critical flag match |
|---|---:|---:|---:|---:|
| KKY-11 | high | high | 8.66 | True |
| KHK-01 | high | high | 8.32 | True |
| CBK-05 | high | high | 8.32 | True |
| TEB-06 | high | high | 7.99 | True |
| TUZUK-01 | high | high | 7.90 | True |
| KANUN-15 | medium | medium | 6.66 | True |
| YON-05 | medium | medium | 6.55 | True |
| TUZUK-04 | medium | medium | 5.43 | True |
| KANUN-01 | medium | medium | 5.25 | True |
| CBY-04 | medium | medium | 5.16 | True |
| CBKAR-03 | low | low | 0.00 | True |
| CBY-01 | low | low | 0.00 | True |
| MULGA-03 | low | low | 0.00 | True |
| CBG-01 | low | low | 0.45 | True |
| KANUN-04 | low | low | 0.45 | True |
| YON-02 | low | low | 0.45 | True |
| UY-10 | low | low | 0.00 | True |
| CBG-04 | low | low | 1.50 | True |
| CBK-04 | low | low | 2.25 | True |
| KANUN-21 | low | low | 2.25 | True |
