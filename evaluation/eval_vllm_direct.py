#!/usr/bin/env python3
"""Direct vLLM evaluation runner for Hukuk-AI.

- Sends questions directly to OpenAI-compatible vLLM /v1/chat/completions
- Extracts answer from choices[0].message.content
- Handles Qwen reasoning field (choices[0].message.reasoning)
- Computes same metrics via evaluation/metrics.py
- Writes JSON report compatible with existing eval report structure
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Same metrics module used by existing runner
sys.path.insert(0, str(Path(__file__).parent))
from metrics import QuestionResult, aggregate_metrics, compute_metrics  # noqa: E402


SYSTEM_PROMPT = (
    "Sen bir Türk hukuku asistanısın. Sorulara Türk hukuku çerçevesinde, "
    "ilgili kanun maddelerine atıf yaparak cevap ver. Cevabında hangi kanun "
    "ve maddeye dayandığını açıkça belirt."
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("eval_vllm_direct")


def extract_citations(answer_text: str) -> list[str]:
    """Extract law-article citations from free text (e.g., TBK m.146)."""
    if not answer_text:
        return []

    text = answer_text

    patterns = [
        # TBK m.146 / TBK md. 146 / TBK madde 146
        r"\b(TBK|TMK|TCK|İK|IK)\s*(?:m\.?|md\.?|madde\s*)?\s*\.?\s*(\d{1,4})\b",
        # TBK'nın 146. maddesi / TBK 146. madde
        r"\b(TBK|TMK|TCK|İK|IK)(?:'?(?:nın|nin|nun|nün|nın|nün|na|ne|ya|ye))?\s*(\d{1,4})\.?\s*madd",
    ]

    found: set[str] = set()
    for p in patterns:
        for law, article in re.findall(p, text, flags=re.IGNORECASE):
            law_u = law.upper().replace("IK", "İK")
            found.add(f"{law_u} m.{int(article)}")

    return sorted(found)


class VLLMClient:
    def __init__(self, api_url: str, model: str, timeout: float = 300.0, enable_thinking: bool = False) -> None:
        self.api_url = api_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.enable_thinking = enable_thinking

    def ask(self, question: str, max_tokens: int) -> dict[str, Any]:
        url = f"{self.api_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            "temperature": 0.0,
            "stream": False,
            "max_tokens": max_tokens,
        }

        # Qwen3.5 may spend most budget in reasoning; keep thinking off by default
        # so answer content is reliably returned while still supporting reasoning field
        # when enabled.
        if not self.enable_thinking:
            payload["chat_template_kwargs"] = {"enable_thinking": False}

        data = json.dumps(payload).encode("utf-8")

        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                body = json.loads(resp.read().decode("utf-8"))

            choices = body.get("choices") or []
            msg = (choices[0] or {}).get("message", {}) if choices else {}
            content = msg.get("content")
            reasoning = msg.get("reasoning")

            # Content is the actual answer; may be null if generation budget is too low
            answer_text = content if isinstance(content, str) else ""
            citations = extract_citations(answer_text)

            return {
                "answer_text": answer_text,
                "reasoning": reasoning,
                "citations": citations,
                "response_time_ms": elapsed_ms,
                "error": None,
            }

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            return {
                "answer_text": "",
                "reasoning": None,
                "citations": [],
                "response_time_ms": 0.0,
                "error": f"HTTP {e.code}: {err_body[:300]}",
            }
        except Exception as exc:
            return {
                "answer_text": "",
                "reasoning": None,
                "citations": [],
                "response_time_ms": 0.0,
                "error": str(exc),
            }


def load_questions(path: Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("questions", [])


def result_to_dict(r: QuestionResult) -> dict[str, Any]:
    d = asdict(r)
    return {k: v for k, v in d.items() if v is not None}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run direct vLLM eval")
    parser.add_argument("--api-url", required=True, help="e.g. http://192.168.12.236:30000")
    parser.add_argument("--model", required=True, help="e.g. hukuk-lora or qwen35-base")
    parser.add_argument("--output", required=True, type=Path, help="Output report JSON path")
    parser.add_argument("--max-tokens", type=int, default=3000, help="Generation max_tokens (min 3000)")
    parser.add_argument("--questions", required=True, type=Path, help="Questions JSON path")
    parser.add_argument("--category", default=None, help="Optional category filter")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (sec)")
    parser.add_argument("--timeout", type=float, default=300.0, help="Per-request timeout seconds")
    parser.add_argument("--enable-thinking", action="store_true", help="Enable Qwen thinking/reasoning mode")
    args = parser.parse_args()

    max_tokens = max(args.max_tokens, 3000)
    if args.max_tokens < 3000:
        logger.warning("--max-tokens=%d too low; using 3000", args.max_tokens)

    if not args.questions.exists():
        logger.error("Questions file not found: %s", args.questions)
        return 1

    questions = load_questions(args.questions)
    if args.category:
        questions = [q for q in questions if q.get("category") == args.category]

    if not questions:
        logger.error("No questions to evaluate.")
        return 1

    client = VLLMClient(
        api_url=args.api_url,
        model=args.model,
        timeout=args.timeout,
        enable_thinking=args.enable_thinking,
    )

    logger.info("Starting eval: model=%s questions=%d api=%s", args.model, len(questions), args.api_url)

    results: list[QuestionResult] = []
    started = time.time()

    for idx, q in enumerate(questions, start=1):
        qid = q.get("id", f"Q{idx}")
        qtext = q.get("question", "")
        logger.info("[%d/%d] %s", idx, len(questions), qid)

        api_result = client.ask(qtext, max_tokens=max_tokens)
        reasoning = api_result.get("reasoning")
        retrieval_diag = {
            "reasoning_chars": len(reasoning) if isinstance(reasoning, str) else 0,
            "content_empty": not bool(api_result.get("answer_text")),
        }

        result = compute_metrics(
            question=q,
            answer_text=api_result["answer_text"],
            cited_sources=api_result["citations"],
            response_time_ms=api_result["response_time_ms"],
            blocked=False,
            verification=None,
            error=api_result["error"],
            retrieval_diagnostic=retrieval_diag,
        )
        results.append(result)

        if result.error:
            logger.warning("  error=%s", result.error)
        else:
            logger.info(
                "  citation=%s source=%.2f hall=%s refusal_ok=%s",
                result.has_citation,
                result.correct_source_rate,
                result.is_hallucination,
                result.refusal_correct,
            )

        if args.delay > 0 and idx < len(questions):
            time.sleep(args.delay)

    summary = aggregate_metrics(results)

    report = {
        "report_meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "questions_source": str(args.questions),
            "api_url": args.api_url,
            "mock_mode": False,
            "retrieval_profile": None,
            "model": args.model,
            "max_tokens": max_tokens,
            "enable_thinking": bool(args.enable_thinking),
            "planned_questions": len(questions),
            "total_questions": summary.total_questions,
            "error_count": summary.error_count,
            "duration_seconds": round(time.time() - started, 1),
        },
        "validation": {
            "is_valid": True,
            "error_count": summary.error_count,
            "max_errors": None,
            "aborted_due_to_errors": False,
            "planned_questions": len(questions),
            "executed_questions": len(results),
            "contamination_reasons": [],
        },
        "summary": {
            "citation_rate": summary.citation_rate,
            "correct_source_rate": summary.correct_source_rate,
            "hallucination_rate": summary.hallucination_rate,
            "refusal_accuracy": summary.refusal_accuracy,
            "in_scope_total_questions": summary.in_scope_total_questions,
            "in_scope_citation_rate": summary.in_scope_citation_rate,
            "in_scope_correct_source_rate": summary.in_scope_correct_source_rate,
            "avg_keyword_coverage": summary.avg_keyword_coverage,
            "phrase_hit_rate": summary.phrase_hit_rate,
            "avg_response_time_ms": summary.avg_response_time_ms,
            "blocked_rate": summary.blocked_rate,
        },
        "faz1_criteria": summary.faz1_criteria,
        "by_category": summary.by_category,
        "by_difficulty": summary.by_difficulty,
        "per_question": [result_to_dict(r) for r in results],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info("Report written: %s", args.output)
    logger.info(
        "Summary: citation=%.4f source=%.4f hall=%.4f refusal=%.4f",
        summary.citation_rate,
        summary.correct_source_rate,
        summary.hallucination_rate,
        summary.refusal_accuracy,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
