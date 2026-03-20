#!/usr/bin/env python3
"""Run direct evaluation against a local transformers-loaded model.

This is a diagnostic fallback for post-train checkpoints when serving/runtime
paths are unavailable or incompatible. It intentionally reuses the shared
metrics and report schema used by the other official evaluators.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from metrics import QuestionResult, aggregate_metrics, compute_metrics
from report_metadata import build_identity_metadata


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
logger = logging.getLogger("eval_transformers_direct")


def extract_citations(answer_text: str) -> list[str]:
    if not answer_text:
        return []

    import re

    patterns = [
        r"\b(TBK|TMK|TCK|İK|IK)\s*(?:m\.?|md\.?|madde\s*)?\s*\.?\s*(\d{1,4})\b",
        r"\b(TBK|TMK|TCK|İK|IK)(?:'?(?:nın|nin|nun|nün|na|ne|ya|ye))?\s*(\d{1,4})\.?\s*madd",
    ]

    found: set[str] = set()
    for pattern in patterns:
        for law, article in re.findall(pattern, answer_text, flags=re.IGNORECASE):
            law_u = law.upper().replace("IK", "İK")
            found.add(f"{law_u} m.{int(article)}")
    return sorted(found)


def load_questions(path: Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return data
    return data.get("questions", [])


def result_to_dict(result: QuestionResult) -> dict[str, Any]:
    payload = asdict(result)
    return {key: value for key, value in payload.items() if value is not None}


def build_messages(question_text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question_text},
    ]


def render_prompt(tokenizer, question_text: str) -> str:
    messages = build_messages(question_text)
    apply_chat_template = getattr(tokenizer, "apply_chat_template", None)
    if callable(apply_chat_template):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception as exc:  # pragma: no cover - defensive fallback only
            logger.warning("apply_chat_template fallback: %s", exc)

    return (
        f"Sistem: {SYSTEM_PROMPT}\n\n"
        f"Kullanıcı: {question_text}\n\n"
        "Asistan:"
    )


def resolve_dtype(name: str):
    import torch

    mapping = {
        "auto": None,
        "bf16": torch.bfloat16,
        "fp16": torch.float16,
        "fp32": torch.float32,
    }
    return mapping[name]


def load_model_and_tokenizer(model_path: Path, *, trust_remote_code: bool, dtype: str, device_map: str):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch_dtype = resolve_dtype(dtype)
    tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=trust_remote_code)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        device_map=device_map,
        torch_dtype=torch_dtype,
        trust_remote_code=trust_remote_code,
    )
    model.eval()
    return model, tokenizer


def generate_answer(
    *,
    model,
    tokenizer,
    question_text: str,
    max_new_tokens: int,
    temperature: float,
    repetition_penalty: float,
    max_input_tokens: int,
) -> tuple[str, float]:
    import torch

    prompt = render_prompt(tokenizer, question_text)
    encoded = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_input_tokens,
    )
    encoded = {key: value.to(model.device) for key, value in encoded.items()}

    started = time.perf_counter()
    with torch.no_grad():
        output_ids = model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            repetition_penalty=repetition_penalty,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    elapsed_ms = (time.perf_counter() - started) * 1000

    input_len = encoded["input_ids"].shape[1]
    new_tokens = output_ids[0][input_len:]
    answer_text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    return answer_text, elapsed_ms


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run direct transformers eval")
    parser.add_argument("--model-path", required=True, type=Path, help="Merged/local checkpoint path")
    parser.add_argument("--model", required=True, help="Logical served model name for report metadata")
    parser.add_argument("--output", required=True, type=Path, help="Output report JSON path")
    parser.add_argument("--questions", required=True, type=Path, help="Questions JSON path")
    parser.add_argument("--category", default=None, help="Optional category filter")
    parser.add_argument("--limit", type=int, default=None, help="Optional question limit for diagnostics")
    parser.add_argument("--max-new-tokens", type=int, default=512, help="Generation max_new_tokens")
    parser.add_argument("--max-input-tokens", type=int, default=2048, help="Prompt truncation limit")
    parser.add_argument("--temperature", type=float, default=0.0, help="Generation temperature")
    parser.add_argument("--repetition-penalty", type=float, default=1.0, help="Generation repetition penalty")
    parser.add_argument("--device-map", default="auto", help="Transformers device_map")
    parser.add_argument("--dtype", choices=("auto", "bf16", "fp16", "fp32"), default="bf16")
    parser.add_argument("--trust-remote-code", action="store_true", help="Enable trust_remote_code")
    parser.add_argument("--eval-family", default=None, help="Eval family label to embed in report metadata")
    parser.add_argument("--model-ref", default=None, help="Logical model identifier to embed in report metadata")
    parser.add_argument("--checkpoint-ref", default=None, help="Checkpoint identifier to embed in report metadata")
    parser.add_argument("--git-commit", default=None, help="Git commit to embed in report metadata")
    parser.add_argument(
        "--report-role",
        default="diagnostic_post_train",
        help="Logical report role to embed in report metadata",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if not args.model_path.exists():
        logger.error("Model path not found: %s", args.model_path)
        return 1
    if not args.questions.exists():
        logger.error("Questions file not found: %s", args.questions)
        return 1

    questions = load_questions(args.questions)
    if args.category:
        questions = [question for question in questions if question.get("category") == args.category]
    if args.limit is not None:
        questions = questions[: args.limit]
    if not questions:
        logger.error("No questions to evaluate.")
        return 1

    logger.info(
        "Starting direct transformers eval: model=%s questions=%d path=%s",
        args.model,
        len(questions),
        args.model_path,
    )
    model, tokenizer = load_model_and_tokenizer(
        args.model_path,
        trust_remote_code=bool(args.trust_remote_code),
        dtype=args.dtype,
        device_map=args.device_map,
    )

    results: list[QuestionResult] = []
    started = time.time()

    for idx, question in enumerate(questions, start=1):
        question_id = question.get("id", f"Q{idx}")
        logger.info("[%d/%d] %s", idx, len(questions), question_id)
        try:
            answer_text, elapsed_ms = generate_answer(
                model=model,
                tokenizer=tokenizer,
                question_text=question.get("question", ""),
                max_new_tokens=args.max_new_tokens,
                temperature=args.temperature,
                repetition_penalty=args.repetition_penalty,
                max_input_tokens=args.max_input_tokens,
            )
            cited_sources = extract_citations(answer_text)
            error = None
        except Exception as exc:  # pragma: no cover - exercised only with real model/runtime
            answer_text = ""
            cited_sources = []
            elapsed_ms = 0.0
            error = str(exc)
            logger.warning("  error=%s", error)

        result = compute_metrics(
            question=question,
            answer_text=answer_text,
            cited_sources=cited_sources,
            response_time_ms=elapsed_ms,
            blocked=False,
            verification=None,
            error=error,
        )
        results.append(result)

        if result.error is None:
            logger.info(
                "  citation=%s source=%.2f hall=%s refusal_ok=%s",
                result.has_citation,
                result.correct_source_rate,
                result.is_hallucination,
                result.refusal_correct,
            )

    summary = aggregate_metrics(results)
    report_meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "questions_source": str(args.questions),
        "api_url": f"local://{args.model_path}",
        "mock_mode": False,
        "retrieval_profile": None,
        "model": args.model,
        "model_path": str(args.model_path),
        "max_new_tokens": args.max_new_tokens,
        "planned_questions": len(questions),
        "total_questions": summary.total_questions,
        "error_count": summary.error_count,
        "duration_seconds": round(time.time() - started, 1),
    }
    report_meta.update(
        build_identity_metadata(
            runner="eval_transformers_direct",
            questions_path=args.questions,
            api_url=f"local://{args.model_path}",
            mock_mode=False,
            eval_family=args.eval_family,
            model_ref=args.model_ref,
            checkpoint_ref=args.checkpoint_ref,
            git_commit=args.git_commit,
            report_role=args.report_role,
            model=args.model,
            config_fingerprint={
                "category_filter": args.category,
                "limit": args.limit,
                "max_new_tokens": args.max_new_tokens,
                "max_input_tokens": args.max_input_tokens,
                "temperature": args.temperature,
                "repetition_penalty": args.repetition_penalty,
                "device_map": args.device_map,
                "dtype": args.dtype,
                "trust_remote_code": bool(args.trust_remote_code),
            },
        )
    )

    report = {
        "report_meta": report_meta,
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
        "per_question": [result_to_dict(result) for result in results],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

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
