# Phase 14 Canonical Span Materialization Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic`
- rows_analyzed: 100
- canonical_span_materialized_count: 87
- corpus_materialization_required_count: 13
- insufficient_canonical_span_evidence_count: 13
- title_only_fallback_used_count: 13
- title_only_answer_degraded_count: 13
- source_key_collision_detected_count: 6
- selected_document_has_body_span_count: 97
- selected_document_has_non_title_span_count: 87
- candidate_completeness_score_avg: 0.912

## By Expected Family
- CB_GENELGE: total=4, materialized=0, corpus_required=4, insufficient_span=4, title_only_fallback=4, candidate_avg=0.513
- CB_KARAR: total=8, materialized=6, corpus_required=2, insufficient_span=2, title_only_fallback=2, candidate_avg=0.806
- CB_KARARNAME: total=6, materialized=6, corpus_required=0, insufficient_span=0, title_only_fallback=0, candidate_avg=1.000
- CB_YONETMELIK: total=6, materialized=6, corpus_required=0, insufficient_span=0, title_only_fallback=0, candidate_avg=0.967
- KANUN: total=21, materialized=20, corpus_required=1, insufficient_span=1, title_only_fallback=1, candidate_avg=0.957
- KHK: total=6, materialized=5, corpus_required=1, insufficient_span=1, title_only_fallback=1, candidate_avg=0.925
- KKY: total=11, materialized=11, corpus_required=0, insufficient_span=0, title_only_fallback=0, candidate_avg=0.973
- MULGA: total=5, materialized=5, corpus_required=0, insufficient_span=0, title_only_fallback=0, candidate_avg=0.960
- TEBLIGLER: total=8, materialized=5, corpus_required=3, insufficient_span=3, title_only_fallback=3, candidate_avg=0.869
- TUZUK: total=5, materialized=4, corpus_required=1, insufficient_span=1, title_only_fallback=1, candidate_avg=0.870
- UY: total=10, materialized=10, corpus_required=0, insufficient_span=0, title_only_fallback=0, candidate_avg=0.910
- YONETMELIK: total=10, materialized=9, corpus_required=1, insufficient_span=1, title_only_fallback=1, candidate_avg=0.935

## Materialization Reason Counts
- non_title_body_span_available: 87
- body_span_available_but_title_or_article_zero: 10
- source_key_collision_without_family_body_span: 2
- title_only_or_unreadable_body: 1

