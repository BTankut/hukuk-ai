# FAZ 3 Selective Claim-Binding v3 Spec

Tarih: 2026-03-23

Referans:
- [FAZ3-ROTASYON-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-VE-REQUALIFICATION-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ3-ROTASYON-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-VE-REQUALIFICATION-TALIMATI-2026-03-23.md)
- [faz3-guardrail-blocker-pack-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz3-guardrail-blocker-pack-2026-03-23.md)

## Amaç

Claim-binding, cevap-geneli block mekanizmasi olmaktan cikarilacak ve yalniz claim-unit bazinda trimming katmani olarak calisacaktir.

## Sabitler

- retrieval degismeyecek
- reranker degismeyecek
- prompt degismeyecek
- whitelist / temporal / law-scope hard-fail yuzeyi degismeyecek
- yeni LLM cagrisi acilmayacak

## Claim-Unit Cikarma Kurali

1. Markdown list item varsa her item bir claim-unit'tir.
2. Liste yoksa cevap metni yalniz `.`, `;`, `?`, `!` ayiraclari ile bolunur.
3. Baslik satirlari ve bos satirlar claim-unit sayilmaz.
4. Claim-unit sirasi korunur.

## Support Predicate

Bir claim-unit ancak su kosullar birlikte saglaniyorsa `supported` sayilir:

1. Claim-unit icinde en az bir canonical citation vardir.
2. Bu canonical citation whitelist icindedir.
3. Bu canonical citation temporal ve law-scope hard-fail yuzeyini gecer.
4. Claim-unit citation kumesi ile allowed evidence kumesi arasinda en az bir `source_id` kesisimi vardir.

Ek kural:

- tam citation-set eslesmesi aranmaz
- en az bir gecerli whitelisted canonical citation kesisimi yeterlidir
- claim-unit baska claim-unit'ten citation odunc alamaz
- fallback tek-kaynak odunc mekanizmasi kullanilmaz

## Trimming Kurali

1. Supported olmayan claim-unit dusurulur.
2. Supported claim-unit korunur.
3. Bir claim-unit dustu diye tum cevap bloklanmaz.
4. Dis API cevabina yalniz kept claim-unit metni tasinir.
5. Dusen claim-unit metni dis API cevabinda gorunmez.

## Global Block Yasagi

Claim-binding sebebiyle global `refusal` yalniz tek durumda verilir:

- trimming sonrasinda sifir supported claim-unit kalmasi

Bunun disinda claim-binding tek basina tum cevabi bloklayamaz.

## Beklenen Etki

- `false_refusal_after_guardrail` ana dusus alani burasidir
- `true_guardrail_block` icindeki gereksiz refusal ve answer-mode source tail'i burada toparlanir
- acceptance leak cizgisi bozulmaz
