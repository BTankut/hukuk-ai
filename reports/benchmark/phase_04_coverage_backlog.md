# Phase 4 Coverage Backlog

- source_run_dir: `reports/benchmark/runs/20260421T211914Z_phase4_verification_first_final_v4`
- rows_analyzed: 100
- failing_rows: 97
- needs_corpus_acquisition: 18
- needs_metadata_enrichment: 53

## Coverage Status Counts
- right_doc_wrong_article_or_span: 74
- not_retrieved_or_not_indexed: 12
- gold_document_not_retrieved: 6
- temporal_state_gap: 5
- not_backlog: 3

## Corpus Acquisition Candidates
- CBKAR-01: expected=CB_KARAR `İthalat Rejimi Kararı (Karar Sayısı: 3350) | 2026 yılı değişiklik kararları`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBKAR-08: expected=CB_KARAR `Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903) | önceki yatırım teşvik kararları ve geçiş hükümleri`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-01: expected=CB_YONETMELIK `Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmelik`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-04: expected=CB_YONETMELIK `Devlet Arşiv Hizmetleri Hakkında Yönetmelik | 11 sayılı Devlet Arşivleri Başkanlığı Hakkında Cumhurbaşkanlığı Kararnamesi`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-05: expected=CB_YONETMELIK `Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği | 2024/7 sayılı Tasarruf Tedbirleri ile İlgili Cumhurbaşkanlığı Genelgesi`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- CBY-06: expected=CB_YONETMELIK `Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği | 2026 tarihli değişiklik (Karar Sayısı: 11153)`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KANUN-06: expected=KANUN `6102 sayılı Türk Ticaret Kanunu`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- KANUN-19: expected=KANUN `7201 sayılı Tebligat Kanunu | Elektronik Tebligat Yönetmeliği`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KKY-03: expected=KKY `Bankaların Bilgi Sistemleri ve Elektronik Bankacılık Hizmetleri Hakkında Yönetmelik | 6698 sayılı Kişisel Verilerin Korunması Kanunu | ilgili bilgi güvenliği düzenlemeleri`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- KKY-10: expected=KKY `Elektronik Haberleşme Sektöründe Tüketici Hakları Yönetmeliği | 5809 sayılı Elektronik Haberleşme Kanunu`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- TEB-06: expected=TEBLIGLER `Ticaret Sicili Tebliği | 6102 sayılı Türk Ticaret Kanunu`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- TUZUK-05: expected=TUZUK `ilgili yürürlükteki tüzük hükümleri`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- UY-07: expected=UY `ilgili üniversitenin Ön Lisans ve Lisans Eğitim-Öğretim ve Sınav Yönetmeliği | 2547 sayılı Yükseköğretim Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-01: expected=YONETMELIK `Elektronik Tebligat Yönetmeliği | 7201 sayılı Tebligat Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-02: expected=YONETMELIK `Mesafeli Sözleşmeler Yönetmeliği | 6502 sayılı Tüketicinin Korunması Hakkında Kanun`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- YON-05: expected=YONETMELIK `Planlı Alanlar İmar Yönetmeliği | 3194 sayılı İmar Kanunu`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval
- YON-06: expected=YONETMELIK `Konkordato Komiserliği Yönetmeliği | 2004 sayılı İcra ve İflas Kanunu`; status=gold_document_not_retrieved; blocker=expected family present but gold document not seen in initial candidates
- YON-08: expected=YONETMELIK `Yükseköğretim Kurumlarında Ön Lisans ve Lisans Düzeyindeki Programlar Arasında Geçiş, Çift Anadal, Yan Dal ile Kurumlar Arası Kredi Transferi Yapılması Esaslarına İlişkin Yönetmelik | ilgili üniversite düzenlemeleri`; status=not_retrieved_or_not_indexed; blocker=expected family absent from initial retrieval

