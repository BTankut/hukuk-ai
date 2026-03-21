# DGXNode3 Qwen External Runbook

Bu runbook, repo içindeki frozen active package'i kullanıcı tarafından verilen proven external Qwen3.5 training path ile çalıştırmak içindir.

## Amaç

- canonical dataset gerçeğini repo içinde tutmak
- node3 proven Qwen trainer'ı onun üstünde çalıştırmak
- dgxnode2'yi inference/runtime işlerinde serbest bırakmak

## Giriş Noktası

Launcher:

- `scripts/finetune/launch_dgxnode3_qwen_external.sh`

Modlar:

- `smoke`
- `full`

## Smoke

```bash
bash scripts/finetune/launch_dgxnode3_qwen_external.sh smoke
```

Bu akış şunları yapar:

1. repo'yu `dgxnode3` üstüne sync eder
2. frozen package gate'i uzakta doğrular
3. active package'i ShareGPT formatına export eder
4. exported dataset'i proven external Qwen repo altına kopyalar
5. detached one-step smoke başlatır

## Full Run

```bash
bash scripts/finetune/launch_dgxnode3_qwen_external.sh full
```

Full mod şu ayarlarla detached run başlatır:

- dataset: exported active `807`-row ShareGPT package
- epochs: `3`
- batch size: `1`
- output dir: `/workspace/outputs/hukuk_ai_active_807_run`

## Varsayılan Remote Path'ler

- repo sync hedefi: `/home/btankut/hukuk-ai-git`
- external trainer repo: `/home/btankut/dgx-spark-unsloth-qwen3.5-training`
- exported dataset target: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/data/hukuk_ai_active_807_sharegpt.jsonl`

## Beklenen Log/PID

- smoke log: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/runtime_logs/hukuk_ai_active_807_smoke.log`
- smoke pid: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/runtime_logs/hukuk_ai_active_807_smoke.pid`
- full log: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/runtime_logs/hukuk_ai_active_807_run.log`
- full pid: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/runtime_logs/hukuk_ai_active_807_run.pid`

## Kural

- canonical source of truth `final_train.jsonl` olmaya devam eder
- ShareGPT dosyası yalnız compatibility export'tur
- smoke başarısı promotion anlamına gelmez
- valid sonraki adım full run + post-train evidence zinciridir
