# FAZ 2B Claim Binding v2 Spec

Tarih: 2026-03-23

## Amaç

Dar ve yüksek güvenli soru tiplerinde unsupported cümleleri düşürmek; yeni metin üretmeden `answer/partial/refusal` kararını deterministic hale getirmek.

## Aktivasyon Kuralı

Claim binding yalnız aşağıdaki koşullarda açılır:

- `single_article`
  - tek açık kanun
  - tek açık madde
  - comparison / istisna sinyali yok
- `definition`
  - `nedir`
  - `tanımı nedir`
  - `ne demektir`
- `elements`
  - `şartları nelerdir`
  - `unsurları nelerdir`
  - `hangi hallerde`
- `procedure`
  - tek açık kanun
  - tek açık madde
  - tek usul eylemi sinyali

## Claim Unit Kuralları

- en fazla `3` cümle
- yalnız sentence-boundary split
- her korunmuş cümle:
  - `source_id`
  - `source_excerpt`
  ile bağlanır

## Davranış

- destekli claim unit’ler korunur
- desteksiz claim unit’ler düşürülür
- hiç destekli claim kalmazsa dış mod `refusal`
- bazı claim’ler kalırsa dış mod `partial`
- tüm claim’ler kalırsa dış mod `answer`
- yeni LLM çağrısı açılmaz

## Kod Yüzeyi

- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)
  - `_split_claim_sentences`
  - `_is_claim_binding_active`
  - `apply_narrow_claim_binding`

## Doğrulama

- `api-gateway/.venv/bin/pytest api-gateway/tests/test_faz2a_hardening.py api-gateway/tests/test_chat_router.py -q`
