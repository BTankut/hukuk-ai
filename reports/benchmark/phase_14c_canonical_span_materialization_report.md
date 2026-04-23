# Phase 14C Canonical Span Materialization Report

Tarih: 2026-04-23

## 1. Commit SHA Listesi
- `641849b` - Phase 14C audit 9903 canonical spans
- `6536eff` - Phase 14C gate canonical span materialization

## 2. Değişen Dosyalar
- `scripts/benchmark/phase14c_source_content_audit.py`
- `api-gateway/src/routers/chat.py`
- `api-gateway/src/answer_contract_v2.py`
- `api-gateway/tests/test_chat_router.py`
- `api-gateway/tests/test_answer_contract_v2.py`
- `scripts/benchmark/run_hukuk_ai_100.py`
- `scripts/benchmark/score_hukuk_ai_100.py`

## 3. Çalıştırılan Testler
- `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/src/answer_contract_v2.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py`
- `cd api-gateway && .venv/bin/python -m pytest tests/test_chat_router.py -k "canonical_span_materialization or insufficient_canonical_span_evidence or pre_generation_family_pool_reports_source_key_collision" -q`
- `cd api-gateway && .venv/bin/python -m pytest tests/test_chat_router.py -k "focus_chunks or article_span_selector or selected_document_only_bundle or completeness_synthesis or pre_generation_family_pool" -q`
- `cd api-gateway && .venv/bin/python -m pytest tests/test_answer_contract_v2.py -q`
- Phase 14C final smoke: `reports/benchmark/runs/20260423T210738Z_phase14c_smoke_span_materialization_r3`

## 4. 9903 Corpus Truth Audit
- `article_rows.jsonl` ve Milvus collection içinde `9903` için 4 row bulundu.
- `CB_KARAR 9903` tarafında yalnız `9903 m.0/f.0` var; body length `197`, alpha `0`, control count `159`, selectable body yok.
- Aynı numeric key altında gelen `m.1-3` satırları `TEBLIG` ailesine ait; başlık `GARANTİ BELGESİ SÜRELERİNİN UZATILMASINA İLİŞKİN TEBLİĞ`.
- Sonuç: `CB_KARAR 9903` için corpus içinde gerçek hüküm/body span materialized değil.

Audit artifactleri:
- `reports/benchmark/phase_14c_9903_corpus_truth_table.csv`
- `reports/benchmark/phase_14c_9903_source_content_audit.json`
- `reports/benchmark/phase_14c_9903_source_content_audit.md`
- `reports/benchmark/phase_14c_9903_source_key_collision_report.csv`

## 5. Source-Key Collision Raporu
- Runtime artık pre-family-filter candidate set üzerinde source-key collision profili çıkarıyor.
- `9903` için collision: `cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903 | teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig ...`
- Collision bilgisi `source_key_collision_detected`, `source_key_collision_keys`, `source_key_collision_pair` alanlarıyla trace ve benchmark CSV’ye taşındı.

## 6. Canonical Span Materialization Sonucu
- Runtime artık seçilen belgedeki body kalitesini ölçüyor: length, printable ratio, alpha count, control count.
- `m.0` veya body kalitesi yetersiz span artık `title_only`/materialization blocker olarak sınıflanıyor.
- Düşük oranlı PDF control karakterleri olan ama okunabilir body metinleri yanlışlıkla elenmesin diye control-ratio toleransı eklendi.
- `answer_contract_v2`, `insufficient_canonical_span_evidence=True` gördüğünde cevabı `insufficient_grounding/not_grounded` sınıfına indiriyor ve confident unsupported answer üretmiyor.

Yeni alanlar:
- `canonical_span_materialized`
- `canonical_span_materialization_reason`
- `title_only_fallback_used`
- `body_text_available`
- `body_text_length`
- `source_key_collision_detected`
- `corpus_materialization_required`
- `candidate_completeness_score`
- `selected_document_has_body_span`
- `selected_document_has_non_title_span`
- `title_only_answer_degraded`
- `insufficient_canonical_span_evidence`

