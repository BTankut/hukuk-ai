# Phase 4 Coverage Backlog

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T065717Z_phase12_full`
- rows_analyzed: 100
- failing_rows: 98
- needs_corpus_acquisition: 26
- needs_metadata_enrichment: 47

## Canonical Metric Counts
- right_document_wrong_article_or_span: 54
- missing_required_content_signal: 98
- partial_grounding_only: 98
- minimum_answer_facts_present_count: 80
- avg_required_fact_coverage_score: 0.943

## Coverage Status Counts
- right_doc_wrong_article_or_span: 54
- not_retrieved_or_not_indexed: 20
- rubric_gap_before_document_alignment: 13
- gold_document_not_retrieved: 6
- temporal_state_gap: 5
- not_backlog: 2

## Corpus Acquisition Candidates
- CBG-01: expected=CB_GENELGE `2024/7 sayılı Tasarruf Tedbirleri ile İlgili Cumhurbaşkanlığı Genelgesi`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- CBG-03: expected=CB_GENELGE `2025/3 sayılı İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi ile İlgili Cumhurbaşkanlığı Genelgesi`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBKAR-01: expected=CB_KARAR `İthalat Rejimi Kararı (Karar Sayısı: 3350) | 2026 yılı değişiklik kararları`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBKAR-05: expected=CB_KARAR `Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karar | Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karara İlişkin Tebliğ (2008-32/34)`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-01: expected=CB_YONETMELIK `Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmelik`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-04: expected=CB_YONETMELIK `Devlet Arşiv Hizmetleri Hakkında Yönetmelik | 11 sayılı Devlet Arşivleri Başkanlığı Hakkında Cumhurbaşkanlığı Kararnamesi`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-05: expected=CB_YONETMELIK `Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği | 2024/7 sayılı Tasarruf Tedbirleri ile İlgili Cumhurbaşkanlığı Genelgesi`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-06: expected=CB_YONETMELIK `Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği | 2026 tarihli değişiklik (Karar Sayısı: 11153)`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KANUN-02: expected=KANUN `4857 sayılı İş Kanunu | Fazla Çalışma ve Fazla Sürelerle Çalışma Yönetmeliği`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KANUN-03: expected=KANUN `4857 sayılı İş Kanunu | Alt İşverenlik Yönetmeliği`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KANUN-06: expected=KANUN `6102 sayılı Türk Ticaret Kanunu`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- KANUN-19: expected=KANUN `7201 sayılı Tebligat Kanunu | Elektronik Tebligat Yönetmeliği`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KHK-03: expected=KHK `703 sayılı Kanun Hükmünde Kararname | ilgili Cumhurbaşkanlığı Kararnameleri`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KKY-02: expected=KKY `Bankalarca Kullanılacak Uzaktan Kimlik Tespiti Yöntemlerine ve Elektronik Ortamda Sözleşme İlişkisinin Kurulmasına İlişkin Yönetmelik`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KKY-04: expected=KKY `Sosyal Sigorta İşlemleri Yönetmeliği | 5510 sayılı Sosyal Sigortalar ve Genel Sağlık Sigortası Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KKY-06: expected=KKY `Elektrik Piyasası Lisans Yönetmeliği | 6446 sayılı Elektrik Piyasası Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KKY-09: expected=KKY `Radyo, Televizyon ve İsteğe Bağlı Yayınların İnternet Ortamından Sunumu Hakkında Yönetmelik | 6112 sayılı Radyo ve Televizyonların Kuruluş ve Yayın Hizmetleri Hakkında Kanun`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KKY-10: expected=KKY `Elektronik Haberleşme Sektöründe Tüketici Hakları Yönetmeliği | 5809 sayılı Elektronik Haberleşme Kanunu`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- TUZUK-05: expected=TUZUK `ilgili yürürlükteki tüzük hükümleri`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- UY-07: expected=UY `ilgili üniversitenin Ön Lisans ve Lisans Eğitim-Öğretim ve Sınav Yönetmeliği | 2547 sayılı Yükseköğretim Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-01: expected=YONETMELIK `Elektronik Tebligat Yönetmeliği | 7201 sayılı Tebligat Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-02: expected=YONETMELIK `Mesafeli Sözleşmeler Yönetmeliği | 6502 sayılı Tüketicinin Korunması Hakkında Kanun`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- YON-05: expected=YONETMELIK `Planlı Alanlar İmar Yönetmeliği | 3194 sayılı İmar Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-06: expected=YONETMELIK `Konkordato Komiserliği Yönetmeliği | 2004 sayılı İcra ve İflas Kanunu`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- YON-07: expected=YONETMELIK `Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği | 6502 sayılı Tüketicinin Korunması Hakkında Kanun`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-08: expected=YONETMELIK `Yükseköğretim Kurumlarında Ön Lisans ve Lisans Düzeyindeki Programlar Arasında Geçiş, Çift Anadal, Yan Dal ile Kurumlar Arası Kredi Transferi Yapılması Esaslarına İlişkin Yönetmelik | ilgili üniversite düzenlemeleri`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval

## Metadata/Selection Candidates
- CBG-01: expected=CB_GENELGE; status=gold_document_not_retrieved; post_top=14 m.0 | Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilme || 15 m.0 | 2026-2028 Dönemi Yatırım Programı Hazırlıkları i
- CBG-02: expected=CB_GENELGE; status=rubric_gap_before_document_alignment; post_top=28 m.0 | Roman Vatandaşlara Yönelik Strateji Belgesi II. Aşama Eylem Planı ile İlgili || 2 m.0 | Dijital Dünyada Çocukların Güçlendirilmesine Yönelik Eylem Plan
- CBG-04: expected=CB_GENELGE; status=rubric_gap_before_document_alignment; post_top=18 m.0 | Sanal Ortamda Yasa Dışı Bahis, Şans Oyunları ve Kumarla Mücadele Eylem Planı (2025-2026) i || 16 m.0 | Türkiye Kooperatifçilik Stratejisi ve Eylem Plan
- CBK-01: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=4 m.162 | BAKANLIKLARA BAĞLI, İLGİLİ, İLİŞKİLİ KURUM VE KURULUŞLAR İLE DİĞER KURUM VE KURULUŞLARIN T || 4 m.162 | BAKANLIKLARA BAĞLI, İLGİLİ, İLİŞKİLİ KURUM VE 
- CBK-03: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=3 m.1 | ÜST KADEME KAMU YÖNETİCİLERİNİN ATANMALARINA İLİŞKİN USÛL VE ESASLAR İLE KAMU KURUM VE KUR || 3 m.5 | ÜST KADEME KAMU YÖNETİCİLERİNİN ATANMALARINA İLİŞK
- CBK-04: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=2 m.1 | GENEL KADRO VE USULÜ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 2) || 2 m.15 | GENEL KADRO VE USULÜ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMES
- CBK-05: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=49 m.3 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 49) || 49 m.19 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI
- CBK-06: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=49 m.19 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 49) || 49 m.3 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI
- CBKAR-02: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=3350 m.17 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m.19 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m.9 | İTHALAT REJİMİ KARARI (KARAR SAYI
- CBKAR-07: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=3350 m.17 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m.4 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m.13 | İTHALAT REJİMİ KARARI (KARAR SAYI
- CBKAR-08: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=9903 m.0 | YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903) || 10019 m.0 | 7452 SAYILI OLAĞANÜSTÜ HAL KAPSAMINDA YERLEŞME VE YAPILAŞMAYA İLİŞK
- CBY-03: expected=CB_YONETMELIK; status=right_doc_wrong_article_or_span; post_top=865 m.19 | BİLGİ EDİNME DEĞERLENDİRME KURULUNUN ÇALIŞMA USUL VE ESASLARI HAKKINDA YÖNETMELİK || 20059668 m.36 | YIPRANAN TARİHİ VE KÜLTÜREL TAŞINMAZ VARLIKLARIN
- CBY-04: expected=CB_YONETMELIK; status=not_retrieved_or_not_indexed; post_top=11 m.9 | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11) || 11 m.4 | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKA
- CBY-05: expected=CB_YONETMELIK; status=not_retrieved_or_not_indexed; post_top=8 m.0 | Ulusal Erişilebilirlik Günü ile İlgili || 14 m.0 | Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilme || 27 m.0 
- KANUN-01: expected=KANUN; status=rubric_gap_before_document_alignment; post_top=24083 m.20 | TÜRKİYE İNSAN HAKLARI VE EŞİTLİK KURUMUNDA SÖZLEŞMELİ PERSONEL İSTİHDAM EDİLMESİNE İLİŞKİN || 24083 m.21 | TÜRKİYE İNSAN HAKLARI VE EŞİTLİK KURUMUN
- KANUN-04: expected=KANUN; status=rubric_gap_before_document_alignment; post_top=16924 m.17 | İŞ SAĞLIĞI VE GÜVENLİĞİ HİZMETLERİ YÖNETMELİĞİ || 16924 m.17 | İŞ SAĞLIĞI VE GÜVENLİĞİ HİZMETLERİ YÖNETMELİĞİ || 16924 m.11 | İŞ SAĞLIĞI VE GÜVENLİ
- KANUN-05: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=KVKK m.9 | KİŞİSEL VERİLERİN KORUNMASI KANUNU || KVKK m.31 | KİŞİSEL VERİLERİN KORUNMASI KANUNU || KVKK m.6 | KİŞİSEL VERİLERİN KORUNMASI KANUNU || KVK m.0 | KU
- KANUN-07: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TTK m.1527 | TÜRK TİCARET KANUNU || TTK m.419 | TÜRK TİCARET KANUNU || TTK m.407 | TÜRK TİCARET KANUNU || TTK m.390 | TÜRK TİCARET KANUNU || TTK m.422 | TÜRK Tİ
- KANUN-08: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=KVKK m.14 | KİŞİSEL VERİLERİN KORUNMASI KANUNU || KVKK m.31 | KİŞİSEL VERİLERİN KORUNMASI KANUNU || KVKK m.13 | KİŞİSEL VERİLERİN KORUNMASI KANUNU || KVKK m.15 
- KANUN-09: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TBK m.647 | TÜRK BORÇLAR KANUNU || TBK m.344 | TÜRK BORÇLAR KANUNU || TBK m.343 | TÜRK BORÇLAR KANUNU || TBK m.0 | TÜRK BORÇLAR KANUNU || TBK m.350 | TÜRK BORÇL
- KANUN-10: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6183 m.58 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN || 6183 m.58 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN || 6183 m.58 | AMME ALACAKLARININ TAHSİ
- KANUN-14: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TKHK m.10 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || TKHK m.11 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || 4077 m.4 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || 20237
- KANUN-15: expected=KANUN; status=rubric_gap_before_document_alignment; post_top=31301 m.20 | YAPI MÜTEAHHİTLERİNİN SINIFLANDIRILMASI VE KAYITLARININ TUTULMASI HAKKINDA YÖNETMELİK || 31301 m.26 | YAPI MÜTEAHHİTLERİNİN SINIFLANDIRILMASI VE KA
- KANUN-16: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6325 m.18 | HUKUK UYUŞMAZLIKLARINDA ARABULUCULUK KANUNU || 6325 m.18 | HUKUK UYUŞMAZLIKLARINDA ARABULUCULUK KANUNU || 6325 m.18 | HUKUK UYUŞMAZLIKLARINDA ARABUL
- KANUN-17: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=IIK m.290 | İCRA VE İFLAS KANUNU || IIK m.289 | İCRA VE İFLAS KANUNU || IIK m.304 | İCRA VE İFLAS KANUNU || IIK m.286 | İCRA VE İFLAS KANUNU || IIK m.306 | İCRA
- KANUN-18: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TBK m.425 | TÜRK BORÇLAR KANUNU || TBK m.423 | TÜRK BORÇLAR KANUNU || TBK m.424 | TÜRK BORÇLAR KANUNU || TBK m.421 | TÜRK BORÇLAR KANUNU || TBK m.92 | TÜRK BORÇ
- KANUN-20: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TMK m.571 | TÜRK MEDENİ KANUNU || TMK m.559 | TÜRK MEDENİ KANUNU || TMK m.300 | TÜRK MEDENİ KANUNU || TMK m.319 | TÜRK MEDENİ KANUNU || TMK m.289 | TÜRK MEDENİ 
- KHK-01: expected=KHK; status=not_backlog; post_top=233 m.2 | KAMU İKTİSADİ TEŞEBBÜSLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME || 233 m.2 | KAMU İKTİSADİ TEŞEBBÜSLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME || 233 m.22 | K
- KHK-02: expected=KHK; status=right_doc_wrong_article_or_span; post_top=7456 m.28 | 6/2/2023 TARİHİNDE MEYDANA GELEN DEPREMLERİN YOL AÇTIĞI EKONOMİK KAYIPLARIN TELAFİSİ İÇİN  || 7456 m.24 | 6/2/2023 TARİHİNDE MEYDANA GELEN DEPREMLER
- KHK-03: expected=KHK; status=not_retrieved_or_not_indexed; post_top=95 m.2 | NÜKLEER DÜZENLEME KURUMUNUN TEŞKİLAT VE GÖREVLERİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (K || 95 m.6 | NÜKLEER DÜZENLEME KURUMUNUN TEŞKİLAT VE GÖREVLER

## Interpretation
- `not_retrieved_or_not_indexed` and `gold_document_not_retrieved` rows are corpus/retrieval coverage candidates, not prompt fixes.
- `candidate_collision_or_metadata` rows indicate the expected family is present but source identity is too weak or lost during selection.
- `right_doc_wrong_article_or_span` rows require article/span selection and evidence support improvements before generation.
- The report is a prioritization backlog; it is not a human legal correctness judgment.
