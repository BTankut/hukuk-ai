# Phase 4 Coverage Backlog

- source_run_dir: `reports/benchmark/runs/20260423T124900Z_phase13_full`
- rows_analyzed: 100
- failing_rows: 96
- needs_corpus_acquisition: 20
- needs_metadata_enrichment: 52

## Canonical Metric Counts
- right_document_wrong_article_or_span: 57
- missing_required_content_signal: 96
- partial_grounding_only: 96
- minimum_answer_facts_present_count: 81
- avg_required_fact_coverage_score: 0.859

## Coverage Status Counts
- right_doc_wrong_article_or_span: 57
- rubric_gap_before_document_alignment: 16
- not_retrieved_or_not_indexed: 15
- gold_document_not_retrieved: 5
- not_backlog: 4
- temporal_state_gap: 3

## Corpus Acquisition Candidates
- CBG-01: expected=CB_GENELGE `2024/7 sayılı Tasarruf Tedbirleri ile İlgili Cumhurbaşkanlığı Genelgesi`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- CBKAR-04: expected=CB_KARAR `2026 Yılı Kamu Yatırım Programının Kabulü ve Uygulanmasına Dair Karar (Karar Sayısı: 10868)`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBKAR-05: expected=CB_KARAR `Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karar | Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karara İlişkin Tebliğ (2008-32/34)`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBKAR-06: expected=CB_KARAR `2026 Yılı Kamu Yatırım Programının Kabulü ve Uygulanmasına Dair Karar (Karar Sayısı: 10868)`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBKAR-08: expected=CB_KARAR `Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903) | önceki yatırım teşvik kararları ve geçiş hükümleri`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-03: expected=CB_YONETMELIK `Devlet Arşiv Hizmetleri Hakkında Yönetmelik (2019)`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- CBY-04: expected=CB_YONETMELIK `Devlet Arşiv Hizmetleri Hakkında Yönetmelik | 11 sayılı Devlet Arşivleri Başkanlığı Hakkında Cumhurbaşkanlığı Kararnamesi`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KANUN-03: expected=KANUN `4857 sayılı İş Kanunu | Alt İşverenlik Yönetmeliği`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KANUN-04: expected=KANUN `6698 sayılı Kişisel Verilerin Korunması Kanunu | Kişisel Verilerin Silinmesi, Yok Edilmesi veya Anonim Hale Getirilmesi Hakkında Yönetmelik`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KHK-03: expected=KHK `703 sayılı Kanun Hükmünde Kararname | ilgili Cumhurbaşkanlığı Kararnameleri`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KKY-02: expected=KKY `Bankalarca Kullanılacak Uzaktan Kimlik Tespiti Yöntemlerine ve Elektronik Ortamda Sözleşme İlişkisinin Kurulmasına İlişkin Yönetmelik`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KKY-06: expected=KKY `Elektrik Piyasası Lisans Yönetmeliği | 6446 sayılı Elektrik Piyasası Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KKY-09: expected=KKY `Radyo, Televizyon ve İsteğe Bağlı Yayınların İnternet Ortamından Sunumu Hakkında Yönetmelik | 6112 sayılı Radyo ve Televizyonların Kuruluş ve Yayın Hizmetleri Hakkında Kanun`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- TEB-06: expected=TEBLIGLER `Ticaret Sicili Tebliği | 6102 sayılı Türk Ticaret Kanunu`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- TUZUK-04: expected=TUZUK `6331 sayılı İş Sağlığı ve Güvenliği Kanunu | ilgili İSG yönetmelikleri | eski İSG tüzükleri`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- TUZUK-05: expected=TUZUK `ilgili yürürlükteki tüzük hükümleri`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- YON-02: expected=YONETMELIK `Mesafeli Sözleşmeler Yönetmeliği | 6502 sayılı Tüketicinin Korunması Hakkında Kanun`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-05: expected=YONETMELIK `Planlı Alanlar İmar Yönetmeliği | 3194 sayılı İmar Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-07: expected=YONETMELIK `Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği | 6502 sayılı Tüketicinin Korunması Hakkında Kanun`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-08: expected=YONETMELIK `Yükseköğretim Kurumlarında Ön Lisans ve Lisans Düzeyindeki Programlar Arasında Geçiş, Çift Anadal, Yan Dal ile Kurumlar Arası Kredi Transferi Yapılması Esaslarına İlişkin Yönetmelik | ilgili üniversite düzenlemeleri`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval

