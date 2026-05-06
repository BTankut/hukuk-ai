# Post-Human-Review TUZUK-05 Policy Update

Generated: 2026-05-06

## Decision
`TUZUK-05` human legal/source ambiguity is closed and the offline scorer policy has been updated for the abstract tüzük/normlar hiyerarşisi class.

This does not open internal eval, serving candidate, productization, live `8000`, model change, prompt change, or top-k change.

## Evidence
| item | value |
|---|---|
| Human review intake | `reports/benchmark/productization/human_legal_review_packet_20260506/intake/human_legal_review_intake_report.md` |
| Scorer implementation | `scripts/benchmark/score_hukuk_ai_100.py` |
| Unit tests | `tests/test_hukuk_ai_100_scorer.py` |
| Verification command | `pytest -q tests/test_hukuk_ai_100_scorer.py` |
| Verification result | `7 passed` |

## Policy Behavior
| case | scorer behavior |
|---|---|
| Abstract hierarchy rubric with generic `ilgili yürürlükteki tüzük hükümleri` gold document | Accepts a general norm-hierarchy answer if it states that tüzük is the upper norm and a kurum içi/alt düzenleme cannot override it. |
| Concrete unrelated tüzük title in the same abstract rubric class | Does not apply the generic hierarchy override; the row remains wrong-document if the concrete title is not the generic hierarchy source. |
| Exact tüzük materialization | Not fabricated; human review says no exact single current tüzük source is identifiable from the prompt. |

## Remaining Gate
Artifact-level non-live runtime priority/scorer smoke passed in `reports/benchmark/phase_24HR_non_live_residual_smoke.md`. Serving/productization still cannot open until shadow/full benchmark validation proves the same policy without regression.
