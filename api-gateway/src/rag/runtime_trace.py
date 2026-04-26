from __future__ import annotations

import hashlib
import json
import os
import re
from itertools import count
from typing import Any

from faz2a_hardening import canonicalize_source_id, dedupe_strings
from release_controls import release_lane_id
from token_accounting import TokenAccountingError, build_text_token_trace

_GENERATION_START_ORDINAL = count(1)
_INLINE_CITATION_RE = re.compile(r"\[Kaynak:\s*([^\]]+)\]")


def _parity_trace_enabled() -> bool:
    return os.getenv("PARITY_TRACE_ENABLED", "false").lower() in {"1", "true", "yes"}


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _canonical_stage_payload(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_stage_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_stage_payload(payload).encode("utf-8")).hexdigest()


def _question_messages_payload(messages: list[Any]) -> list[dict[str, str]]:
    return [{"role": msg.role, "content": msg.content} for msg in messages]


def _request_stage_payload(request_body: Any) -> dict[str, Any]:
    return {
        "model": request_body.model,
        "messages": _question_messages_payload(request_body.messages),
        "stream": request_body.stream,
        "temperature": request_body.temperature,
        "max_tokens": request_body.max_tokens,
        "session_id_present": bool(request_body.session_id),
        "law_filter": request_body.law_filter,
        "use_verification": request_body.use_verification,
        "top_k": request_body.top_k,
        "include_trace": request_body.include_trace,
    }


def _normalized_request_stage_payload(request_body: Any) -> dict[str, Any]:
    return {
        "model": request_body.model,
        "messages": _question_messages_payload(request_body.messages),
        "stream": bool(request_body.stream),
        "temperature": request_body.temperature if request_body.temperature is not None else 0.1,
        "max_tokens": request_body.max_tokens if request_body.max_tokens is not None else 512,
        "law_filter": request_body.law_filter,
        "use_verification": bool(request_body.use_verification),
        "top_k": int(request_body.top_k),
        "include_trace": bool(request_body.include_trace),
    }


def _auth_enriched_stage_payload(
    *,
    request_body: Any,
    request: Any,
) -> dict[str, Any]:
    _ = request
    return _normalized_request_stage_payload(request_body)


def _session_enriched_stage_payload(
    *,
    request_body: Any,
    request: Any,
    session_id: str,
    conversation_history: list[dict[str, str]],
) -> dict[str, Any]:
    payload = _normalized_request_stage_payload(request_body)
    payload.update(
        {
            "session_id_present": bool(session_id),
            "conversation_history": conversation_history,
            "request_id_present": isinstance(getattr(request.state, "request_id", None), str),
            "trace_id_present": isinstance(getattr(request.state, "trace_id", None), str),
        }
    )
    return payload


def _retrieval_input_stage_payload(
    *,
    pre_answer_payload: dict[str, Any],
    law_filter: str | None,
) -> dict[str, Any]:
    return {
        "query": pre_answer_payload.get("retrieval_query"),
        "top_k": pre_answer_payload.get("top_k_effective"),
        "metadata_filter": {"law_short_name": law_filter} if law_filter else None,
        "mentioned_laws": pre_answer_payload.get("mentioned_laws") or [],
        "retrieval_plan": pre_answer_payload.get("retrieval_plan"),
        "explicit_article_refs": pre_answer_payload.get("explicit_article_refs") or [],
        "forced_article_refs": pre_answer_payload.get("forced_article_refs") or [],
        "applied_expansions": pre_answer_payload.get("applied_expansions") or [],
        "reranker_enabled": bool(pre_answer_payload.get("reranker_enabled")),
    }


def _retrieved_source_id_stage_payload(trace_payload: dict[str, Any]) -> dict[str, Any]:
    retrieval = trace_payload.get("retrieval") if isinstance(trace_payload, dict) else {}
    chunks = retrieval.get("post_rerank_chunks") if isinstance(retrieval, dict) else []
    ordered_source_ids: list[str] = []
    if isinstance(chunks, list):
        for item in chunks:
            if not isinstance(item, dict):
                continue
            source_id = item.get("source_id")
            if not isinstance(source_id, str) or not source_id.strip():
                continue
            ordered_source_ids.append(canonicalize_source_id(source_id) or source_id)
    return {
        "ordered_source_id_list": ordered_source_ids,
    }


