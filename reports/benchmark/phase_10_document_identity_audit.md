# Phase 10 Document Identity Audit

- source_run_dir: `reports/benchmark/runs/20260422T180225Z_phase10_full`
- rows_analyzed: 100
- wrong_document: 15
- hallucinated_identifier: 32
- hallucinated_source_count: 15
- selected_article_equals_claimed_article_count: 64
- right_document_wrong_article_or_span: 51

## Metadata Identity Strength
- medium: 22
- none: 3
- strong: 75

## Title Match Type
- exact_phrase: 2
- medium_overlap: 28
- none: 45
- strong_overlap: 3
- weak_overlap: 22

## Identifier Integrity
- exact: 45
- replaced_by_selected_evidence: 31
- selected_evidence_identifier_suppressed: 10
- unverified_claim_suppressed: 14

## Article Alignment
- exact: 54
- neighbor: 5
- none: 27
- title_only: 14

## Worst Rows
- CBG-01: selected=rehberlik, teftiş ve denetim faaliyetlerinin düzenli ve etkin bir şekilde yerine getirilmesi ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, identity=medium/none/not_requested, identifier_integrity=exact, article_alignment=title_only, score=3.25
- CBG-02: selected=roman vatandaşlara yönelik strateji belgesi ii. aşama eylem planı ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, identity=strong/none/exact_identifier, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=3.25
- CBG-03: selected=sanal ortamda yasa dışı bahis, şans oyunları ve kumarla mücadele eylem planı (2025-2026) ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=3.25
- CBG-04: selected=sanal ortamda yasa dışı bahis, şans oyunları ve kumarla mücadele eylem planı (2025-2026) ile i̇lgili, expected_family=CB_GENELGE, claimed_family=CB_GENELGE, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=2.50
- CBKAR-01: selected=kullanilmiş veya yeni̇leşti̇ri̇lmi̇ş eşya i̇thalatina i̇li̇şki̇n tebli̇ğ (i̇thalat: 2026/9), expected_family=CB_KARAR, claimed_family=TEBLIGLER, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=5.00
- CBKAR-04: selected=ti̇caret bakanliği gümrükler muhafaza genel müdürlüğü tarafindan 4734 sayili kamu i̇hale kanununun 3 üncü maddesi̇ni̇n (b) bendi̇ kapsaminda yapilacak i̇halelere i̇li̇şki̇n usul ve esaslar (karar sayisi: 5997), expected_family=CB_KARAR, claimed_family=CB_YONETMELIK, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=1.45
- CBKAR-05: selected=türk parasi kiymeti̇ni̇ koruma hakkinda 32 sayili karara i̇li̇şki̇n tebli̇ğ (tebli̇ğ no: 2018-32/45), expected_family=CB_KARAR, claimed_family=TEBLIGLER, identity=strong/weak_overlap/exact_identifier, identifier_integrity=exact, article_alignment=none, score=7.19
- CBKAR-08: selected=türk ti̇caret kanununun mer'i̇yet ve tatbi̇k şekli̇ hakkinda kanunun yürürlükten kaldirilan hükümleri̇, expected_family=CB_KARAR, claimed_family=MULGA, identity=strong/none/none, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=5.00
- CBY-01: selected=vali̇li̇k ve kaymakamlik bi̇ri̇mleri̇ teşki̇lat, görev ve çalişma yönetmeli̇ği̇, expected_family=CB_YONETMELIK, claimed_family=KKY, identity=strong/none/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.85
- CBY-04: selected=devlet arşi̇vleri̇ başkanliği hakkinda cumhurbaşkanliği kararnamesi̇ (kararname numarasi: 11), expected_family=CB_YONETMELIK, claimed_family=CB_KARARNAME, identity=medium/none/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=exact, score=7.12
- CBY-05: selected=ulusal erişilebilirlik günü ile i̇lgili, expected_family=CB_YONETMELIK, claimed_family=CB_GENELGE, identity=medium/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=title_only, score=1.45
- CBY-06: selected=kamuda geçi̇ci̇ i̇ş pozi̇syonlarinda çalişanlarin sürekli̇ i̇şçi̇ kadrolarina veya sözleşmeli̇ personel statüsüne geçi̇ri̇lmeleri̇, geçi̇ci̇ i̇şçi̇ çaliştirilmasi i̇le bazi kanunlarda deği̇şi̇kli̇k yapilmasi hakkinda kanun, expected_family=CB_YONETMELIK, claimed_family=KANUN, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.10
- KANUN-02: selected=fazla çalişmanin uygulama esaslarinin gösteri̇r yönetmeli̇k, expected_family=KANUN, claimed_family=YONETMELIK, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=5.75
- KANUN-03: selected=i̇şyeri̇ sendi̇ka temsi̇lci̇leri̇ni̇n faali̇yetleri̇ i̇le çalişmaya devam eden sendi̇ka yöneti̇ci̇leri̇ne veri̇lecek haftada bi̇r gün i̇zni̇n kullandirilmasina i̇li̇şki̇n usul ve esaslar hakkinda tebli̇ğ, expected_family=KANUN, claimed_family=TEBLIGLER, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=title_only, score=6.85
- KANUN-04: selected=i̇ş sağliği ve güvenli̇ği̇ hi̇zmetleri̇ yönetmeli̇ği̇, expected_family=KANUN, claimed_family=KKY, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=5.75
- KANUN-06: selected=türk ti̇caret kanununun yürürlükten kaldirilan hükümleri̇, expected_family=KANUN, claimed_family=MULGA, identity=strong/none/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=1.45
- KANUN-09: selected=türk borçlar kanunu, expected_family=KANUN, claimed_family=KANUN, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.70
- KANUN-19: selected=turi̇zmi̇ teşvi̇k kanunu hükümleri̇ uyarinca veri̇len i̇dari̇ para cezalarinin tebli̇gatinin elektroni̇k ortamda yapilmasina i̇li̇şki̇n tebli̇ğ, expected_family=KANUN, claimed_family=TEBLIGLER, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=neighbor, score=7.75
- KHK-03: selected=mi̇llî güvenli̇k kurulu genel sekreterli̇ği̇ni̇n teşki̇lat ve görevleri̇ hakkinda cumhurbaşkanliği kararnamesi̇ (kararname numarasi: 6), expected_family=KHK, claimed_family=CB_KARARNAME, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.55
- KKY-02: selected=bankalarin i̇zne tabi̇ i̇şlemleri̇ i̇le dolayli pay sahi̇pli̇ği̇ne i̇li̇şki̇n yönetmeli̇k, expected_family=KKY, claimed_family=KKY, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=3.25
- KKY-04: selected=sosyal si̇gortalar ve genel sağlik si̇gortasi kanunu, expected_family=KKY, claimed_family=KANUN, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=6.85
- KKY-06: selected=ardahan üni̇versi̇tesi̇ önli̇sans-li̇sans eği̇ti̇m-öğreti̇m ve sinav yönetmeli̇ği̇, expected_family=KKY, claimed_family=UY, identity=strong/medium_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=7.53
- KKY-10: selected=tari̇fe yönetmeli̇ği̇, expected_family=KKY, claimed_family=KKY, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=3.25
- MULGA-01: selected=munzur üni̇versi̇tesi̇ ön li̇sans ve li̇sans eği̇ti̇m-öğreti̇m yönetmeli̇ği̇, expected_family=MULGA, claimed_family=UY, identity=medium/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=none, score=3.43
- MULGA-03: selected=tapu si̇ci̇li̇ tüzüğü, expected_family=MULGA, claimed_family=TUZUK, identity=strong/exact_phrase/not_requested, identifier_integrity=exact, article_alignment=exact, score=0.00
- MULGA-04: selected=patent haklarinin korunmasi hakkinda kanun hükmünde kararname, expected_family=MULGA, claimed_family=KHK, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.78
- MULGA-05: selected=gayri̇menkul ki̇ralari hakkinda kanunun yürürlükten kaldirilan hükümleri̇, expected_family=MULGA, claimed_family=MULGA, identity=strong/none/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=6.05
- TEB-04: selected=vergi̇ usul kanunu genel tebli̇ği̇ (sira no: 520), expected_family=TEBLIGLER, claimed_family=TEBLIGLER, identity=medium/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=title_only, score=2.50
- TUZUK-05: selected=gida maddeleri̇ni̇n ve umumi̇ sağliği i̇lgi̇lendi̇ren eşya ve levazimin hususi̇ vasiflarini gösteren tüzük, expected_family=TUZUK, claimed_family=TUZUK, identity=medium/none/not_requested, identifier_integrity=selected_evidence_identifier_suppressed, article_alignment=title_only, score=3.25
- UY-07: selected=ki̇şi̇sel veri̇leri̇n korunmasi kanunu, expected_family=UY, claimed_family=KANUN, identity=medium/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=none, score=1.45
- UY-08: selected=yükseköğreti̇m kurumlarinin yurt dişi yükseköğreti̇m kurumlariyla ortak eği̇ti̇m öğreti̇m programlarina dai̇r yönetmeli̇k, expected_family=UY, claimed_family=KKY, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=6.55
- UY-10: selected=kafkas üni̇versi̇tesi̇ önli̇sans ve li̇sans uzaktan eği̇ti̇m-öğreti̇m ve sinav yönetmeli̇ği̇, expected_family=UY, claimed_family=UY, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=exact, score=3.59
- YON-01: selected=elektroni̇k tebli̇gat si̇stemi̇ genel tebli̇ği̇ (sira no: 1), expected_family=YONETMELIK, claimed_family=TEBLIGLER, identity=strong/weak_overlap/not_requested, identifier_integrity=exact, article_alignment=exact, score=5.75
- YON-02: selected=adalet bakanliği tarafindan 4734 sayili kamu i̇hale kanununun 3 üncü maddesi̇ni̇n (b) bendi̇ kapsaminda yapilacak i̇halelere i̇li̇şki̇n esas ve usuller, expected_family=YONETMELIK, claimed_family=CB_YONETMELIK, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=1.45
- YON-03: selected=i̇ş sağliği ve güvenli̇ği̇ ri̇sk değerlendi̇rmesi̇ yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=KKY, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=none, score=5.75
- YON-05: selected=i̇mar kanunu, expected_family=YONETMELIK, claimed_family=KANUN, identity=strong/weak_overlap/not_requested, identifier_integrity=replaced_by_selected_evidence, article_alignment=exact, score=5.75
- YON-06: selected=havacilik tibbi eği̇ti̇m yönetmeli̇ği̇ (shy-hte), expected_family=YONETMELIK, claimed_family=KKY, identity=medium/none/not_requested, identifier_integrity=unverified_claim_suppressed, article_alignment=neighbor, score=1.45
- YON-07: selected=ti̇cari̇ reklam ve haksiz ti̇cari̇ uygulamalar yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=KKY, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=exact, score=6.43
- YON-08: selected=işik üni̇versi̇tesi̇ yatay geçi̇ş, çi̇ft anadal, yan dal ve kredi̇ transferi̇ yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=UY, identity=strong/medium_overlap/not_requested, identifier_integrity=exact, article_alignment=none, score=5.00
- YON-09: selected=mesafeli̇ sözleşmeler yönetmeli̇ği̇, expected_family=YONETMELIK, claimed_family=KKY, identity=strong/none/not_requested, identifier_integrity=exact, article_alignment=none, score=5.75