## 7. CBKAR-08 Before / After
| Metrik | Phase 14B | Phase 14C final |
|---|---:|---:|
| selected span | `9903 m.0/f.0` | `9903 m.0/f.0` |
| main span match | `title_only` | `title_only` |
| source-key collision | n/a | `True` |
| canonical span materialized | n/a | `False` |
| corpus materialization required | n/a | `True` |
| candidate completeness score | n/a | `0.2` |
| completeness degrade reason | `complete_enough` | `insufficient_canonical_span_evidence` |
| unsupported confident answer | `False` | `False` |

Sonuç: CBKAR-08 doğru cevaplanmadı; çünkü corpus içinde gerçek `CB_KARAR 9903` hüküm span’i yok. Ancak artık bu durum doğru sınıfa düşüyor ve title-only span ile confident hukuki sonuç üretilmiyor.

## 8. Smoke Delta
Final smoke run: `reports/benchmark/runs/20260423T210738Z_phase14c_smoke_span_materialization_r3`

| Metrik | Phase 14B | Phase 14C final |
|---|---:|---:|
| raw score | `68.12 / 80` | `68.12 / 80` |
| average score | `8.52` | `8.52` |
| pass_proxy | `7/8` | `7/8` |
| hallucinated_source_count | `0` | `0` |
| unsupported_confident_answer_count | `0` | `0` |
| selected_article_equals_claimed_article_rate | `1.00` | `1.00` |
| canonical_span_materialized_count | n/a | `7/8` |
| corpus_materialization_required_count | n/a | `1/8` |
| insufficient_canonical_span_evidence_count | n/a | `1/8` |
| minimum_answer_facts_present_count | `7/8` | `6/8` |

QID özeti:
- `CBKAR-08`: Fail, `source_key_collision_without_family_body_span`, corpus blocker.
- `CBKAR-04`: Pass, `767 m.2/f.0` body valid, canonical span materialized.
- `CBKAR-06`: Pass, `767 m.2/f.0` body valid, canonical span materialized; completeness sadece `document_selection_reason` slotunda eksik.
- `KHK-03`, `KKY-02`, `KKY-06`, `KKY-09`, `YON-07`: Pass, non-title body span materialized.

## 9. Title-Only / Candidate Completeness Analizi
- `CBKAR-08` artık `title_only_answer_degraded=True`, `insufficient_canonical_span_evidence=True`.
- `CBKAR-04/06` ilk denemede fazla sert body-quality eşiğiyle yanlış degrade olmuştu; control-ratio toleransı sonrası readable body olarak kabul edildi.
- Final smoke’ta sadece `CBKAR-08` corpus/materialization blocker olarak kaldı.
- `missing_required_content_signal` ve `partial_grounding_only` deterministic scorer seviyesinde hâlâ tüm smoke satırlarında görünüyor; fakat root cause artık ayrıştı: yalnız `CBKAR-08` canonical body yokluğundan, diğerleri scorer/rubric completeness sinyallerinden etkileniyor.

## 10. Full Rerun Hazır mı?
Full benchmark artık diagnostik rerun olarak açılabilir; çünkü Phase 14C gate şartları sağlandı:
- `9903` truth netleşti.
- Title-only fallback nedeni trace’e taşındı.
- Gerçek span yoksa `corpus_materialization_required=True` ile güvenli sınıflama yapılıyor.
- Smoke’ta hallucination ve unsupported confident regresyonu yok.

Product acceptance açısından `CB_KARAR 9903` gerçek body materialization tamamlanmadan bu satır hukuki başarı kabul edilmemeli.

## 11. Kalan Riskler
- `CB_KARAR 9903` için resmi PDF/HTML’den gerçek body span çıkarılıp canonical corpus’a alınmalı.
- Source-key alanı numeric-only kaldığı sürece farklı ailelerde `9903` gibi collision üretme riski var; kalıcı çözüm family-aware canonical source key.
- Score summary’de `missing_required_content_signal` ve `partial_grounding_only` hâlâ çok geniş sinyal veriyor; Phase 14 sonrası metric/rubric kalibrasyonu gerekli.