def _assembly_payload_from_trace(trace_payload: dict[str, Any]) -> dict[str, Any]:
    parsed_query = trace_payload.get("parsed_query") if isinstance(trace_payload, dict) else {}
    context_assembly = trace_payload.get("context_assembly") if isinstance(trace_payload, dict) else {}
    return {
        "query": parsed_query.get("enriched_query") if isinstance(parsed_query, dict) else None,
        "assembled_context": (
            context_assembly.get("assembled_context") if isinstance(context_assembly, dict) else None
        ),
        "allowed_source_whitelist": (
            context_assembly.get("allowed_source_whitelist") if isinstance(context_assembly, dict) else []
        ),
        "assembled_evidence_source_ids": [
            item.get("source_id")
            for item in (context_assembly.get("assembled_evidence") if isinstance(context_assembly, dict) else [])
            if isinstance(item, dict) and item.get("source_id")
        ],
    }


def _context_enriched_stage_payload(
    *,
    request: Any,
    session_id: str,
    conversation_history: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "auth_subject": getattr(request.state, "auth_subject", None),
        "session_id_present": bool(session_id),
        "conversation_history": conversation_history,
        "request_id_present": isinstance(getattr(request.state, "request_id", None), str),
        "trace_id_present": isinstance(getattr(request.state, "trace_id", None), str),
    }


def _source_projection_payload(source_ids: list[str]) -> dict[str, Any]:
    return {
        "ordered_source_id_list": source_ids,
        "ordered_canonical_norm_keys": [canonicalize_source_id(item) or item for item in source_ids],
    }


def _pre_answer_stage_payload(
    *,
    decision_lane: str,
    user_message: str,
    enriched_query: str,
    retrieval_query: str,
    conversation_history: list[dict[str, str]],
    mentioned_laws: list[str],
    requested_source_families: list[str],
    explicit_article_refs: list[tuple[str, str]],
    forced_article_refs: list[tuple[str, str]],
    applied_expansions: list[str],
    top_k_requested: int,
    top_k_effective: int,
    reranker_enabled: bool,
    retrieval_plan: dict[str, Any] | None = None,
    metadata_first_selector: dict[str, Any] | None = None,
    source_identity_reranker: dict[str, Any] | None = None,
    source_cluster_selector: dict[str, Any] | None = None,
    article_span_selector: dict[str, Any] | None = None,
    source_family_resolution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "decision_lane": decision_lane,
        "user_message": user_message,
        "enriched_query": enriched_query,
        "retrieval_query": retrieval_query,
        "conversation_history": conversation_history,
        "mentioned_laws": mentioned_laws,
        "requested_source_families": requested_source_families,
        "explicit_article_refs": explicit_article_refs,
        "forced_article_refs": forced_article_refs,
        "applied_expansions": applied_expansions,
        "retrieval_plan": retrieval_plan,
        "metadata_first_selector": metadata_first_selector,
        "source_identity_reranker": source_identity_reranker,
        "source_cluster_selector": source_cluster_selector,
        "article_span_selector": article_span_selector,
        "source_family_resolution": source_family_resolution,
        "top_k_requested": top_k_requested,
        "top_k_effective": top_k_effective,
        "reranker_enabled": reranker_enabled,
    }


def _raw_answer_stage_payload(
    *,
    raw_answer_object: dict[str, Any] | None,
    fallback_answer_text: str,
) -> dict[str, Any]:
    if isinstance(raw_answer_object, dict) and raw_answer_object:
        return raw_answer_object
    return {
        "role": "assistant",
        "content": fallback_answer_text,
        "bypassed_model": True,
    }


def _extract_answer_source_ids(
    *,
    answer_contract: dict[str, Any] | None,
    citations: list[str],
) -> list[str]:
    source_ids: list[str] = []
    if isinstance(answer_contract, dict):
        primary = answer_contract.get("primary_source_id")
        if isinstance(primary, str) and primary.strip():
            source_ids.append(primary.strip())
        secondary = answer_contract.get("secondary_source_ids")
        if isinstance(secondary, list):
            for item in secondary:
                if isinstance(item, str) and item.strip():
                    source_ids.append(item.strip())
    if source_ids:
        return source_ids
    return [item for item in citations if isinstance(item, str) and item.strip()]


def _visible_projection_stage_payload(
    *,
    answer_text: str,
    citations: list[str],
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
) -> dict[str, Any]:
    source_ids = _extract_answer_source_ids(answer_contract=answer_contract, citations=citations)
    return {
        "final_mode": final_mode,
        "answer_body": answer_text if final_mode != "refusal" else "",
        "refusal_body": answer_text if final_mode == "refusal" else "",
        "refusal_reason": final_reason,
        "ordered_citation_list": list(citations),
        "visible_citation_projection": list(citations),
        **_source_projection_payload(source_ids),
    }


