# Hukuk-AI — Phase 18 Recovery A1.9 Controlled Live Cutover Brief

## Karar

A1.8 candidate gate **PASS** aldı. Bu nedenle artık yeni family/document remediation yapılmayacak.

Sıradaki doğru iş:

1. A1.8 candidate durumunu temiz commit/push ile dondurmak
2. live `8000` cutover öncesi provenance snapshot almak
3. kontrollü live collection binding değişimi yapmak
4. live `8000` üzerinde 20-QID smoke koşmak
5. live `8000` üzerinde full 100 benchmark confirmation koşmak
6. candidate `8018` ile live `8000` sonuçlarını karşılaştırmak
7. başarılıysa yeni stable recovery baseline ilan etmek
8. başarısızsa rollback yapmak

Fine-tuning hâlâ kapalıdır. Productization hâlâ kapalıdır.

---

## 1. A1.8 Sonucu

A1.8 after-MULGA-fix candidate run gate’i geçti.

### Runtime

```text
api_url = http://127.0.0.1:8018/v1
milvus_collection = mevzuat_faz1_shadow_20260418_compat1024
milvus_entity_count = 349191
vector_dimension = 1024
model = hukuk-ai-poc
dgx_model_env = /models/merged_model_fabric_stage_20260321
guardrails_enabled = false
presidio_enabled = false
live_8000_untouched = true
```

### Gate sonucu

| Metric | A1.7 | A1.8 after MULGA fix | Target | Status |
|---|---:|---:|---:|---|
| raw_score_proxy | 729.10 | 766.48 | >=735 | PASS |
| pass_proxy | 71 | 80 | >=73 | PASS |
| wrong_family | 17 | 11 | <=15 | PASS |
| wrong_document | 17 | 12 | <=15 | PASS |
| hallucinated_identifier | 24 | 16 | <=23 | PASS |
| unsupported_confident_claim | 0 | 0 | <=8 | PASS |
| contract_valid | 100/100 | 100/100 | 100/100 | PASS |
| green_lane | pass | pass | PASS | PASS |
| corpus_materialization_required_count | 1 | 2 | <=6 | PASS |
| canonical_span_materialized_count | 99 | 98 | >=90 | PASS |

### Watch metrics

| Watch | Result | Status |
|---|---:|---|
| YONETMELIK pass >= 6/10 | 6/10 | PASS |
| MULGA pass >= 3/5 | 3/5 | PASS |
| strong-family regressions absent | yes | PASS |
| repealed_as_active_count | 0 | PASS |
| source_key_v2_collision_detected_count | 0 | PASS |
| binding_source_key_collision_detected_count | 0 | PASS |

Bu sonuç controlled cutover değerlendirmesi için yeterlidir.

---

## 2. Zorunlu Ön Koşul: Clean Commit State

A1.8 candidate report provenance içinde `dirty_worktree=True` görünüyor.

Live cutover öncesi:

- working tree temizlenmeli
- tüm A1.8 değişiklikleri commit edilmeli
- push yapılmalı
- cutover commit SHA net olmalı
- yeni cutover run’larında `dirty_worktree=False` hedeflenmeli

## Yapılacaklar

```bash
git status
git diff --stat
git add <all intended A1.8 files and reports>
git commit -m "benchmark: phase 18 recovery A1.8 pass candidate gate"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

Eğer bilinçli olarak untracked/local artifact bırakılacaksa bunlar `.gitignore` ile güvenceye alınmalı.

---

## 3. Controlled Live Cutover Plan

## 3.1 Pre-Cutover Live Snapshot

Live `8000` değiştirilmeden önce snapshot alınmalı:

```text
reports/benchmark/phase_18_recovery_A1_9_live_precutover_snapshot.md
reports/benchmark/phase_18_recovery_A1_9_live_precutover_runtime_provenance.json
```

Snapshot şunları içermeli:

- active live collection
- entity count
- git SHA
- dirty worktree
- DGX model
- embedding endpoint
- source catalog hash
- source supplement hash
- guardrails / presidio flags
- current live health response
- rollback collection name

Expected current live:

```text
MILVUS_COLLECTION=mevzuat_e5_shadow
entity_count=12923
```

---

## 3.2 Live Collection Binding Change

Live binding şu collection’a geçirilmelidir:

```text
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
```

Bu değişiklik tek ve izole commit olmalı.

### Commit

```bash
git add <runtime env/config files>
git commit -m "ops: switch benchmark serving collection to full mevzuat corpus"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

Not: Değişiklik config/env üzerinden yapılmalı; runtime logic değiştirilmemeli.

---

## 3.3 Live Gateway Restart

Live `8000` restart sonrası health ve provenance doğrulanmalı.

Health/provenance şunları göstermeli:

```text
api_url = http://127.0.0.1:8000/v1
milvus_collection = mevzuat_faz1_shadow_20260418_compat1024
milvus_entity_count = 349191
vector_dimension = 1024
dgx_model_env = /models/merged_model_fabric_stage_20260321
```

Eğer provenance yanlışsa benchmark koşma; önce config düzelt.

---

# 4. Live 20-QID Smoke Confirmation

## Amaç

Live `8000` cutover sonrası candidate `8018` ile aynı davranışa yakın mı kontrol etmek.

## Smoke QID seti

A1.8 recovery ve cutover risklerini kapsayan set:

```text
CBG-01 CBG-02 CBG-03 CBG-04
MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05
CBKAR-01 CBKAR-02 CBKAR-08
YON-01 YON-02 YON-03
KANUN-01 KANUN-06 KANUN-15
TEB-01 TEB-02
```

