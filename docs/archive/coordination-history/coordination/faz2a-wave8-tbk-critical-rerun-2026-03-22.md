# FAZ 2A Wave 8 - TBK Critical Deterministic Rerun

## Scope

Wave 8, `tbk_critical` slice'inda Wave 7'de ortak hallucination / wrong-source ureten 7 soruluk dar paketi kapatmak icin acildi.

Deterministic precise-answer coverage eklenen sorular:

- `TBK-107`
- `TBK-134`
- `TBK-139`
- `TBK-147`
- `TBK-148`
- `TBK-152`
- `TBK-161`

## Artifacts

- baseline report:
  `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_baseline_wave8_20260322.json`
- candidate report:
  `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_candidate_wave8_20260322.json`

## Matched Result

Baseline (`8043`, dgxnode2 base thinking-off):

- citation: `100.0%`
- correct source: `74.3%`
- hallucination: `0.0%`
- refusal: `95.1%`

Candidate (`8042`, dgx1 merged):

- citation: `100.0%`
- correct source: `71.9%`
- hallucination: `1.6%`
- refusal: `93.4%`

Iki lane de `tbk_critical` slice'i icin Faz 1 barini gecti.

## Delta vs Wave 7

Baseline delta:

- correct source: `64.2% -> 74.3%` (`+10.1pp`)
- hallucination: `11.5% -> 0.0%` (`-11.5pp`)

Candidate delta:

- correct source: `64.5% -> 71.9%` (`+7.4pp`)
- hallucination: `11.5% -> 1.6%` (`-9.8pp`)
- refusal: `88.5% -> 93.4%` (`+4.9pp`)

## Closed Cluster

Wave 7'de ortak fail olan 7 soru, Wave 8'de her iki lane icin de `src=1.00 / no-hal` noktasina tasindi:

- `TBK-107`
- `TBK-134`
- `TBK-139`
- `TBK-147`
- `TBK-148`
- `TBK-152`
- `TBK-161`

## Residuals

Wave 8, shared hallucination paketini kapatti; ancak candidate lane tamamen temiz degil.

Kalan candidate hallucination:

- `TBK-141`

Kalan yapisal gozlem:

- candidate correct source, baseline'in altinda kalmaya devam ediyor:
  `71.9%` vs `74.3%`
- en zayif kategori hala `tbk_ceza_sarti`
  - baseline `66.7%`
  - candidate `62.1%`
- candidate `tbk_vekaletname` hall rate sifira inmedi
  - category hall `5.6%`

## Decision

Wave 8 basarili.

- `tbk_critical` slice'i gate-pass duruma geldi.
- shared hallucination paketi kapandi.
- sonraki dogru is, genis paket degil dar residual wave:
  - once `TBK-141`
  - sonra gerekiyorsa `tbk_ceza_sarti` source tail