def _extract_inline_citation_ids(answer_text: str) -> list[str]:
    extracted: list[str] = []
    for raw_citation in _INLINE_CITATION_RE.findall(answer_text or ""):
        canonical = canonicalize_source_id(raw_citation)
        if canonical:
            extracted.append(canonical)
    return dedupe_strings(extracted)


def _project_rc_l_guardrails_reasons(
    *,
    answer_text: str,
    citations: list[str],
    guardrails_reasons: list[str],
) -> list[str]:
    projected = dedupe_strings(list(guardrails_reasons))
    if release_lane_id().lower() != "rc_l":
        return projected

    inline_citations = _extract_inline_citation_ids(answer_text)
    visible_citations = dedupe_strings(
        [canonicalize_source_id(citation) or citation for citation in citations]
    )
    if not inline_citations or not visible_citations:
        return projected

    visible_set = set(visible_citations)
    if any(citation not in visible_set for citation in inline_citations):
        projected.append("source_lock_fallback")
    return dedupe_strings(projected)


def _response_envelope_stage_payload(
    *,
    request_body: Any,
    answer_text: str,
    citations: list[str],
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
) -> dict[str, Any]:
    projected_guardrails_reasons = _project_rc_l_guardrails_reasons(
        answer_text=answer_text,
        citations=citations,
        guardrails_reasons=guardrails_reasons,
    )
    return {
        "object": "chat.completion",
        "model": request_body.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer_text},
                "finish_reason": "stop",
            }
        ],
        "citations": list(citations),
        "blocked": blocked,
        "guardrails_reasons": projected_guardrails_reasons,
        "verification": verification,
        "final_mode": final_mode,
        "final_reason": final_reason,
        "answer_contract": answer_contract,
    }


def _eval_client_parsed_stage_payload(
    *,
    answer_text: str,
    citations: list[str],
    blocked: bool,
    verification: dict[str, Any] | None,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
) -> dict[str, Any]:
    return {
        "answer_text": answer_text,
        "citations": list(citations),
        "blocked": blocked,
        "verification": verification,
        "final_mode": final_mode,
        "final_reason": final_reason,
        "answer_contract": answer_contract,
    }


def _normalized_parity_stage_payload(
    *,
    answer_text: str,
    citations: list[str],
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
) -> dict[str, Any]:
    source_ids = _extract_answer_source_ids(answer_contract=answer_contract, citations=citations)
    refusal_reason = None
    if isinstance(answer_contract, dict):
        unsupported_reason = answer_contract.get("unsupported_reason")
        if isinstance(unsupported_reason, str) and unsupported_reason.strip():
            refusal_reason = unsupported_reason
    if refusal_reason is None:
        refusal_reason = final_reason

    return {
        "final_mode": final_mode,
        "answer_body": answer_text if final_mode != "refusal" else "",
        "refusal_body": answer_text if final_mode == "refusal" else "",
        "refusal_reason": refusal_reason,
        "ordered_citation_list": list(citations),
        "ordered_source_id_list": source_ids,
        "ordered_canonical_norm_keys": [canonicalize_source_id(item) or item for item in source_ids],
        "visible_citation_projection": list(citations),
    }


def _append_parity_stage(
    stages: list[dict[str, Any]],
    *,
    stage_name: str,
    payload: dict[str, Any],
) -> None:
    stages.append(
        {
            "stage": stage_name,
            "hash": _hash_stage_payload(payload),
            "payload": payload,
        }
    )


def _v3_parity_topology_label() -> str:
    return (os.getenv("PARITY_TOPOLOGY_LABEL") or "canonical").strip() or "canonical"


def _worker_assignment_stage_payload() -> dict[str, Any]:
    return {
        "topology_label": _v3_parity_topology_label(),
        "process_mode": os.getenv("PARITY_PROCESS_MODE", "shared_process"),
        "fresh_client_per_request": _env_flag("PARITY_FRESH_CLIENT_PER_REQUEST", False),
        "hard_reset_after_request": _env_flag("PARITY_HARD_RESET_AFTER_REQUEST", False),
        "worker_count": int(os.getenv("PARITY_WORKER_COUNT", "1")),
        "pinned_worker_id": os.getenv("PARITY_PINNED_WORKER_ID", "worker-0"),
        "parallelism_enabled": _env_flag("PARITY_PARALLELISM_ENABLED", False),
        "failover_enabled": _env_flag("PARITY_FAILOVER_ENABLED", False),
    }


