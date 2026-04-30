# Phase 22B Residual Source/Span Backlog Audit

Input run: `reports/benchmark/runs/20260430T112106Z_phase22A_stability_full`

This audit classifies the 11 Phase21F residual backlog rows using systemic root-cause categories. It does not authorize QID-specific patches.

## Counts

- `P0_blocks_productization`: 2
- `P1_high_value_next_iteration`: 6
- `P2_watchlist`: 3

- root_cause `document_identity`: 4
- root_cause `family_boundary`: 2
- root_cause `source_identity`: 2
- root_cause `span_materialization`: 3

- safe_action `defer_needs_corpus`: 2
- safe_action `fix_now_generalizable`: 6
- safe_action `watch_only_pass_row`: 3

## Audit Table

| QID | Family | Score | Pass | Blocker Type | Root Cause | Safe Action | Priority | Selected Document | Selected Span |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CBG-02 | CB_GENELGE | 8.65 | PASS | insufficient_canonical_span_evidence | span_materialization | watch_only_pass_row | P2_watchlist | Bilgi ve İletişim Güvenliği Tedbirleri ile İlgili | 2019/12 m.0/f.0 |
| CBKAR-05 | CB_KARAR | 7.19 | PASS | wrong_family,hallucinated_identifier | family_boundary | watch_only_pass_row | P2_watchlist | TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/34) | 11990 m.8/f.0 |
| CBY-01 | CB_YONETMELIK | 7.75 | PASS | wrong_family,hallucinated_identifier | family_boundary | watch_only_pass_row | P2_watchlist | ELEKTRONİK İMZA KANUNUNUN UYGULANMASINA İLİŞKİN USUL VE ESASLAR HAKKINDA YÖNETMELİK | 7224 m.2/f.0 |
| CBY-04 | CB_YONETMELIK | 6.85 | FAIL | wrong_family,hallucinated_identifier | source_identity | fix_now_generalizable | P1_high_value_next_iteration | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11) | 11 m.10/f.0 |
| KANUN-12 | KANUN | 1.45 | FAIL | wrong_family,wrong_document,missing_gold_document_signal | document_identity | fix_now_generalizable | P1_high_value_next_iteration | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12879 m.15/f.0 |
| KKY-01 | KKY | 6.65 | FAIL | wrong_family,hallucinated_identifier | source_identity | fix_now_generalizable | P1_high_value_next_iteration | BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKACILIK HİZMETLERİ HAKKINDA YÖNETMELİK | 34360 m.1/f.0 |
| KKY-03 | KKY | 1.45 | FAIL | wrong_family,wrong_document,missing_gold_document_signal | document_identity | fix_now_generalizable | P1_high_value_next_iteration | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12879 m.4/f.0 |
| MULGA-01 | MULGA | 0.00 | FAIL | wrong_article,insufficient_canonical_span_evidence | span_materialization | defer_needs_corpus | P0_blocks_productization | SAYIŞTAY KANUNU | 832 m.98/f.0 |
| TEB-06 | TEBLIGLER | 3.25 | FAIL | wrong_document,missing_gold_document_signal,hallucinated_identifier,insufficient_canonical_span_evidence | span_materialization | defer_needs_corpus | P0_blocks_productization | ŞİRKET KURULUŞ SÖZLEŞMESİNİN TİCARET SİCİLİ MÜDÜRLÜKLERİNDE İMZALANMASI HAKKINDA TEBLİĞ | 23093 m.6/f.0 |
| TUZUK-05 | TUZUK | 3.25 | FAIL | wrong_document,missing_gold_document_signal | document_identity | fix_now_generalizable | P1_high_value_next_iteration | GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK | 315481 m.0/f.0 |
| YON-04 | YONETMELIK | 3.25 | FAIL | wrong_document,missing_gold_document_signal | document_identity | fix_now_generalizable | P1_high_value_next_iteration | NÜKLEER GÜÇ SANTRALLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12536 m.23/f.0 |

## Interpretation

- PASS-but-flagged rows are watchlist items, not immediate remediation targets.
- `MULGA-01` and `TEB-06` are P0 because they combine failing output with span/materialization risk and should block productization readiness until resolved or legally accepted.
- Remaining failed rows are P1 source/document identity work and should only be fixed through general retrieval/source-span improvements.
- No row should be addressed with QID-specific branching.
