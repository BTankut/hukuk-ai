# FAZ 2A Ek Sertleştirme — Temporal Validity Policy

Tarih: 2026-03-23

## Amaç

Yürürlük bilgisi runtime karar zincirine bağlanır. Current-date soruda yürürlük dışı primary source ile dış cevap verilmez; açık tarihli soruda tarihsel kaynak yalnız o tarihle uyumluysa `historical` olarak taşınır.

## Target Date Kuralı

- soruda açık tarih varsa o tarih kullanılır
- açık tarih yoksa sistem günü kullanılır

Owner helper:

- `api-gateway/src/faz2a_hardening.py::resolve_target_date`

## Validity Değerleri

- `active`
- `historical`
- `repealed`
- `unknown`

## Runtime Kuralları

- `mulga=true` ise source `repealed` sayılır
- `target_date < yururluk_baslangic` veya `target_date > yururluk_bitis` ise sonuç `blocked`
- açık tarihli soru, kaynağın geçmişte geçerli olduğu pencereye düşüyorsa `source_validity=historical`
- metadata bulunuyor ama current-date ile uyumsuzsa `final_reason=temporal_mismatch`
- metadata hiç bulunamayan source id için validity bilgisi trace'te `unknown` kalır; sonraki serialization gate dış teslimi yine fail-closed tutar

## Runtime Bağlantı Noktası

- `api-gateway/src/faz2a_hardening.py::apply_temporal_validity_policy`
- çağrı sırası: structured answer contract ve law-scope validation sonrası, serialization whitelist gate öncesi

## Doğrulama

2026-03-23 doğrulaması:

- `api-gateway/tests/test_faz2a_hardening.py::test_harden_answer_blocks_temporal_mismatch_for_current_question`
- `api-gateway/tests/test_faz2a_hardening.py::test_harden_answer_allows_historical_source_when_target_date_matches`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_faz2a_hardening.py api-gateway/tests/test_chat_router.py -q`

Tamamı geçti.