def _session_namespace_stage_payload(*, request: Any, session_id: str) -> dict[str, Any]:
    base_namespace = os.getenv("SESSION_STORE_NAMESPACE", "hukuk-ai")
    mode = os.getenv("PARITY_SESSION_NAMESPACE_MODE", "canonical")
    namespace = base_namespace
    request_local_suffix = None
    if mode == "fresh_per_request":
        request_local_suffix = "request_id"
        namespace = f"{base_namespace}:<request-local>"
    return {
        "mode": mode,
        "namespace": namespace,
        "request_local_suffix": request_local_suffix,
        "session_id_present": bool(session_id),
    }


def _cache_namespace_stage_payload(*, model_request_payload: dict[str, Any]) -> dict[str, Any]:
    policy = os.getenv("PARITY_GENERATION_CACHE_POLICY", "off")
    namespace = None if policy == "off" else os.getenv("PARITY_GENERATION_CACHE_NAMESPACE", "canonical")
    cache_key = None
    if policy != "off":
        cache_key = _hash_stage_payload(
            {
                "namespace": namespace,
                "model_request_payload": model_request_payload,
            }
        )
    return {
        "policy": policy,
        "namespace": namespace,
        "cache_key": cache_key,
    }


def _generation_start_ordinal_stage_payload() -> dict[str, Any]:
    return {
        "ordinal": next(_GENERATION_START_ORDINAL),
        "request_ordering": os.getenv("PARITY_REQUEST_ORDERING", "serial"),
        "serial_execution": os.getenv("PARITY_REQUEST_ORDERING", "serial") == "serial",
    }


