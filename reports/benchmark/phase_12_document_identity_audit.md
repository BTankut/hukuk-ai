# Phase 12 Document Identity Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T065717Z_phase12_full`
- rows_analyzed: 100
- wrong_document: 16
- hallucinated_identifier: 32
- hallucinated_source_count: 16
- selected_article_equals_claimed_article_count: 65
- right_document_wrong_article_or_span: 54
- avg_document_identity_score: 112.246
- avg_title_bias_applied: 27.768
- avg_issuer_bias_applied: 0.303

## Metadata Identity Strength
- medium: 19
- none: 3
- strong: 77
- unknown: 1

## Identity Lock Strength
- medium: 9
- none: 1
- strong: 48
- unknown: 1
- weak: 41

## Metadata Lookup Source
- exact_identifier_lookup: 12
- issuer_family_lookup: 2
- none: 46
- normalized_title_lookup: 9
- title_ngram_family_lookup: 31

## Identity Rerank Input Source
- dense_retrieval: 3
- metadata_lookup_selector: 53
- source_family_prior: 43
- unknown: 1

## Title Match Type
- exact_phrase: 3
- medium_overlap: 32
- none: 42
- strong_overlap: 5
- unknown: 1
- weak_overlap: 17

## Identifier Integrity
- exact: 46
- missing: 1
- replaced_by_selected_evidence: 32
- selected_evidence_identifier_suppressed: 9
- unverified_claim_suppressed: 12

## Article Alignment
- exact: 54
- neighbor: 5
- none: 25
- title_only: 15
- unknown: 1

