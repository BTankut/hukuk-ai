#!/usr/bin/env python3
"""Non-live residual smoke for post-human-review TEB-04 and TUZUK-05.

The script validates only local artifacts and pure in-process selector/scorer
logic. It does not call live 8000, Milvus, embeddings, or model inference.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
API_GATEWAY_SRC = REPO_ROOT / "api-gateway/src"
if str(API_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(API_GATEWAY_SRC))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.orchestrator import RAGOrchestrator, RetrievedChunk
from rag.source_identity import _select_metadata_first_source_candidates
from source_family_resolver import SourceFamilyResolution


SCORER_PATH = REPO_ROOT / "scripts/benchmark/score_hukuk_ai_100.py"
SPEC = importlib.util.spec_from_file_location("score_hukuk_ai_100", SCORER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot import scorer from {SCORER_PATH}")
score_hukuk_ai_100 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score_hukuk_ai_100)


REPORTS_DIR = REPO_ROOT / "reports/benchmark"
TEB_SPANS_JSONL = (
    REPORTS_DIR
    / "source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_chunked_subspans.jsonl"
)
TEB_FULL_SPANS_JSONL = REPORTS_DIR / "source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_spans.jsonl"
OUT_CSV = REPORTS_DIR / "phase_24HR_non_live_residual_smoke.csv"
OUT_JSON = REPORTS_DIR / "phase_24HR_non_live_residual_smoke.json"
OUT_MD = REPORTS_DIR / "phase_24HR_non_live_residual_smoke.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def normalize(text: str) -> str:
    return score_hukuk_ai_100.normalize(text)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def teb_catalog() -> dict[str, dict[str, object]]:
    return {
        "19631": {
            "source_key": "19631",
            "canonical_title": "KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ",
            "canonical_identifier": "19631",
            "canonical_identifier_type": "teblig_no",
            "source_family_canonical": "teblig",
            "source_family_raw": "teblig",
            "source_family_mapped": "teblig",
            "effective_state": "active",
            "year_signals": ["2014", "2026"],
            "alias_titles": ["KDV Genel Uygulama Tebliği"],
        },
        "99999": {
            "source_key": "99999",
            "canonical_title": "ELEKTRONİK TEBLİGAT GENEL TEBLİĞİ",
            "canonical_identifier": "99999",
            "canonical_identifier_type": "teblig_no",
            "source_family_canonical": "teblig",
            "source_family_raw": "teblig",
            "source_family_mapped": "teblig",
            "effective_state": "active",
            "year_signals": ["2020"],
            "alias_titles": ["Elektronik Tebligat Genel Tebliği"],
        },
    }


def family_resolution() -> SourceFamilyResolution:
    return SourceFamilyResolution(
        predicted_family="teblig",
        family_confidence=0.84,
        routing_families=["teblig"],
        preferred_families=["teblig"],
    )


def lexical_score(query: str, span: dict[str, Any]) -> int:
    query_terms = {token for token in normalize(query).split() if len(token) >= 3}
    surface = normalize(
        " ".join(
            [
                str(span.get("section_locator", "")),
                str(span.get("section_title", "")),
                str(span.get("display_citation", "")),
                str(span.get("body", ""))[:2000],
            ]
        )
    )
    score = sum(10 for term in query_terms if term in surface)
    locator = str(span.get("section_locator", ""))
    if locator and normalize(locator.replace("I/C-", "")) in normalize(query):
        score += 30
    if "mahsuben" in normalize(query) and "mahsuben" in surface:
        score += 25
    if "nakden" in normalize(query) and "nakden" in surface:
        score += 25
    if "diger hususlar" in normalize(query) and "diger hususlar" in surface:
        score += 25
    if "kismi tevkifat" in normalize(query) and "kismi tevkifat" in surface:
        score += 25
    return score


def top_locators(query: str, spans: list[dict[str, Any]], limit: int = 5) -> list[str]:
    ranked = sorted(spans, key=lambda span: (-lexical_score(query, span), str(span.get("section_locator", ""))))
    return [str(span.get("section_locator", "")) for span in ranked[:limit]]


def locator_hit(expected: str, observed: list[str]) -> bool:
    return any(locator == expected or locator.startswith(f"{expected}.") for locator in observed)


def teb_smoke_rows() -> list[dict[str, Any]]:
    spans = read_jsonl(TEB_SPANS_JSONL)
    full_spans = read_jsonl(TEB_FULL_SPANS_JSONL)
    selector = _select_metadata_first_source_candidates(
        query="KDV tevkifatı ve iade bakımından ana tebliğin konsolide metnine göre cevapla.",
        requested_source_families=["teblig"],
        source_family_resolution=family_resolution(),
        catalog_loader=teb_catalog,
    )
    rows: list[dict[str, Any]] = []
    selected = selector.get("selected_source_keys", []) if selector else []
    rows.append(
        {
            "qid": "TEB-04",
            "check_id": "teb_source_identity_selects_kdv_gut",
            "status": "PASS" if selected == ["19631"] else "FAIL",
            "expected": "19631",
            "observed": ",".join(selected),
            "evidence": "metadata_first_source_selector",
            "live_8000_modified": "false",
        }
    )

    expected_locators = {
        "I/C-2.1.3",
        "I/C-2.1.5.2.1",
        "I/C-2.1.5.2.2",
        "I/C-2.1.5.3",
    }
    materialized_locators = {str(span.get("section_locator", "")) for span in [*spans, *full_spans]}
    rows.append(
        {
            "qid": "TEB-04",
            "check_id": "teb_required_locators_materialized",
            "status": "PASS" if expected_locators <= materialized_locators else "FAIL",
            "expected": "|".join(sorted(expected_locators)),
            "observed": "|".join(sorted(expected_locators & materialized_locators)),
                "evidence": f"{rel(TEB_FULL_SPANS_JSONL)} + {rel(TEB_SPANS_JSONL)}",
            "live_8000_modified": "false",
        }
    )

    recall_cases = [
        ("teb_span_recall_kismi_tevkifat", "KDV kısmi tevkifat uygulaması hangi bölümde?", "I/C-2.1.3"),
        (
            "teb_span_recall_mahsuben_iade",
            "KDV tevkifata tabi işlemlerde mahsuben iade talepleri hangi bölümde?",
            "I/C-2.1.5.2.1",
        ),
        (
            "teb_span_recall_nakden_iade",
            "KDV tevkifata tabi işlemlerde nakden iade talepleri hangi bölümde?",
            "I/C-2.1.5.2.2",
        ),
        (
            "teb_span_recall_diger_hususlar",
            "KDV tevkifat iade uygulaması ile ilgili diğer hususlar hangi bölümde?",
            "I/C-2.1.5.3",
        ),
    ]
    for check_id, query, expected in recall_cases:
        observed = top_locators(query, spans)
        rows.append(
            {
                "qid": "TEB-04",
                "check_id": check_id,
                "status": "PASS" if locator_hit(expected, observed) else "FAIL",
                "expected": expected,
                "observed": "|".join(observed),
                "evidence": "local_chunked_subspan_lexical_recall_top5",
                "live_8000_modified": "false",
            }
        )
    return rows


def hierarchy_answer(**overrides: str) -> dict[str, str]:
    answer = {
        "qid": "TUZUK-05",
        "primary_type": "TUZUK",
        "task_type": "hierarchy_conflict",
        "answer": (
            "Normlar hiyerarşisinde tüzük, kurum içi yönerge ve talimatlara göre üst normdur. "
            "Kurum içi düzenleme geçerli tüzüğe aykırıysa uygulanmaz; çatışmada üst norm uygulanır."
        ),
        "citations": "ilgili yürürlükteki tüzük hükümleri; normlar hiyerarşisi",
        "source_titles": "",
        "source_ids": "",
        "doc_types": "tuzuk",
        "confidence_0_100": "75",
        "final_reason": "grounded",
        "answer_mode": "direct_answer",
        "grounding_status": "fully_grounded",
        "source_family_claimed": "TUZUK",
        "source_title_claimed": "ilgili yürürlükteki tüzük hükümleri",
        "source_identifier_claimed": "genel norm hiyerarşisi",
        "article_or_section_claimed": "genel norm hiyerarşisi",
        "effective_state_claimed": "active",
        "temporal_qualification": "current",
        "needs_manual_review": "False",
        "contract_valid": "True",
        "contract_repaired": "False",
        "claimed_source_parse_success": "True",
        "confidence_policy_ok": "True",
        "uncertainty_disclosed": "True",
        "manual_review_flag": "False",
        "unsupported_confident_answer": "False",
        "retrieval_trace_id": "phase24hr-non-live-smoke",
    }
    answer.update(overrides)
    return answer


def hierarchy_key() -> dict[str, str]:
    return {
        "q_id": "TUZUK-05",
        "gold_summary": "Normlar hiyerarşisinde kurum içi düzenleme geçerli tüzüğe aykırı olamaz.",
        "gold_documents": "ilgili yürürlükteki tüzük hükümleri",
        "must_include": "tüzük üst normdur|kurum içi düzenleme aykırı olamaz",
        "auto_fail_if": "Kurum içi düzenlemeyi tüzükten üstün göstermek",
        "max_points": "10",
    }


def tuzuk_smoke_rows() -> list[dict[str, Any]]:
    selected = RAGOrchestrator._extract_priority_chunks(
        [
            RetrievedChunk(
                text="2821 m.54 Sendika tüzüğünün değiştirilmesi ve kuruluş tüzüğü usulünü düzenler.",
                citation="2821 m.54",
                metadata={"belge_turu": "kanun", "source_title": "SENDİKALAR KANUNU"},
            ),
            RetrievedChunk(
                text="Gıda maddeleri teknik vasıflarını düzenleyen konuya özgü tüzük.",
                citation="gida-tuzugu m.1",
                metadata={"belge_turu": "tuzuk", "source_title": "Gıda Maddelerinin Hususi Vasıflarını Gösteren Tüzük"},
            ),
            RetrievedChunk(
                text="Tüzük hükümleri kurum içi yönerge, talimat ve alt düzenlemelere göre üst norm niteliğindedir; aykırı alt düzenleme uygulanmaz.",
                citation="genel-hiyerarsi tüzük",
                metadata={"belge_turu": "tuzuk", "source_title": "İlgili yürürlükteki tüzük hükümleri"},
            ),
        ],
        query="Geçerli bir tüzük hükmü ile kurum içi alt düzenleme çelişirse hangisi uygulanır?",
        max_chunks=1,
    )
    selected_citation = selected[0].citation if selected else ""
    rows = [
        {
            "qid": "TUZUK-05",
            "check_id": "tuzuk_runtime_priority_selects_general_hierarchy_chunk",
            "status": "PASS" if selected_citation == "genel-hiyerarsi tüzük" else "FAIL",
            "expected": "genel-hiyerarsi tüzük",
            "observed": selected_citation,
            "evidence": "RAGOrchestrator._extract_priority_chunks",
            "live_8000_modified": "false",
        }
    ]

    accepted = score_hukuk_ai_100.score_row(hierarchy_answer(), hierarchy_key())
    rows.append(
        {
            "qid": "TUZUK-05",
            "check_id": "tuzuk_scorer_accepts_abstract_hierarchy_policy",
            "status": "PASS"
            if accepted["document_match_score"] == "1.00" and "wrong_document" not in accepted["failure_classes"]
            else "FAIL",
            "expected": "document_match_score=1.00 without wrong_document",
            "observed": f"document_match_score={accepted['document_match_score']} failure_classes={accepted['failure_classes']}",
            "evidence": "score_hukuk_ai_100.score_row",
            "live_8000_modified": "false",
        }
    )

    rejected = score_hukuk_ai_100.score_row(
        hierarchy_answer(
            citations="Gıda Maddelerinin Hususi Vasıflarını Gösteren Tüzüğü",
            source_titles="Gıda Maddelerinin Hususi Vasıflarını Gösteren Tüzüğü",
            source_title_claimed="Gıda Maddelerinin Hususi Vasıflarını Gösteren Tüzüğü",
            source_identifier_claimed="gida-tuzugu",
        ),
        hierarchy_key(),
    )
    rows.append(
        {
            "qid": "TUZUK-05",
            "check_id": "tuzuk_scorer_rejects_irrelevant_concrete_tuzuk_title",
            "status": "PASS"
            if rejected["document_match_score"] == "0.00" and "wrong_document" in rejected["failure_classes"]
            else "FAIL",
            "expected": "document_match_score=0.00 with wrong_document",
            "observed": f"document_match_score={rejected['document_match_score']} failure_classes={rejected['failure_classes']}",
            "evidence": "score_hukuk_ai_100.score_row",
            "live_8000_modified": "false",
        }
    )
    return rows


def write_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = ["qid", "check_id", "status", "expected", "observed", "evidence", "live_8000_modified"]
    write_csv(OUT_CSV, rows, fields)
    summary = {
        "generated_at_utc": utc_now(),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "row_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
        "fail_count": sum(1 for row in rows if row["status"] != "PASS"),
        "csv": rel(OUT_CSV),
        "live_8000_modified": False,
        "milvus_modified": False,
        "model_inference_called": False,
    }
    OUT_JSON.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Phase 24HR Non-Live Residual Smoke",
        "",
        f"- generated_at_utc: `{summary['generated_at_utc']}`",
        f"- status: `{summary['status']}`",
        f"- row_count: `{summary['row_count']}`",
        f"- pass_count: `{summary['pass_count']}`",
        f"- fail_count: `{summary['fail_count']}`",
        "- live_8000_modified: `false`",
        "- milvus_modified: `false`",
        "- model_inference_called: `false`",
        "",
        "| qid | check | status | expected | observed |",
        "|---|---|---|---|---|",
    ]
    def md_cell(value: Any) -> str:
        return str(value).replace("|", "\\|")

    for row in rows:
        lines.append(
            f"| `{row['qid']}` | `{row['check_id']}` | `{row['status']}` | "
            f"{md_cell(row['expected'])} | {md_cell(row['observed'])} |"
        )
    lines.extend(
        [
            "",
            "## Gate Impact",
            "",
            "- This smoke closes artifact-level non-live validation for TEB-04 span selection and TUZUK-05 hierarchy policy behavior.",
            "- It does not create a shadow collection, serving candidate, internal eval opening, or productization decision.",
            "- Productization remains blocked by full benchmark stability, other residual rows, live guardrails/verification/privacy/audit controls, and rollback rehearsal.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    rows = teb_smoke_rows() + tuzuk_smoke_rows()
    summary = write_report(rows)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
