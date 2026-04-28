# Phase 20F Source / Span Blocker Backlog

Total source/span blockers: `17`

## Priority Counts

- `YONETMELIK`: 4
- `TEBLIGLER`: 3
- `CB_YONETMELIK`: 2
- `KKY`: 2
- `MULGA`: 2
- `CB_GENELGE`: 1
- `CB_KARAR`: 1
- `KANUN`: 1
- `TUZUK`: 1

## Backlog Rows

| QID | Family | Score | Pass | Blocker Type | Failure Classes | Selected Document | Selected Span | Selected Article | Phase 21 Lane |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| TEB-03 | TEBLIGLER | 5.35 | FAIL | wrong_family,hallucinated_identifier | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | 6563 SAYILI ELEKTRONİK TİCARETİN DÜZENLENMESİ HAKKINDA KANUNUN 12 NCİ MADDESİNE GÖRE 2026 YILINDA UYGULANACAK OLAN İDARİ PARA CEZALARINA İLİŞKİN TEBLİĞ | 42805 m.0/f.0 | 0 | 21A_TEBLIGLER |
| TEB-06 | TEBLIGLER | 3.25 | FAIL | wrong_document,missing_gold_document_signal,hallucinated_identifier | missing_gold_document_signal / missing_required_content_signal / wrong_document / hallucinated_identifier / partial_grounding_only | TİCARET ŞİRKETLERİNDE ANONİM ŞİRKET GENEL KURULLARI DIŞINDA ELEKTRONİK ORTAMDA YAPILACAK KURULLAR HAKKINDA TEBLİĞ | 16558 m.14/f.0 | 14 | 21A_TEBLIGLER |
| TEB-07 | TEBLIGLER | 1.45 | FAIL | wrong_family,wrong_document,missing_gold_document_signal,hallucinated_identifier | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / hallucinated_identifier / partial_grounding_only | KİŞİSEL VERİLERİN KORUNMASI KANUNU | KVKK m.6/f.0 | 6 | 21A_TEBLIGLER |
| YON-04 | YONETMELIK | 3.25 | FAIL | wrong_document,missing_gold_document_signal | missing_gold_document_signal / missing_required_content_signal / wrong_document / partial_grounding_only | NÜKLEER GÜÇ SANTRALLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12536 m.23/f.0 | 23 | 21B_YONETMELIK |
| YON-05 | YONETMELIK | 3.25 | FAIL | wrong_document,missing_gold_document_signal,hallucinated_identifier | missing_gold_document_signal / missing_required_content_signal / wrong_document / hallucinated_identifier / partial_grounding_only | ONDOKUZ MAYIS ÜNİVERSİTESİ TAŞINMAZLARININ İDARESİ HAKKINDA YÖNETMELİK | 15459 m.3/f.0 | 3 | 21B_YONETMELIK |
| YON-06 | YONETMELIK | 1.45 | FAIL | wrong_family,wrong_document,missing_gold_document_signal,hallucinated_identifier | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / hallucinated_identifier / partial_grounding_only | CEZA İNFAZ KURUMLARININ YÖNETİMİ İLE CEZA VE GÜVENLİK TEDBİRLERİNİN İNFAZI HAKKINDA YÖNETMELİK | 2324 m.25/f.0 | 25 | 21B_YONETMELIK |
| YON-08 | YONETMELIK | 5.45 | FAIL | wrong_family,hallucinated_identifier | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | IŞIK ÜNİVERSİTESİ YATAY GEÇİŞ, ÇİFT ANADAL, YAN DAL VE KREDİ TRANSFERİ YÖNETMELİĞİ | 31299 m.4/f.0 | 4 | 21B_YONETMELIK |
| MULGA-01 | MULGA | 0.00 | FAIL | wrong_article,insufficient_canonical_span_evidence | auto_fail_triggered / missing_required_content_signal / wrong_article / partial_grounding_only / insufficient_canonical_span_evidence | SAYIŞTAY KANUNU | 832 m.98/f.0 | 98 | 21C_MULGA |
| MULGA-05 | MULGA | 0.00 | FAIL | wrong_document,wrong_article,missing_gold_document_signal,hallucinated_identifier | auto_fail_triggered / missing_gold_document_signal / missing_required_content_signal / wrong_document / wrong_article / hallucinated_identifier / partial_grounding_only | GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ | 6570 m.16/f.0 | 16 | 21C_MULGA |
| CBKAR-05 | CB_KARAR | 7.19 | PASS | wrong_family,hallucinated_identifier | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/34) | 11990 m.8/f.0 | 8 | 21D_CB_KARAR |
| CBG-02 | CB_GENELGE | 8.65 | PASS | insufficient_canonical_span_evidence | missing_required_content_signal / partial_grounding_only / insufficient_canonical_span_evidence | Bilgi ve İletişim Güvenliği Tedbirleri ile İlgili | 2019/12 m.0/f.0 | 0 | 21X_source_span_general |
| CBY-01 | CB_YONETMELIK | 0.00 | FAIL | wrong_family,hallucinated_identifier | auto_fail_triggered / missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | VALİLİK VE KAYMAKAMLIK BİRİMLERİ TEŞKİLAT, GÖREV VE ÇALIŞMA YÖNETMELİĞİ | 15030 m.38/f.0 | 38 | 21X_source_span_general |
| CBY-04 | CB_YONETMELIK | 6.85 | FAIL | wrong_family,hallucinated_identifier | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11) | 11 m.10/f.0 | 10 | 21X_source_span_general |
| KANUN-12 | KANUN | 1.45 | FAIL | wrong_family,wrong_document,missing_gold_document_signal | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12879 m.15/f.0 | 15 | 21X_source_span_general |
| KKY-01 | KKY | 6.65 | FAIL | wrong_family,hallucinated_identifier | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only | BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKACILIK HİZMETLERİ HAKKINDA YÖNETMELİK | 34360 m.1/f.0 | 1 | 21X_source_span_general |
| KKY-03 | KKY | 1.45 | FAIL | wrong_family,wrong_document,missing_gold_document_signal | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 12879 m.4/f.0 | 4 | 21X_source_span_general |
| TUZUK-05 | TUZUK | 3.25 | FAIL | wrong_document,missing_gold_document_signal | missing_gold_document_signal / missing_required_content_signal / wrong_document / partial_grounding_only | GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK | 315481 m.0/f.0 | 0 | 21X_source_span_general |