## Metadata/Selection Candidates
- CBG-01: expected=CB_GENELGE; status=right_doc_wrong_article_or_span; post_top=14 m.0 | Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilme || 15 m.0 | 2026-2028 Dönemi Yatırım Programı Hazırlıkları i
- CBG-02: expected=CB_GENELGE; status=right_doc_wrong_article_or_span; post_top=26 m.0 | Yurt Dışında Yürütülen Faaliyetlerde Dikkat Edilmesi Gereken Hususlar ile İlgili || 25 m.0 | Bazı Genelgelerin Yürürlükten Kaldırılması ile İlgili || 2
- CBG-03: expected=CB_GENELGE; status=right_doc_wrong_article_or_span; post_top=18 m.0 | Sanal Ortamda Yasa Dışı Bahis, Şans Oyunları ve Kumarla Mücadele Eylem Planı (2025-2026) i || 19 m.0 | Kadına Yönelik Şiddetle Mücadele V. Ulusal Eylem
- CBG-04: expected=CB_GENELGE; status=right_doc_wrong_article_or_span; post_top=18 m.0 | Sanal Ortamda Yasa Dışı Bahis, Şans Oyunları ve Kumarla Mücadele Eylem Planı (2025-2026) i || 19 m.0 | Kadına Yönelik Şiddetle Mücadele V. Ulusal Eylem
- CBK-01: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=4 m.162 | BAKANLIKLARA BAĞLI, İLGİLİ, İLİŞKİLİ KURUM VE KURULUŞLAR İLE DİĞER KURUM VE KURULUŞLARIN T || 4 m.162 | BAKANLIKLARA BAĞLI, İLGİLİ, İLİŞKİLİ KURUM VE 
- CBK-03: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=3 m.1 | ÜST KADEME KAMU YÖNETİCİLERİNİN ATANMALARINA İLİŞKİN USÛL VE ESASLAR İLE KAMU KURUM VE KUR || 3 m.5 | ÜST KADEME KAMU YÖNETİCİLERİNİN ATANMALARINA İLİŞK
- CBK-04: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=2 m.1 | GENEL KADRO VE USULÜ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 2) || 2 m.15 | GENEL KADRO VE USULÜ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMES
- CBK-05: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=49 m.3 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 49) || 49 m.19 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI
- CBK-06: expected=CB_KARARNAME; status=right_doc_wrong_article_or_span; post_top=49 m.19 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 49) || 49 m.12 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞ
- CBKAR-02: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=3350 m.17 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m.19 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 3350 m.13 | İTHALAT REJİMİ KARARI (KARAR SAY
- CBKAR-04: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=15 m.0 | 2026-2028 Dönemi Yatırım Programı Hazırlıkları ile İlgili || 14 m.0 | Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine 
- CBKAR-05: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=11990 m.8 | TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/ || 24355 m.3 | TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 S
- CBKAR-07: expected=CB_KARAR; status=right_doc_wrong_article_or_span; post_top=3350 m.4 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) || 4115 m.16 | İHRACATTA KOTA VE TARİFE KONTENJANI BELİRLENMESİ VE İDARESİNE İLİŞKİN YÖNETMELİK || 19132 m
- CBKAR-08: expected=CB_KARAR; status=not_retrieved_or_not_indexed; post_top=6763 m.20 | TÜRK TİCARET KANUNUNUN MER'İYET VE TATBİK ŞEKLİ HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜ || 6763 m.12 | TÜRK TİCARET KANUNUNUN MER'İYET VE TATBİK 
- CBY-01: expected=CB_YONETMELIK; status=not_retrieved_or_not_indexed; post_top=20146289 m.15 | TERÖRLE MÜCADELE KANUNU KAPSAMINDA KAMU KURUM VE KURULUŞLARINDA İSTİHDAM EDİLECEKLER HAKKI || 20146289 m.13 | TERÖRLE MÜCADELE KANUNU KAPSAMINDA
- CBY-02: expected=CB_YONETMELIK; status=right_doc_wrong_article_or_span; post_top=39610 m.6 | KAMU BİLİŞİM HİZMET ALIMI KAPSAMINDA KATILIMCILARIN YETKİLENDİRİLMESİ HAKKINDA YÖNETMELİK || 20146289 m.8 | TERÖRLE MÜCADELE KANUNU KAPSAMINDA KAMU 
- CBY-04: expected=CB_YONETMELIK; status=not_retrieved_or_not_indexed; post_top=11 m.9 | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11) || 11 m.4 | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKA
- CBY-05: expected=CB_YONETMELIK; status=not_retrieved_or_not_indexed; post_top=8 m.0 | Ulusal Erişilebilirlik Günü ile İlgili || 14 m.0 | Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilme || 27 m.0 
- KANUN-01: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=24083 m.20 | TÜRKİYE İNSAN HAKLARI VE EŞİTLİK KURUMUNDA SÖZLEŞMELİ PERSONEL İSTİHDAM EDİLMESİNE İLİŞKİN || 24083 m.21 | TÜRKİYE İNSAN HAKLARI VE EŞİTLİK KURUMUN
- KANUN-02: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=IK m.14 | İŞ KANUNU || IK m.41 | İŞ KANUNU || 5003 m.6 | KARAYOLLARI GENEL MÜDÜRLÜĞÜNCE YAPILACAK BÖLÜNMÜŞ YOL İNŞASINDA UYGULANACAK USUL VE ESASLA || TBK m.423
- KANUN-04: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=16924 m.17 | İŞ SAĞLIĞI VE GÜVENLİĞİ HİZMETLERİ YÖNETMELİĞİ || 16924 m.17 | İŞ SAĞLIĞI VE GÜVENLİĞİ HİZMETLERİ YÖNETMELİĞİ || 16924 m.11 | İŞ SAĞLIĞI VE GÜVENLİ
- KANUN-05: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=KVKK m.9 | KİŞİSEL VERİLERİN KORUNMASI KANUNU || KVK m.0 | KURUMLAR VERGİSİ KANUNU || KVK m.0 | KURUMLAR VERGİSİ KANUNU || KVKK m.31 | KİŞİSEL VERİLERİN KORUNMA
- KANUN-07: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TTK m.1527 | TÜRK TİCARET KANUNU || TTK m.390 | TÜRK TİCARET KANUNU || TTK m.644 | TÜRK TİCARET KANUNU || TTK m.422 | TÜRK TİCARET KANUNU || TTK m.420 | TÜRK Tİ
- KANUN-08: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=KVKK m.14 | KİŞİSEL VERİLERİN KORUNMASI KANUNU || KVKK m.31 | KİŞİSEL VERİLERİN KORUNMASI KANUNU || KVKK m.13 | KİŞİSEL VERİLERİN KORUNMASI KANUNU || KVKK m.15 
- KANUN-09: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TBK m.647 | TÜRK BORÇLAR KANUNU || TBK m.344 | TÜRK BORÇLAR KANUNU || TBK m.343 | TÜRK BORÇLAR KANUNU || TBK m.0 | TÜRK BORÇLAR KANUNU || TBK m.350 | TÜRK BORÇL
- KANUN-10: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6183 m.58 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN || 6183 m.58 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN || 6183 m.58 | AMME ALACAKLARININ TAHSİ
- KANUN-14: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=TKHK m.10 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || TKHK m.11 | TÜKETİCİNİN KORUNMASI HAKKINDA KANUN || 20237 m.10 | MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ || 19782 m
- KANUN-15: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=31301 m.20 | YAPI MÜTEAHHİTLERİNİN SINIFLANDIRILMASI VE KAYITLARININ TUTULMASI HAKKINDA YÖNETMELİK || 40109 m.6 | YAPI DENETİM KURULUŞLARININ FAALİYETLERİNİN DE
- KANUN-16: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=6325 m.18 | HUKUK UYUŞMAZLIKLARINDA ARABULUCULUK KANUNU || 6325 m.18 | HUKUK UYUŞMAZLIKLARINDA ARABULUCULUK KANUNU || 6325 m.18 | HUKUK UYUŞMAZLIKLARINDA ARABUL
- KANUN-17: expected=KANUN; status=right_doc_wrong_article_or_span; post_top=IIK m.290 | İCRA VE İFLAS KANUNU || IIK m.289 | İCRA VE İFLAS KANUNU || IIK m.304 | İCRA VE İFLAS KANUNU || IIK m.286 | İCRA VE İFLAS KANUNU || IIK m.306 | İCRA

## Interpretation
- `not_retrieved_or_not_indexed` and `gold_document_not_retrieved` rows are corpus/retrieval coverage candidates, not prompt fixes.
- `candidate_collision_or_metadata` rows indicate the expected family is present but source identity is too weak or lost during selection.
- `right_doc_wrong_article_or_span` rows require article/span selection and evidence support improvements before generation.
- The report is a prioritization backlog; it is not a human legal correctness judgment.
