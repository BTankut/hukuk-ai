# Phase 14 Document Identity Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic`
- rows_analyzed: 100
- wrong_document: 13
- hallucinated_identifier: 21
- hallucinated_source_count: 13
- selected_article_equals_claimed_article_count: 80
- right_document_wrong_article_or_span: 70
- avg_document_identity_score: 124.288

## Metadata Identity Strength
- strong: 85
- medium: 12
- weak: 3

## Identity Lock Strength
- weak: 53
- strong: 29
- medium: 18

## Metadata Lookup Source
- none: 59
- title_ngram_family_lookup: 21
- exact_identifier_lookup: 12
- normalized_title_lookup: 7
- issuer_family_lookup: 1

## Title Match Type
- none: 55
- medium_overlap: 30
- weak_overlap: 8
- strong_overlap: 6
- exact_phrase: 1

## Identifier Integrity
- exact: 72
- unverified_claim_suppressed: 16
- replaced_by_selected_evidence: 7
- selected_evidence_identifier_suppressed: 5

## Article Alignment
- exact: 70
- none: 16
- title_only: 12
- neighbor: 2

## Worst Rows
- MULGA-02: selected=DEVLET ARŞİV HİZMETLERİ HAKKINDA YÖNETMELİK, expected_family=MULGA, claimed_family=YONETMELIK, metadata_lookup=normalized_title_lookup, identity=strong/medium_overlap/not_requested, article_alignment=exact, score=0.00
- MULGA-03: selected=TAPU SİCİLİ TÜZÜĞÜ, expected_family=MULGA, claimed_family=TUZUK, metadata_lookup=none, identity=medium/exact_phrase/not_requested, article_alignment=exact, score=0.00
- KANUN-04: selected=DIŞ TİCARETTE RİSK ESASLI KONTROL SİSTEMİ TEBLİĞİ (ÜRÜN GÜVENLİĞİ VE DENETİMİ: 2011/53), expected_family=KANUN, claimed_family=TEBLIGLER, metadata_lookup=title_ngram_family_lookup, identity=strong/medium_overlap/not_requested, article_alignment=exact, score=1.45
- MULGA-04: selected=COĞRAFİ İŞARETLERİN KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME, expected_family=MULGA, claimed_family=KHK, metadata_lookup=exact_identifier_lookup, identity=strong/none/not_requested, article_alignment=exact, score=1.45
- CBG-04: selected=İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi ile İlgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=exact_identifier_lookup, identity=strong/none/not_requested, article_alignment=title_only, score=2.50
- TUZUK-04: selected=GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK, expected_family=TUZUK, claimed_family=TUZUK, metadata_lookup=none, identity=medium/none/not_requested, article_alignment=exact, score=2.50
- TEB-01: selected=KAMU İHALE TEBLİĞİ (TEBLİĞ NO: 2026/1), expected_family=TEBLIGLER, claimed_family=TEBLIGLER, metadata_lookup=normalized_title_lookup, identity=strong/strong_overlap/not_requested, article_alignment=title_only, score=2.95
- CBG-01: selected=Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilmesi ile İlgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=none, identity=medium/none/not_requested, article_alignment=title_only, score=3.25
- CBG-02: selected=Ulusal Akıllı Şehirler Stratejisi ve Eylem Planı ile İlgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=exact_identifier_lookup, identity=strong/none/exact_identifier, article_alignment=title_only, score=3.25
- CBG-03: selected=Sanal Ortamda Yasa Dışı Bahis, Şans Oyunları ve Kumarla Mücadele Eylem Planı (2025-2026) ile İlgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=title_only, score=3.25
- KANUN-18: selected=TÜRK BORÇLAR KANUNU, expected_family=KANUN, claimed_family=KANUN, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=exact, score=3.25
- TEB-06: selected=TİCARET ŞİRKETLERİNDE ANONİM ŞİRKET GENEL KURULLARI DIŞINDA ELEKTRONİK ORTAMDA YAPILACAK KURULLAR HAKKINDA TEBLİĞ, expected_family=TEBLIGLER, claimed_family=TEBLIGLER, metadata_lookup=title_ngram_family_lookup, identity=strong/medium_overlap/not_requested, article_alignment=exact, score=3.25
- TUZUK-05: selected=GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK, expected_family=TUZUK, claimed_family=TUZUK, metadata_lookup=none, identity=medium/none/not_requested, article_alignment=title_only, score=3.25
- KANUN-02: selected=TÜRK BORÇLAR KANUNU, expected_family=KANUN, claimed_family=KANUN, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=exact, score=3.59
- YON-06: selected=YÜKSEKÖĞRETİM DENETLEME KURULU TEŞKİLÂT, GÖREV VE ÇALIŞMA USULLERİ YÖNETMELİĞİ, expected_family=YONETMELIK, claimed_family=YONETMELIK, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=exact, score=3.59
- MULGA-05: selected=PERAKENDE TİCARETİN DÜZENLENMESİ HAKKINDA KANUN, expected_family=MULGA, claimed_family=KANUN, metadata_lookup=none, identity=medium/none/not_requested, article_alignment=exact, score=4.25
- MULGA-01: selected=İSTANBUL 29 MAYIS ÜNİVERSİTESİ LİSANS EĞİTİM-ÖĞRETİM VE SINAV YÖNETMELİĞİ, expected_family=MULGA, claimed_family=UY, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=exact, score=4.90
- YON-08: selected=İSTANBUL TEKNİK ÜNİVERSİTESİ ÇİFT DİPLOMAYA YÖNELİK ULUSLARARASI ORTAK LİSANS PROGRAMLARI EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ, expected_family=YONETMELIK, claimed_family=UY, metadata_lookup=title_ngram_family_lookup, identity=strong/none/not_requested, article_alignment=none, score=5.45
- CBY-04: selected=DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11), expected_family=CB_YONETMELIK, claimed_family=CB_KARARNAME, metadata_lookup=none, identity=medium/none/not_requested, article_alignment=exact, score=5.75
- YON-05: selected=İMAR KANUNU, expected_family=YONETMELIK, claimed_family=KANUN, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=exact, score=5.75
- KANUN-15: selected=İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA UYGULANACAK BAZI İŞLEMLER VE 6785 SAYILI İMAR KANUNUNUN BİR MADDESİNİN DEĞİŞTİRİLMESİ HAKKINDA KANUN, expected_family=KANUN, claimed_family=KANUN, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=exact, score=6.05
- KANUN-19: selected=TEBLİGAT KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ, expected_family=KANUN, claimed_family=KANUN, metadata_lookup=none, identity=medium/none/not_requested, article_alignment=none, score=6.05
- KANUN-03: selected=ALT İŞVERENLİK YÖNETMELİĞİ, expected_family=KANUN, claimed_family=YONETMELIK, metadata_lookup=none, identity=medium/medium_overlap/not_requested, article_alignment=neighbor, score=6.09
- KKY-01: selected=BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKACILIK HİZMETLERİ HAKKINDA YÖNETMELİK, expected_family=KKY, claimed_family=YONETMELIK, metadata_lookup=title_ngram_family_lookup, identity=strong/strong_overlap/not_requested, article_alignment=none, score=6.20
- CBKAR-03: selected=BURSA İLİNDE YAPILACAK OLAN BATARYA HÜCRESİ VE MODÜL ÜRETİM TESİSİ YATIRIMINA PROJE BAZLI DEVLET YARDIMI VERİLMESİNE İLİŞKİN KARAR (KARAR SAYISI: 4924), expected_family=CB_KARAR, claimed_family=CB_KARAR, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=exact, score=6.80
- CBKAR-08: selected=YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903), expected_family=CB_KARAR, claimed_family=CB_KARAR, metadata_lookup=exact_identifier_lookup, identity=strong/medium_overlap/exact_identifier, article_alignment=title_only, score=6.80
- CBY-06: selected=KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ, expected_family=CB_YONETMELIK, claimed_family=CB_YONETMELIK, metadata_lookup=none, identity=strong/medium_overlap/not_requested, article_alignment=exact, score=6.80
- TUZUK-03: selected=TAPU SİCİLİ TÜZÜĞÜ, expected_family=TUZUK, claimed_family=TUZUK, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=exact, score=6.80
- KKY-04: selected=İŞSİZLİK SİGORTASI KANUNU ( SOSYAL SİGORTALAR KANUNU, TARIM İŞÇİLERİ SOSYAL SİGORTALAR KANUNU, TÜRKİYE CUMHURİYETİ EMEKLİ SANDIĞI KANUNU, ESNAF VE SANATKARLAR VE DİĞER BAĞIMSIZ ÇALIŞANLAR SOSYAL SİGORTALAR KURUMU KANUNU, TARIMDA KENDİ ADINA VE HESABINA ÇALIŞANLAR SOSYAL SİGORTALAR KANUNU İLE İŞ KANUNUNUN BİR MADDESİNİN DEĞİŞTİRİLMESİ VE BU KANUNLARA EK VE GEÇİCİ MADDELER EKLENMESİ, İŞSİZLİK SİGORTASI KURULMASI, ÇALIŞANLARIN TASARRUFA TEŞVİK EDİL- MESİ VE BU TASARRUFLARIN DEĞERLENDİRİLMESİNE DAİR KANUNUN İKİ MADDESİNİN YÜRÜRLÜKTEN KALDIRILMASI İLE GENEL KADRO VE USULÜ HAKKINDA KANUN HÜKMÜNDE KARARNAMENİN EKİ CETVELLERDE DEĞİŞİKLİK YAPILMASI HAKKINDA KANUN), expected_family=KKY, claimed_family=KHK, metadata_lookup=none, identity=weak/weak_overlap/not_requested, article_alignment=exact, score=6.85
- YON-02: selected=TÜKETİCİNİN KORUNMASI HAKKINDA KANUN, expected_family=YONETMELIK, claimed_family=KANUN, metadata_lookup=none, identity=weak/none/not_requested, article_alignment=exact, score=6.85
- KANUN-06: selected=TÜRK TİCARET KANUNUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ, expected_family=KANUN, claimed_family=KANUN, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=none, score=7.15
- TEB-03: selected=6563 SAYILI ELEKTRONİK TİCARETİN DÜZENLENMESİ HAKKINDA KANUNUN 12 NCİ MADDESİNE GÖRE 2026 YILINDA UYGULANACAK OLAN İDARİ PARA CEZALARINA İLİŞKİN TEBLİĞ, expected_family=TEBLIGLER, claimed_family=TEBLIGLER, metadata_lookup=title_ngram_family_lookup, identity=medium/weak_overlap/not_requested, article_alignment=title_only, score=7.15
- CBKAR-05: selected=TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/34), expected_family=CB_KARAR, claimed_family=TEBLIGLER, metadata_lookup=exact_identifier_lookup, identity=strong/weak_overlap/exact_identifier, article_alignment=none, score=7.19
- CBKAR-02: selected=İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350), expected_family=CB_KARAR, claimed_family=CB_KARAR, metadata_lookup=normalized_title_lookup, identity=strong/strong_overlap/not_requested, article_alignment=exact, score=7.25
- KHK-03: selected=ANAYASADA YAPILAN DEĞİŞİKLİKLERE UYUM SAĞLANMASI AMACIYLA BAZI KANUN VE KANUN HÜKMÜNDE KARARNAMELERDE DEĞİŞİKLİK YAPILMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME, expected_family=KHK, claimed_family=KHK, metadata_lookup=none, identity=strong/none/not_requested, article_alignment=exact, score=7.25
