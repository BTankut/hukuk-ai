# Phase 18 Recovery A1.8 Failed Row Cluster Audit

Scope: read-only audit of A1.7 full-collection candidate run. No runtime logic was changed.

- Input run: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260425T_phase18_recovery_A1_7_full_collection_candidate`
- Rows audited: `28`
- YONETMELIK dominant failure: `family_prior_error (3/7)`
- MULGA dominant failure: `active_repealed_arbitration_error (3/3)`
- KANUN dominant failure: `document_identity_rerank_error (2/6)`
- Strong-family watch dominant failure: `strong_family_regression (8/12)`

## Fix Type Counts

| fix_type | count |
|---|---:|
| `strong_family_regression` | 8 |
| `source_key_alias_collision` | 4 |
| `family_prior_error` | 3 |
| `wrong_supporting_source_promoted` | 3 |
| `active_repealed_arbitration_error` | 3 |
| `rubric_only_not_source_error` | 3 |
| `document_identity_rerank_error` | 2 |
| `metadata_candidate_missing` | 1 |
| `relation_query_arbitration_error` | 1 |

## Cluster Matrix

| cluster | fix_type | count |
|---|---|---:|
| `KANUN` | `document_identity_rerank_error` | 2 |
| `KANUN` | `relation_query_arbitration_error` | 1 |
| `KANUN` | `source_key_alias_collision` | 1 |
| `KANUN` | `wrong_supporting_source_promoted` | 2 |
| `MULGA` | `active_repealed_arbitration_error` | 3 |
| `STRONG_FAMILY_WATCH` | `rubric_only_not_source_error` | 3 |
| `STRONG_FAMILY_WATCH` | `source_key_alias_collision` | 1 |
| `STRONG_FAMILY_WATCH` | `strong_family_regression` | 8 |
| `YONETMELIK` | `family_prior_error` | 3 |
| `YONETMELIK` | `metadata_candidate_missing` | 1 |
| `YONETMELIK` | `source_key_alias_collision` | 2 |
| `YONETMELIK` | `wrong_supporting_source_promoted` | 1 |

## Dominant Failure Notes

- YONETMELIK: family boundary is being overwritten by KKY/UY/CB_YONETMELIK and, in some rows, supporting KANUN/TEBLIGLER sources become primary.
- MULGA: family detection is mostly correct, but historical/repealed internal document arbitration selects the wrong repealed/current-adjacent source and sometimes lacks materialized span evidence.
- KANUN: relation and hierarchy questions still promote regulation/teblig/repealed material as primary or select the wrong active law inside KANUN.
- Strong-family watch: failures split between true family/document regressions and rubric-only/source-content gaps; the latter should not drive broad routing changes.

## Audited Rows

| qid | cluster | score | expected | claimed | selected_document | fix_type |
|---|---|---:|---|---|---|---|
| `YON-01` | `YONETMELIK` | 5.75 | `YONETMELIK` | `KKY` | SENDİKALAR VE TOPLU İŞ SÖZLEŞMESİ KANUNU | `source_key_alias_collision` |
| `YON-02` | `YONETMELIK` | 6.85 | `YONETMELIK` | `KKY` | MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ | `family_prior_error` |
| `YON-03` | `YONETMELIK` | 1.45 | `YONETMELIK` | `CB_YONETMELIK` | 6713 SAYILI KOLLUK GÖZETİM KOMİSYONU KURULMASI HAKKINDA KANUNUN UYGULANMASINA DAİR YÖNETME | `family_prior_error` |
| `YON-05` | `YONETMELIK` | 5.75 | `YONETMELIK` | `KANUN` | İMAR KANUNU | `wrong_supporting_source_promoted` |
| `YON-06` | `YONETMELIK` | 3.25 | `YONETMELIK` | `YONETMELIK` | CEZA İNFAZ KURUMLARI VE TUTUKEVLERİ PERSONELİ EĞİTİM MERKEZLERİ KURULUŞ, GÖREV VE ÇALIŞMA  | `metadata_candidate_missing` |
| `YON-08` | `YONETMELIK` | 5.45 | `YONETMELIK` | `UY` | IŞIK ÜNİVERSİTESİ YATAY GEÇİŞ, ÇİFT ANADAL, YAN DAL VE KREDİ TRANSFERİ YÖNETMELİĞİ | `family_prior_error` |
| `YON-10` | `YONETMELIK` | 1.45 | `YONETMELIK` | `KKY` | SENDİKALAR VE TOPLU İŞ SÖZLEŞMESİ KANUNU | `source_key_alias_collision` |
| `MULGA-01` | `MULGA` | 0.00 | `MULGA` | `MULGA` | MİLLİ EĞİTİM BAKANLIĞININ TEŞKİLAT VE GÖREVLERİ HAKKINDA KANUN | `active_repealed_arbitration_error` |
| `MULGA-02` | `MULGA` | 3.25 | `MULGA` | `MULGA` | KÜLTÜR VE TURİZM BAKANLIĞI TEŞKİLAT VE GÖREVLERİ HAKKINDA KANUN | `active_repealed_arbitration_error` |
| `MULGA-05` | `MULGA` | 2.50 | `MULGA` | `MULGA` | GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ | `active_repealed_arbitration_error` |
| `KANUN-02` | `KANUN` | 3.59 | `KANUN` | `KANUN` | TÜRK BORÇLAR KANUNU | `document_identity_rerank_error` |
| `KANUN-03` | `KANUN` | 6.09 | `KANUN` | `YONETMELIK` | ALT İŞVERENLİK YÖNETMELİĞİ | `relation_query_arbitration_error` |
| `KANUN-04` | `KANUN` | 1.45 | `KANUN` | `TEBLIGLER` | DIŞ TİCARETTE RİSK ESASLI KONTROL SİSTEMİ TEBLİĞİ (ÜRÜN GÜVENLİĞİ VE DENETİMİ: 2011/53) | `wrong_supporting_source_promoted` |
| `KANUN-09` | `KANUN` | 0.70 | `KANUN` | `MULGA` | GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ | `wrong_supporting_source_promoted` |
| `KANUN-18` | `KANUN` | 3.25 | `KANUN` | `KANUN` | TÜRK BORÇLAR KANUNU | `document_identity_rerank_error` |
| `KANUN-19` | `KANUN` | 6.05 | `KANUN` | `KANUN` | TEBLİGAT KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ | `source_key_alias_collision` |
| `CBKAR-03` | `STRONG_FAMILY_WATCH` | 6.80 | `CB_KARAR` | `CB_KARAR` | İSTANBUL İLİNDE YAPILACAK OLAN İNSANSIZ HAVA ARAÇLARI VE AKILLI SİSTEMLER ÜRETİM TESİSİ YA | `rubric_only_not_source_error` |
| `CBKAR-08` | `STRONG_FAMILY_WATCH` | 6.80 | `CB_KARAR` | `CB_KARAR` | Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903) | `source_key_alias_collision` |
| `CBY-01` | `STRONG_FAMILY_WATCH` | 1.45 | `CB_YONETMELIK` | `YONETMELIK` | ELEKTRONİK İMZA KANUNUNUN UYGULANMASINA İLİŞKİN USUL VE ESASLAR HAKKINDA YÖNETMELİK | `strong_family_regression` |
| `CBY-03` | `STRONG_FAMILY_WATCH` | 2.50 | `CB_YONETMELIK` | `CB_YONETMELIK` | MADEN VE PETROL İŞLERİ GENEL MÜDÜRLÜĞÜ TEFTİŞ KURULU YÖNETMELİĞİ | `strong_family_regression` |
| `KHK-06` | `STRONG_FAMILY_WATCH` | 6.80 | `KHK` | `KHK` | PATENT HAKLARININ KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME | `rubric_only_not_source_error` |
| `KKY-01` | `STRONG_FAMILY_WATCH` | 6.65 | `KKY` | `YONETMELIK` | BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKACILIK HİZMETLERİ HAKKINDA YÖNETMELİK | `strong_family_regression` |
| `KKY-04` | `STRONG_FAMILY_WATCH` | 3.25 | `KKY` | `KKY` | TARIM İŞLETMELERİ GENEL MÜDÜRLÜĞÜ ANA STATÜSÜ HAKKINDA KARAR (KARAR SAYISI: 5141) | `strong_family_regression` |
| `KKY-10` | `STRONG_FAMILY_WATCH` | 6.09 | `KKY` | `TEBLIGLER` | SABİT TELEFON ŞEBEKESİNE ERİŞİM VEYA SABİT ŞEBEKE ÜZERİNDEN ARAMA HİZMETLERİNE YÖNELİK İLG | `strong_family_regression` |
| `TUZUK-04` | `STRONG_FAMILY_WATCH` | 0.70 | `TUZUK` | `MULGA` | TÜRK TİCARET KANUNUNUN MER'İYET VE TATBİK ŞEKLİ HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜ | `strong_family_regression` |
| `TUZUK-05` | `STRONG_FAMILY_WATCH` | 3.25 | `TUZUK` | `TUZUK` | TÜRK MEDENİ KANUNUNUN VELAYET, VESAYET VE MİRAS HÜKÜMLERİNİN UYGULANMASINA DAİR TÜZÜK | `strong_family_regression` |
| `UY-07` | `STRONG_FAMILY_WATCH` | 1.45 | `UY` | `KANUN` | TÜRK BORÇLAR KANUNU | `strong_family_regression` |
| `UY-08` | `STRONG_FAMILY_WATCH` | 6.80 | `UY` | `UY` | YENİ YÜZYIL ÜNİVERSİTESİ ÇİFT ANADAL VE YANDAL YÖNETMELİĞİ | `rubric_only_not_source_error` |

## Acceptance Check

- Every targeted failed/watch row has a non-empty `fix_type`.
- YONETMELIK and MULGA dominant failures are separated above.
- The audit is generated from scored/trace artifacts only; no QID-specific runtime patch is introduced.
