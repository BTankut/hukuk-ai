# Phase 18 Recovery A1.8-B YONETMELIK Smoke

## Scope

- Runtime: temporary candidate `http://127.0.0.1:8018/v1`
- Collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Model: `hukuk-ai-poc` via `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
- Run: `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_yon_smoke_v2`
- Live `8000`: unchanged

## Systemic Changes

- Title-inferred `... Kanunu` records no longer stay in `kky/uy/yonetmelik` routing families when the title itself is a primary-law title.
- Natural-language regulation requests now recognize `hangi yönetmeliği`, `yönetmelik detayı`, `yönetmeliği de`, and `ana yönetmelik` as explicit YONETMELIK signals.
- `kurul` no longer matches verb forms such as `kurulurken`; KKY agency detection now requires more specific board/institution forms.
- Central higher-education regulation language prefers the national YONETMELIK family while keeping UY as controlled supporting context.

No QID-specific condition was added.

## Result

| Metric | A1.7 full candidate YON rows | A1.8-B YON smoke |
|---|---:|---:|
| pass_proxy | 3/10 | 7/10 |
| raw_score_proxy | 53.27 | 66.32 |
| wrong_family | 6 | 2 |
| wrong_document | 3 | 2 |
| hallucinated_identifier | 6 | 3 |
| contract_valid | 10/10 | 10/10 |

## Remaining YON Failures

| qid | score | claimed_family | selected_document | remaining issue |
|---|---:|---|---|---|
| `YON-03` | 1.45 | `UY` | `TRAKYA ÜNİVERSİTESİ RİSK YÖNETİMİ VE KURUMSAL SÜRDÜRÜLEBİLİRLİK UYGULAMA VE ARAŞTIRMA MERKEZİ YÖNETMELİĞİ` | wrong family/document |
| `YON-06` | 3.25 | `YONETMELIK` | `CEZA İNFAZ KURUMLARI VE TUTUKEVLERİ PERSONELİ EĞİTİM MERKEZLERİ KURULUŞ, GÖREV VE ÇALIŞMA YÖNETMELİĞİ` | wrong document |
| `YON-08` | 5.45 | `UY` | `IŞIK ÜNİVERSİTESİ YATAY GEÇİŞ, ÇİFT ANADAL, YAN DAL VE KREDİ TRANSFERİ YÖNETMELİĞİ` | local UY promoted over central YONETMELIK |

## Acceptance

- Required target `YONETMELIK pass >= 6/10`: PASS (`7/10`)
- Wrong-family count materially reduced: PASS (`6 -> 2`)
- Supporting law/source promotion reduced: PASS (`YON-05`, `YON-10` recovered)
