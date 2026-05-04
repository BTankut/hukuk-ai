# Phase 24N Targeted Shadow Smoke Report

- generated_at_utc: `2026-05-04T08:40:32.860456+00:00`
- status: `FAIL`
- run_dir: `reports/benchmark/runs/phase_24N_targeted_shadow_smoke_20260504T083103Z`
- api_url: `http://127.0.0.1:8031/v1`
- model: `hukuk-ai-poc`
- collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24n`
- live_8000_untouched: `true`

## Runtime Contract

| Check | Result |
|---|---:|
| total | 12 |
| answered | 12 |
| refused_or_empty | 0 |
| errors | 0 |
| missing_trace | 0 |
| missing_contract_fields | 0 |
| contract_valid | 12 |
| unsupported_confident_answer | 0 |
| answer_contract_invalid | 0 |
| source_key_v2_collision | 0 |
| binding_collision | 0 |
| repealed_as_active_scorer_count | 0 |

## Score Summary

| Metric | Value |
|---|---:|
| raw_score_proxy | 72.22 / 120 |
| average_score_0_10_proxy | 6.02 |
| pass_proxy | 7 |
| fail_proxy | 5 |
| wrong_family | 2 |
| wrong_document | 3 |
| hallucinated_source_count | 3 |

## Delta Vs Phase 24J-R2 Base Residual Targeted

| qid | base_score | base_result | phase24n_score | phase24n_result | delta |
|---|---:|---|---:|---|---:|
| KANUN-12 | 1.45 | FAIL | 1.45 | FAIL | 0.00 |
| KKY-03 | 1.45 | FAIL | 1.45 | FAIL | 0.00 |
| YON-04 | 3.25 | FAIL | 3.25 | FAIL | 0.00 |
| TUZUK-04 | 6.43 | FAIL | 6.43 | FAIL | 0.00 |
| MULGA-01 | 8.37 | PASS | 8.37 | PASS | 0.00 |
| MULGA-05 | 7.10 | PASS | 7.10 | PASS | 0.00 |
| TEB-04 | 0.00 | FAIL | 0.00 | FAIL | 0.00 |
| TEB-06 | 8.90 | PASS | 8.90 | PASS | 0.00 |
| CBG-01 | 8.65 | PASS | 8.65 | PASS | 0.00 |
| CBKAR-08 | 9.25 | PASS | 9.25 | PASS | 0.00 |
| UY-01 | 7.82 | PASS | 7.82 | PASS | 0.00 |
| YON-05 | 9.55 | PASS | 9.55 | PASS | 0.00 |

## Per-QID Result

| qid | score | result | selected_document | failure_classes |
|---|---:|---|---|---|
| KANUN-12 | 1.45 | FAIL | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only |
| KKY-03 | 1.45 | FAIL | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only |
| YON-04 | 3.25 | FAIL | NÜKLEER GÜÇ SANTRALLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | missing_gold_document_signal / missing_required_content_signal / wrong_document / partial_grounding_only |
| TUZUK-04 | 6.43 | FAIL | RADYASYON GÜVENLİĞİ TÜZÜĞÜ | missing_required_content_signal / partial_grounding_only |
| MULGA-01 | 8.37 | PASS | YÜKSEKÖĞRETİM KURUMLARI ÖĞRENCİ DİSİPLİN YÖNETMELİĞİ | missing_required_content_signal / partial_grounding_only |
| MULGA-05 | 7.10 | PASS | GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ | missing_required_content_signal / partial_grounding_only |
| TEB-04 | 0.00 | FAIL | KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ | auto_fail_triggered / missing_required_content_signal / partial_grounding_only |
| TEB-06 | 8.90 | PASS | ŞİRKET KURULUŞ SÖZLEŞMESİNİN TİCARET SİCİLİ MÜDÜRLÜKLERİNDE İMZALANMASI HAKKINDA TEBLİĞ |  |
| CBG-01 | 8.65 | PASS | Tasarruf Tedbirleri ile İlgili | missing_required_content_signal / partial_grounding_only |
| CBKAR-08 | 9.25 | PASS | Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903) |  |
| UY-01 | 7.82 | PASS | STRATEJİK ARAŞTIRMALAR ENSTİTÜSÜ (SAREN) LİSANSÜSTÜ EĞİTİM-ÖĞRETİM YÖNETMELİĞİ | missing_required_content_signal / partial_grounding_only |
| YON-05 | 9.55 | PASS | PLANLI ALANLAR İMAR YÖNETMELİĞİ | missing_required_content_signal / partial_grounding_only |

## Gate Findings

- critical_guard_regressions: `none`
- targeted_improved_rows: `none`
- tuzuk04_active_current_law_claim_detected: `true`
- target_full_shadow_allowed: `false`

## Decision

Phase 24N-E targeted shadow smoke is `FAIL`. Do not run Phase 24N-F full shadow benchmark.

The failure is not a transport/contract failure: all 12 answers were returned, contract-valid, with zero unsupported confident answers and zero source-key-v2/binding collisions. The stop rule is triggered because eligible target rows did not improve, and `TUZUK-04` still claimed the historical Radyasyon Güvenliği Tüzüğü as `active` current-law evidence.
