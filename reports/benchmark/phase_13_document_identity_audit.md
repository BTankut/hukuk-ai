# Phase 13 Document Identity Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T124900Z_phase13_full`
- rows_analyzed: 100
- wrong_document: 18
- hallucinated_identifier: 24
- hallucinated_source_count: 18
- selected_article_equals_claimed_article_count: 55
- right_document_wrong_article_or_span: 57
- avg_document_identity_score: 129.297
- avg_title_bias_applied: 25.490
- avg_issuer_bias_applied: 0.150

## Metadata Identity Strength
- strong: 83
- medium: 13
- weak: 4

## Identity Lock Strength
- weak: 47
- strong: 34
- medium: 18
- none: 1

## Metadata Lookup Source
- none: 58
- title_ngram_family_lookup: 20
- exact_identifier_lookup: 11
- normalized_title_lookup: 9
- issuer_family_lookup: 2

## Identity Rerank Input Source
- source_family_prior: 57
- metadata_lookup_selector: 42
- dense_retrieval: 1

## Title Match Type
- none: 49
- medium_overlap: 35
- weak_overlap: 9
- strong_overlap: 6
- exact_phrase: 1

## Identifier Integrity
- exact: 40
- unverified_claim_suppressed: 28
- replaced_by_selected_evidence: 27
- selected_evidence_identifier_suppressed: 5

## Article Alignment
- exact: 45
- none: 34
- title_only: 16
- neighbor: 5

