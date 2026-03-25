# FAZ14 RC-L Build Contract

Tarih: 2026-03-25

## Tanım

`RC-L = RC-J frozen manifest + localized authoritative output repair`

## Tek Yetkili Build Zinciri

- `RC-J freeze -> RC-L build`

## Allowed Runtime Diff Surface

- `api-gateway/src/routers/chat.py`

## Allowed Logic Surface

- `final_mode_mapping` projection parity
- `blocked_reason_set` projection parity
- `response_envelope` projection parity
- `serialized_output_hash` yalnız yukarıdaki zincirin doğal son yüzeyi olarak değişebilir

## Yasak

- request canonicalization değişikliği yok
- middleware ordering değişikliği yok
- generation contract değişikliği yok
- preprojection değişikliği yok
- cited projection değişikliği yok
- citation set projection değişikliği yok
- final answer payload / answer body / citation body / refusal body değişikliği yok
- retrieval / prompt / claim binding / source election / release-controls değişikliği yok

## Kabul

- `RC-L manifest` yazılacak
- `answer_path_delta = []`
- build diff yüzeyi yalnız bu contract içinde kalacak
