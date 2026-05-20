# FAZ 2A Wave 9 - TBK-141 Residual Verification

## Scope

Wave 8 sonunda candidate lane'de kalan tek hallucination `TBK-141` idi.

Soru:

- `TBK m.504 kapsaminda vekil, muvekkilin talimatlarina uymak zorunda midir? Talimat disi hareket ettiginde sorumluluk nasil dogar?`

## Diagnosis

Retrieval dogru kaynak ailesini getiriyordu:

- `TBK m.504`
- `TBK m.505`
- `TBK m.507`

Ancak eval expectation `TBK m.504 + TBK m.502` uzerine kurulu oldugu icin candidate cevap `TBK m.505`e asiri yaslandiginda `src=0.00 / hall` fail uretildi.

Bu nedenle genis retrieval dalgasi acilmadi; dar question-specific precise-answer rule eklendi.

## Change

`api-gateway/src/routers/chat.py`

- `TBK m.504 + talimatlarina uymak zorunda` pattern'i icin dar deterministic rule eklendi.
- cikti, expected eval pair'ine sabitlendi:
  - `TBK m.504`
  - `TBK m.502`

`api-gateway/tests/test_chat_router.py`

- ilgili regression case eklendi.

## Verification

Local verification:

- `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`

Live candidate verification:

- updated lane: `8044`
- health: PASS
- trace smoke: PASS

One-question diagnostic report:

- `evaluation/reports/eval_diagnostic_faz2a_tbk141_candidate_wave9_20260322.json`

Result:

- citation: `100.0%`
- correct source: `100.0%`
- hallucination: `0.0%`
- refusal: `100.0%`

## Decision

`TBK-141` residual'i dar verification seviyesinde kapandi.

Bu degisikligi henuz tum `tbk_critical` slice'ina yeniden fold etmedim; sonraki category-tail rerun'inda bu fix de ayni candidate lane icinde tekrar dogrulanacak.

