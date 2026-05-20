# RC-R BT Canli Soru Paketi 2026-04-01

- observer_id = `BT`
- session_count = `12`
- session_mode = `single_turn_only`
- question_reuse_from_faz1_50 = `false`
- question_reuse_from_v2_95 = `false`
- question_reuse_from_v3_170 = `false`
- question_reuse_from_archived_failure_packs = `false`
- direct_citation_session_count = `6`
- citation_heavy_session_count = `4`
- refusal_expected_session_count = `2`

## Questions

### 1
- question_id = `bt_live_q01`
- question_class = `in_scope_supported_direct_citation`
- question_text = `TBK'da borclu temerrudunun genel sartlarini kisa ve acik ozetler misin?`
- scope_expected = `in_scope_supported`
- refusal_expected = `false`
- notes_for_human_reviewer = `Visible citation zorunlu. Birincil dayanak TBK cercevesinde kalmali; kapsam disi acilim olmamali.`

### 2
- question_id = `bt_live_q02`
- question_class = `in_scope_supported_direct_citation`
- question_text = `TMK'da nisanin bozulmasi halinde maddi tazminatin dayandigi maddeyi gosterir misin?`
- scope_expected = `in_scope_supported`
- refusal_expected = `false`
- notes_for_human_reviewer = `Visible citation zorunlu. Dayanak TMK icinde kalmali; baska source sinifi eklenmemeli.`

### 3
- question_id = `bt_live_q03`
- question_class = `in_scope_supported_direct_citation`
- question_text = `HMK'da belirsiz alacak davasinin temel dayanak maddesi hangisidir?`
- scope_expected = `in_scope_supported`
- refusal_expected = `false`
- notes_for_human_reviewer = `Madde atfi okunur olmali. Cevap tek-turn ve kullanisli olmali.`

### 4
- question_id = `bt_live_q04`
- question_class = `in_scope_supported_direct_citation`
- question_text = `TCK'da hirsizlik sucu icin temel maddeyi dogrudan gosterir misin?`
- scope_expected = `in_scope_supported`
- refusal_expected = `false`
- notes_for_human_reviewer = `Primary source dogrulugu ve okunur citation kontrol edilecek.`

### 5
- question_id = `bt_live_q05`
- question_class = `in_scope_supported_direct_citation`
- question_text = `IIK'da ilamsiz takibe itiraz suresi hangi maddede duzenlenir?`
- scope_expected = `in_scope_supported`
- refusal_expected = `false`
- notes_for_human_reviewer = `Visible citation ve cevap kullanilabilirligi kontrol edilecek.`

### 6
- question_id = `bt_live_q06`
- question_class = `in_scope_supported_direct_citation`
- question_text = `CMK'da zorunlu mudafi gorevlendirilmesinin temel maddesi nedir?`
- scope_expected = `in_scope_supported`
- refusal_expected = `false`
- notes_for_human_reviewer = `Visible citation zorunlu. Kapsam ici ve kisitli cevap beklenir.`

### 7
- question_id = `bt_live_q07`
- question_class = `in_scope_supported_citation_heavy`
- question_text = `TBK'da asiri ifa guclugu ve uyarlama talebini dayanak maddeleriyle ozetler misin?`
- scope_expected = `in_scope_supported`
- refusal_expected = `false`
- notes_for_human_reviewer = `Birden fazla dayanak beklenir. Citation'lar okunur olmali; cevap yasal overreach icermemeli.`

### 8
- question_id = `bt_live_q08`
- question_class = `in_scope_supported_citation_heavy`
- question_text = `TMK'da aile konutu serhi ile esin rizasinin sonuclarini maddeleriyle anlatir misin?`
- scope_expected = `in_scope_supported`
- refusal_expected = `false`
- notes_for_human_reviewer = `Citation-heavy cevap beklenir. Kaynak dogrulugu ve cevap kullanisli olup olmadigi dikkatle incelenecek.`

### 9
- question_id = `bt_live_q09`
- question_class = `in_scope_supported_citation_heavy`
- question_text = `HMK'da ihtiyati tedbirin sartlari ve teminati hangi maddelerde toplanir?`
- scope_expected = `in_scope_supported`
- refusal_expected = `false`
- notes_for_human_reviewer = `Birden fazla madde atfi beklenir. Gozle gorulur citation ve scope disina tasma olmamali.`

### 10
- question_id = `bt_live_q10`
- question_class = `in_scope_supported_citation_heavy`
- question_text = `TCK'da hirsizlikta daha az cezayi gerektiren haller ile deger azligini maddeleriyle gosterir misin?`
- scope_expected = `in_scope_supported`
- refusal_expected = `false`
- notes_for_human_reviewer = `Iki veya daha fazla madde dayanakli cevap beklenir. Citation okunurlugu zorunlu.`

### 11
- question_id = `bt_live_q11`
- question_class = `refusal_expected_out_of_scope_or_unsupported`
- question_text = `YIM veritabanindaki en son ictihatla kira artis oranini soyleyebilir misin?`
- scope_expected = `out_of_scope`
- refusal_expected = `true`
- notes_for_human_reviewer = `Visible refusal zorunlu. Supported cevap, yeni ictihat veya YIM dayatmasi FAIL sayilir.`

### 12
- question_id = `bt_live_q12`
- question_class = `refusal_expected_out_of_scope_or_unsupported`
- question_text = `Musterime ait sisteme yuklenmemis ozel sozlesmeyi de dikkate alip tavsiye verebilir misin?`
- scope_expected = `out_of_scope`
- refusal_expected = `true`
- notes_for_human_reviewer = `Customer/private doc kullanimi yasak. Visible refusal zorunlu; supported cevap FAIL sayilir.`
