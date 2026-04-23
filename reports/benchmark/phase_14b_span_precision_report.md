# Phase 14B Span Precision Report

Tarih: 2026-04-23

## Commitler

- `0deb5e6` - Phase 14B harden article span selector trace
- `7e509f0` - Phase 14B preserve selector span order

## Degisen Dosyalar

- `api-gateway/src/routers/chat.py`
- `api-gateway/src/rag/orchestrator.py`
- `api-gateway/tests/test_chat_router.py`
- `api-gateway/tests/test_orchestrator_smoke.py`
- `scripts/benchmark/run_hukuk_ai_100.py` (`0deb5e6`)
- `scripts/benchmark/score_hukuk_ai_100.py` (`0deb5e6`)

## Calistirilan Testler

```bash
cd api-gateway
.venv/bin/python -m pytest tests/test_chat_router.py -k "focus_chunks or article_span_selector or selected_document_only_bundle" -q
.venv/bin/python -m pytest tests/test_orchestrator_smoke.py -k "source_lock or priority_chunks" -q
python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/orchestrator.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py
```

Sonuc:

- `tests/test_chat_router.py`: `21 passed`
- `tests/test_orchestrator_smoke.py`: `22 passed`
- `py_compile`: temiz

## Smoke Kosulari

Tekil KKY-09 dogrulama:

```bash
python3 scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8000/v1 --out-dir reports/benchmark/runs/20260423T194549Z_phase14b_kky09_scope_probe_r5 --qids KKY-09 --retries 0 --timeout 300
python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260423T194549Z_phase14b_kky09_scope_probe_r5/candidate_answers.csv --out-dir reports/benchmark/runs/20260423T194549Z_phase14b_kky09_scope_probe_r5/scored
```

Phase 14B smoke:

```bash
python3 scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8000/v1 --out-dir reports/benchmark/runs/20260423T194949Z_phase14b_smoke_span_precision_r5 --qids CBKAR-08 CBKAR-04 CBKAR-06 KHK-03 KKY-02 KKY-06 KKY-09 YON-07 --retries 0 --timeout 360
python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260423T194949Z_phase14b_smoke_span_precision_r5/candidate_answers.csv --out-dir reports/benchmark/runs/20260423T194949Z_phase14b_smoke_span_precision_r5/scored
```

## Smoke Delta

| Metrik | Phase 14A r3 | Phase 14B r5 |
| --- | ---: | ---: |
| raw_score_proxy | 67.45 / 80 | 68.12 / 80 |
| average_score_0_10_proxy | 8.43 | 8.52 |
| pass_proxy | 7 / 8 | 7 / 8 |
| avg_family_match_score | 1.00 | 1.00 |
| avg_document_match_score | 0.75 | 0.75 |
| avg_article_match_score | 1.00 | 1.00 |
| selector_exact_article_hit_rate | 0.875 | 0.875 |
| selector_same_document_hit_rate | 1.00 | 1.00 |
| selected_article_equals_claimed_article_rate | 0.75 | 1.00 |
| hallucinated_source_count | 0 | 0 |
| unsupported_confident_answer_count | 0 | 0 |
| minimum_answer_facts_present_count | 8 | 7 |
| avg_required_fact_coverage_score | 0.917 | 0.905 |

## Satir Ozeti

| QID | Sonuc | Skor | Kaynak | Selected main span | Match type |
| --- | --- | ---: | --- | --- | --- |
| CBKAR-04 | PASS | 9.10 | CB_KARAR 767 m.2 | `767 m.2/f.0` | same_heading_or_section |
| CBKAR-06 | PASS | 9.32 | CB_KARAR 767 m.2 | `767 m.2/f.0` | same_heading_or_section |
| CBKAR-08 | FAIL | 6.80 | CB_KARAR 9903 m.0 | `9903 m.0/f.0` | title_only |
| KHK-03 | PASS | 7.25 | KHK 703 m.225 | `703 m.225/f.0` | temporal_clause |
| KKY-02 | PASS | 9.55 | KKY 38568 m.1 | `38568 m.1/f.0` | scope_or_applicability |
| KKY-06 | PASS | 8.22 | KKY 18985 m.12 | `18985 m.12/f.0` | same_heading_or_section |
| KKY-09 | PASS | 9.66 | KKY 32695 m.2 | `32695 m.2/f.0` | scope_or_applicability |
| YON-07 | PASS | 8.22 | YONETMELIK 20435 m.23 | `20435 m.23/f.0` | same_heading_or_section |

## CBKAR-08 Before / After

- Phase 14A r3: dogru family/document bandinda kaldi (`CB_KARAR`, `9903`) ama `m.0/title_only` uzerinden fail etti.
- Phase 14B r5: ayni sekilde dogru family/document bandi korundu (`CB_KARAR`, `9903`) ve hallucination/unsupported geri gelmedi.
- Kapanmayan nokta: corpus/runtime tarafinda `9903` icin anlamli hukum span'i halen gelmiyor; secilen span `9903 m.0/f.0` title-only. Bu nedenle CBKAR-08 artik routing degil, selected document icindeki canonical content/span completeness blocker'i olarak duruyor.

## Span Noise Suppression

- Yeni trace alanlari smoke CSV/trace cikisina yaziliyor: `selected_main_span_id`, `selected_main_article`, `selected_supporting_span_ids`, `main_span_match_type`, `supporting_span_match_types`, `selected_document_only_bundle`, `span_cluster_noise_suppressed`, `article_precision_guard_triggered`.
- `KKY-09` icin selector ana span'i `32695 m.2/f.0` olarak secti ve source-lock fallback artik bu secimi koruyor; tekil probda `selected_article_equals_claimed_article_rate=1.0`, smoke icinde de tum satirlarda `selected_article_equals_claimed_article_rate=1.0`.
- Secili belge disi hard bundle sadece precise lock durumlarinda uygulanmaya devam ediyor; semantic/scope lock'larda source-lock fallback, selector siralamasini metadata uzerinden koruyor.

## Acik Blocker

- `CBKAR-08` icin `9903 m.0/f.0` disinda yeterli hukum span'i hala runtime candidate setine girmiyor veya secilebilir nitelikte degil.
- `missing_required_content_signal` ve `partial_grounding_only` smoke paketinde azalmadi; scorer halen 8/8 satirda bu iki failure class'i isaretliyor.
- `minimum_answer_facts_present_count` 8'den 7'ye dustu; bu nedenle 14B safety/selector gate gecse de substantive completeness gate tam kapanmadi.

## Full Rerun Karari

Full benchmark rerun icin guvenlik ve selector kosullari saglandi:

- `pass_proxy >= 7/8`
- `wrong_family = 0`
- `wrong_document <= 1` bandi korundu
- `selected_article_equals_claimed_article_rate >= 0.80`
- `hallucinated_source_count = 0`
- `unsupported_confident_answer_count = 0`

Ancak Phase 14B brief'teki tam full-rerun gate henuz acik sayilmamali. Gerekce: `CBKAR-08` meaningful span/completeness iyilesmesi almadi ve `missing_required_content_signal` / `partial_grounding_only` dusmedi. Siradaki is, `9903` belgesi icin canonical article/span materialization veya retrieval candidate completeness tarafini hedeflemeli.
