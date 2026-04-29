# Phase 21F Residual Fail Audit

Run: `reports/benchmark/runs/20260429T174747Z_phase21F_full`

This audit lists mandatory Phase21F watch rows plus residual failed source/span rows. Classifications are systemic categories, not QID-specific remediation instructions.

| QID | Family | Pass | Score | Class | Disposition | Failure Classes | Selected Document | Selected Span | Support Insufficient | Corpus Materialization Required |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MULGA-01 | MULGA | FAIL | 0.00 | article_span_selection | safe_to_fix | auto_fail_triggered / missing_required_content_signal / wrong_article / partial_grounding_only / insufficient_canonical_span_evidence | SAYIŞTAY KANUNU | 832 m.98/f.0 | True | True |
| TEB-06 | TEBLIGLER | FAIL | 3.25 | document_identity | safe_to_fix | missing_gold_document_signal / missing_required_content_signal / wrong_document / hallucinated_identifier / partial_grounding_only / insufficient_canonical_span_evidence | ŞİRKET KURULUŞ SÖZLEŞMESİNİN TİCARET SİCİLİ MÜDÜRLÜKLERİNDE İMZALANMASI HAKKINDA TEBLİĞ | 23093 m.6/f.0 | True | True |
| YON-04 | YONETMELIK | FAIL | 3.25 | document_identity | safe_to_fix | missing_gold_document_signal / missing_required_content_signal / wrong_document / partial_grounding_only | NÜKLEER GÜÇ SANTRALLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12536 m.23/f.0 | False | False |
| CBY-01 | CB_YONETMELIK | PASS | 7.75 | source_identity | safe_to_fix | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | ELEKTRONİK İMZA KANUNUNUN UYGULANMASINA İLİŞKİN USUL VE ESASLAR HAKKINDA YÖNETMELİK | 7224 m.2/f.0 | False | False |
| KKY-01 | KKY | FAIL | 6.65 | source_identity | safe_to_fix | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKACILIK HİZMETLERİ HAKKINDA YÖNETMELİK | 34360 m.1/f.0 | False | False |
| TEB-07 | TEBLIGLER | PASS | 7.52 | scorer_proxy_mismatch | safe_to_fix | missing_required_content_signal / partial_grounding_only | MUHASEBAT GENEL MÜDÜRLÜĞÜ GENEL TEBLİĞİ (SIRA NO: 81) (EMANET İŞLEMLERİNİN ELEKTRONİK ORTAMDA GERÇEKLEŞTİRİLMESİNE İLİŞKİN USUL VE ESASLAR) | 40136 m.9/f.0 | True | False |
| CBKAR-03 | CB_KARAR | PASS | 8.80 | watch_only_resolved | no_action | missing_required_content_signal / partial_grounding_only | BURSA İLİNDE YAPILACAK OLAN ELEKTRİKLİ OTOMOBİL ÜRETİM TESİSİ YATIRIMINA PROJE BAZLI DEVLET YARDIMI VERİLMESİNE İLİŞKİN KARARIN YÜRÜRLÜĞE KONULMASI HAKKINDA KARAR (KARAR SAYISI: 1945) | 1945 m.10/f.0 | False | False |
| CBY-04 | CB_YONETMELIK | FAIL | 6.85 | source_identity | safe_to_fix | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11) | 11 m.10/f.0 | False | False |
| KANUN-12 | KANUN | FAIL | 1.45 | source_identity | safe_to_fix | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12879 m.15/f.0 | False | False |
| KKY-03 | KKY | FAIL | 1.45 | source_identity | safe_to_fix | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12879 m.4/f.0 | False | False |
| TUZUK-04 | TUZUK | FAIL | 0.00 | private_rubric_auto_fail | safe_to_fix | auto_fail_triggered / missing_required_content_signal / partial_grounding_only | RADYASYON GÜVENLİĞİ TÜZÜĞÜ | 859727 m.4/f.0 | False | False |
| TUZUK-05 | TUZUK | FAIL | 3.25 | document_identity | safe_to_fix | missing_gold_document_signal / missing_required_content_signal / wrong_document / partial_grounding_only | GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK | 315481 m.0/f.0 | True | False |

## Summary

- `CBKAR-03` is resolved as a pass/watch-only row in the full run: exact family, exact document, exact article, and no span/corpus blocker flags.
- The remaining hard residuals concentrate in source identity, document identity, article/span selection, and corpus materialization, so Phase22 should stay in retrieval/source-span hardening rather than fine-tuning.
