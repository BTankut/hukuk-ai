# FAZ 4 Citation Fidelity Controller v1 Spec

Tarih: 2026-03-23

Referans:
- [FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md)
- [faz4-citation-family-failure-pack-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz4-citation-family-failure-pack-2026-03-23.md)

## Problem

FAZ 4 quality-loss pack icinde baskin failure sinifi `citation_under_emission` oldu. `RC-D`, destekli cevap urettigi halde final emitted citation listesi kept claim support yuzeyini eksik yansitiyor.

## Amac

Final emitted citation listesi, modelin ham cite ciktisindan degil, final kept-claim destek yuzeyinden uretilecek.

## Sabitler

- canonical citation normalization degismeyecek
- whitelist gate degismeyecek
- temporal gate degismeyecek
- law-scope gate v2 degismeyecek
- selective claim-binding v3 degismeyecek
- retrieval, reranker, model, adapter, prompt, parser degismeyecek

## Davranis

1. `final_mode` `answer` veya `partial` ise emitted citation listesi kept claim projection yuzeyinden uretilecektir.
2. `primary_source_id`, gecerli ise emitted citation listesinde zorunlu olarak yer alacaktir.
3. Her kept claim unit en az bir emitted supporting `source_id` ile baglanacaktir.
4. Supported olmayan hicbir `source_id` emitted citation listesine girmeyecektir.
5. Ayni kept claim unit icin lexical excerpt yeniden eslestirilmeyecektir.
6. Emitted citation listesi dedupe edilebilir; ancak `primary_source_id` veya bir claim unit'in tek supporting source'u dusurulemez.

## Siralama

Final emitted citation listesi su sirayla kurulacaktir:

1. `primary_source_id`
2. kalan kaynaklar `supported_claim_count desc`
3. esitlikte `retrieval_rank asc`
4. esitlikte `source_id asc`

## Beklenen Etki

- `citation_under_emission` sinifi dogrudan azalacak
- emitted citation listesi kept claim projection ile birebir hizalanacak
- whitelist disi emisyon eklenmeyecek