## Blocker Rows
- CBG-04: expected=CB_GENELGE, selected=İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi ile İlgili, reason=source_key_collision_without_family_body_span, corpus_required=True, insufficient=True, collision=3=cb_genelge:is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili|cb_kararname:ust kademe kamu yoneticilerinin atanmalarina iliskin usul ve esaslar ile kamu ku, score=2.50
- TEB-01: expected=TEBLIGLER, selected=KAMU İHALE TEBLİĞİ (TEBLİĞ NO: 2026/1), reason=body_span_available_but_title_or_article_zero, corpus_required=True, insufficient=True, collision=none, score=2.95
- CBG-01: expected=CB_GENELGE, selected=Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilmesi ile İlgili, reason=body_span_available_but_title_or_article_zero, corpus_required=True, insufficient=True, collision=none, score=3.25
- CBG-02: expected=CB_GENELGE, selected=Ulusal Akıllı Şehirler Stratejisi ve Eylem Planı ile İlgili, reason=body_span_available_but_title_or_article_zero, corpus_required=True, insufficient=True, collision=26=cb_genelge:yurt disinda yurutulen faaliyetlerde dikkat edilmesi gereken hususlar ile ilgili|cb_karar:4 7 1956 tarihli ve 6772 sayili kanun kapsamina giren kurumlarda calisan isciler; 29=cb_genelge:ulusal akilli sehirler stratejisi ve eylem plani ile ilgili|cb_karar:turkakim kara kismi 2 gaz boru hatti projesi kapsaminda tekirdag ve kirklareli i, score=3.25
- CBG-03: expected=CB_GENELGE, selected=Sanal Ortamda Yasa Dışı Bahis, Şans Oyunları ve Kumarla Mücadele Eylem Planı (2025-2026) ile İlgili, reason=body_span_available_but_title_or_article_zero, corpus_required=True, insufficient=True, collision=none, score=3.25
- TUZUK-05: expected=TUZUK, selected=GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK, reason=body_span_available_but_title_or_article_zero, corpus_required=True, insufficient=True, collision=none, score=3.25
- KANUN-15: expected=KANUN, selected=İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA UYGULANACAK BAZI İŞLEMLER VE 6785 SAYILI İMAR KANUNUNUN BİR MADDESİNİN DEĞİŞTİRİLMESİ HAKKINDA KANUN, reason=non_title_body_span_available, corpus_required=False, insufficient=False, collision=2981=kanun:imar ve gecekondu mevzuatina aykiri yapilara uygulanacak bazi islemler ve 6785 s|mulga_kanun:imar ve gecekondu mevzuatina aykiri yapilara uygulanacak bazi islemler ve 6785 s, score=6.05
- KANUN-19: expected=KANUN, selected=TEBLİGAT KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ, reason=non_title_body_span_available, corpus_required=False, insufficient=False, collision=7201=kanun:tebligat kanunu|mulga_kanun:tebligat kanununun yururlukten kaldirilmis hukumleri, score=6.05
- CBKAR-08: expected=CB_KARAR, selected=YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903), reason=source_key_collision_without_family_body_span, corpus_required=True, insufficient=True, collision=9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig teblig no trkgm 2006 1, score=6.80
- KANUN-06: expected=KANUN, selected=TÜRK TİCARET KANUNUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ, reason=title_only_or_unreadable_body, corpus_required=True, insufficient=True, collision=none, score=7.15
- TEB-03: expected=TEBLIGLER, selected=6563 SAYILI ELEKTRONİK TİCARETİN DÜZENLENMESİ HAKKINDA KANUNUN 12 NCİ MADDESİNE GÖRE 2026 YILINDA UYGULANACAK OLAN İDARİ PARA CEZALARINA İLİŞKİN TEBLİĞ, reason=body_span_available_but_title_or_article_zero, corpus_required=True, insufficient=True, collision=none, score=7.15
- TEB-04: expected=TEBLIGLER, selected=VERGİ USUL KANUNU GENEL TEBLİĞİ (SIRA NO:429), reason=body_span_available_but_title_or_article_zero, corpus_required=True, insufficient=True, collision=none, score=7.25
- YON-04: expected=YONETMELIK, selected=KİŞİSEL VERİLERİN SİLİNMESİ, YOK EDİLMESİ VEYA ANONİM HALE GETİRİLMESİ HAKKINDA YÖNETMELİK, reason=body_span_available_but_title_or_article_zero, corpus_required=True, insufficient=True, collision=none, score=7.55
- CBKAR-07: expected=CB_KARAR, selected=İTHALAT REJİMİ KARARINDA DEĞİŞİKLİK YAPILMASINA İLİŞKİN KARAR (KARAR SAYISI: 8688), reason=body_span_available_but_title_or_article_zero, corpus_required=True, insufficient=True, collision=none, score=8.65
- KANUN-10: expected=KANUN, selected=AMME ALACAKLARININ TAHSİL USULÜ HAKKINDAKİ KANUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ, reason=non_title_body_span_available, corpus_required=False, insufficient=False, collision=6183=kanun:amme alacaklarinin tahsil usulu hakkinda kanun|mulga_kanun:amme alacaklarinin tahsil usulu hakkindaki kanunun yururlukten kaldirilmis hukum, score=8.92
- KHK-05: expected=KHK, selected=DEVLET MEMURLARI KANUNU GENEL TEBLİĞİ (Seri No: 161) (666 Sayılı Kanun Hükmünde Kararname Hükümlerine İlişkin), reason=body_span_available_but_title_or_article_zero, corpus_required=True, insufficient=True, collision=none, score=9.10