## Metadata/Selection Candidates
- CBG-01: expected=CB_GENELGE; status=gold_document_not_retrieved; post_top=14 m.0 | Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilme || 15 m.0 | 2026-2028 Dönemi Yatırım Programı Hazırlıkları i
- CBG-03: expected=CB_GENELGE; status=rubric_gap_before_document_alignment; post_top=18 m.0 | Sanal Ortamda Yasa Dışı Bahis, Şans Oyunları ve Kumarla Mücadele Eylem Planı (2025-2026) i || 16 m.0 | Türkiye Kooperatifçilik Stratejisi ve Eylem Plan
- CBK-01: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=1 m.96 | CUMHURBAŞKANLIĞI TEŞKİLATI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 1) || 1 m.96 | CUMHURBAŞKANLIĞI TEŞKİLATI HAKKINDA CUMHURBAŞKANLI
- CBK-03: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=3 m.1 | ÜST KADEME KAMU YÖNETİCİLERİNİN ATANMALARINA İLİŞKİN USÛL VE ESASLAR İLE KAMU KURUM VE KUR || 3 m.2 | ÜST KADEME KAMU YÖNETİCİLERİNİN ATANMALARINA İLİŞK
- CBK-04: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=2 m.1 | GENEL KADRO VE USULÜ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 2) || 2 m.4 | GENEL KADRO VE USULÜ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ
- CBK-05: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=49 m.1 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 49) || 49 m.6 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI 
- CBKAR-02: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=3350 m.17 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m.19 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m.2 | İTHALAT REJİMİ KARARI (KARAR SAYI
- CBKAR-04: expected=CB_KARAR; status=not_retrieved_or_not_indexed; post_top=15 m.0 | 2026-2028 Dönemi Yatırım Programı Hazırlıkları ile İlgili || 18 m.0 | Sanal Ortamda Yasa Dışı Bahis, Şans Oyunları ve Kumarla Mücadele Eylem Planı (202
- CBKAR-06: expected=CB_KARAR; status=not_retrieved_or_not_indexed; post_top=15 m.0 | 2026-2028 Dönemi Yatırım Programı Hazırlıkları ile İlgili || 21 m.0 | Ulusal Genç İstihdam Stratejisi ve Eylem Planı (2021-2023) ile İlgili || 23 m.0 |
- CBKAR-07: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=8688 m.0 | İTHALAT REJİMİ KARARINDA DEĞİŞİKLİK YAPILMASINA İLİŞKİN KARAR (KARAR SAYISI: 8688) || 3350 m.17 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 
- CBKAR-08: expected=CB_KARAR; status=not_retrieved_or_not_indexed; post_top=10019 m.0 | 7452 SAYILI OLAĞANÜSTÜ HAL KAPSAMINDA YERLEŞME VE YAPILAŞMAYA İLİŞKİN CUMHURBAŞKANLIĞI KAR || 7700 m.6 | 7452 SAYILI OLAĞANÜSTÜ HAL KAPSAMINDA YERLE
- CBY-02: expected=CB_YONETMELIK; status=right_doc_wrong_article_or_span; post_top=200915611 m.17 | KAMU İHALE KURUMU TEŞKİLATI VE PERSONELİNİN ÇALIŞMA USUL VE ESASLARI HAKKINDA YÖNETMELİK || 200915611 m.47 | KAMU İHALE KURUMU TEŞKİLATI VE PER
- CBY-03: expected=CB_YONETMELIK; status=gold_document_not_retrieved; post_top=201811993 m.8 | 4735 SAYILI KAMU İHALE SÖZLEŞMELERİ KANUNUNUN GEÇİCİ 3 ÜNCÜ MADDESİ UYARINCA HESAPLANACAK  || 5649 m.16 | GÜVENLİK SORUŞTURMASI VE ARŞİV ARAŞTIR
- CBY-05: expected=CB_YONETMELIK; status=right_doc_wrong_article_or_span; post_top=20046801 m.9 | KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ || 20046801 m.5 | KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ || 20
- CBY-06: expected=CB_YONETMELIK; status=right_doc_wrong_article_or_span; post_top=20046801 m.5 | KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ || 20046801 m.14 | KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ || 2
- KANUN-01: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=IK m.18 | İŞ KANUNU || TBK m.438 | TÜRK BORÇLAR KANUNU || IK m.31 | İŞ KANUNU || TBK m.432 | TÜRK BORÇLAR KANUNU || IK m.8 | İŞ KANUNU
- KANUN-05: expected=KANUN; status=rubric_gap_before_document_alignment; post_top=6763 m.26 | TÜRK TİCARET KANUNUNUN MER'İYET VE TATBİK ŞEKLİ HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜ || 6763 m.25 | TÜRK TİCARET KANUNUNUN MER'İYET VE TATBİK 
- KANUN-06: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6762 m.511 | TÜRK TİCARET KANUNUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ || TTK m.338 | TÜRK TİCARET KANUNU || 6103 m.23 | TÜRK TİCARET KANUNUNUN YÜRÜRLÜĞÜ VE UYGUL
- KANUN-07: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TTK m.1527 | TÜRK TİCARET KANUNU || TTK m.419 | TÜRK TİCARET KANUNU || TTK m.390 | TÜRK TİCARET KANUNU || 1479 m.9 | ESNAF VE SANATKARLAR VE DİĞER BAĞIMSIZ ÇALI
- KANUN-08: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TKHK m.18 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || TKHK m.43 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || 20447 m.7 | TAKSİTLE SATIŞ SÖZLEŞMELERİ HAKKINDA YÖNETME
- KANUN-09: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TBK m.344 | TÜRK BORÇLAR KANUNU || TBK m.647 | TÜRK BORÇLAR KANUNU || 5737 m.20 | VAKIFLAR KANUNU || TKHK m.26 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || TBK m.3
- KANUN-10: expected=KANUN; status=rubric_gap_before_document_alignment; post_top=6183 m.60 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDAKİ KANUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ || 6183 m.60 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN |
- KANUN-11: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6183 m.1 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN || 6183 m.1 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN || 4854 m.3 | BAZI KANUNLARDAKİ CEZALARIN
- KANUN-13: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6331 m.10 | İŞ SAĞLIĞI VE GÜVENLİĞİ KANUNU || 6331 m.25 | İŞ SAĞLIĞI VE GÜVENLİĞİ KANUNU || 506 m.11 | SOSYAL SİGORTALAR KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜM
- KANUN-14: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TBK m.227 | TÜRK BORÇLAR KANUNU || TBK m.226 | TÜRK BORÇLAR KANUNU || TKHK m.10 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || TKHK m.11 | TÜKETİCİNİN KORUNMASI HAKK
- KANUN-15: expected=KANUN; status=rubric_gap_before_document_alignment; post_top=2981 m.9 | İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA UYGULANACAK BAZI İŞLEMLER VE 6785 SAYILI İMAR || 2981 m.9 | İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA
- KANUN-17: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=IIK m.290 | İCRA VE İFLAS KANUNU || IIK m.289 | İCRA VE İFLAS KANUNU || IIK m.304 | İCRA VE İFLAS KANUNU || 5684 m.26 | SİGORTACILIK KANUNU || 6762 m.297 | TÜRK
- KANUN-18: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TBK m.424 | TÜRK BORÇLAR KANUNU || 1475 m.54 | İŞ KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ || 1475 m.52 | İŞ KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ || I
- KANUN-19: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=7201 m.60 | TEBLİGAT KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ || 5549 m.9 | SUÇ GELİRLERİNİN AKLANMASININ ÖNLENMESİ HAKKINDA KANUN || 7201 m.56 | TEBLİGAT KA
- KANUN-20: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TMK m.571 | TÜRK MEDENİ KANUNU || TMK m.559 | TÜRK MEDENİ KANUNU || TTK m.1188 | TÜRK TİCARET KANUNU || TMK m.300 | TÜRK MEDENİ KANUNU || TMK m.319 | TÜRK MEDEN

## Interpretation
- `not_retrieved_or_not_indexed` and `gold_document_not_retrieved` rows are corpus/retrieval coverage candidates, not prompt fixes.
- `candidate_collision_or_metadata` rows indicate the expected family is present but source identity is too weak or lost during selection.
- `right_doc_wrong_article_or_span` rows require article/span selection and evidence support improvements before generation.
- The report is a prioritization backlog; it is not a human legal correctness judgment.
