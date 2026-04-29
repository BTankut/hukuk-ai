# Phase 21F Source / Span Blocker Backlog

Run: `reports/benchmark/runs/20260429T174747Z_phase21F_full`

Total source/span blockers: `11`

## Priority Counts

- `CB_YONETMELIK`: 2
- `KKY`: 2
- `CB_GENELGE`: 1
- `CB_KARAR`: 1
- `KANUN`: 1
- `MULGA`: 1
- `TEBLIGLER`: 1
- `TUZUK`: 1
- `YONETMELIK`: 1

## Backlog Rows

| QID | Family | Score | Pass | Blocker Type | Failure Classes | Selected Document | Selected Span | Selected Article | Phase 22 Lane |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CBG-02 | CB_GENELGE | 8.65 | PASS | insufficient_canonical_span_evidence | missing_required_content_signal / partial_grounding_only / insufficient_canonical_span_evidence | Bilgi ve İletişim Güvenliği Tedbirleri ile İlgili | 2019/12 m.0/f.0 | 0 | Phase22_span_materialization |
| CBKAR-05 | CB_KARAR | 7.19 | PASS | wrong_family,hallucinated_identifier | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/34) | 11990 m.8/f.0 | 8 | Phase22_source_identity |
| CBY-01 | CB_YONETMELIK | 7.75 | PASS | wrong_family,hallucinated_identifier | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | ELEKTRONİK İMZA KANUNUNUN UYGULANMASINA İLİŞKİN USUL VE ESASLAR HAKKINDA YÖNETMELİK | 7224 m.2/f.0 | 2 | Phase22_source_identity |
| CBY-04 | CB_YONETMELIK | 6.85 | FAIL | wrong_family,hallucinated_identifier | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11) | 11 m.10/f.0 | 10 | Phase22_source_identity |
| KANUN-12 | KANUN | 1.45 | FAIL | wrong_family,wrong_document,missing_gold_document_signal | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12879 m.15/f.0 | 15 | Phase22_document_identity |
| KKY-01 | KKY | 6.65 | FAIL | wrong_family,hallucinated_identifier | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKACILIK HİZMETLERİ HAKKINDA YÖNETMELİK | 34360 m.1/f.0 | 1 | Phase22_source_identity |
| KKY-03 | KKY | 1.45 | FAIL | wrong_family,wrong_document,missing_gold_document_signal | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12879 m.4/f.0 | 4 | Phase22_document_identity |
| MULGA-01 | MULGA | 0.00 | FAIL | wrong_article,insufficient_canonical_span_evidence | auto_fail_triggered / missing_required_content_signal / wrong_article / partial_grounding_only / insufficient_canonical_span_evidence | SAYIŞTAY KANUNU | 832 m.98/f.0 | 98 | Phase22_span_materialization |
| TEB-06 | TEBLIGLER | 3.25 | FAIL | wrong_document,missing_gold_document_signal,hallucinated_identifier,insufficient_canonical_span_evidence | missing_gold_document_signal / missing_required_content_signal / wrong_document / hallucinated_identifier / partial_grounding_only / insufficient_canonical_span_evidence | ŞİRKET KURULUŞ SÖZLEŞMESİNİN TİCARET SİCİLİ MÜDÜRLÜKLERİNDE İMZALANMASI HAKKINDA TEBLİĞ | 23093 m.6/f.0 | 6 | Phase22_span_materialization |
| TUZUK-05 | TUZUK | 3.25 | FAIL | wrong_document,missing_gold_document_signal | missing_gold_document_signal / missing_required_content_signal / wrong_document / partial_grounding_only | GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK | 315481 m.0/f.0 | 0 | Phase22_document_identity |
| YON-04 | YONETMELIK | 3.25 | FAIL | wrong_document,missing_gold_document_signal | missing_gold_document_signal / missing_required_content_signal / wrong_document / partial_grounding_only | NÜKLEER GÜÇ SANTRALLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12536 m.23/f.0 | 23 | Phase22_document_identity |
