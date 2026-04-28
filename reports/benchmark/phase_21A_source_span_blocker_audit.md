# Phase 21A Source / Span Blocker Audit

Status: AUDIT_ONLY_NO_RUNTIME_CHANGE

Input backlog: `reports/benchmark/phase_20F_source_span_blocker_backlog.md`
Run source: `reports/benchmark/runs/20260428T_phase20F_full_after_C_D`

## Acceptance

- blocker_rows_classified: `17/17`
- runtime_behavior_change: `none`
- source_identity_change: `none`
- article_span_selection_change: `none`

## Root Cause Counts

| Root Cause | Count |
| --- | ---: |
| `cb_authority_document_selection` | 2 |
| `cb_karar_exception_span` | 1 |
| `kky_yonetmelik_label_bridge` | 2 |
| `mulga_article_span_selection` | 1 |
| `mulga_historical_document_identity` | 1 |
| `teblig_identifier_disambiguation` | 3 |
| `unknown` | 3 |
| `yonetmelik_boundary_document_identity` | 4 |

## Family Counts

| Family | Count |
| --- | ---: |
| `CB_GENELGE` | 1 |
| `CB_KARAR` | 1 |
| `CB_YONETMELIK` | 2 |
| `KANUN` | 1 |
| `KKY` | 2 |
| `MULGA` | 2 |
| `TEBLIGLER` | 3 |
| `TUZUK` | 1 |
| `YONETMELIK` | 4 |

## Dominant Patterns

- `TEBLIGLER`: `teblig_identifier_disambiguation` (3 blocker row)
- `YONETMELIK`: `yonetmelik_boundary_document_identity` (4 blocker row)
- `MULGA`: `mulga_historical_document_identity + mulga_article_span_selection` (2 blocker row)
- `CB_KARAR`: `cb_karar_exception_span` (1 blocker row)

## Audit Rows

