# Phase 24T-C Document Identity Regression Audit

Generated at UTC: `2026-05-05T10:24:43Z`  
Git HEAD before C commit: `ab73dc67677aa52045e1db49245daa543905f4d4`

## Scope

Compared Phase23R-E good baseline against Phase24R BASE full. Included rows that were good or acceptable in Phase23R-E and became bad, or where Phase23R-E had selected source evidence but Phase24R BASE had no selected source evidence.

```text
phase23RE_good = reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full
phase24R_base = reports/benchmark/runs/phase_24R_D_base_full_20260504T2035Z
audit_rows = 91
```

## Regression Point Counts

- scorer_only: `91`

## Evidence Availability

```text
phase23RE_evidence_present_and_phase24R_missing = 91
identifier_changed_rows = 11
retrieval_topk_diff_available = false
selector_diff_available = false for scorer_only rows
```

## Critical Interpretation

The audit does not prove that dense retrieval, metadata lookup, rerank, or source identity selection regressed. Phase24R BASE was run with trace disabled, so trace-derived selected document/source/binding fields are absent. That makes the observed wrong-document and hallucinated-identifier spike primarily a scoring/provenance artifact until a trace-on matched rerun proves otherwise.

## Audited Rows

| QID | Phase23R-E selected document | Phase24R selected document | Phase23R-E identifier | Phase24R identifier | Regression point | Safe recovery action |
| --- | --- | --- | --- | --- | --- | --- |
| KKY-11 | BANKA KARTLARI VE KREDİ KARTLARI HAKKINDA YÖNETMELİK | - | 11180 | 31039 m.6 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-08 | TÜRK BORÇLAR KANUNU | - | TBK m.255 | - | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KKY-04 | SOSYAL SİGORTA İŞLEMLERİ YÖNETMELİĞİ | - | 13973 m.2 | 20334 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KKY-08 | ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN YETKİLENDİRME YÖNETMELİĞİ | - | 13078 m.1 | 14387 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBY-02 | KAMU İHALE KURUMU TEŞKİLATI VE PERSONELİNİN ÇALIŞMA USUL VE ESASLARI HAKKINDA YÖNETMELİK | - | 200915611 m.17 | 200915611 m.17 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-02 | İŞ KANUNU | - | IK m.41 | IK m.41 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-05 | KİŞİSEL VERİLERİN KORUNMASI KANUNU | - | KVKK m.6 | KVKK m.6 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-11 | BELEDİYE KANUNU | - | 5393 m.47 | 5393 m.47 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-13 | TÜRK BORÇLAR KANUNU | - | TBK m.417 | TBK m.417 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-14 | TÜRK BORÇLAR KANUNU | - | TBK m.227 | TBK m.227 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-18 | İŞ KANUNU | - | IK m.56 | IK m.56 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-20 | TÜRK MEDENİ KANUNU | - | TMK m.571 | TMK m.571 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-06 | TÜRK TİCARET KANUNU | - | TTK m.595 | TTK m.595 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-04 | KİŞİSEL VERİLERİN KORUNMASI KANUNU | - | KVKK m.6 | KVKK m.6 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-16 | SENDİKALAR VE TOPLU İŞ SÖZLEŞMESİ KANUNU | - | 6356 m.52 | TTK m.4 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-17 | İCRA VE İFLAS KANUNU | - | İİK m.290 | İİK m.290 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| MULGA-04 | COĞRAFİ İŞARETLERİN KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME | - | 555 | 555 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| UY-07 | DİCLE ÜNİVERSİTESİ DİŞ HEKİMLİĞİ FAKÜLTESİ EĞİTİM-ÖĞRETİM SINAV VE KLİNİK DERS YÜKÜ PRATİK UYGULAMA YÖNETMELİĞİ | - | 18872 m.20 | 18872 m.20 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-07 | TÜRK TİCARET KANUNU | - | TTK m.1527 | TTK m.1527 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| YON-05 | PLANLI ALANLAR İMAR YÖNETMELİĞİ | - | 23722 m.1 | 3194 m.18 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| MULGA-05 | GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ | - | 6570 m.gec1 | 6570 m.gec1 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| YON-08 | YÜKSEKÖĞRETİM KURUMLARINDA ÖNLİSANS VE LİSANS DÜZEYİNDEKİ PROGRAMLAR ARASINDA GEÇİŞ, ÇİFT ANADAL, YAN DAL İLE KURUMLAR ARASI KREDİ TRANSFERİ YAPILMASI ESASLARINA İLİŞKİN YÖNETMELİK | - | 13948 | 13948 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBKAR-01 | BİRLEŞMİŞ MİLLETLER GÜVENLİK KONSEYİ'NİN 1970 VE 1973 SAYILI KARARLARI ÇERÇEVESİNDE KABUL EDİLEN 21/6/2011 TARİHLİ VE 2011/2001 SAYILI BAKANLAR KURULU KARARINDA DEĞİŞİKLİK YAPILMASINA DAİR KARAR (KARAR SAYISI: 1169) | - | 1169 | 1169 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-01 | İŞ KANUNU | - | IK m.18 | IK m.18 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-03 | İŞ KANUNU | - | IK m.2 | IK m.2 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| UY-04 | YÜKSEK İHTİSAS ÜNİVERSİTESİ ÖN LİSANS VE LİSANS EĞİTİM-ÖĞRETİM VE SINAV YÖNETMELİĞİ | - | 41014 m.34 | 41014 m.34 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| YON-03 | İŞ SAĞLIĞI VE GÜVENLİĞİ RİSK DEĞERLENDİRMESİ YÖNETMELİĞİ | - | 16925 m.12 | 16925 m.12 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KKY-07 | ELEKTRİK PİYASASI TÜKETİCİ HİZMETLERİ YÖNETMELİĞİ | - | 24630 m.2 | 24630 m.2 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| TUZUK-01 | TAPU SİCİLİ TÜZÜĞÜ | - | 20135150 m.7 | 20135150 m.7 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-19 | TEBLİGAT KANUNU | - | 7201 m.20 | 7201 m.1 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBK-01 | CUMHURBAŞKANLIĞI TEŞKİLATI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 1) | - | 1 | 1 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| MULGA-02 | DEVLET ARŞİV HİZMETLERİ HAKKINDA YÖNETMELİK | - | 33899 | 33899 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBG-01 | Tasarruf Tedbirleri ile İlgili | - | 2024/7 m.0 | 2024/7 m.0 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBG-02 | Bilgi ve İletişim Güvenliği Tedbirleri ile İlgili | - | 2019/12 m.0 | 2019/12 m.0 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBG-03 | İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi ile İlgili | - | 3 m.0 | 3 m.0 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBG-04 | İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi ile İlgili | - | 3 m.0 | 3 m.0 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBK-02 | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11) | - | 11 | 11 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBK-03 | SİBER GÜVENLİK BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 177) | - | 177 | 177 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBK-04 | Dijital Dünyada Çocukların Güçlendirilmesine Yönelik Eylem Planı (2026-2030) ile İlgili | - | 12 | 12 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBK-05 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 49) | - | 49 | 49 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBK-06 | COĞRAFİ BİLGİ SİSTEMLERİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 49) | - | 49 | 49 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBKAR-02 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) | - | 3350 | 3350 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBKAR-03 | BURSA İLİNDE YAPILACAK OLAN ELEKTRİKLİ OTOMOBİL ÜRETİM TESİSİ YATIRIMINA PROJE BAZLI DEVLET YARDIMI VERİLMESİNE İLİŞKİN KARARIN YÜRÜRLÜĞE KONULMASI HAKKINDA KARAR (KARAR SAYISI: 1945) | - | 1945 | 1945 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBKAR-04 | 2019 YILI YATIRIM PROGRAMININ KABULÜ VE UYGULANMASINA DAİR KARAR (KARAR SAYISI: 767) | - | 767 | 767 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBKAR-05 | TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/34) | - | 2008 | 2008 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBKAR-06 | 2019 YILI YATIRIM PROGRAMININ KABULÜ VE UYGULANMASINA DAİR KARAR (KARAR SAYISI: 767) | - | 767 | 767 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBKAR-07 | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) | - | 3350 | 3350 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBKAR-08 | Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903) | - | 9903 | 9903 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBY-01 | ELEKTRONİK İMZA KANUNUNUN UYGULANMASINA İLİŞKİN USUL VE ESASLAR HAKKINDA YÖNETMELİK | - | 7224 | 7224 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBY-03 | DEVLET ARŞİV HİZMETLERİ HAKKINDA YÖNETMELİK | - | 5649 | 5649 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| CBY-05 | KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ | - | 20046801 m.9 | 20046801 m.9 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-09 | TÜRK BORÇLAR KANUNU | - | TBK m.344 | TBK m.344 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-10 | AMME ALACAKLARININ TAHSİL USULÜ HAKKINDA KANUN | - | 6183 | 6183 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-15 | İMAR VE GECEKONDU MEVZUATINA AYKIRI YAPILARA UYGULANACAK BAZI İŞLEMLER VE 6785 SAYILI İMAR KANUNUNUN BİR MADDESİNİN DEĞİŞTİRİLMESİ HAKKINDA KANUN | - | 2981 | 2981 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KANUN-21 | HUKUK UYUŞMAZLIKLARINDA ARABULUCULUK KANUNU | - | 6325 m.18 | 6325 m.18 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KHK-01 | KAMU İKTİSADİ TEŞEBBÜSLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME | - | 233 | 233 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KHK-02 | 657 SAYILI DEVLET MEMURLARI KANUNU, 926 SAYILI TÜRK SİLAHLI KUVVETLERİ PERSONEL KANUNU, 2802 SAYILI HAKİMLER VE SAVCILAR KANUNU, 2914 SAYILI YÜKSEKÖĞRETİM PERSONEL KANUNU, 5434 SAYILI T.C. EMEKLİ SANDIĞI KANUNU İLE DİĞER BAZI KANUN VE KANUN HÜKMÜNDE KARARNAMELERDE DEĞİŞİKLİK YAPILMASI, DEVLET MEMURLARI VE DİĞER KAMU GÖREVLİLERİNE MEMURİYET TABAN AYLIĞI VE KIDEM AYLIĞI İLE EK TAZMİNAT ÖDENMESİ HAKKINDA KANUN HÜKMÜNDE KARARNAME | - | 375 | 375 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KHK-03 | KAMU GÖZETİMİ, MUHASEBE VE DENETİM STANDARTLARI KURUMUNUN TEŞKİLAT VE GÖREVLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME | - | 660 | 660 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KHK-04 | KAMU İKTİSADİ TEŞEBBÜSLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME | - | 233 | 233 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KHK-05 | DEVLET MEMURLARI KANUNU GENEL TEBLİĞİ (Seri No: 161) (666 Sayılı Kanun Hükmünde Kararname Hükümlerine İlişkin) | - | 666 | 666 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KHK-06 | PATENT HAKLARININ KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME | - | 551 | 551 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KKY-02 | BANKALARCA KULLANILACAK UZAKTAN KİMLİK TESPİTİ YÖNTEMLERİNE VE ELEKTRONİK ORTAMDA SÖZLEŞME İLİŞKİSİNİN KURULMASINA İLİŞKİN YÖNETMELİK | - | - | - | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KKY-05 | GENEL SAĞLIK SİGORTASI TESCİL, PRİM VE MÜSTEHAKLIK İŞLEMLERİ YÖNETMELİĞİ | - | 19594 m.17 | 19594 m.17 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KKY-09 | RADYO, TELEVİZYON VE İSTEĞE BAĞLI YAYINLARIN İNTERNET ORTAMINDAN SUNUMU HAKKINDA YÖNETMELİK | - | 32695 | 32695 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KKY-10 | ABONELİK SÖZLEŞMELERİ YÖNETMELİĞİ | - | 20480 m.1 | 20480 m.1 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| MULGA-01 | YÜKSEKÖĞRETİM KURUMLARI ÖĞRENCİ DİSİPLİN YÖNETMELİĞİ | - | 2547 m.54 | 2547 m.54 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| MULGA-03 | TAPU SİCİLİ TÜZÜĞÜ | - | 20135150 m.90 | 20135150 m.90 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| TEB-01 | KAMU İHALE GENEL TEBLİĞİ | - | 13354 m.78 | 13354 m.78 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| TEB-02 | TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/34) | - | 2008 | 2008 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| TEB-03 | VERGİ USUL KANUNU GENEL TEBLİĞİ (SIRA NO: 509) | - | 33905 m.0 | 33905 m.0 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| TEB-05 | SERMAYE PİYASASINDA FİNANSAL RAPORLAMAYA İLİŞKİN ESASLAR TEBLİĞİ (II-14.1) | - | 18477 m.2 | 18477 m.2 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| TEB-06 | ŞİRKET KURULUŞ SÖZLEŞMESİNİN TİCARET SİCİLİ MÜDÜRLÜKLERİNDE İMZALANMASI HAKKINDA TEBLİĞ | - | 23093 | 23093 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| TEB-07 | MUHASEBAT GENEL MÜDÜRLÜĞÜ GENEL TEBLİĞİ (SIRA NO: 81) (EMANET İŞLEMLERİNİN ELEKTRONİK ORTAMDA GERÇEKLEŞTİRİLMESİNE İLİŞKİN USUL VE ESASLAR) | - | - | - | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| TEB-08 | POSTA VE HIZLI KARGO YOLUYLA TAŞINAN EŞYANIN GÜMRÜK İŞLEMLERİNE İLİŞKİN TEBLİĞ (SERİ NO: 1) | - | 39511 m.1 | 39511 m.1 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| TUZUK-02 | TAPU SİCİLİ TÜZÜĞÜ | - | 20135150 m.12 | 20135150 m.12 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| TUZUK-03 | TAPU SİCİLİ TÜZÜĞÜ | - | 20135150 m.69 | 20135150 m.69 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| UY-01 | STRATEJİK ARAŞTIRMALAR ENSTİTÜSÜ (SAREN) LİSANSÜSTÜ EĞİTİM-ÖĞRETİM YÖNETMELİĞİ | - | 24839 m.7 | 24839 m.7 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| UY-02 | ÖZYEĞİN ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ | - | 24070 m.13 | 24070 m.13 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| UY-03 | PAMUKKALE ÜNİVERSİTESİ YABANCI DİLLER YÜKSEKOKULU ÖN LİSANS VE LİSANS YABANCI DİL HAZIRLIK VE YABANCI DİL EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ | - | 14161 m.11 | 14161 m.12 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| UY-06 | MARMARA ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ | - | 23945 m.30 | 19896 m.3 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| UY-08 | YENİ YÜZYIL ÜNİVERSİTESİ ÇİFT ANADAL VE YANDAL YÖNETMELİĞİ | - | 15894 m.17 | 15894 m.17 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| UY-09 | HASAN KALYONCU ÜNİVERSİTESİ ÖNLİSANS VE LİSANS EĞİTİM ÖĞRETİM VE SINAV YÖNETMELİĞİ | - | 16588 m.15 | 16588 m.15 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| UY-10 | İSTANBUL AYDIN ÜNİVERSİTESİ UZAKTAN EĞİTİM PROGRAMLARI UYGULAMA, EĞİTİM-ÖĞRETİM VE SINAV YÖNETMELİĞİ | - | 13219 m.1 | 13219 m.1 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| YON-01 | ELEKTRONİK TEBLİGAT YÖNETMELİĞİ | - | 29033 m.1 | 29033 m.1 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| YON-02 | MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ | - | 20237 m.5 | 20495 m.5 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| YON-06 | KONKORDATO KOMİSERLİĞİ VE ALACAKLILAR KURULUNA DAİR YÖNETMELİK | - | 31238 | 31238 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| YON-07 | TİCARİ REKLAM VE HAKSIZ TİCARİ UYGULAMALAR YÖNETMELİĞİ | - | 20435 m.23 | 20435 m.23 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| YON-09 | MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ | - | 20237 m.8 | 20237 m.8 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| YON-10 | İŞ SAĞLIĞI VE GÜVENLİĞİ RİSK DEĞERLENDİRMESİ YÖNETMELİĞİ | - | 16925 m.15 | 16925 m.15 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| UY-05 | HACETTEPE ÜNİVERSİTESİ YAZ OKULU EĞİTİM-ÖĞRETİM YÖNETMELİĞİ | - | 18365 m.8 | 18365 m.8 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |
| KKY-06 | ELEKTRİK PİYASASI LİSANS YÖNETMELİĞİ | - | 18985 m.12 | 18985 m.2 | scorer_only | rerun Phase24R/S matched full with include_trace=True before code or collection remediation |

## Safe Recovery Direction

- Do not change runtime logic from this audit alone.
- Rerun matched BASE/CBY full with `include_trace=True` and identical scorer/config before diagnosing retrieval or selector regression.
- If trace-on matched BASE reproduces Phase23R-E, archive Phase24R/S trace-off full scores as non-equivalent evidence.
- If trace-on matched BASE remains low, then open a code regression audit between `b34ed1c` and current HEAD.
