# Node3 Merged Weak Slices

Date: 2026-03-21
Scope: isolate the main regressions in the merged `vLLM` serving lane compared with the older node3 adapter/proxy candidate path
Decision: the merged lane is accepted for serving because it still passes Faz 1 gates, but the next tuning/eval wave should explicitly target a small set of source-precision regressions

## Compared Reports

- baseline candidate:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321_t600.json`
- merged candidate:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_merged_20260321.json`

## Highest-Impact Regressions

### 1) `TBK-043` — manevi tazminat maddeleri

- category: `tbk_haksiz_fiil`
- old source rate: `1.0`
- merged source rate: `0.0`
- merged eval outcome: `timed out`

Immediate manual retry:

- returned in `25.835s`
- cited `TBK m.58`, `TBK m.56` correctly
- but also introduced extra unrelated citations (`TMK m.174`, `TMK m.121`, `TBK m.439`, `TMK m.120`, `TBK m.72`, `TBK m.73`, `TMK m.25`)

Interpretation:

- the core problem is source over-expansion / answer drift
- the timeout in the full run appears transient, but the precision issue is real

### 2) `TBK-026` — müteselsil kefalet şartları

- category: `tbk_kefalet`
- old source rate: `1.0`
- merged source rate: `0.0`
- merged hallucination: `true`

Interpretation:

- this is the clearest persistent quality regression cluster
- the category-level merged summary already reflects this weakness:
  - `tbk_kefalet` source rate `50.0%`
  - `tbk_kefalet` hallucination rate `50.0%`

### 3) `TBK-037` — bağışlamanın geri alınması

- category: `tbk_genel`
- old source rate: `1.0`
- merged source rate: `0.0`
- merged hallucination: `true`

Interpretation:

- merged lane is occasionally over-answering on narrower doctrinal questions

### 4) `TBK-021` — satışta gözden geçirme ve bildirim külfeti

- category: `tbk_satis`
- old source rate: `1.0`
- merged source rate: `0.0`
- no hard timeout, but precision dropped materially

### 5) `TBK-012` — TBK m.112 ifa edilmemesi / temerrüt

- category: `tbk_genel`
- old source rate: `0.6667`
- merged source rate: `0.3333`

Interpretation:

- not a total failure
- still a meaningful regression in article grounding

## What Did Not Regress

- refusal handling stayed strong:
  - `refusal_accuracy = 100%`
- out-of-scope TMK/TTK style rejections remained clean
- latency improved very substantially despite the regressions

## Target List For Next Wave

1. `TBK-043` — constrain citation spread around `TBK m.56` / `TBK m.58`
2. `TBK-026` — kefalet source precision
3. `TBK-037` — bağışlama geri alma source precision
4. `TBK-021` — satış / ayıba karşı tekeffül answer narrowing
5. `TBK-012` — m.112 anchoring

## Recommendation

- keep merged `vLLM` as the primary serving lane
- do not spend the next wave on general latency
- spend it on a narrow source-precision patch set built around the five items above, especially `TBK-043` and the kefalet cluster
