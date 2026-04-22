#!/usr/bin/env python3
"""Run the public hukuk-ai 100 benchmark against an OpenAI-compatible gateway."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.hukuk_ai_100_article_alignment import (
    articles_equal,
    classify_article_alignment,
)

DEFAULT_QUESTIONS = REPO_ROOT / "configs/evaluation/hukuk_ai_100_public_questions.csv"
DEFAULT_RUNS_DIR = REPO_ROOT / "reports/benchmark/runs"

ANSWER_FIELDS = [
    "qid",
    "difficulty",
    "primary_type",
    "secondary_types",
    "task_type",
    "reference_date",
    "question",
    "answer",
    "citations",
    "source_titles",
    "source_ids",
    "doc_types",
    "confidence_0_100",
    "final_reason",
    "answer_mode",
    "grounding_status",
    "source_family_claimed",
    "source_title_claimed",
    "source_identifier_claimed",
    "article_or_section_claimed",
    "effective_state_claimed",
    "temporal_qualification",
    "family_compatibility_status",
    "identifier_integrity_status",
    "needs_manual_review",
    "contract_valid",
    "contract_repaired",
    "claimed_source_parse_success",
    "confidence_policy_ok",
    "uncertainty_disclosed",
    "manual_review_flag",
    "unsupported_confident_answer",
    "selector_document_rank",
    "selector_article_rank",
    "selector_exact_article_hit",
    "selector_support_span_count",
    "selected_document_id",
    "selected_article",
    "selected_paragraph_or_clause",
    "support_span_count",
    "support_span_diversity",
    "support_contains_article_number",
    "support_contains_temporal_clause",
    "support_contains_exception_signal",
    "selector_reason",
    "article_match_type",
    "selector_article_lock_type",
    "preferred_source_families",
    "selector_preferred_family_hit",
    "query_article_alignment",
    "article_alignment",
    "selected_article_equals_claimed_article",
    "selector_evidence_sufficiency",
    "metadata_identity_strength",
    "document_identity_score",
    "title_match_type",
    "identifier_match_type",
    "issuer_match_type",
    "year_match_type",
    "document_rerank_reason",
    "temporal_state_resolved",
    "manual_review_trigger_reason",
    "article_lock_failed",
    "support_insufficient_for_specific_claim",
    "temporal_clause_missing",
    "answer_suppressed_due_to_evidence_gap",
    "required_fact_coverage_score",
    "minimum_answer_facts_present",
    "completeness_degrade_reason",
    "task_type_answer_template_used",
    "expected_family_prior",
    "preferred_family_pool_size",
    "cross_family_fallback_used",
    "family_override_reason",
    "selected_family_confidence",
    "retrieval_trace_id",
    "final_mode",
    "blocked",
    "error",
    "response_time_ms",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--api-url", default=os.getenv("HUKUK_AI_BASE_URL", "http://127.0.0.1:8000/v1"))
    parser.add_argument("--model", default=os.getenv("HUKUK_AI_MODEL", "hukuk-ai-poc"))
    parser.add_argument("--api-key", default=os.getenv("HUKUK_AI_API_KEY", "benchmark"))
    parser.add_argument("--max-tokens", type=int, default=int(os.getenv("HUKUK_AI_BENCHMARK_MAX_TOKENS", "1200")))
    parser.add_argument("--top-k", type=int, default=int(os.getenv("HUKUK_AI_BENCHMARK_TOP_K", "20")))
    parser.add_argument("--timeout", type=int, default=int(os.getenv("HUKUK_AI_BENCHMARK_TIMEOUT", "180")))
    parser.add_argument("--retries", type=int, default=int(os.getenv("HUKUK_AI_BENCHMARK_RETRIES", "2")))
    parser.add_argument("--sleep", type=float, default=float(os.getenv("HUKUK_AI_BENCHMARK_SLEEP", "0.4")))
    parser.add_argument("--limit", type=int, help="Run only the first N questions for smoke testing.")
    parser.add_argument("--no-trace", action="store_true", help="Disable include_trace. Phase 0 default is trace-on.")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Append to an existing run directory and skip qids already present in candidate_answers.csv.",
    )
    parser.add_argument(
        "--allow-missing-trace",
        action="store_true",
        help="Do not return a non-zero exit code when successful responses lack trace payloads.",
    )
    return parser.parse_args()


def endpoint_from_api_url(api_url: str) -> str:
    url = api_url.rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    return f"{url}/chat/completions"


def load_questions(path: Path, limit: int | None) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if limit is not None:
        rows = rows[:limit]
    return rows


def question_qid(row: dict[str, str], index: int) -> str:
    return row.get("q_id") or row.get("qid") or f"row-{index}"


def load_existing_answers(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_user_message(row: dict[str, str]) -> str:
    deliverable = row.get("expected_deliverable", "").strip()
    deliverable_part = f"\nBeklenen çıktı tipi: {deliverable}." if deliverable else ""
    return (
        f"Bu soruyu {row.get('reference_date', '').strip()} tarihindeki yururluk durumuna gore cevapla. "
        "Yaniti kisa sonuc, kisa gerekce, dayanak belge zinciri ve gerekiyorsa "
        "yururluk/guncellik notu seklinde ver."
        f"{deliverable_part}\n\n"
        f"{row.get('question', '').strip()}"
    )


def request_json(endpoint: str, payload: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def call_api(
    endpoint: str,
    row: dict[str, str],
    args: argparse.Namespace,
    include_trace: bool,
) -> tuple[dict[str, Any], int]:
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": build_user_message(row)}],
        "stream": False,
        "temperature": 0,
        "max_tokens": args.max_tokens,
        "top_k": args.top_k,
        "include_trace": include_trace,
    }

    started = time.perf_counter()
    for attempt in range(args.retries + 1):
        try:
            response = request_json(endpoint, payload, args.api_key, args.timeout)
            return response, int((time.perf_counter() - started) * 1000)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt < args.retries:
                time.sleep(3)
                continue
            return {"_error": str(exc), "_error_type": exc.__class__.__name__}, int(
                (time.perf_counter() - started) * 1000
            )
    return {"_error": "max retries exceeded"}, int((time.perf_counter() - started) * 1000)


def first_choice_content(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message") if isinstance(choices[0], dict) else {}
    content = message.get("content") if isinstance(message, dict) else ""
    return content.strip() if isinstance(content, str) else ""


def stringify_list(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item.strip())
            else:
                parts.append(json.dumps(item, ensure_ascii=False, sort_keys=True))
        return " | ".join(p for p in parts if p)
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def iter_dicts(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(iter_dicts(child))
    elif isinstance(value, list):
        for item in value:
            found.extend(iter_dicts(item))
    return found


def unique_join(values: list[Any], limit: int = 30) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text[:240])
        if len(out) >= limit:
            break
    return " | ".join(out)


def collect_source_fields(response: dict[str, Any]) -> tuple[str, str, str]:
    title_keys = ("source_title", "title", "official_title", "document_title", "law_name")
    id_keys = ("source_id", "doc_id", "document_id", "canonical_id", "source_key")
    type_keys = ("doc_type", "document_type", "primary_type", "belge_turu", "source_type")

    titles: list[Any] = []
    source_ids: list[Any] = []
    doc_types: list[Any] = []
    for item in iter_dicts(response):
        for key in title_keys:
            if key in item:
                titles.append(item.get(key))
        for key in id_keys:
            if key in item:
                source_ids.append(item.get(key))
        for key in type_keys:
            if key in item:
                doc_types.append(item.get(key))
    return unique_join(titles), unique_join(source_ids), unique_join(doc_types)


def extract_trace_id(response: dict[str, Any]) -> str:
    trace = response.get("trace")
    if isinstance(trace, dict):
        for key in ("trace_id", "request_id", "retrieval_trace_id", "id"):
            value = trace.get(key)
            if value:
                return str(value)
    for key in ("retrieval_trace_id", "request_id", "id"):
        value = response.get(key)
        if value:
            return str(value)
    return ""


def extract_confidence(response: dict[str, Any]) -> str:
    for container in (response, response.get("answer_contract")):
        if not isinstance(container, dict):
            continue
        value = container.get("confidence_0_100")
        if value is None:
            value = container.get("confidence")
        if value is not None:
            return str(value)
    return ""


def extract_final_reason(response: dict[str, Any]) -> str:
    for container in (response.get("answer_contract"), response):
        if not isinstance(container, dict):
            continue
        value = container.get("final_reason")
        if value:
            return str(value)
    if response.get("blocked") is True:
        return "blocked"
    if "_error" in response:
        return "api_error"
    return ""


def answer_contract(response: dict[str, Any]) -> dict[str, Any]:
    value = response.get("answer_contract")
    return value if isinstance(value, dict) else {}


def trace_payload(response: dict[str, Any]) -> dict[str, Any]:
    value = response.get("trace")
    return value if isinstance(value, dict) else {}


def article_span_selector(response: dict[str, Any]) -> dict[str, Any]:
    trace = trace_payload(response)
    for container_name in ("retrieval", "parsed_query", "query_signals", "context_assembly"):
        container = trace.get(container_name)
        if not isinstance(container, dict):
            continue
        selector = container.get("article_span_selector")
        if isinstance(selector, dict):
            return selector
    return {}


def contract_validation(response: dict[str, Any]) -> dict[str, Any]:
    contract = answer_contract(response)
    value = contract.get("contract_validation")
    if isinstance(value, dict):
        return value
    trace = response.get("trace")
    if isinstance(trace, dict):
        value = trace.get("answer_contract_validation")
        if isinstance(value, dict):
            return value
    return {}


def contract_value(response: dict[str, Any], key: str) -> str:
    value = answer_contract(response).get(key)
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return ""
    return str(value)


def validation_value(response: dict[str, Any], key: str) -> str:
    value = contract_validation(response).get(key)
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return ""
    return str(value)


def selector_value(response: dict[str, Any], key: str) -> str:
    value = article_span_selector(response).get(key)
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return ""
    if isinstance(value, list):
        return stringify_list(value)
    return str(value)


def retrieval_feature_value(response: dict[str, Any], key: str) -> str:
    trace = trace_payload(response)
    for container_name in ("retrieval", "parsed_query", "query_signals", "context_assembly"):
        container = trace.get(container_name)
        if not isinstance(container, dict):
            continue
        if key in container:
            value = container.get(key)
        else:
            features = container.get("retrieval_verification_features")
            value = features.get(key) if isinstance(features, dict) else None
        if isinstance(value, bool):
            return "True" if value else "False"
        if value is None:
            continue
        if isinstance(value, list):
            return stringify_list(value)
        return str(value)
    return ""


def source_identity_value(response: dict[str, Any], key: str) -> str:
    trace = trace_payload(response)
    for container_name in ("retrieval", "parsed_query", "query_signals"):
        container = trace.get(container_name)
        if not isinstance(container, dict):
            continue
        if key in container:
            value = container.get(key)
        else:
            reranker = container.get("source_identity_reranker")
            if not isinstance(reranker, dict):
                continue
            value = reranker.get(key)
            if value is None:
                top_scores = reranker.get("top_scores")
                if isinstance(top_scores, list) and top_scores and isinstance(top_scores[0], dict):
                    value = top_scores[0].get(key)
        if isinstance(value, bool):
            return "True" if value else "False"
        if value is None:
            continue
        if isinstance(value, list):
            return stringify_list(value)
        return str(value)
    return ""


def extracted_article_alignment(response: dict[str, Any]) -> str:
    selected_article = selector_value(response, "selected_article")
    claimed_article = contract_value(response, "article_or_section_claimed")
    return classify_article_alignment(
        selected_article=selected_article,
        claimed_article=claimed_article,
        article_match_type=selector_value(response, "article_match_type"),
        selected_paragraph_or_clause=selector_value(response, "selected_paragraph_or_clause"),
    )


def extract_row(row: dict[str, str], response: dict[str, Any], response_time_ms: int) -> dict[str, str]:
    qid = row.get("q_id") or row.get("qid") or ""
    content = first_choice_content(response)
    if not content and "_error" in response:
        content = f"ERROR: {response.get('_error', '')}"
    elif not content:
        reason = extract_final_reason(response) or "empty_content"
        content = f"REFUSED_OR_EMPTY: {reason}"

    source_titles, source_ids, doc_types = collect_source_fields(response)
    return {
        "qid": qid,
        "difficulty": row.get("difficulty", ""),
        "primary_type": row.get("primary_type", ""),
        "secondary_types": row.get("secondary_types", ""),
        "task_type": row.get("task_type", ""),
        "reference_date": row.get("reference_date", ""),
        "question": row.get("question", ""),
        "answer": content,
        "citations": stringify_list(response.get("citations")),
        "source_titles": source_titles,
        "source_ids": source_ids,
        "doc_types": doc_types,
        "confidence_0_100": extract_confidence(response),
        "final_reason": extract_final_reason(response),
        "answer_mode": contract_value(response, "answer_mode"),
        "grounding_status": contract_value(response, "grounding_status"),
        "source_family_claimed": contract_value(response, "source_family_claimed"),
        "source_title_claimed": contract_value(response, "source_title_claimed"),
        "source_identifier_claimed": contract_value(response, "source_identifier_claimed"),
        "article_or_section_claimed": contract_value(response, "article_or_section_claimed"),
        "effective_state_claimed": contract_value(response, "effective_state_claimed"),
        "temporal_qualification": contract_value(response, "temporal_qualification"),
        "family_compatibility_status": contract_value(response, "family_compatibility_status"),
        "identifier_integrity_status": contract_value(response, "identifier_integrity_status"),
        "needs_manual_review": contract_value(response, "needs_manual_review"),
        "contract_valid": validation_value(response, "contract_valid"),
        "contract_repaired": validation_value(response, "contract_repaired"),
        "claimed_source_parse_success": validation_value(response, "claimed_source_parse_success"),
        "confidence_policy_ok": validation_value(response, "confidence_policy_ok"),
        "uncertainty_disclosed": validation_value(response, "uncertainty_disclosed"),
        "manual_review_flag": validation_value(response, "manual_review_flag"),
        "unsupported_confident_answer": validation_value(response, "unsupported_confident_answer"),
        "selector_document_rank": selector_value(response, "selector_document_rank"),
        "selector_article_rank": selector_value(response, "selector_article_rank"),
        "selector_exact_article_hit": selector_value(response, "selector_exact_article_hit"),
        "selector_support_span_count": selector_value(response, "selector_support_span_count"),
        "selected_document_id": selector_value(response, "selected_document_id"),
        "selected_article": selector_value(response, "selected_article"),
        "selected_paragraph_or_clause": selector_value(response, "selected_paragraph_or_clause"),
        "support_span_count": selector_value(response, "support_span_count"),
        "support_span_diversity": selector_value(response, "support_span_diversity"),
        "support_contains_article_number": selector_value(response, "support_contains_article_number"),
        "support_contains_temporal_clause": selector_value(response, "support_contains_temporal_clause"),
        "support_contains_exception_signal": selector_value(response, "support_contains_exception_signal"),
        "selector_reason": selector_value(response, "selector_reason"),
        "article_match_type": selector_value(response, "article_match_type"),
        "selector_article_lock_type": selector_value(response, "selector_article_lock_type"),
        "preferred_source_families": selector_value(response, "preferred_source_families"),
        "selector_preferred_family_hit": selector_value(response, "selector_preferred_family_hit"),
        "query_article_alignment": selector_value(response, "query_article_alignment"),
        "article_alignment": extracted_article_alignment(response),
        "selected_article_equals_claimed_article": (
            "True"
            if articles_equal(
                selector_value(response, "selected_article"),
                contract_value(response, "article_or_section_claimed"),
            )
            else "False"
        ),
        "selector_evidence_sufficiency": selector_value(response, "selector_evidence_sufficiency"),
        "metadata_identity_strength": selector_value(response, "metadata_identity_strength"),
        "document_identity_score": source_identity_value(response, "document_identity_score"),
        "title_match_type": source_identity_value(response, "title_match_type"),
        "identifier_match_type": source_identity_value(response, "identifier_match_type"),
        "issuer_match_type": source_identity_value(response, "issuer_match_type"),
        "year_match_type": source_identity_value(response, "year_match_type"),
        "document_rerank_reason": source_identity_value(response, "document_rerank_reason"),
        "temporal_state_resolved": selector_value(response, "temporal_state_resolved"),
        "manual_review_trigger_reason": selector_value(response, "manual_review_trigger_reason"),
        "article_lock_failed": contract_value(response, "article_lock_failed"),
        "support_insufficient_for_specific_claim": contract_value(response, "support_insufficient_for_specific_claim"),
        "temporal_clause_missing": contract_value(response, "temporal_clause_missing"),
        "answer_suppressed_due_to_evidence_gap": contract_value(response, "answer_suppressed_due_to_evidence_gap"),
        "required_fact_coverage_score": contract_value(response, "required_fact_coverage_score"),
        "minimum_answer_facts_present": contract_value(response, "minimum_answer_facts_present"),
        "completeness_degrade_reason": contract_value(response, "completeness_degrade_reason"),
        "task_type_answer_template_used": contract_value(response, "task_type_answer_template_used"),
        "expected_family_prior": retrieval_feature_value(response, "expected_family_prior"),
        "preferred_family_pool_size": retrieval_feature_value(response, "preferred_family_pool_size"),
        "cross_family_fallback_used": retrieval_feature_value(response, "cross_family_fallback_used"),
        "family_override_reason": retrieval_feature_value(response, "family_override_reason"),
        "selected_family_confidence": retrieval_feature_value(response, "selected_family_confidence"),
        "retrieval_trace_id": extract_trace_id(response),
        "final_mode": str(response.get("final_mode", "")),
        "blocked": str(response.get("blocked", "")),
        "error": str(response.get("_error", "")),
        "response_time_ms": str(response_time_ms),
    }


def write_summary(run_dir: Path, summary: dict[str, Any]) -> None:
    (run_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# hukuk-ai 100 benchmark run",
        "",
        f"- run_dir: `{run_dir}`",
        f"- api_url: `{summary['api_url']}`",
        f"- model: `{summary['model']}`",
        f"- include_trace: `{summary['include_trace']}`",
        f"- total: {summary['total']}",
        f"- answered: {summary['answered']}",
        f"- refused_or_empty: {summary['refused_or_empty']}",
        f"- errors: {summary['errors']}",
        f"- missing_trace: {summary['missing_trace']}",
        f"- missing_confidence_0_100: {summary['missing_confidence_0_100']}",
        f"- missing_final_reason: {summary['missing_final_reason']}",
        f"- missing_contract_fields: {summary['missing_contract_fields']}",
        f"- contract_valid: {summary['contract_valid']}",
        f"- unsupported_confident_answer: {summary['unsupported_confident_answer']}",
    ]
    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    include_trace = not args.no_trace
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.out_dir or (DEFAULT_RUNS_DIR / timestamp)
    run_dir.mkdir(parents=True, exist_ok=True)
    endpoint = endpoint_from_api_url(args.api_url)
    questions = load_questions(args.questions, args.limit)

    answers_path = run_dir / "candidate_answers.csv"
    trace_path = run_dir / "trace.jsonl"
    existing_rows = load_existing_answers(answers_path) if args.resume else []
    completed_qids = {row.get("qid", "") for row in existing_rows if row.get("qid")}
    pending_questions = [
        question
        for index, question in enumerate(questions, 1)
        if question_qid(question, index) not in completed_qids
    ]
    rows: list[dict[str, str]] = list(existing_rows)

    print(f"Run dir: {run_dir}")
    print(f"Endpoint: {endpoint}")
    print(f"Questions: {len(questions)}")
    if args.resume:
        print(f"Resume: {len(completed_qids)} completed, {len(pending_questions)} pending")

    write_header = not (args.resume and answers_path.exists())
    answer_mode = "a" if args.resume else "w"
    trace_mode = "a" if args.resume else "w"
    with answers_path.open(answer_mode, newline="", encoding="utf-8") as answers_file, trace_path.open(
        trace_mode, encoding="utf-8"
    ) as trace_file:
        writer = csv.DictWriter(answers_file, fieldnames=ANSWER_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()

        for index, question in enumerate(pending_questions, 1):
            qid = question_qid(question, index)
            global_index = len(completed_qids) + index
            print(f"[{global_index:>3}/{len(questions)}] {qid:<16}", end=" ", flush=True)
            response, response_time_ms = call_api(endpoint, question, args, include_trace)
            extracted = extract_row(question, response, response_time_ms)
            writer.writerow(extracted)
            answers_file.flush()
            rows.append(extracted)

            trace_record = {
                "qid": qid,
                "question": question.get("question", ""),
                "reference_date": question.get("reference_date", ""),
                "request": {
                    "api_url": args.api_url,
                    "endpoint": endpoint,
                    "model": args.model,
                    "include_trace": include_trace,
                    "top_k": args.top_k,
                    "max_tokens": args.max_tokens,
                },
                "response": response,
                "extracted": extracted,
            }
            trace_file.write(json.dumps(trace_record, ensure_ascii=False, sort_keys=True) + "\n")
            trace_file.flush()

            if extracted["error"]:
                print(f"ERR {extracted['response_time_ms']}ms")
            elif extracted["answer"].startswith("REFUSED_OR_EMPTY:"):
                print(f"EMPTY {extracted['response_time_ms']}ms")
            else:
                print(f"OK {len(extracted['answer'])} chars {extracted['response_time_ms']}ms")
            time.sleep(args.sleep)

    total = len(rows)
    summary = {
        "api_url": args.api_url,
        "endpoint": endpoint,
        "model": args.model,
        "questions": str(args.questions),
        "run_dir": str(run_dir),
        "include_trace": include_trace,
        "total": total,
        "answered": sum(1 for r in rows if not r["error"] and not r["answer"].startswith("REFUSED_OR_EMPTY:")),
        "refused_or_empty": sum(1 for r in rows if r["answer"].startswith("REFUSED_OR_EMPTY:")),
        "errors": sum(1 for r in rows if r["error"]),
        "missing_trace": sum(1 for r in rows if not r["retrieval_trace_id"]),
        "missing_confidence_0_100": sum(1 for r in rows if not r["confidence_0_100"]),
        "missing_final_reason": sum(1 for r in rows if not r["final_reason"]),
        "missing_contract_fields": sum(
            1
            for r in rows
            if not r["answer_mode"]
            or not r["grounding_status"]
            or not r["source_family_claimed"]
            or not r["source_identifier_claimed"]
            or not r["article_or_section_claimed"]
            or not r["effective_state_claimed"]
            or not r["temporal_qualification"]
            or not r["needs_manual_review"]
        ),
        "contract_valid": sum(1 for r in rows if r["contract_valid"] == "True"),
        "unsupported_confident_answer": sum(1 for r in rows if r["unsupported_confident_answer"] == "True"),
        "candidate_answers": str(answers_path),
        "trace": str(trace_path),
    }
    write_summary(run_dir, summary)
    print(f"Summary: {run_dir / 'summary.md'}")

    if include_trace and summary["missing_trace"] and not args.allow_missing_trace:
        print("ERROR: include_trace was enabled but at least one response lacked retrieval_trace_id.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
