from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_build_extra_hardening_report_pack(tmp_path: Path) -> None:
    report = {
        "report_meta": {
            "eval_family": "faz1-50",
            "error_count": 0,
        },
        "summary": {
            "citation_rate": 1.0,
            "correct_source_rate": 1.0,
            "hallucination_rate": 0.0,
            "refusal_accuracy": 1.0,
            "avg_response_time_ms": 1000.0,
        },
        "per_question": [
            {
                "question_id": "Q1",
                "cited_sources": ["TBK m.49"],
                "final_mode": "answer",
                "final_reason": None,
                "answer_contract": {
                    "answer_text": "Yanıt. [Kaynak: TBK m.49]",
                    "primary_source_id": "TBK m.49",
                    "secondary_source_ids": [],
                    "law_scope": ["TBK"],
                    "source_validity": "active",
                    "unsupported_reason": None,
                    "verifier_status": "pass",
                    "final_mode": "answer",
                    "claim_units": [
                        {
                            "claim_text": "Yanıt.",
                            "source_id": "TBK m.49",
                            "source_excerpt": "TBK 49 excerpt",
                        }
                    ],
                },
                "trace": {
                    "request_id": "req-1",
                    "timestamp": "2026-03-23T10:00:00+00:00",
                    "question_raw": "TBK m.49 nedir?",
                    "question_normalized": "tbk m.49 nedir?",
                    "parsed_query": {},
                    "law_scope_signal": {
                        "expected_law_scope": ["TBK"],
                        "resolved_law_scope": ["TBK"],
                        "single_law_question": True,
                        "multi_law_question": False,
                        "scope_ambiguous": False,
                    },
                    "question_type": "single_article",
                    "target_date": "2026-03-23",
                    "retrieval_top_k": 5,
                    "rerank_list": [],
                    "assembled_evidence": [
                        {
                            "source_id": "TBK m.49",
                            "citation": "TBK m.49",
                            "excerpt": "TBK 49 excerpt",
                            "yururluk_baslangic": "2011-07-01",
                            "yururluk_bitis": None,
                            "mulga": False,
                        }
                    ],
                    "allowed_source_whitelist": ["TBK m.49"],
                    "answer_contract": {
                        "answer_text": "Yanıt. [Kaynak: TBK m.49]",
                        "primary_source_id": "TBK m.49",
                        "secondary_source_ids": [],
                        "law_scope": ["TBK"],
                        "source_validity": "active",
                        "unsupported_reason": None,
                        "verifier_status": "pass",
                        "final_mode": "answer",
                        "claim_units": [
                            {
                                "claim_text": "Yanıt.",
                                "source_id": "TBK m.49",
                                "source_excerpt": "TBK 49 excerpt",
                            }
                        ],
                    },
                    "model_cited_source_ids": ["TBK m.49"],
                    "verifier_verdict": "pass",
                    "final_mode": "answer",
                    "final_reason": None,
                    "query_signals": {},
                    "retrieval": {"pre_rerank_chunks": [{"source_id": "TBK m.49"}]},
                    "context_assembly": {"allowed_source_whitelist": ["TBK m.49"]},
                    "generation_outcome": {},
                },
            }
        ],
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    trace_dir = tmp_path / "traces"
    trace_dir.mkdir()
    (trace_dir / "req-1.json").write_text(json.dumps(report["per_question"][0]["trace"]), encoding="utf-8")

    source_selection = {
        "generated_at": "2026-03-23T10:00:00+00:00",
        "reports": [
            {
                "label": "faz1-50",
                "question_count": 1,
                "retrieved_correct_source_at_k": 1.0,
                "assembled_correct_source_present": 1.0,
                "model_selected_correct_source": 1.0,
                "whitelist_violation_rate": 0.0,
                "law_scope_mismatch_rate": 0.0,
                "temporal_mismatch_rate": 0.0,
            }
        ],
        "overall": {
            "question_count": 1,
            "retrieved_correct_source_at_k": 1.0,
            "assembled_correct_source_present": 1.0,
            "model_selected_correct_source": 1.0,
            "whitelist_violation_rate": 0.0,
            "law_scope_mismatch_rate": 0.0,
            "temporal_mismatch_rate": 0.0,
        },
    }
    source_selection_path = tmp_path / "source_selection.json"
    source_selection_path.write_text(json.dumps(source_selection), encoding="utf-8")

    output_trace_index = tmp_path / "trace_index.json"
    output_trace_pack_smoke = tmp_path / "trace_smoke.md"
    output_answer_schema = tmp_path / "schema.md"
    output_law_scope = tmp_path / "law_scope.md"
    output_temporal = tmp_path / "temporal.md"
    output_citation = tmp_path / "citation.md"
    output_narrow = tmp_path / "narrow.md"
    output_smoke = tmp_path / "smoke.md"
    output_family = tmp_path / "family.md"
    output_final = tmp_path / "final.md"

    subprocess.run(
        [
            sys.executable,
            "scripts/faz2a/build_extra_hardening_report_pack.py",
            "--report",
            str(report_path),
            "--trace-dir",
            str(trace_dir),
            "--source-selection-json",
            str(source_selection_path),
            "--output-trace-index",
            str(output_trace_index),
            "--output-trace-pack-smoke",
            str(output_trace_pack_smoke),
            "--output-answer-schema-validation",
            str(output_answer_schema),
            "--output-law-scope-delta",
            str(output_law_scope),
            "--output-temporal-delta",
            str(output_temporal),
            "--output-citation-gate-delta",
            str(output_citation),
            "--output-narrow-claim-delta",
            str(output_narrow),
            "--output-smoke",
            str(output_smoke),
            "--output-family-eval",
            str(output_family),
            "--output-final-report",
            str(output_final),
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )

    trace_index = json.loads(output_trace_index.read_text(encoding="utf-8"))
    assert trace_index["matched_eval"]["coverage_rate"] == 1.0
    assert "PASS" in output_trace_pack_smoke.read_text(encoding="utf-8")
    assert "schema_validation_pass_rate" in output_answer_schema.read_text(encoding="utf-8")
    assert "correct_source" in output_family.read_text(encoding="utf-8")
    assert "karar: `PASS`" in output_final.read_text(encoding="utf-8")