| QID | Family | Score | Pass | Root Cause | Recommended Fix | Selected Document | Expected Document | Failure Classes |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| TEB-03 | TEBLIGLER | 5.35 | FAIL | `teblig_identifier_disambiguation` | source_identity: teblig identifier/title/year/issuer arbitration | 6563 SAYILI ELEKTRONİK TİCARETİN DÜZENLENMESİ HAKKINDA KANUNUN 12 NCİ MADDESİNE GÖRE 2026 YILINDA UYGULANACAK… | Vergi Usul Kanunu Genel Tebliği (Sıra No: 509) / 213 sayılı Vergi Usul Kanunu | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only |
| TEB-06 | TEBLIGLER | 3.25 | FAIL | `teblig_identifier_disambiguation` | source_identity: teblig identifier/title/year/issuer arbitration | TİCARET ŞİRKETLERİNDE ANONİM ŞİRKET GENEL KURULLARI DIŞINDA ELEKTRONİK ORTAMDA YAPILACAK KURULLAR HAKKINDA TE… | Ticaret Sicili Tebliği / 6102 sayılı Türk Ticaret Kanunu | missing_gold_document_signal / missing_required_content_signal / wrong_document / hallucinated_identifier / partial_gro… |
| TEB-07 | TEBLIGLER | 1.45 | FAIL | `teblig_identifier_disambiguation` | source_identity: teblig identifier/title/year/issuer arbitration | KİŞİSEL VERİLERİN KORUNMASI KANUNU | 1 Sıra No.lu Elektronik Defter Genel Tebliği / 213 sayılı Vergi Usul Kanunu / 6102 sayılı Türk Ticaret Kanunu | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / hallucinated_identifie… |
| YON-04 | YONETMELIK | 3.25 | FAIL | `yonetmelik_boundary_document_identity` | source_identity: regulation title and family-boundary arbitration | NÜKLEER GÜÇ SANTRALLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | Kişisel Verilerin Silinmesi, Yok Edilmesi veya Anonim Hale Getirilmesi Hakkında Yönetmelik / 6698 sayılı Kişi… | missing_gold_document_signal / missing_required_content_signal / wrong_document / partial_grounding_only |
| YON-05 | YONETMELIK | 3.25 | FAIL | `yonetmelik_boundary_document_identity` | source_identity: regulation title and family-boundary arbitration | ONDOKUZ MAYIS ÜNİVERSİTESİ TAŞINMAZLARININ İDARESİ HAKKINDA YÖNETMELİK | Planlı Alanlar İmar Yönetmeliği / 3194 sayılı İmar Kanunu | missing_gold_document_signal / missing_required_content_signal / wrong_document / hallucinated_identifier / partial_gro… |
| YON-06 | YONETMELIK | 1.45 | FAIL | `yonetmelik_boundary_document_identity` | source_identity: regulation title and family-boundary arbitration | CEZA İNFAZ KURUMLARININ YÖNETİMİ İLE CEZA VE GÜVENLİK TEDBİRLERİNİN İNFAZI HAKKINDA YÖNETMELİK | Konkordato Komiserliği Yönetmeliği / 2004 sayılı İcra ve İflas Kanunu | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / hallucinated_identifie… |
| YON-08 | YONETMELIK | 5.45 | FAIL | `yonetmelik_boundary_document_identity` | source_identity: regulation title and family-boundary arbitration | IŞIK ÜNİVERSİTESİ YATAY GEÇİŞ, ÇİFT ANADAL, YAN DAL VE KREDİ TRANSFERİ YÖNETMELİĞİ | Yükseköğretim Kurumlarında Ön Lisans ve Lisans Düzeyindeki Programlar Arasında Geçiş, Çift Anadal, Yan Dal il… | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only |
| MULGA-01 | MULGA | 0.00 | FAIL | `mulga_article_span_selection` | article_span_selection: repealed provision span evidence | SAYIŞTAY KANUNU | Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği (mülga) / 2547 sayılı Yükseköğretim Kanunu m.54 / ilgili… | auto_fail_triggered / missing_required_content_signal / wrong_article / partial_grounding_only / insufficient_canonical… |
| MULGA-05 | MULGA | 0.00 | FAIL | `mulga_historical_document_identity` | source_identity: repealed/historical document identity | GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ | Geçici %25 kira artış sınırına ilişkin düzenleme (süreli/sona eren rejim) / 6098 sayılı Türk Borçlar Kanunu m… | auto_fail_triggered / missing_gold_document_signal / missing_required_content_signal / wrong_document / wrong_article /… |
| CBKAR-05 | CB_KARAR | 7.19 | PASS | `cb_karar_exception_span` | article_span_selection/source_identity: CB karar primary-vs-support source handling | TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/34) | Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karar / Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karar… | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only |
| CBG-02 | CB_GENELGE | 8.65 | PASS | `unknown` | manual audit before runtime change | Bilgi ve İletişim Güvenliği Tedbirleri ile İlgili | 2019/12 sayılı Bilgi ve İletişim Güvenliği Tedbirleri ile İlgili Cumhurbaşkanlığı Genelgesi | missing_required_content_signal / partial_grounding_only / insufficient_canonical_span_evidence |
| CBY-01 | CB_YONETMELIK | 0.00 | FAIL | `cb_authority_document_selection` | source_identity: CB authority signal required for CB_YONETMELIK | VALİLİK VE KAYMAKAMLIK BİRİMLERİ TEŞKİLAT, GÖREV VE ÇALIŞMA YÖNETMELİĞİ | Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmelik | auto_fail_triggered / missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only |
| CBY-04 | CB_YONETMELIK | 6.85 | FAIL | `cb_authority_document_selection` | source_identity: CB authority signal required for CB_YONETMELIK | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11) | Devlet Arşiv Hizmetleri Hakkında Yönetmelik / 11 sayılı Devlet Arşivleri Başkanlığı Hakkında Cumhurbaşkanlığı… | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only |
| KANUN-12 | KANUN | 1.45 | FAIL | `unknown` | manual audit before runtime change | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | 5651 sayılı İnternet Ortamında Yapılan Yayınların Düzenlenmesi Hakkında Kanun / İnternet Ortamında Yapılan Ya… | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only |
| KKY-01 | KKY | 6.65 | FAIL | `kky_yonetmelik_label_bridge` | source_identity: KKY/YONETMELIK label bridge without family drift | BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKACILIK HİZMETLERİ HAKKINDA YÖNETMELİK | Bankaların Bilgi Sistemleri ve Elektronik Bankacılık Hizmetleri Hakkında Yönetmelik / 5411 sayılı Bankacılık… | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only |
| KKY-03 | KKY | 1.45 | FAIL | `kky_yonetmelik_label_bridge` | source_identity: KKY/YONETMELIK label bridge without family drift | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | Bankaların Bilgi Sistemleri ve Elektronik Bankacılık Hizmetleri Hakkında Yönetmelik / 6698 sayılı Kişisel Ver… | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only |
| TUZUK-05 | TUZUK | 3.25 | FAIL | `unknown` | manual audit before runtime change | GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK | ilgili yürürlükteki tüzük hükümleri | missing_gold_document_signal / missing_required_content_signal / wrong_document / partial_grounding_only |

## Next Phase Input

- Phase 21B should start with `TEBLIGLER` rows where source family/document arbitration drifted: `TEB-03`, `TEB-06`, `TEB-07`.
- `TEB-01` is intentionally not classified as a source/span blocker here because Phase 20F shows exact family/document/article with `auto_fail_triggered`; it belongs to rubric audit backlog unless a generalized source/span pattern is later proven.
- Phase 21C should target `YONETMELIK` document identity and boundary rows: `YON-04`, `YON-05`, `YON-06`, `YON-08`.
- Phase 21D should split `MULGA` into historical document identity (`MULGA-05`) and repealed article/span evidence (`MULGA-01`).
