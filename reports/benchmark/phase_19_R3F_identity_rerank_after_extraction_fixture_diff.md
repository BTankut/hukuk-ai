# Phase 19 R3F Identity Rerank After-Extraction Fixture Diff

Purpose: verify that extracting `_rerank_chunks_by_source_identity(...)` from `chat.py` to `rag/source_identity.py` is behavior-preserving.

- baseline main run: `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity`
- baseline UY-07 run: `reports/benchmark/runs/20260426T_phase19_R3F_fixture_UY07_envparity`
- after-extraction run: `reports/benchmark/runs/20260426T_phase19_R3F_after_extraction_fixture_envparity`
- result: `8/8 PASS`, `drift_count=0`

Compared fields: pre-count, pre-top, first_changed, identity_rerank_input_source, post-top citation/family/title, document_identity_score, title/identifier match types, identity lock, rerank reason, selected document/article/canonical keys, selector reason, source-key v2 collision, binding collision, canonical binding.

| QID | Status | Changed Fields | Post Top | Score | Lock | Selected Document | Selected Article |
|---|---|---|---|---:|---|---|---|
| CBG-01 | `PASS` | - | `2024/7 m.0/f.0 / cb_genelge / Tasarruf Tedbirleri ile İlgili` | 198.0 | `strong` | `2024/7` | `0` |
| CBKAR-01 | `PASS` | - | `10395 m.0/f.0 / cb_karar / 2024-2026 YILLARINDA YAPILACAK HAYVANCILIK DESTEKLEMELERİNE İLİŞKİN KARARDA DEĞİŞİKLİK YAPILMASINA DAİR KARAR (KARAR SAYISI: 10395)` | 171.8683 | `strong` | `3351` | `2` |
| CBKAR-08 | `PASS` | - | `9903 geçici m.1/f.0 / cb_karar / Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903)` | 378.0 | `strong` | `9903` | `gecici-1` |
| MULGA-02 | `PASS` | - | `33899 m.4/f.0 / kky / DEVLET ARŞİV HİZMETLERİ HAKKINDA YÖNETMELİK` | 203.9132 | `strong` | `33899` | `32` |
| YON-01 | `PASS` | - | `20631 m.7/f.0 / kky / MALİ SUÇLARI ARAŞTIRMA KURULU BAŞKANLIĞI ELEKTRONİK TEBLİGAT SİSTEMİNE İLİŞKİN USUL VE ESASLAR HAKKINDA YÖNETMELİK` | 79.9235 | `weak` | `29033` | `1` |
| TEB-01 | `PASS` | - | `44999 m.0/f.0 / teblig / KAMU İHALE TEBLİĞİ (TEBLİĞ NO: 2026/1)` | 303.9385 | `strong` | `13354` | `79` |
| KANUN-01 | `PASS` | - | `7088 m.2/f.0 / cb_karar / GELİR İDARESİ BAŞKANLIĞI MERKEZ VE TAŞRA TEŞKİLATININ 657 SAYILI DEVLET MEMURLARI KANUNUNA TABİ PERSONELİNE FAZLA ÇALIŞMA ÜCRETİ ÖDENMESİNE İLİŞKİN EKLİ KARARIN YÜRÜRLÜĞE KONULMASI HAKKINDA KARAR (KARAR SAYISI: 7088)` | 71.9146 | `weak` | `4857` | `18` |
| UY-07 | `PASS` | - | `40291 m.27/f.0 / uy / İSTANBUL ATLAS ÜNİVERSİTESİ ÖN LİSANS VE LİSANS EĞİTİM-ÖĞRETİM VE SINAV YÖNETMELİĞİ` | 59.9253 | `weak` | `40291` | `27` |

Verdict: R3F fixture gate PASS. No selected-source, source-family, source-key collision, lock, score, or reason drift detected.
