# Reranker Safe Activation Decision — 2026-03-20

## Kapsam

- Set: `faz1-50`
- Live API: `http://localhost:8000`
- Live model runtime: `192.168.12.236:8080/v1` (`Qwen3.5-35B-A3B-Q8_0.gguf`)
- Gateway mode: `GUARDRAILS_ENABLED=true`, `RERANKER_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`

## Sonuç

- Karar: `keep-off`
- Gerekçe: `faz1-50` üzerinde hiçbir reranker threshold'u `baseline-off` varyantını hem `citation_rate` hem `correct_source_rate` tarafında geçemedi.
- Bu nedenle `phase3-95` ve `faz2-170` regresyon koşularına yükseltilmedi.

## Canlı Matris

| Variant | Error | Citation | Correct Source | Hallucination | Refusal | Phrase Hit | Avg Response |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline-off | 0 | 84.0% | 74.1% | 4.0% | 96.0% | 62.8% | 15020 ms |
| thr=0.1 | 0 | 82.0% | 70.2% | 4.0% | 94.0% | 60.5% | 12643 ms |
| thr=0.2 | 2 | 81.2% | 72.1% | 2.1% | 95.8% | 61.0% | 14887 ms |
| thr=0.3 | 0 | 82.0% | 69.2% | 6.0% | 96.0% | 65.1% | 12672 ms |
| thr=0.4 | 0 | 80.0% | 71.2% | 2.0% | 96.0% | 58.1% | 12720 ms |
| thr=0.5 | 0 | 80.0% | 68.2% | 4.0% | 92.0% | 58.1% | 12566 ms |

## Yorum

- `thr=0.1`, en yakın varyant olsa da baseline'a göre hem `citation_rate` hem `correct_source_rate` düşüyor.
- `thr=0.2`, source tarafında `0.1`'den biraz iyi ama baseline'ın altında kalıyor ve ayrıca iki timeout üretiyor.
- `thr=0.3` ve `thr=0.5`, doğrudan Faz 1 `correct_source_rate` kapısını kaçırıyor.
- `thr=0.4`, kabul kapısını geçse de baseline'a göre citation ve source kalitesinde açık regresyon üretiyor.
- Latency bazı threshold'larda düşüyor, ancak repo karar kuralı source kalitesi ve citation lehine net kazanım istiyor; bu sağlanmadı.

## Tooling Notu

- `evaluation/run_reranker_safe_activation.py`, başlangıçta `eval_runner.py` bir varyantta `1` döndürdüğünde matrisi yarıda kesiyordu.
- Bu davranış düzeltildi; Faz 1 gate fail'leri artık kaydediliyor ve sweep devam ediyor.
- Regresyon testi eklendi:
  - `api-gateway/tests/test_run_reranker_safe_activation.py`

## Artefact'ler

- Summary: `evaluation/reports/reranker_safe_activation_20260320_173726.json`
- Reports:
  - `evaluation/reports/reranker_safe_activation_20260320_173726/baseline-off__faz1-50.json`
  - `evaluation/reports/reranker_safe_activation_20260320_173726/reranker-on-thr-0p1__faz1-50.json`
  - `evaluation/reports/reranker_safe_activation_20260320_173726/reranker-on-thr-0p2__faz1-50.json`
  - `evaluation/reports/reranker_safe_activation_20260320_173726/reranker-on-thr-0p3__faz1-50.json`
  - `evaluation/reports/reranker_safe_activation_20260320_173726/reranker-on-thr-0p4__faz1-50.json`
  - `evaluation/reports/reranker_safe_activation_20260320_173726/reranker-on-thr-0p5__faz1-50.json`

## Sonraki Adım

1. Reranker `default-off` kalacak şekilde runtime korunacak.
2. P0 sırasına göre `guardrails facts-only + latency` ölçümüne geçilecek.
