# Phase 4 Coverage Backlog

- source_run_dir: `reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic`
- rows_analyzed: 100
- failing_rows: 96
- needs_corpus_acquisition: 18
- needs_metadata_enrichment: 43

## Canonical Metric Counts
- right_document_wrong_article_or_span: 70
- missing_required_content_signal: 96
- partial_grounding_only: 96
- minimum_answer_facts_present_count: 75
- avg_required_fact_coverage_score: 0.882

## Coverage Status Counts
- right_doc_wrong_article_or_span: 70
- not_retrieved_or_not_indexed: 11
- gold_document_not_retrieved: 7
- rubric_gap_before_document_alignment: 5
- not_backlog: 4
- temporal_state_gap: 3

## Corpus Acquisition Candidates
- CBG-01: expected=CB_GENELGE `2024/7 sayılı Tasarruf Tedbirleri ile İlgili Cumhurbaşkanlığı Genelgesi`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- CBG-04: expected=CB_GENELGE `2025/3 sayılı İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi ile İlgili Cumhurbaşkanlığı Genelgesi`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- CBKAR-05: expected=CB_KARAR `Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karar | Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karara İlişkin Tebliğ (2008-32/34)`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-01: expected=CB_YONETMELIK `Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmelik`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-04: expected=CB_YONETMELIK `Devlet Arşiv Hizmetleri Hakkında Yönetmelik | 11 sayılı Devlet Arşivleri Başkanlığı Hakkında Cumhurbaşkanlığı Kararnamesi`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KANUN-02: expected=KANUN `4857 sayılı İş Kanunu | Fazla Çalışma ve Fazla Sürelerle Çalışma Yönetmeliği`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- KANUN-03: expected=KANUN `4857 sayılı İş Kanunu | Alt İşverenlik Yönetmeliği`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KANUN-04: expected=KANUN `6698 sayılı Kişisel Verilerin Korunması Kanunu | Kişisel Verilerin Silinmesi, Yok Edilmesi veya Anonim Hale Getirilmesi Hakkında Yönetmelik`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KANUN-18: expected=KANUN `4857 sayılı İş Kanunu`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- MULGA-03: expected=MULGA `1994 tarihli Tapu Sicili Tüzüğü (mülga) | 2013 tarihli Tapu Sicili Tüzüğü`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- MULGA-04: expected=MULGA `551/554/555/556 sayılı KHK'lar (mülga/yerine yeni kanun gelen rejim) | 6769 sayılı Sınai Mülkiyet Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- TEB-06: expected=TEBLIGLER `Ticaret Sicili Tebliği | 6102 sayılı Türk Ticaret Kanunu`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- TUZUK-04: expected=TUZUK `6331 sayılı İş Sağlığı ve Güvenliği Kanunu | ilgili İSG yönetmelikleri | eski İSG tüzükleri`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- TUZUK-05: expected=TUZUK `ilgili yürürlükteki tüzük hükümleri`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- YON-02: expected=YONETMELIK `Mesafeli Sözleşmeler Yönetmeliği | 6502 sayılı Tüketicinin Korunması Hakkında Kanun`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-05: expected=YONETMELIK `Planlı Alanlar İmar Yönetmeliği | 3194 sayılı İmar Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-06: expected=YONETMELIK `Konkordato Komiserliği Yönetmeliği | 2004 sayılı İcra ve İflas Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-08: expected=YONETMELIK `Yükseköğretim Kurumlarında Ön Lisans ve Lisans Düzeyindeki Programlar Arasında Geçiş, Çift Anadal, Yan Dal ile Kurumlar Arası Kredi Transferi Yapılması Esaslarına İlişkin Yönetmelik | ilgili üniversite düzenlemeleri`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval

## Metadata/Selection Candidates
- CBG-01: expected=CB_GENELGE; status=gold_document_not_retrieved; post_top=14 m.0 | Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilme
- CBK-01: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=1 m.96 | CUMHURBAŞKANLIĞI TEŞKİLATI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 1) || 1 m.96 | CUMHURBAŞKANLIĞI TEŞKİLATI HAKKINDA CUMHURBAŞKANLI
- CBK-03: expected=CB_KARARNAME; status=not_backlog; post_top=3 m.1 | ÜST KADEME KAMU YÖNETİCİLERİNİN ATANMALARINA İLİŞKİN USÛL VE ESASLAR İLE KAMU KURUM VE KUR || 3 m.13 | ÜST KADEME KAMU YÖNETİCİLERİNİN ATANMALARINA İLİŞ
- CBK-04: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=2 m.1 | GENEL KADRO VE USULÜ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 2) || 2 m.4 | GENEL KADRO VE USULÜ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ
- CBK-05: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=49 m.1 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 49) || 49 m.6 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI 
- CBKAR-01: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=1676 m.2 | NAYLON VEYA DİĞER POLİAMİDLERDEN İPLİKLERİN İTHALATINDA KORUNMA ÖNLEMİ UYGULANMASINA İLİŞK || 1013 m.6 | BAZI BAKANLAR KURULU KARARLARINDA DEĞİŞİKLİK
- CBKAR-02: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=3350 m.17 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m.19 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m.2 | İTHALAT REJİMİ KARARI (KARAR SAYI
- CBKAR-07: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=8688 m.0 | İTHALAT REJİMİ KARARINDA DEĞİŞİKLİK YAPILMASINA İLİŞKİN KARAR (KARAR SAYISI: 8688) || 3350 m.4 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m
- CBY-02: expected=CB_YONETMELIK; status=right_doc_wrong_article_or_span; post_top=200915611 m.17 | KAMU İHALE KURUMU TEŞKİLATI VE PERSONELİNİN ÇALIŞMA USUL VE ESASLARI HAKKINDA YÖNETMELİK || 200915611 m.47 | KAMU İHALE KURUMU TEŞKİLATI VE PER
- CBY-03: expected=CB_YONETMELIK; status=right_doc_wrong_article_or_span; post_top=201811993 m.8 | 4735 SAYILI KAMU İHALE SÖZLEŞMELERİ KANUNUNUN GEÇİCİ 3 ÜNCÜ MADDESİ UYARINCA HESAPLANACAK  || 20047189 m.40 | BİLGİ EDİNME HAKKI KANUNUNUN UYGUL
- CBY-05: expected=CB_YONETMELIK; status=right_doc_wrong_article_or_span; post_top=20046801 m.9 | KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ || 20046801 m.5 | KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ || 20
- CBY-06: expected=CB_YONETMELIK; status=right_doc_wrong_article_or_span; post_top=20046801 m.5 | KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ || 20046801 m.14 | KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ || 2
- KANUN-01: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=IK m.18 | İŞ KANUNU || IK m.31 | İŞ KANUNU || IK m.8 | İŞ KANUNU || IK m.21 | İŞ KANUNU || IK m.20 | İŞ KANUNU
- KANUN-06: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6762 m.511 | TÜRK TİCARET KANUNUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ || TTK m.587 | TÜRK TİCARET KANUNU || TTK m.566 | TÜRK TİCARET KANUNU || TTK m.212 | TÜRK T
- KANUN-07: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TTK m.1527 | TÜRK TİCARET KANUNU || TTK m.390 | TÜRK TİCARET KANUNU
- KANUN-08: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TKHK m.18 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || TKHK m.43 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || 20237 m.11 | MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ || 20237 m
- KANUN-09: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TBK m.344 | TÜRK BORÇLAR KANUNU || TBK m.647 | TÜRK BORÇLAR KANUNU || TBK m.343 | TÜRK BORÇLAR KANUNU || TKHK m.26 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN
- KANUN-10: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6183 m.60 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDAKİ KANUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ || 6183 m.60 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN |
- KANUN-11: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6183 m.1 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN || 6183 m.1 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN || 4854 m.3 | BAZI KANUNLARDAKİ CEZALARIN
- KANUN-13: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6331 m.10 | İŞ SAĞLIĞI VE GÜVENLİĞİ KANUNU || 16925 m.12 | İŞ SAĞLIĞI VE GÜVENLİĞİ RİSK DEĞERLENDİRMESİ YÖNETMELİĞİ || 18709 m.6 | KİMYASAL MADDELERLE ÇALIŞMALA
- KANUN-14: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TBK m.227 | TÜRK BORÇLAR KANUNU || TBK m.226 | TÜRK BORÇLAR KANUNU || TKHK m.10 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || TKHK m.11 | TÜKETİCİNİN KORUNMASI HAKK
- KANUN-15: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=2981 m.9 | İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA UYGULANACAK BAZI İŞLEMLER VE 6785 SAYILI İMAR || 2981 m.9 | İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA
- KANUN-17: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=IIK m.290 | İCRA VE İFLAS KANUNU || IIK m.289 | İCRA VE İFLAS KANUNU || IIK m.304 | İCRA VE İFLAS KANUNU || 6384 m.4 | TAZMİNAT KOMİSYONUNUN GÖREVLERİ İLE ÇALIŞ
- KANUN-19: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=7201 m.60 | TEBLİGAT KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ || 7201 m.56 | TEBLİGAT KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ || 7201 m.1 | TEBLİGAT KANU
- KANUN-20: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TMK m.571 | TÜRK MEDENİ KANUNU || TMK m.559 | TÜRK MEDENİ KANUNU || TMK m.300 | TÜRK MEDENİ KANUNU || TMK m.319 | TÜRK MEDENİ KANUNU || TTK m.1188 | TÜRK TİCARE
- KHK-01: expected=KHK; status=right_doc_wrong_article_or_span; post_top=233 m.2 | KAMU İKTİSADİ TEŞEBBÜSLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME || 233 m.2 | KAMU İKTİSADİ TEŞEBBÜSLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME || 233 m.22 | K
- KHK-02: expected=KHK; status=right_doc_wrong_article_or_span; post_top=375 m.31 | 657 SAYILI DEVLET MEMURLARI KANUNU, 926 SAYILI TÜRK SİLAHLI KUVVETLERİ PERSONEL KANUNU, 28 || 375 m.1 | 657 SAYILI DEVLET MEMURLARI KANUNU, 926 SAYIL
- KHK-03: expected=KHK; status=right_doc_wrong_article_or_span; post_top=703 m.225 | ANAYASADA YAPILAN DEĞİŞİKLİKLERE UYUM SAĞLANMASI AMACIYLA BAZI KANUN VE KANUN HÜKMÜNDE KAR
- KHK-04: expected=KHK; status=right_doc_wrong_article_or_span; post_top=233 m.3 | KAMU İKTİSADİ TEŞEBBÜSLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME || 233 m.63 | KAMU İKTİSADİ TEŞEBBÜSLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME || 233 m.0 | K
- KKY-03: expected=KKY; status=right_doc_wrong_article_or_span; post_top=34360 m.3 | BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKACILIK HİZMETLERİ HAKKINDA YÖNETMELİK || 34360 m.13 | BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKAC

## Interpretation
- `not_retrieved_or_not_indexed` and `gold_document_not_retrieved` rows are corpus/retrieval coverage candidates, not prompt fixes.
- `candidate_collision_or_metadata` rows indicate the expected family is present but source identity is too weak or lost during selection.
- `right_doc_wrong_article_or_span` rows require article/span selection and evidence support improvements before generation.
- The report is a prioritization backlog; it is not a human legal correctness judgment.