## Worst Rows
- CBKAR-08: selected=7452 SAYILI OLAĞANÜSTÜ HAL KAPSAMINDA YERLEŞME VE YAPILAŞMAYA İLİŞKİN CUMHURBAŞKANLIĞI KARARNAMESİNİN KABUL EDİLMESİNE DAİR KANUNUN EK 1 İNCİ MADDESİ KAPSAMINDA YAPILACAK YENİ YAPILARIN BULUNDUĞU PARSELLERİN MALİKİ OLAN GERÇEK VEYA TÜZEL KİŞİLERE HİBE VE YAPIM KREDİSİ VERİLMESİNE İLİŞKİN 5/10/2023 TARİHLİ VE 7700 SAYILI CUMHURBAŞKANI KARARINDA DEĞİŞİKLİK YAPILMASINA DAİR KARAR (KARAR SAYISI: 10019), expected_family=CB_KARAR, claimed_family=CB_KARARNAME, metadata_lookup=normalized_title_lookup, rerank_input=metadata_lookup_selector, identity=strong/weak_overlap/none, identifier_integrity=unverified_claim_suppressed, article_alignment=title_only, score=0.70
- KHK-03: selected=TÜRKİYE ADALET AKADEMİSİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 34), expected_family=KHK, claimed_family=CB_KARARNAME, metadata_lookup=issuer_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=0.70
- MULGA-01: selected=İSTANBUL 29 MAYIS ÜNİVERSİTESİ LİSANS EĞİTİM-ÖĞRETİM VE SINAV YÖNETMELİĞİ, expected_family=MULGA, claimed_family=UY, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=none, score=0.70
- CBKAR-06: selected=2026-2028 Dönemi Yatırım Programı Hazırlıkları ile İlgili, expected_family=CB_KARAR, claimed_family=CB_GENELGE, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/medium_overlap/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=title_only, score=1.45
- KANUN-04: selected=DIŞ TİCARETTE RİSK ESASLI KONTROL SİSTEMİ TEBLİĞİ (ÜRÜN GÜVENLİĞİ VE DENETİMİ: 2011/53), expected_family=KANUN, claimed_family=TEBLIGLER, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=1.45
- KKY-02: selected=ABANT İZZET BAYSAL ÜNİVERSİTESİ UZAKTAN EĞİTİM UYGULAMA VE ARAŞTIRMA MERKEZİ YÖNETMELİĞİ, expected_family=KKY, claimed_family=UY, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=title_only, score=1.45
- KKY-09: selected=İNÖNÜ ÜNİVERSİTESİ ZORUNLU VE İSTEĞE BAĞLI YABANCI DİL HAZIRLIK SINIFLARIEĞİTİM-ÖĞRETİM VE SINAV YÖNETMELİĞİ, expected_family=KKY, claimed_family=UY, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=neighbor, score=1.45
- YON-07: selected=ANADOLU ÜNİVERSİTESİ SOSYAL MEDYA VE DİJİTAL GÜVENLİK EĞİTİM, UYGULAMA VE ARAŞTIRMA MERKEZİ YÖNETMELİĞİ, expected_family=YONETMELIK, claimed_family=UY, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=1.79
- CBKAR-04: selected=2026-2028 Dönemi Yatırım Programı Hazırlıkları ile İlgili, expected_family=CB_KARAR, claimed_family=CB_GENELGE, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/medium_overlap/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=title_only, score=1.90
- KKY-06: selected=AMASYA ÜNİVERSİTESİ ÖNLİSANS VE LİSANS EĞİTİM-ÖĞRETİM VE SINAV YÖNETMELİĞİ, expected_family=KKY, claimed_family=UY, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=2.12
- CBG-04: selected=Sanal Ortamda Yasa Dışı Bahis, Şans Oyunları ve Kumarla Mücadele Eylem Planı (2025-2026) ile İlgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=exact_identifier_lookup, rerank_input=metadata_lookup_selector, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=title_only, score=2.50
- CBY-03: selected=4735 SAYILI KAMU İHALE SÖZLEŞMELERİ KANUNUNUN GEÇİCİ 3 ÜNCÜ MADDESİ UYARINCA HESAPLANACAK EK FİYAT FARKINA İLİŞKİN ESASLAR, expected_family=CB_YONETMELIK, claimed_family=CB_YONETMELIK, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=none, score=2.50
- TUZUK-04: selected=GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK, expected_family=TUZUK, claimed_family=TUZUK, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=exact, score=2.50
- CBG-01: selected=Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilmesi ile İlgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=exact, article_alignment=title_only, score=3.25
- CBG-02: selected=Ulusal Akıllı Şehirler Stratejisi ve Eylem Planı ile İlgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=exact_identifier_lookup, rerank_input=metadata_lookup_selector, identity=strong/none/exact_identifier, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=3.25
- CBG-03: selected=Sanal Ortamda Yasa Dışı Bahis, Şans Oyunları ve Kumarla Mücadele Eylem Planı (2025-2026) ile İlgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=title_only, score=3.25
- TEB-06: selected=TİCARET ŞİRKETLERİNDE ANONİM ŞİRKET GENEL KURULLARI DIŞINDA ELEKTRONİK ORTAMDA YAPILACAK KURULLAR HAKKINDA TEBLİĞ, expected_family=TEBLIGLER, claimed_family=TEBLIGLER, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=3.25
- TUZUK-05: selected=GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK, expected_family=TUZUK, claimed_family=TUZUK, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=title_only, score=3.25
- KANUN-15: selected=İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA UYGULANACAK BAZI İŞLEMLER VE 6785 SAYILI İMAR KANUNUNUN BİR MADDESİNİN DEĞİŞTİRİLMESİ HAKKINDA KANUN, expected_family=KANUN, claimed_family=MULGA, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=none, score=6.02
- KANUN-03: selected=ALT İŞVERENLİK YÖNETMELİĞİ, expected_family=KANUN, claimed_family=KKY, metadata_lookup=none, rerank_input=dense_retrieval, identity=medium/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=neighbor, score=6.09
- MULGA-02: selected=ADNAN MENDERES ÜNİVERSİTESİ ARŞİV YÖNETMELİĞİ, expected_family=MULGA, claimed_family=UY, metadata_lookup=normalized_title_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.10
- KKY-01: selected=BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKACILIK HİZMETLERİ HAKKINDA YÖNETMELİK, expected_family=KKY, claimed_family=YONETMELIK, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/strong_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=6.20
- KKY-08: selected=ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN YETKİLENDİRME YÖNETMELİĞİ, expected_family=KKY, claimed_family=YONETMELIK, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/strong_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=6.65
- TUZUK-03: selected=TAPU SİCİLİ TÜZÜĞÜ, expected_family=TUZUK, claimed_family=MULGA, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=none, score=6.78
- CBY-01: selected=VALİLİK VE KAYMAKAMLIK BİRİMLERİ TEŞKİLAT, GÖREV VE ÇALIŞMA YÖNETMELİĞİ, expected_family=CB_YONETMELIK, claimed_family=YONETMELIK, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=6.85
- YON-10: selected=İŞ SAĞLIĞI VE GÜVENLİĞİ RİSK DEĞERLENDİRMESİ YÖNETMELİĞİ, expected_family=YONETMELIK, claimed_family=KKY, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.85
- CBKAR-05: selected=TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/34), expected_family=CB_KARAR, claimed_family=TEBLIGLER, metadata_lookup=exact_identifier_lookup, rerank_input=metadata_lookup_selector, identity=strong/weak_overlap/exact_identifier, identifier_integrity=exact, article_alignment=none, score=7.19
- CBY-04: selected=DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11), expected_family=CB_YONETMELIK, claimed_family=CB_KARARNAME, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=7.66
- KKY-11: selected=BANKA KARTLARI VE KREDİ KARTLARI HAKKINDA YÖNETMELİK, expected_family=KKY, claimed_family=YONETMELIK, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=title_only, score=7.86