def _raw_generation_hash_payloads(raw_answer_payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    text = raw_answer_payload.get("extracted_text") or raw_answer_payload.get("content") or ""
    try:
        token_trace = build_text_token_trace(text if isinstance(text, str) else str(text))
    except TokenAccountingError as exc:
        token_trace = {
            "source": "error",
            "tokenizer_ref": None,
            "token_count": 0,
            "first_token_id_hash": None,
            "raw_token_stream_hash": None,
            "error": str(exc),
        }
    first_token_payload = {
        "first_token_id_hash": token_trace.get("first_token_id_hash"),
        "source": token_trace.get("source"),
        "tokenizer_ref": token_trace.get("tokenizer_ref"),
        "token_count": token_trace.get("token_count"),
    }
    raw_stream_payload = {
        "raw_token_stream_hash": token_trace.get("raw_token_stream_hash"),
        "source": token_trace.get("source"),
        "tokenizer_ref": token_trace.get("tokenizer_ref"),
        "token_count": token_trace.get("token_count"),
    }
    if token_trace.get("error"):
        first_token_payload["error"] = token_trace["error"]
        raw_stream_payload["error"] = token_trace["error"]
    return first_token_payload, raw_stream_payload


def _build_v3_runtime_parity_trace(
    *,
    request: Any,
    request_body: Any,
    session_id: str,
    answer_text: str,
    citations: list[str],
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
    llm_trace: dict[str, Any] | None,
) -> dict[str, Any]:
    model_request_payload = (llm_trace or {}).get("model_request_payload") or {}
    generation_contract = (llm_trace or {}).get("generation_contract") or {}
    raw_answer_payload = _raw_answer_stage_payload(
        raw_answer_object=(llm_trace or {}).get("raw_answer_object"),
        fallback_answer_text=answer_text,
    )
    first_token_payload, raw_stream_payload = _raw_generation_hash_payloads(raw_answer_payload)

    stages: list[dict[str, Any]] = []
    _append_parity_stage(
        stages,
        stage_name="normalized_request",
        payload=_normalized_request_stage_payload(request_body),
    )
    _append_parity_stage(
        stages,
        stage_name="model_request_payload",
        payload=model_request_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="generation_contract",
        payload=generation_contract,
    )
    _append_parity_stage(
        stages,
        stage_name="worker_assignment_tuple",
        payload=_worker_assignment_stage_payload(),
    )
    _append_parity_stage(
        stages,
        stage_name="session_namespace_after_payload_freeze",
        payload=_session_namespace_stage_payload(request=request, session_id=session_id),
    )
    _append_parity_stage(
        stages,
        stage_name="cache_namespace_or_cache_key",
        payload=_cache_namespace_stage_payload(model_request_payload=model_request_payload),
    )
    _append_parity_stage(
        stages,
        stage_name="generation_start_ordinal",
        payload=_generation_start_ordinal_stage_payload(),
    )
    _append_parity_stage(
        stages,
        stage_name="first_token_id_hash",
        payload=first_token_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="raw_token_stream_hash",
        payload=raw_stream_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="raw_answer_object",
        payload=raw_answer_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="response_envelope",
        payload=_response_envelope_stage_payload(
            request_body=request_body,
            answer_text=answer_text,
            citations=citations,
            blocked=blocked,
            guardrails_reasons=guardrails_reasons,
            verification=verification,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="eval_client_parsed_object",
        payload=_eval_client_parsed_stage_payload(
            answer_text=answer_text,
            citations=citations,
            blocked=blocked,
            verification=verification,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="normalized_parity_object",
        payload=_normalized_parity_stage_payload(
            answer_text=answer_text,
            citations=citations,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )
    return {
        "schema_version": "faz10-v3-runtime-parity-trace-schema-v1",
        "topology_label": _v3_parity_topology_label(),
        "stages": stages,
        "preprojection_hash": stages[9]["hash"],
        "normalized_parity_hash": stages[12]["hash"],
    }


def _attach_parity_trace(
    *,
    trace_payload: dict[str, Any],
    request: Any,
    request_body: Any,
    session_id: str,
    conversation_history: list[dict[str, str]],
    pre_answer_payload: dict[str, Any],
    answer_text: str,
    citations: list[str],
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
    llm_trace: dict[str, Any] | None,
) -> dict[str, Any]:
    if not _parity_trace_enabled():
        return trace_payload

    stages: list[dict[str, Any]] = []
    normalized_request_payload = _normalized_request_stage_payload(request_body)
    _append_parity_stage(
        stages,
        stage_name="raw_input_request",
        payload=_request_stage_payload(request_body),
    )
    _append_parity_stage(
        stages,
        stage_name="normalized_request",
        payload=normalized_request_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="auth_enriched_request",
        payload=_auth_enriched_stage_payload(
            request_body=request_body,
            request=request,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="session_enriched_request",
        payload=_session_enriched_stage_payload(
            request_body=request_body,
            request=request,
            session_id=session_id,
            conversation_history=conversation_history,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="retrieval_input_payload",
        payload=_retrieval_input_stage_payload(
            pre_answer_payload=pre_answer_payload,
            law_filter=request_body.law_filter,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="retrieved_source_id_ordered_list",
        payload=_retrieved_source_id_stage_payload(trace_payload),
    )
    _append_parity_stage(
        stages,
        stage_name="assembly_payload",
        payload=(llm_trace or {}).get("assembly_payload") or _assembly_payload_from_trace(trace_payload),
    )
    _append_parity_stage(
        stages,
        stage_name="model_request_payload",
        payload=(llm_trace or {}).get("model_request_payload") or {},
    )
    _append_parity_stage(
        stages,
        stage_name="generation_contract",
        payload=(llm_trace or {}).get("generation_contract") or {},
    )
    raw_answer_payload = _raw_answer_stage_payload(
        raw_answer_object=(llm_trace or {}).get("raw_answer_object"),
        fallback_answer_text=answer_text,
    )
    _append_parity_stage(
        stages,
        stage_name="raw_answer_object",
        payload=raw_answer_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="response_envelope",
        payload=_response_envelope_stage_payload(
            request_body=request_body,
            answer_text=answer_text,
            citations=citations,
            blocked=blocked,
            guardrails_reasons=guardrails_reasons,
            verification=verification,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="eval_client_parsed_object",
        payload=_eval_client_parsed_stage_payload(
            answer_text=answer_text,
            citations=citations,
            blocked=blocked,
            verification=verification,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="normalized_parity_object",
        payload=_normalized_parity_stage_payload(
            answer_text=answer_text,
            citations=citations,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )

    enriched_trace = dict(trace_payload)
    enriched_trace["parity_trace"] = {
        "stages": stages,
        "preprojection_hash": raw_answer_payload and stages[9]["hash"],
        "normalized_parity_hash": stages[12]["hash"],
    }
    enriched_trace["v3_runtime_parity_trace"] = _build_v3_runtime_parity_trace(
        request=request,
        request_body=request_body,
        session_id=session_id,
        answer_text=answer_text,
        citations=citations,
        blocked=blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
        answer_contract=answer_contract,
        final_mode=final_mode,
        final_reason=final_reason,
        llm_trace=llm_trace,
    )
    return enriched_trace
