# Phase 3 Retrieval Routing Final Summary

## 1. Commit SHA Listesi

- `39b057a` - `benchmark: add phase 3 retrieval forensics`
- `48cd54e` - `gateway: add source family routing prior`
- Commit 3 - hybrid retrieval, source selector hardening, verification gate and final rerun

## 2. Değişen Dosyalar

- `api-gateway/src/routers/chat.py`
- `api-gateway/src/source_family_resolver.py`
- `api-gateway/src/answer_contract_v2.py`
- `api-gateway/src/faz2a_hardening.py`
- `api-gateway/src/rag/orchestrator.py`
- `api-gateway/tests/test_chat_router.py`
- `api-gateway/tests/test_answer_contract_v2.py`
- `reports/benchmark/phase_03_trace_forensics.md`
- `reports/benchmark/phase_03_failure_clusters.csv`
- `reports/benchmark/phase_03_retrieval_routing_final_summary.md`

## 3. Çalıştırılan Komutlar

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/source_family_resolver.py api-gateway/src/answer_contract_v2.py api-gateway/src/faz2a_hardening.py api-gateway/src/rag/orchestrator.py`
- `api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_answer_contract_v2.py api-gateway/tests/test_chat_router.py`
- `api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --questions configs/evaluation/hukuk_ai_100_public_questions.csv --out-dir reports/benchmark/runs/20260421T174105Z_phase3_retrieval_routing_final_v2 --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --max-tokens 1200 --top-k 20 --timeout 180 --retries 2 --sleep 0.2`
- `api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260421T174105Z_phase3_retrieval_routing_final_v2/candidate_answers.csv --out-dir reports/benchmark/runs/20260421T174105Z_phase3_retrieval_routing_final_v2`
- `api-gateway/.venv/bin/python scripts/benchmark/phase3_trace_forensics.py --run-dir reports/benchmark/runs/20260421T174105Z_phase3_retrieval_routing_final_v2 --out-md reports/benchmark/phase_03_trace_forensics.md --out-csv reports/benchmark/phase_03_failure_clusters.csv`
- `bash scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260421T174105Z_phase3_retrieval_routing_final_v2`

## 4. Test / Eval Sonuçları

- Unit tests: `170 passed, 1 warning`
- Green lane: `pass`
- Final run: `reports/benchmark/runs/20260421T174105Z_phase3_retrieval_routing_final_v2`
- Contract validity: `100/100`
- Contract completeness: `1.0`
- API/runtime errors: `0`
- Trace rows: `100`

## 5. Phase 2'ye Göre Metrik Farkları

- Raw score: `657.50 -> 658.94` (`+1.44`)
- Average score: `6.58 -> 6.59`
- Pass proxy: `55 -> 56`
- Wrong family: `36 -> 34`
- Unsupported confident claim: `62 -> 49`
- Hallucinated identifier: `44 -> 46`
- Wrong document: `22 -> 23`
- Missing required content signal: `97 -> 98`
- Partial grounding only: `97 -> 98`

Acceptance sonucu: kısmi iyileşme var, ancak Phase 3 hedefleri tam kapanmadı. Özellikle `hallucinated_identifier`, `wrong_document`, `missing_required_content_signal` ve `partial_grounding_only` hedef dışı kaldı.

## 6. Weak Family Impact Özeti

- `CB_GENELGE`: average `3.06 -> 4.53`, pass `0 -> 1`
- `CB_YONETMELIK`: average `3.16 -> 3.65`
- `KHK`: average `9.04 -> 8.93`, pass `5 -> 6`
- `UY`: average `7.76 -> 7.79`, pass `6 -> 7`
- `TUZUK`: average `6.75 -> 6.89`
- `TEBLIGLER`: average `8.78 -> 8.05`, pass `8 -> 6`
- `CB_KARAR`: average `4.03 -> 3.95`, pass `1 -> 0`

En büyük pozitif etki `CB_GENELGE` ve `UY` tarafında görüldü. En belirgin negatif basınç `TEBLIGLER` ve `CB_KARAR` tarafında kaldı.

## 7. Retrieval Trace Forensics Özeti

Final forensics dominant mekanizmaları:

- Right-document wrong-article/span: `36`
- Evidence insufficiency: `16`
- Generation overreach: `16`
- Wrong-family retrieval: `13`
- Right-family wrong-document: `12`
- Temporal miss: `5`

Bu dağılım, sadece family routing ile kapanmayacak bir sonraki katman ihtiyacını gösteriyor: article/span-aware evidence selection, title/issuer metadata enrichment ve verification-first answer synthesis.

## 8. Index Audit Özeti

- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Scanned rows: `349191`
- Family / identifier / article fields: complete
- Full title: `100.0%` missing
- Issuer: `100.0%` missing
- Official gazette date / effective start: `10.6%` missing

Somut corpus blokajı: `TEB-06` için gold kaynak olan `Ticaret Sicili Tebliği` metni final collection içinde `text like "%Ticaret Sicili Tebliği%"` sorgusunda bulunmadı. Bu nedenle ilgili soru mevcut corpus ile güvenilir biçimde kapanamaz.

## 9. Riskler / Bilinen Açıklar

- `TEB-06` coverage açığı kodla değil corpus/source acquisition ile çözülmeli.
- `CBKAR-06` için 2026 karar kaydı (`10868`) collection içinde var, ancak title metadata eksikliği ve dense retrieval sıralaması yüzünden dinamik olarak güvenilir seçilemiyor.
- `MULGA` ailesinde temporal miss devam ediyor; active/repealed state answer contract'a taşınıyor ama evidence selection hâlâ yeterince sert değil.
- Source-lock fallback bazı sorularda doğru sentez yerine chunk listeleme davranışına düşüyor; bu Phase 4 generation/verification konusu.
- Full title ve issuer eksikliği giderilmeden issuer-aware tie-breaker güvenilir kurulamaz.

## 10. Sonraki Faz Önerisi

Phase 4, fine-tuning değil, `Verification-first answer synthesis hardening` olmalı.

Öncelik sırası:

1. Canonical title/issuer enrichment ve affected collection reindex.
2. Article/span-aware evidence selector.
3. Current-year annual/source selection için metadata-first candidate path.
4. Source-title/source-identifier same-evidence verification gate.
5. Source-lock fallback yerine evidence-grounded synthesis fallback.
