# Phase 24HR Option C Targeted Smoke Run Report

- generated_at_utc: `2026-05-07T04:20:43.511615+00:00`
- technical_status: `PASS`
- quality_gate_status: `FAIL`
- api_url: `http://127.0.0.1:8010/v1`
- model: `hukuk-ai-poc`
- target_qids: `TEB-04 TUZUK-05 KANUN-08 YON-05`
- run_dir: `reports/benchmark/runs/phase_24HR_option_C_targeted_candidate_smoke`
- live_8000_modified: `false`
- candidate_gateway_started_by_option_c: `false`
- chat_completions_called: `true`
- model_inference_called: `true`

## Score Summary

| metric | value |
|---|---:|
| total | 4 |
| raw_score_proxy | 10.45 / 40 |
| pass_proxy | 0 |
| fail_proxy | 4 |
| answer_contract_invalid_count | 0 |
| unsupported_confident_answer_count | 0 |
| source_key_v2_collision_detected_count | 0 |
| binding_source_key_collision_detected_count | 0 |
| repealed_as_active_count | 0 |
| temporal_validity_miss_count | 0 |
| hallucinated_source_count | 2 |
| manual_review_count | 4 |

## QID Results

| qid | score | result | selected document | failure classes |
|---|---:|---|---|---|
| `TEB-04` | 0.00 | FAIL | `KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ` | `auto_fail_triggered`, `missing_required_content_signal`, `wrong_family`, `hallucinated_identifier`, `partial_grounding_only` |
| `TUZUK-05` | 3.25 | FAIL | `GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK` | `missing_gold_document_signal`, `missing_required_content_signal`, `wrong_document`, `partial_grounding_only` |
| `KANUN-08` | 1.45 | FAIL | `ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN TÜKETİCİ HAKLARI YÖNETMELİĞİ` | `missing_gold_document_signal`, `missing_required_content_signal`, `wrong_family`, `wrong_document`, `partial_grounding_only` |
| `YON-05` | 5.75 | FAIL | `İMAR KANUNU` | `missing_required_content_signal`, `wrong_family`, `hallucinated_identifier`, `partial_grounding_only` |

## Stop-Condition Review

- `TEB-04`: source `19631` / KDV Genel Uygulama Tebliği was selected, but the answer claimed `MULGA` / `repealed` for an active source and auto-failed.
- `TUZUK-05`: stop condition failed because the candidate selected a concrete irrelevant tüzük as primary source instead of the human-reviewed general hierarchy handling.
- Hard counters stayed clean: answer contract invalid `0`, unsupported confident answer `0`, source-key collision `0`, binding collision `0`.

## Decision

Option `C` is executed, but it does **not** pass the targeted quality gate.

Do not run option `D` full trace-on candidate benchmark from this state. The next step is systemic remediation of source identity, temporal/source-family policy, and grounded answer synthesis, followed by another targeted smoke under a new explicit authorization.

Full trace `trace.jsonl` is local-only under ignored `reports/benchmark/runs/`; committed evidence is limited to summary/report artifacts.