## Worst Rows
- KANUN-01: selected=türki̇ye i̇nsan haklari ve eşi̇tli̇k kurumunda sözleşmeli̇ personel i̇sti̇hdam edi̇lmesi̇ne i̇li̇şki̇n usul ve esaslar, expected_family=KANUN, claimed_family=TEBLIGLER, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/weak_overlap/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=exact, score=0.00
- MULGA-03: selected=tapu si̇ci̇li̇ tüzüğü, expected_family=MULGA, claimed_family=TUZUK, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/exact_phrase/not_requested, identifier_integrity=exact, article_alignment=exact, score=0.00
- MULGA-04: selected=patent haklarinin korunmasi hakkinda kanun hükmünde kararname, expected_family=MULGA, claimed_family=KHK, metadata_lookup=exact_identifier_lookup, rerank_input=metadata_lookup_selector, identity=strong/none/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=0.00
- CBG-03: selected=5015 sayili petrol pi̇yasasi kanununun 19 uncu maddesi̇ uyarinca 2025 yilinda uygulanacak i̇dari̇ para cezalari hakkinda tebli̇ğ, expected_family=CB_GENELGE, claimed_family=TEBLIGLER, metadata_lookup=normalized_title_lookup, rerank_input=metadata_lookup_selector, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=1.45
- CBY-05: selected=ulusal erişilebilirlik günü ile i̇lgili, expected_family=CB_YONETMELIK, claimed_family=CB_GENELGE, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=title_only, score=1.45
- KANUN-02: selected=2019 yili yatirim programinda 2013a010230 proje numarasi i̇le yer alan devlet su i̇şleri̇ genel müdürlüğüne ai̇t çermi̇k-kale (gap) projesi̇ kapsamindaki̇ kale baraji i̇çi̇n alinan kamu yarari kararinin i̇lan süresi̇ni̇n bi̇ti̇mi̇nden i̇ti̇baren başlayan, 2942 sayili kamulaştirma kanununun 25 i̇nci̇ maddesi̇ni̇n üçüncü fikrasi kapsamindaki̇ sinirlamaya i̇li̇şki̇n süreni̇n, bi̇r defaya mahsus olmak üzere beş yil uzatilmasi hakkinda karar (karar sayisi: 1901), expected_family=KANUN, claimed_family=CB_KARAR, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=1.45
- KANUN-06: selected=türk ti̇caret kanununun yürürlükten kaldirilan hükümleri̇, expected_family=KANUN, claimed_family=MULGA, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=1.45
- KKY-02: selected=abdullah gül üni̇versi̇tesi̇ uzaktan eği̇ti̇m uygulama ve araştirma merkezi̇ yönetmeli̇ği̇, expected_family=KKY, claimed_family=UY, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=exact, score=1.45
- YON-02: selected=adalet bakanliği tarafindan 4734 sayili kamu i̇hale kanununun 3 üncü maddesi̇ni̇n (b) bendi̇ kapsaminda yapilacak i̇halelere i̇li̇şki̇n esas ve usuller, expected_family=YONETMELIK, claimed_family=CB_YONETMELIK, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=1.45
- YON-06: selected=havacilik tibbi eği̇ti̇m yönetmeli̇ği̇ (shy-hte), expected_family=YONETMELIK, claimed_family=KKY, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=neighbor, score=1.45
- CBG-04: selected=sanal ortamda yasa dışı bahis, şans oyunları ve kumarla mücadele eylem planı (2025-2026) ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=exact_identifier_lookup, rerank_input=metadata_lookup_selector, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=2.50
- TEB-04: selected=vergi̇ usul kanunu genel tebli̇ği̇ (sira no: 520), expected_family=TEBLIGLER, claimed_family=TEBLIGLER, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=title_only, score=2.50
- UY-07: selected=, expected_family=UY, claimed_family=UNKNOWN, metadata_lookup=title_ngram_family_lookup, rerank_input=none, identity=//, identifier_integrity=missing, article_alignment=unknown, score=3.10
- CBG-01: selected=rehberlik, teftiş ve denetim faaliyetlerinin düzenli ve etkin bir şekilde yerine getirilmesi ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=exact, article_alignment=title_only, score=3.25
- CBG-02: selected=roman vatandaşlara yönelik strateji belgesi ii. aşama eylem planı ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, metadata_lookup=exact_identifier_lookup, rerank_input=metadata_lookup_selector, identity=strong/none/exact_identifier, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=3.25
- KKY-03: selected=elektroni̇k haberleşme sektöründe şebeke ve bi̇lgi̇ güvenli̇ği̇ yönetmeli̇ği̇, expected_family=KKY, claimed_family=KKY, metadata_lookup=normalized_title_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=3.25
- KKY-10: selected=tari̇fe yönetmeli̇ği̇, expected_family=KKY, claimed_family=KKY, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=3.25
- TUZUK-05: selected=gida maddeleri̇ni̇n ve umumi̇ sağliği i̇lgi̇lendi̇ren eşya ve levazimin hususi̇ vasiflarini gösteren tüzük, expected_family=TUZUK, claimed_family=TUZUK, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=title_only, score=3.25
- MULGA-01: selected=yükseköğreti̇m kurumlari öğrenci̇ di̇si̇pli̇n yönetmeli̇ği̇, expected_family=MULGA, claimed_family=KKY, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/exact_phrase/not_requested, identifier_integrity=exact, article_alignment=exact, score=4.17
- TUZUK-04: selected=çukurova üni̇versi̇tesi̇ i̇ş sağliği ve güvenli̇ği̇ eği̇ti̇m, uygulama ve araştirma merkezi̇ yönetmeli̇ği̇, expected_family=TUZUK, claimed_family=UY, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=none, score=4.63
- CBKAR-01: selected=kullanilmiş veya yeni̇leşti̇ri̇lmi̇ş eşya i̇thalatina i̇li̇şki̇n tebli̇ğ (i̇thalat: 2026/9), expected_family=CB_KARAR, claimed_family=TEBLIGLER, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=5.00
- KHK-03: selected=nükleer düzenleme kurumunun teşki̇lat ve görevleri̇ hakkinda cumhurbaşkanliği kararnamesi̇ (kararname numarasi: 95), expected_family=KHK, claimed_family=CB_KARARNAME, metadata_lookup=issuer_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=5.00
- YON-08: selected=işik üni̇versi̇tesi̇ yatay geçi̇ş, çi̇ft anadal, yan dal ve kredi̇ transferi̇ yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=UY, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=5.00
- KANUN-03: selected=i̇şyeri̇ sendi̇ka temsi̇lci̇leri̇ni̇n faali̇yetleri̇ i̇le çalişmaya devam eden sendi̇ka yöneti̇ci̇leri̇ne veri̇lecek haftada bi̇r gün i̇zni̇n kullandirilmasina i̇li̇şki̇n usul ve esaslar hakkinda tebli̇ğ, expected_family=KANUN, claimed_family=TEBLIGLER, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=5.75
- KANUN-04: selected=i̇ş sağliği ve güvenli̇ği̇ hi̇zmetleri̇ yönetmeli̇ği̇, expected_family=KANUN, claimed_family=KKY, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=5.75
- YON-01: selected=elektroni̇k tebli̇gat si̇stemi̇ genel tebli̇ği̇ (sira no: 1), expected_family=YONETMELIK, claimed_family=TEBLIGLER, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=exact, score=5.75
- YON-03: selected=i̇ş sağliği ve güvenli̇ği̇ ri̇sk değerlendi̇rmesi̇ yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=KKY, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=none, score=5.75
- YON-05: selected=i̇mar kanunu, expected_family=YONETMELIK, claimed_family=KANUN, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=5.75
- YON-09: selected=mesafeli̇ sözleşmeler yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=KKY, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=none, score=5.75
- YON-10: selected=i̇ş sağliği ve güvenli̇ği̇ ri̇sk değerlendi̇rmesi̇ yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=KKY, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/medium_overlap/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=neighbor, score=5.75
- CBY-06: selected=kamuda geçi̇ci̇ i̇ş pozi̇syonlarinda çalişanlarin sürekli̇ i̇şçi̇ kadrolarina veya sözleşmeli̇ personel statüsüne geçi̇ri̇lmeleri̇, geçi̇ci̇ i̇şçi̇ çaliştirilmasi i̇le bazi kanunlarda deği̇şi̇kli̇k yapilmasi hakkinda kanun, expected_family=CB_YONETMELIK, claimed_family=KANUN, metadata_lookup=none, rerank_input=source_family_prior, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.10
- MULGA-02: selected=devlet arşi̇v hi̇zmetleri̇ hakkinda yönetmeli̇k, expected_family=MULGA, claimed_family=KKY, metadata_lookup=normalized_title_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.10
- KKY-09: selected=i̇nönü üni̇versi̇tesi̇ zorunlu ve i̇steğe bağli yabanci di̇l hazirlik siniflarieği̇ti̇m-öğreti̇m ve sinav yönetmeli̇ği̇, expected_family=KKY, claimed_family=UY, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.43
- KANUN-19: selected=turi̇zmi̇ teşvi̇k kanunu hükümleri̇ uyarinca veri̇len i̇dari̇ para cezalarinin tebli̇gatinin elektroni̇k ortamda yapilmasina i̇li̇şki̇n tebli̇ğ, expected_family=KANUN, claimed_family=TEBLIGLER, metadata_lookup=normalized_title_lookup, rerank_input=metadata_lookup_selector, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.65
- CBY-01: selected=vali̇li̇k ve kaymakamlik bi̇ri̇mleri̇ teşki̇lat, görev ve çalişma yönetmeli̇ği̇, expected_family=CB_YONETMELIK, claimed_family=KKY, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=none, score=6.85
- KANUN-13: selected=i̇ş sağliği ve güvenli̇ği̇ ri̇sk değerlendi̇rmesi̇ yönetmeli̇ği̇, expected_family=KANUN, claimed_family=KKY, metadata_lookup=none, rerank_input=dense_retrieval, identity=none/none/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=exact, score=6.85
- KANUN-15: selected=yapi müteahhi̇tleri̇ni̇n siniflandirilmasi ve kayitlarinin tutulmasi hakkinda yönetmeli̇k, expected_family=KANUN, claimed_family=KKY, metadata_lookup=none, rerank_input=dense_retrieval, identity=none/weak_overlap/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=none, score=6.85
- KKY-04: selected=sosyal si̇gortalar ve genel sağlik si̇gortasi kanunu, expected_family=KKY, claimed_family=KANUN, metadata_lookup=title_ngram_family_lookup, rerank_input=metadata_lookup_selector, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=none, score=6.85
- YON-04: selected=ki̇şi̇sel veri̇leri̇n si̇li̇nmesi̇, yok edi̇lmesi̇ veya anoni̇m hale geti̇ri̇lmesi̇ hakkinda yönetmeli̇k, expected_family=YONETMELIK, claimed_family=KKY, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=title_only, score=6.85
- CBY-04: selected=devlet arşi̇vleri̇ başkanliği hakkinda cumhurbaşkanliği kararnamesi̇ (kararname numarasi: 11), expected_family=CB_YONETMELIK, claimed_family=CB_KARARNAME, metadata_lookup=none, rerank_input=source_family_prior, identity=medium/none/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=exact, score=7.12
