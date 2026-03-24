# FAZ 6 Attribution Trace Schema v1

Tarih: 2026-03-23

Referans:
- [FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md)

## Amac

Citation/source-attribution kaybini stage-level izlenebilir kilmak.

## Zorunlu Alanlar

Asagidaki alanlar isim degistirmeden zorunludur:

| Alan | Tip | Aciklama |
| --- | --- | --- |
| `question_id` | string | Eval icindeki sabit soru kimligi |
| `family` | string | `faz1-50`, `v2-95`, `v3-170` |
| `question_text` | string | Ham soru metni |
| `gold_sources` | list[string] | Eval gold source listesi |
| `retrieved_source_ids` | list[string] | Retrieval ciktisinda gorulen source id listesi |
| `assembled_source_ids` | list[string] | Assembly sonrasinda kalan source id listesi |
| `assembled_source_order` | list[string] | Assembly sirasi |
| `assembled_primary_candidate` | string or null | Assembly asamasindaki birinci aday |
| `model_answer_text` | string | Modelin ham cevap metni |
| `model_emitted_sources` | list[string] | Modelin gorunur olarak yaydigi source id listesi |
| `kept_claims` | list[string] | Guardrail sonrasi tutulan claim listesi |
| `kept_claim_support_modes` | list[string] | Her kept claim icin support mode |
| `kept_claim_source_ids` | list[list[string]] | Her kept claim icin destek source id listesi |
| `final_answer_text` | string | Final kullaniciya giden metin |
| `final_citations` | list[string] | Final citation listesi |
| `final_mode` | string | `answer`, `partial`, `refusal`, `blocked` |
| `block_reasons` | list[string] | Final mod veya verifier kaynakli block reason listesi |
| `canonical_norm_keys` | list[string] | Canonical normalization key listesi |
| `normalization_map` | object | Source id -> canonical key/alias haritasi |
| `trace_complete` | boolean | Her replay kaydinda `true` olmak zorunda |

## Closure Kurallari

- Alan adlari degistirilmeyecek
- Eksik alanli kayit basarisiz sayilacak
- `trace_complete = true` olmayan kayit basarisiz sayilacak
- Summary veya taxonomy, trace tam kapanmadan resmi kabul almayacak

## FAZ 6 Sonucu

FAZ 6 tracked replay ve blocker rerun ciktisinda:

- `trace_complete_rate = 100%`
- `schema_validation_pass_rate = 100%`

Bu nedenle trace schema v1 resmi olarak kapanmistir.
