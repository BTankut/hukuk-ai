# Phase 11 Document Identity Audit

- source_run_dir: `reports/benchmark/runs/20260422T204628Z_phase11_full`
- rows_analyzed: 100
- wrong_document: 15
- hallucinated_identifier: 32
- hallucinated_source_count: 15
- selected_article_equals_claimed_article_count: 63
- right_document_wrong_article_or_span: 51
- avg_document_identity_score: 100.073
- avg_title_bias_applied: 23.12
- avg_issuer_bias_applied: 0.3

## Metadata Identity Strength
- medium: 22
- none: 3
- strong: 75

## Identity Lock Strength
- medium: 8
- none: 1
- strong: 42
- weak: 49

## Title Match Type
- exact_phrase: 2
- medium_overlap: 31
- none: 45
- strong_overlap: 3
- weak_overlap: 19

## Identifier Integrity
- exact: 44
- replaced_by_selected_evidence: 32
- selected_evidence_identifier_suppressed: 9
- unverified_claim_suppressed: 15

## Article Alignment
- exact: 53
- neighbor: 5
- none: 28
- title_only: 14

## Worst Rows
- KANUN-01: selected=türki̇ye i̇nsan haklari ve eşi̇tli̇k kurumunda sözleşmeli̇ personel i̇sti̇hdam edi̇lmesi̇ne i̇li̇şki̇n usul ve esaslar, expected_family=KANUN, claimed_family=TEBLIGLER, identity=weak/weak_overlap/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=exact, score=0.00
- MULGA-03: selected=tapu si̇ci̇li̇ tüzüğü, expected_family=MULGA, claimed_family=TUZUK, identity=strong/exact_phrase/not_requested, identifier_integrity=exact, article_alignment=exact, score=0.00
- CBY-05: selected=ulusal erişilebilirlik günü ile i̇lgili, expected_family=CB_YONETMELIK, claimed_family=CB_GENELGE, identity=weak/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=title_only, score=1.45
- KANUN-06: selected=türk ti̇caret kanununun yürürlükten kaldirilan hükümleri̇, expected_family=KANUN, claimed_family=MULGA, identity=weak/none/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=1.45
- UY-07: selected=ki̇şi̇sel veri̇leri̇n korunmasi kanunu, expected_family=UY, claimed_family=KANUN, identity=weak/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=none, score=1.45
- YON-02: selected=adalet bakanliği tarafindan 4734 sayili kamu i̇hale kanununun 3 üncü maddesi̇ni̇n (b) bendi̇ kapsaminda yapilacak i̇halelere i̇li̇şki̇n esas ve usuller, expected_family=YONETMELIK, claimed_family=CB_YONETMELIK, identity=weak/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=1.45
- YON-06: selected=havacilik tibbi eği̇ti̇m yönetmeli̇ği̇ (shy-hte), expected_family=YONETMELIK, claimed_family=KKY, identity=weak/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=neighbor, score=1.45
- CBG-04: selected=sanal ortamda yasa dışı bahis, şans oyunları ve kumarla mücadele eylem planı (2025-2026) ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, identity=weak/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=2.50
- TEB-04: selected=vergi̇ usul kanunu genel tebli̇ği̇ (sira no: 520), expected_family=TEBLIGLER, claimed_family=TEBLIGLER, identity=weak/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=title_only, score=2.50
- CBG-01: selected=rehberlik, teftiş ve denetim faaliyetlerinin düzenli ve etkin bir şekilde yerine getirilmesi ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, identity=weak/none/not_requested, identifier_integrity=exact, article_alignment=title_only, score=3.25
- CBG-02: selected=roman vatandaşlara yönelik strateji belgesi ii. aşama eylem planı ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, identity=strong/none/exact_identifier, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=3.25
- CBG-03: selected=sanal ortamda yasa dışı bahis, şans oyunları ve kumarla mücadele eylem planı (2025-2026) ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, identity=weak/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=3.25
- CBKAR-04: selected=ti̇caret bakanliği gümrükler muhafaza genel müdürlüğü tarafindan 4734 sayili kamu i̇hale kanununun 3 üncü maddesi̇ni̇n (b) bendi̇ kapsaminda yapilacak i̇halelere i̇li̇şki̇n usul ve esaslar (karar sayisi: 5997), expected_family=CB_KARAR, claimed_family=CB_KARAR, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=3.25
- KKY-02: selected=bankalarin i̇zne tabi̇ i̇şlemleri̇ i̇le dolayli pay sahi̇pli̇ği̇ne i̇li̇şki̇n yönetmeli̇k, expected_family=KKY, claimed_family=KKY, identity=weak/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=3.25
- KKY-10: selected=tari̇fe yönetmeli̇ği̇, expected_family=KKY, claimed_family=KKY, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=3.25
- TUZUK-05: selected=gida maddeleri̇ni̇n ve umumi̇ sağliği i̇lgi̇lendi̇ren eşya ve levazimin hususi̇ vasiflarini gösteren tüzük, expected_family=TUZUK, claimed_family=TUZUK, identity=weak/none/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=title_only, score=3.25
- MULGA-01: selected=munzur üni̇versi̇tesi̇ ön li̇sans ve li̇sans eği̇ti̇m-öğreti̇m yönetmeli̇ği̇, expected_family=MULGA, claimed_family=UY, identity=weak/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=none, score=3.43
- UY-10: selected=kafkas üni̇versi̇tesi̇ önli̇sans ve li̇sans uzaktan eği̇ti̇m-öğreti̇m ve sinav yönetmeli̇ği̇, expected_family=UY, claimed_family=UY, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=exact, score=3.59
- TUZUK-04: selected=çukurova üni̇versi̇tesi̇ i̇ş sağliği ve güvenli̇ği̇ eği̇ti̇m, uygulama ve araştirma merkezi̇ yönetmeli̇ği̇, expected_family=TUZUK, claimed_family=UY, identity=weak/none/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=none, score=4.63
- CBKAR-01: selected=kullanilmiş veya yeni̇leşti̇ri̇lmi̇ş eşya i̇thalatina i̇li̇şki̇n tebli̇ğ (i̇thalat: 2026/9), expected_family=CB_KARAR, claimed_family=TEBLIGLER, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=5.00
- CBKAR-08: selected=türk ti̇caret kanununun mer'i̇yet ve tatbi̇k şekli̇ hakkinda kanunun yürürlükten kaldirilan hükümleri̇, expected_family=CB_KARAR, claimed_family=MULGA, identity=weak/none/none, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=5.00
- MULGA-02: selected=güvenli̇k soruşturmasi ve arşi̇v araştirmasi yapilmasina dai̇r yönetmeli̇k, expected_family=MULGA, claimed_family=CB_YONETMELIK, identity=weak/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=none, score=5.00
- YON-08: selected=işik üni̇versi̇tesi̇ yatay geçi̇ş, çi̇ft anadal, yan dal ve kredi̇ transferi̇ yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=UY, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=5.00
- KANUN-02: selected=fazla çalişmanin uygulama esaslarinin gösteri̇r yönetmeli̇k, expected_family=KANUN, claimed_family=YONETMELIK, identity=weak/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=5.75
- KANUN-04: selected=i̇ş sağliği ve güvenli̇ği̇ hi̇zmetleri̇ yönetmeli̇ği̇, expected_family=KANUN, claimed_family=KKY, identity=weak/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=5.75
- YON-01: selected=elektroni̇k tebli̇gat si̇stemi̇ genel tebli̇ği̇ (sira no: 1), expected_family=YONETMELIK, claimed_family=TEBLIGLER, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=exact, score=5.75
- YON-03: selected=i̇ş sağliği ve güvenli̇ği̇ ri̇sk değerlendi̇rmesi̇ yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=KKY, identity=weak/none/not_requested, identifier_integrity=exact, article_alignment=none, score=5.75
- YON-05: selected=i̇mar kanunu, expected_family=YONETMELIK, claimed_family=KANUN, identity=weak/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=5.75
- YON-09: selected=mesafeli̇ sözleşmeler yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=KKY, identity=weak/none/not_requested, identifier_integrity=exact, article_alignment=none, score=5.75
- YON-10: selected=i̇ş sağliği ve güvenli̇ği̇ ri̇sk değerlendi̇rmesi̇ yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=KKY, identity=medium/medium_overlap/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=neighbor, score=5.75
- MULGA-05: selected=gayri̇menkul ki̇ralari hakkinda kanunun yürürlükten kaldirilan hükümleri̇, expected_family=MULGA, claimed_family=MULGA, identity=weak/none/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.05
- CBY-06: selected=kamuda geçi̇ci̇ i̇ş pozi̇syonlarinda çalişanlarin sürekli̇ i̇şçi̇ kadrolarina veya sözleşmeli̇ personel statüsüne geçi̇ri̇lmeleri̇, geçi̇ci̇ i̇şçi̇ çaliştirilmasi i̇le bazi kanunlarda deği̇şi̇kli̇k yapilmasi hakkinda kanun, expected_family=CB_YONETMELIK, claimed_family=KANUN, identity=weak/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.10
- YON-07: selected=ti̇cari̇ reklam ve haksiz ti̇cari̇ uygulamalar yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=KKY, identity=weak/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.43
- KHK-03: selected=mi̇llî güvenli̇k kurulu genel sekreterli̇ği̇ni̇n teşki̇lat ve görevleri̇ hakkinda cumhurbaşkanliği kararnamesi̇ (kararname numarasi: 6), expected_family=KHK, claimed_family=CB_KARARNAME, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.55
- UY-08: selected=yükseköğreti̇m kurumlarinin yurt dişi yükseköğreti̇m kurumlariyla ortak eği̇ti̇m öğreti̇m programlarina dai̇r yönetmeli̇k, expected_family=UY, claimed_family=KKY, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=6.55
- KANUN-09: selected=türk borçlar kanunu, expected_family=KANUN, claimed_family=KANUN, identity=weak/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.70
- MULGA-04: selected=patent haklarinin korunmasi hakkinda kanun hükmünde kararname, expected_family=MULGA, claimed_family=KHK, identity=weak/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.78
- CBKAR-02: selected=i̇thalat reji̇mi̇ karari (karar sayisi: 3350), expected_family=CB_KARAR, claimed_family=CB_KARAR, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.80
- CBKAR-03: selected=bursa i̇li̇nde yapilacak olan batarya hücresi̇ ve modül üreti̇m tesi̇si̇ yatirimina proje bazli devlet yardimi veri̇lmesi̇ne i̇li̇şki̇n karar (karar sayisi: 4924), expected_family=CB_KARAR, claimed_family=CB_KARAR, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.80
- CBY-01: selected=vali̇li̇k ve kaymakamlik bi̇ri̇mleri̇ teşki̇lat, görev ve çalişma yönetmeli̇ği̇, expected_family=CB_YONETMELIK, claimed_family=KKY, identity=weak/none/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.85
