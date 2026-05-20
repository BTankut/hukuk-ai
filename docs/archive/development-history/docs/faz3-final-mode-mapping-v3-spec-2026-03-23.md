# FAZ 3 Final-Mode Mapping v3 Spec

Tarih: 2026-03-23

Referans:
- [FAZ3-ROTASYON-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-VE-REQUALIFICATION-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ3-ROTASYON-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-VE-REQUALIFICATION-TALIMATI-2026-03-23.md)
- [faz3-selective-claim-binding-v3-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz3-selective-claim-binding-v3-spec-2026-03-23.md)

## Amaç

Guardrail cikisini deterministik hale getirmek ve claim-binding kaynakli asiri fail-closed davranisi kaldirmak.

## Islem Sirasi

Su sira degismeyecek:

1. schema validation
2. canonical citation normalization
3. citation whitelist gate
4. temporal validity gate
5. law-scope gate v2
6. selective claim-binding v3
7. final-mode mapping v3

## Mode Mapping Kurali

1. Hard-fail tetiklendiyse `final_mode = refusal`
2. Hard-fail yoksa ve kept claim-unit sayisi `0` ise `final_mode = refusal`
3. Hard-fail yoksa, kept claim-unit sayisi `>= 1` ve dropped claim-unit sayisi `0` ise `final_mode = answer`
4. Hard-fail yoksa, kept claim-unit sayisi `>= 1` ve dropped claim-unit sayisi `>= 1` ise `final_mode = partial`

## Output Kurali

1. `answer` ve `partial` modlarinda yalniz kept claim-unit metni tasinir.
2. Citation listesi yalniz kept claim-unit'lerden uretilir.
3. Citation listesi duplicate-free olur ve ilk gorunum sirasi korunur.
4. `partial` modunda dusen claim-unit'ler serbest metinle telafi edilmez.
5. `refusal` modunda answer text bos olur.

## Sabitler

- internal `blocked` dis API'ye serbest mod olarak sizmayacak
- external mode kumesi yalniz `answer`, `partial`, `refusal`
- trace/schema yuzeyi semantik olarak degismeyecek

## Beklenen Etki

- block yerine `partial` davranisinin kontrollu acilmasi
- kept claim-unit varsa gereksiz global refusal'in kalkmasi
- answer/partial/refusal seciminin tek girdide ayni sonucu uretmesi
