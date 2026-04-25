# Phase 18 Recovery Trace Diff

- left_run: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260424T212636_phase17f_full`
- right_run: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260425T_phase18_recovery_A0_phase17f_smoke20`
- compared_qids: 20
- left_summary_raw_score_proxy: `767.91`
- right_summary_raw_score_proxy: `88.77`
- left_pass_proxy: `77`
- right_pass_proxy: `6`
- left_compared_subset_score: `141.18`
- right_compared_subset_score: `88.77`
- left_compared_subset_pass: `14/20`
- right_compared_subset_pass: `6/20`
- degraded_qids: 14

## Most Changed Fields

- final_reason: 18
- score_0_10_proxy: 18
- selected_canonical_source_key_v2: 18
- selected_document_id: 18
- selected_main_span_id: 18
- source_title_claimed: 18
- binding_source_key: 17
- selected_canonical_document_key_v2: 17
- source_identifier_claimed: 17
- article_or_section_claimed: 16
- selected_article: 16
- selected_main_article: 16
- document_match_score: 15
- grounding_status: 15
- hallucinated_source_penalty: 13
- article_match_score: 12
- pass_fail_proxy: 12
- selected_family_source: 12
- answer_slot_coverage_score: 11
- source_family_claimed: 11

## Degraded Rows

- CBKAR-01: delta `-6.23`, family `CB_KARAR` -> `UNKNOWN`, identifier `1362 m.1` -> `unknown`, selected_doc `İTHALAT REJİMİ KARARINA EK KARAR (KARAR SAYISI: 1362)` -> ``
- CBKAR-02: delta `-4.90`, family `CB_KARAR` -> `UNKNOWN`, identifier `3350 m.17` -> `unknown`, selected_doc `İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350)` -> ``
- KANUN-01: delta `-5.63`, family `KANUN` -> `KANUN`, identifier `IK m.18` -> `HMK m.452`, selected_doc `İŞ KANUNU` -> `HUKUK MUHAKEMELERİ KANUNU`
- KANUN-15: delta `-0.29`, family `KANUN` -> `KANUN`, identifier `2981 m.9` -> `TCK m.184`, selected_doc `İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA UYGULANACAK BAZI İŞLEMLER VE 6785 SAYILI İMAR KANUNUNUN BİR MADDESİNİN DEĞİŞTİRİLMESİ HAKKINDA KANUN` -> `TÜRK CEZA KANUNU`
- MULGA-01: delta `-5.73`, family `MULGA` -> `KANUN`, identifier `2547 m.65` -> `HMK m.42`, selected_doc `YÜKSEKÖĞRETİM KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ` -> `HUKUK MUHAKEMELERİ KANUNU`
- MULGA-02: delta `-7.95`, family `MULGA` -> `KANUN`, identifier `4045 m.1` -> `unknown`, selected_doc `GÜVENLİK SORUŞTURMASI,BAZI NEDENLERLE GÖREVLERİNE SON VERİLEN KAMU PERSONELİ İLE KAMU GÖREVİNE ALINMAYANLARIN HAKLARININ GERİ VERİLMESİNE VE 1402 NUMARALI SIKI- YÖNETİM KANUNUNDA DEĞİŞİKLİK YAPILMASINA İLİŞKİN KANUN` -> `HUKUK MUHAKEMELERİ KANUNU`
- MULGA-03: delta `-1.45`, family `MULGA` -> `KANUN`, identifier `743 m.924` -> `unknown`, selected_doc `TÜRK KANUNU MEDENİSİNİN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ` -> `TÜRK MEDENİ KANUNU`
- MULGA-04: delta `-7.52`, family `MULGA` -> `KANUN`, identifier `556 m.42` -> `TTK m.56`, selected_doc `MARKALARIN KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME` -> `TÜRK TİCARET KANUNU`
- MULGA-05: delta `-1.80`, family `MULGA` -> `KANUN`, identifier `6570 m.16` -> `unknown`, selected_doc `GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ` -> `İCRA VE İFLAS KANUNU`
- TEB-01: delta `-6.00`, family `TEBLIGLER` -> `UNKNOWN`, identifier `13354 m.79` -> `unknown`, selected_doc `KAMU İHALE GENEL TEBLİĞİ` -> ``
- TEB-02: delta `-5.55`, family `TEBLIGLER` -> `UNKNOWN`, identifier `11990 m.1` -> `unknown`, selected_doc `TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/34)` -> ``
- YON-01: delta `-4.45`, family `YONETMELIK` -> `UNKNOWN`, identifier `18615 m.26` -> `unknown`, selected_doc `İŞYERİ HEKİMİ VE DİĞER SAĞLIK PERSONELİNİN GÖREV, YETKİ, SORUMLULUK VE EĞİTİMLERİ HAKKINDA YÖNETMELİK` -> ``
- YON-02: delta `-2.80`, family `KANUN` -> `KANUN`, identifier `unknown` -> `unknown`, selected_doc `TÜKETİCİNİN KORUNMASI HAKKINDA KANUN` -> `TÜRK TİCARET KANUNU`
- YON-03: delta `-6.10`, family `YONETMELIK` -> `KANUN`, identifier `16925 m.12` -> `TTK m.1445`, selected_doc `İŞ SAĞLIĞI VE GÜVENLİĞİ RİSK DEĞERLENDİRMESİ YÖNETMELİĞİ` -> `TÜRK TİCARET KANUNU`
