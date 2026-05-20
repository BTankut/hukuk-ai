# FAZ 2B Claim Binding v2 Delta

Tarih: 2026-03-23

Referans:
- [faz2b-guardrail-regression-diff-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-guardrail-regression-diff-2026-03-23.md)
- [faz2b-guardrail-regression-diff-rc-c-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-guardrail-regression-diff-rc-c-2026-03-23.md)
- [faz2b-rc-c-family-eval-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-rc-c-family-eval-2026-03-23.md)

## Delta

- claim-binding answer leak
  - `RC-C`: `0`

- `excerpt_match_false_negative`
  - `RC-B`: `68`
  - `RC-C`: `2`

- `false_refusal_after_guardrail`
  - `RC-B`: `6`
  - `RC-C`: `30`

- `true_guardrail_block`
  - `RC-B`: `23`
  - `RC-C`: `47`

## Yorum

Claim binding v2 dar kapsamlı desteksiz cevap sızıntısını kapattı ve excerpt eşleştirme hatasını dramatik biçimde azalttı. Ancak aynı anda yanlış refusal / over-tightening etkisi büyüdü.

Kaynak temelli okuma:
- `excerpt_match_false_negative` problemi büyük ölçüde kapandı.
- Buna karşılık kalite-preserving hedefi kapanmadı; regresyon ağırlığı `false_refusal_after_guardrail` ve geniş `true_guardrail_block` kümesine kaydı.

Bu yüzden `WP-4` blocker'ı doğrudan unsupported answer leak değil, guardrail entegrasyonunun kaliteyi koruyamamasıdır.
