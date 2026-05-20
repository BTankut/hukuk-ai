# FAZ 4 Primary Source Anchor v1 Spec

Tarih: 2026-03-23

Referans:
- [FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md)
- [faz4-citation-family-failure-pack-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz4-citation-family-failure-pack-2026-03-23.md)

## Problem

`wrong_primary_source_with_supported_answer` sinifi, destekli cevap uretildigi halde final `primary_source_id` seciminin deterministic olmadigini gosteriyor.

## Amac

`primary_source_id`, modelin ham cite sirasina gore degil, kept claim destek yogunluguna gore deterministic secilecektir.

## Secim Kurali

1. Her kept claim unit'i destekleyen `source_id` icin `supported_claim_count` hesaplanir.
2. En yuksek `supported_claim_count` degerine sahip adaylar tutulur.
3. Esitlik varsa `single_law_high_conf` + tek article parse sinyaline tam uyan kaynak once gelir.
4. Esitlik devam ederse daha dusuk `retrieval_rank` once gelir.
5. Esitlik devam ederse `source_id` alfabetik kucuk olani secilir.

## Davranis

1. `primary_source_id`, final emitted citation listesinde birinci sirada yer alacaktir.
2. `primary_source_id` whitelist disi veya gecersiz ise `answer` ya da `partial` teslim edilmeyecektir.
3. `primary_source_id` olmadan `answer` ya da `partial` kurulmayacaktir.

## Beklenen Etki

- `wrong_primary_source_with_supported_answer` azalacak
- `correct_source` metri gi aile seviyesinde geriye gitmeyecek
- emitted citation listesi ile primary anchor ayni support yuzeyine baglanacak