## Komut

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py   --api-url http://127.0.0.1:8000/v1   --model hukuk-ai-poc   --qids CBG-01 CBG-02 CBG-03 CBG-04 MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 CBKAR-01 CBKAR-02 CBKAR-08 YON-01 YON-02 YON-03 KANUN-01 KANUN-06 KANUN-15 TEB-01 TEB-02   --out-dir reports/benchmark/runs/<timestamp>_phase18_recovery_A1_9_live_smoke20   --timeout 420   --retries 0   --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py   --answers reports/benchmark/runs/<timestamp>_phase18_recovery_A1_9_live_smoke20/candidate_answers.csv   --out-dir reports/benchmark/runs/<timestamp>_phase18_recovery_A1_9_live_smoke20
```

## Live smoke acceptance

Live smoke aşağıdaki seviyeyi yakalamalı:

| Metric | Minimum |
|---|---:|
| raw_score_proxy | >= 130 / 200 |
| pass_proxy | >= 12 / 20 |
| wrong_family | <= 3 |
| wrong_document | <= 5 |
| unsupported_confident_claim | <= 1 |
| contract_valid | 20/20 |
| provenance collection | full collection |

A1.8 candidate seviyesine yakınsa full confirmation’a geç.

---

# 5. Live Full 100 Confirmation

## Komut

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py   --api-url http://127.0.0.1:8000/v1   --model hukuk-ai-poc   --out-dir reports/benchmark/runs/<timestamp>_phase18_recovery_A1_9_live_full100   --timeout 420   --retries 0   --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py   --answers reports/benchmark/runs/<timestamp>_phase18_recovery_A1_9_live_full100/candidate_answers.csv   --out-dir reports/benchmark/runs/<timestamp>_phase18_recovery_A1_9_live_full100

GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/<timestamp>_phase18_recovery_A1_9_live_full100   bash scripts/benchmark/run_green_lane.sh   --run-dir reports/benchmark/runs/<timestamp>_phase18_recovery_A1_9_live_full100
```

## Live full acceptance gate

Live full run şu eşiği karşılamalı:

| Metric | Target |
|---|---:|
| raw_score_proxy | >= 735 |
| pass_proxy | >= 73 |
| wrong_family | <= 15 |
| wrong_document | <= 15 |
| hallucinated_identifier | <= 23 |
| unsupported_confident_claim | <= 8 |
| contract_valid | 100/100 |
| green_lane | PASS |
| corpus_materialization_required_count | <= 6 |
| canonical_span_materialized_count | >= 90 |
| YONETMELIK pass | >= 6/10 |
| MULGA pass | >= 3/5 |
| repealed_as_active_count | 0 preferred |
| source_key_v2_collision_detected_count | 0 |
| binding_source_key_collision_detected_count | 0 |

## Candidate/live equivalence

Live full result, A1.8 candidate resultten materially farklı olmamalı.

Tolerance:

```text
raw_score delta <= 10
pass delta <= 2
wrong_family delta <= 2
wrong_document delta <= 2
```

Daha büyük fark varsa cutover başarısız kabul edilir.

---

# 6. Rollback Plan

Aşağıdaki durumlardan biri olursa rollback yap:

- live smoke fail
- live full fail
- provenance yanlış collection gösteriyor
- API/contract/green lane fail
- candidate/live equivalence bozuluyor
- latency veya operational error kabul edilemez

## Rollback steps

1. Live config eski collection’a döndür:

```text
MILVUS_COLLECTION=mevzuat_e5_shadow
```

2. Gateway restart.
3. Rollback provenance al.
4. 20-QID smoke koş.
5. Rollback raporu üret:

```text
reports/benchmark/phase_18_recovery_A1_9_rollback_report.md
```

---

# 7. Başarılı Cutover Sonrası

Eğer live smoke + live full gate geçerse:

## Yeni baseline ilan et

```text
Phase 18 Recovery Baseline
```

Zorunlu artifactler:

- `phase_18_recovery_A1_9_cutover_summary.md`
- `phase_18_recovery_A1_9_live_smoke_summary.md`
- `phase_18_recovery_A1_9_live_full_summary.md`
- `phase_18_recovery_A1_9_candidate_live_comparison.md`
- `phase_18_recovery_A1_9_runtime_provenance.md`
- `phase_18_recovery_A1_9_cutover_decision.md`

## Bundan sonra sıra

1. behavior-preserving `chat.py` decomposition
2. sonra Phase 18 slot-completion redesign

Yeni slot-completion veya retrieval logic eklemeye başlamadan önce bu baseline dondurulmalı.

---

# 8. Productization / Fine-Tuning

Bu cutover geçse bile:

- productization hâlâ kapalı
- fine-tuning hâlâ kapalı

Çünkü hâlâ:

- residual deterministic-proxy FAIL rows var
- KKY / YONETMELIK / CB authority / remaining MULGA precision backlog var
- Phase 18 slot-completion henüz güvenli şekilde yeniden tasarlanmadı
- `chat.py` decomposition yapılmadı

---

# 9. Commit Plan

## Commit 1

- A1.8 candidate gate pass report
- clean commit state
- provenance confirmation

## Commit 2

- live config cutover
- pre/post cutover provenance
- live smoke artifacts

## Commit 3

- live full confirmation artifacts
- candidate/live comparison
- cutover decision report

Her commit sonrası push.

---

# 10. Final Not

A1.8 sonrası artık aday collection gate’i geçti.
Ama controlled live cutover ayrı bir operasyonel adımdır.

Kural:

**Candidate pass != live cutover complete.**

Live `8000` ancak smoke + full confirmation + provenance equivalence geçerse yeni baseline kabul edilir.
