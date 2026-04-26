# Phase 18 Recovery A1.10 Trace Ordering Diff

## Scope

- Candidate trace: `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_full_candidate_rerun_after_mulga_fix`
- Live trace: `reports/benchmark/runs/20260426T_phase18_recovery_A1_9_live_full100`
- Compared QIDs: A1.9 row-level PASS/FAIL drift set.
- Detail CSV: `reports/benchmark/phase_18_recovery_A1_10_trace_ordering_diff.csv`

## Classification Summary

| Classification | Count |
| --- | ---: |
| retrieval_ordering_nondeterminism | 7 |
| confidence/finalization drift | 4 |

## Row Summary

| QID | Direction | Classification | Candidate selected source | Live selected source | Candidate -> Live score | Candidate -> Live pass |
| --- | --- | --- | --- | --- | ---: | --- |
| `CBY-01` | candidate_PASS_live_FAIL | confidence/finalization drift | YONETMELIK / VALİLİK VE KAYMAKAMLIK BİRİMLERİ TEŞKİLAT, GÖREV VE ÇALIŞMA YÖNETMELİĞİ / m.38 | YONETMELIK / VALİLİK VE KAYMAKAMLIK BİRİMLERİ TEŞKİLAT, GÖREV VE ÇALIŞMA YÖNETMELİĞİ / m.38 | 7.75 -> 0.00 | PASS -> FAIL |
| `CBY-06` | candidate_PASS_live_FAIL | confidence/finalization drift | CB_YONETMELIK / KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ / m.14 | CB_YONETMELIK / KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ / m.14 | 7.14 -> 6.80 | PASS -> FAIL |
| `KANUN-15` | candidate_PASS_live_FAIL | confidence/finalization drift | KANUN / İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA UYGULANACAK BAZI İŞLEMLER VE 6785 SAYILI İMAR KANUNUNUN BİR MADDESİNİN DEĞİŞTİRİLMESİ HAKKINDA KANUN / m.9 | KANUN / İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA UYGULANACAK BAZI İŞLEMLER VE 6785 SAYILI İMAR KANUNUNUN BİR MADDESİNİN DEĞİŞTİRİLMESİ HAKKINDA KANUN / m.9 | 7.55 -> 6.32 | PASS -> FAIL |
| `TEB-01` | candidate_PASS_live_FAIL | confidence/finalization drift | TEBLIGLER / KAMU İHALE GENEL TEBLİĞİ / m.79 | TEBLIGLER / KAMU İHALE GENEL TEBLİĞİ / m.79 | 8.35 -> 0.00 | PASS -> FAIL |
| `TEB-03` | candidate_PASS_live_FAIL | retrieval_ordering_nondeterminism | TEBLIGLER / VERGİ USUL KANUNU GENEL TEBLİĞİ (SIRA NO: 431) / m.8 | MULGA / 6563 SAYILI ELEKTRONİK TİCARETİN DÜZENLENMESİ HAKKINDA KANUNUN 12 NCİ MADDESİNE GÖRE 2026 YILINDA UYGULANACAK OLAN İDARİ PARA CEZALARINA İLİŞKİN TEBLİĞ / m.0 | 9.10 -> 5.35 | PASS -> FAIL |
| `YON-05` | candidate_PASS_live_FAIL | retrieval_ordering_nondeterminism | YONETMELIK / GAZİANTEP BÜYÜKŞEHİR BELEDİYESİ İMAR YÖNETMELİĞİ / m.5 | YONETMELIK / ONDOKUZ MAYIS ÜNİVERSİTESİ TAŞINMAZLARININ İDARESİ HAKKINDA YÖNETMELİK / m.3 | 9.10 -> 3.25 | PASS -> FAIL |
| `CBY-03` | candidate_FAIL_live_PASS | retrieval_ordering_nondeterminism | CB_YONETMELIK / MADEN VE PETROL İŞLERİ GENEL MÜDÜRLÜĞÜ TEFTİŞ KURULU YÖNETMELİĞİ / m.88 | CB_YONETMELIK / DEVLET ARŞİV HİZMETLERİ HAKKINDA YÖNETMELİK / m.4 | 2.50 -> 8.80 | FAIL -> PASS |
| `KHK-06` | candidate_FAIL_live_PASS | retrieval_ordering_nondeterminism | KHK / ENDÜSTRİYEL TASARIMLARIN KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME / m.3 | KHK / PATENT HAKLARININ KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME / m.136 | 6.80 -> 9.25 | FAIL -> PASS |
| `KKY-02` | candidate_FAIL_live_PASS | retrieval_ordering_nondeterminism | KANUN / KİŞİSEL VERİLERİN KORUNMASI KANUNU / m.2 | KKY / BANKALARCA KULLANILACAK UZAKTAN KİMLİK TESPİTİ YÖNTEMLERİNE VE ELEKTRONİK ORTAMDA SÖZLEŞME İLİŞKİSİNİN KURULMASINA İLİŞKİN YÖNETMELİK / m.1 | 1.45 -> 9.55 | FAIL -> PASS |
| `KKY-04` | candidate_FAIL_live_PASS | retrieval_ordering_nondeterminism | KKY / TARIM İŞLETMELERİ GENEL MÜDÜRLÜĞÜ ANA STATÜSÜ HAKKINDA KARAR (KARAR SAYISI: 5141) / m.13 | KKY / BANKALAR VE KAMU İDARELERİ TARAFINDAN YAPILACAK OLAN SİGORTALILIK KONTROLÜ İLE KURUM VE KURULUŞLARDAN BİLGİ VE BELGELERİN ALINMASINA İLİŞKİN USUL VE ESASLAR HAKKINDA YÖNETMELİK / m.9 | 3.25 -> 9.32 | FAIL -> PASS |
| `YON-03` | candidate_FAIL_live_PASS | retrieval_ordering_nondeterminism | UY / TRAKYA ÜNİVERSİTESİ RİSK YÖNETİMİ VE KURUMSAL SÜRDÜRÜLEBİLİRLİK UYGULAMA VE ARAŞTIRMA MERKEZİ YÖNETMELİĞİ / m.2 | YONETMELIK / İŞ SAĞLIĞI VE GÜVENLİĞİ RİSK DEĞERLENDİRMESİ YÖNETMELİĞİ / m.12 | 1.45 -> 7.82 | FAIL -> PASS |

## Interpretation

The A1.9 row drift is not caused by same-endpoint instability in the 20-QID repeat probes. The drift concentrates in candidate/live source selection and finalization differences from separate process lifecycles/runs.

- Rows with changed selected document or family are classified as `retrieval_ordering_nondeterminism` when top-ranked candidate lists also differ, otherwise `source_lock_tie_break`.
- Rows with the same selected source but changed pass/fail or confidence are classified as `confidence/finalization drift`.
- The detailed top5 candidate lists, metadata lookup values, source-lock keys, and confidence values are preserved in the CSV.

## Decision

Trace drift is explainable and bounded for cutover purposes under A1.10 because same-endpoint repeatability passed and the directional adverse-delta gate passed. The remaining drift should be tracked before productization, but it does not block the controlled cutover retry.
