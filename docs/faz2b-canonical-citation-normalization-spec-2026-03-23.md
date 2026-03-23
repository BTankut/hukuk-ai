# FAZ 2B Canonical Citation Normalization Spec

Tarih: 2026-03-23

## Amaç

Whitelist gate öncesinde model citation yüzeyini deterministic biçimde canonical `source_id`'ye taşımak.

## Uygulama Sınırı

- yalnız `api-gateway/src/faz2a_hardening.py`
- yeni retrieval veya ikinci LLM çağrısı yok

## Eşleştirme Sırası

1. exact canonical `source_id` match
2. exact `source_hash` match
3. exact `(kanun_no|law_short_name, madde_no, fikra_no)` tuple match

Fuzzy eşleştirme yoktur.

## Davranış

- canonical eşleşme bulunduğunda citation whitelist içindeki canonical `source_id` ile taşınır
- eşleşme bulunmazsa mevcut citation korunur ve whitelist gate karar verir
- answer text yeniden üretilmez

## Kod Yüzeyi

- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)
  - `_extract_exact_source_tuple`
  - `_extract_citation_tuple`
  - `_resolve_canonical_citation`
  - `extract_model_cited_source_ids`

## Doğrulama

- `python3 -m py_compile api-gateway/src/faz2a_hardening.py`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_faz2a_hardening.py tests/test_faz2b_guardrail_regression_diff.py -q`
