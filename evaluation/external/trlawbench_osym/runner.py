from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_DATA_URL = "https://raw.githubusercontent.com/saidsurucu/TRLawBench/main/data/osym_legal_questions.json"
OPTION_KEYS = ("A", "B", "C", "D", "E")
LAW_NUMBER_RE = re.compile(r"\b(?!(?:202[0-9])\b)(\d{3,5})\b")
YEAR_RE = re.compile(r"\b(20\d{2})\b")
FAILURE_BUCKETS = (
    "wrong_option_verified",
    "wrong_option_limited_evidence",
    "blocked_no_choice",
    "retrieval_missing_mevzuat",
    "retrieval_missing_judicial",
    "wrong_legal_rule",
    "source_type_confusion",
    "citation_mismatch",
    "current_law_possible_conflict",
    "non_legal_or_iktisat",
    "llm_reasoning_error",
    "timeout_or_api_error",
    "unparseable",
    "unknown",
)
APP_MODES = {"app_rag_mcq", "app_rag_strict_advisor", "app"}
MCQ_EVIDENCE_STATUSES = {"evidence_used", "limited_evidence", "unsupported_best_effort", "blocked"}


@dataclass(frozen=True)
class PreflightResult:
    passed: bool
    payload: dict[str, Any]
    questions: list[dict[str, Any]]


def str_to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


def load_dataset(*, data_url: str | None, data_path: Path | None) -> tuple[Any, str]:
    if data_path and data_path.exists():
        return json.loads(data_path.read_text(encoding="utf-8")), str(data_path)
    if not data_url:
        raise ValueError("either --data-url or an existing --data-path is required")
    with urllib.request.urlopen(data_url, timeout=30) as response:
        raw = response.read().decode("utf-8")
    if data_path:
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(raw, encoding="utf-8")
    return json.loads(raw), data_url


def preflight_dataset(data: Any) -> PreflightResult:
    failures: list[str] = []
    payload: dict[str, Any] = {
        "valid_json": True,
        "top_level_list": isinstance(data, list),
        "question_count": len(data) if isinstance(data, list) else 0,
        "required_fields": ["id", "question_name", "question", "options", "answer"],
        "missing_fields": [],
        "option_key_deviations": [],
        "invalid_answers": [],
        "duplicate_ids": [],
        "empty_questions": [],
        "empty_options": [],
    }
    if not isinstance(data, list):
        failures.append("top_level_not_list")
        payload["pass"] = False
        payload["failures"] = failures
        return PreflightResult(False, payload, [])

    seen: dict[str, int] = {}
    questions: list[dict[str, Any]] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            failures.append(f"item_not_object:{idx}")
            continue
        qid = str(item.get("id", f"index:{idx}"))
        missing = [field for field in payload["required_fields"] if field not in item]
        if missing:
            payload["missing_fields"].append({"id": qid, "fields": missing})
        seen[qid] = seen.get(qid, 0) + 1
        question = str(item.get("question") or "").strip()
        if not question:
            payload["empty_questions"].append(qid)
        options = item.get("options")
        if not isinstance(options, dict) or not options:
            payload["empty_options"].append(qid)
            option_keys: set[str] = set()
        else:
            option_keys = {str(key).strip().upper() for key in options}
            empty_option_keys = [key for key in OPTION_KEYS if not str(options.get(key, "")).strip()]
            if empty_option_keys:
                payload["empty_options"].append({"id": qid, "keys": empty_option_keys})
        if option_keys != set(OPTION_KEYS):
            payload["option_key_deviations"].append({"id": qid, "keys": sorted(option_keys)})
        answer = str(item.get("answer", "")).strip().upper()
        if answer not in option_keys:
            payload["invalid_answers"].append({"id": qid, "answer": answer})
        if not missing and question and isinstance(options, dict) and answer in option_keys:
            normalized = dict(item)
            normalized["id"] = qid
            normalized["answer"] = answer
            normalized["options"] = {key: str(options.get(key, "")).strip() for key in OPTION_KEYS}
            questions.append(normalized)

    payload["duplicate_ids"] = sorted(qid for qid, count in seen.items() if count > 1)
    for key in ("missing_fields", "invalid_answers", "duplicate_ids", "empty_questions", "empty_options"):
        if payload[key]:
            failures.append(key)
    payload["pass"] = not failures
    payload["failures"] = failures
    return PreflightResult(not failures, payload, questions)


def build_prompt(question: dict[str, Any]) -> str:
    options = question["options"]
    return (
        "Aşağıdaki Türk hukuku çoktan seçmeli sorusunu cevapla.\n\n"
        "Çıktı kuralları:\n"
        "- İlk satır tam olarak şu formatta olmalı: SEÇENEK: <A|B|C|D|E>\n"
        "- İkinci bölümde kısa gerekçe ver.\n"
        "- Gerekçede mevzuat ve varsa yargı kararı kanıtlarını kullan.\n"
        "- Cevap anahtarına erişimin yoktur.\n"
        "- Sadece soru metni, seçenekler ve getirilen hukukî kanıtları kullan.\n"
        "- Kanıt yetersizse yine en iyi hukukî değerlendirmeyle bir seçenek seç, ancak kanıt durumunu belirt.\n"
        "- Kaynak uydurma.\n\n"
        f"Soru adı:\n{question['question_name']}\n\n"
        f"Soru:\n{question['question']}\n\n"
        "Seçenekler:\n"
        f"A) {options['A']}\n"
        f"B) {options['B']}\n"
        f"C) {options['C']}\n"
        f"D) {options['D']}\n"
        f"E) {options['E']}\n"
    )


def build_strict_advisor_prompt(question: dict[str, Any]) -> str:
    options = question["options"]
    return (
        "Aşağıdaki Türk hukuku çoktan seçmeli sorusunu kaynaklı hukuk danışmanı gibi değerlendir.\n\n"
        "Cevap anahtarına erişimin yoktur; yalnızca soru metni, seçenekler ve hukuki kanıtları kullan.\n\n"
        f"Soru adı:\n{question['question_name']}\n\n"
        f"Soru:\n{question['question']}\n\n"
        "Seçenekler:\n"
        f"A) {options['A']}\n"
        f"B) {options['B']}\n"
        f"C) {options['C']}\n"
        f"D) {options['D']}\n"
        f"E) {options['E']}\n"
    )


def _selected_option_from_payload(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    candidates = [
        payload.get("selected_option"),
        payload.get("predicted_answer"),
    ]
    answer_contract = payload.get("answer_contract") if isinstance(payload.get("answer_contract"), dict) else {}
    candidates.extend(
        [
            answer_contract.get("selected_option"),
            answer_contract.get("predicted_answer"),
        ]
    )
    for candidate in candidates:
        value = str(candidate or "").strip().upper()
        if value in OPTION_KEYS:
            return value
    return None


def _parse_success(option: str, method: str, confidence: float = 1.0) -> dict[str, Any]:
    return {
        "predicted_answer": option,
        "answer_parse_method": method,
        "answer_parse_confidence": confidence,
        "unparseable": False,
    }


def _parse_failure(method: str = "unparseable") -> dict[str, Any]:
    return {
        "predicted_answer": None,
        "answer_parse_method": method,
        "answer_parse_confidence": 0.0,
        "unparseable": True,
    }


def extract_selected_option(text: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    first_line = lines[0] if lines else ""
    first_line_match = re.match(r"^SE[ÇC]ENEK\s*:\s*([A-E])\s*$", first_line, re.IGNORECASE)
    if first_line_match:
        return _parse_success(first_line_match.group(1).upper(), "secenek_first_line")

    payload_option = _selected_option_from_payload(payload)
    if payload_option:
        return _parse_success(payload_option, "json_selected_option")

    head = lines[:5]
    exact_candidates: list[tuple[str, str]] = []
    for line in head:
        suffix = r"(?:[\s'’]*(?:dir|dır|dur|dür|tir|tır|tur|tür))?"
        cevap_match = re.match(rf"^CEVAP\s*:\s*([A-E]){suffix}[\s.!]*$", line, re.IGNORECASE)
        if cevap_match:
            exact_candidates.append((cevap_match.group(1).upper(), "cevap_line"))
            continue
        dogru_match = re.match(
            rf"^DO[ĞG]RU\s+SE[ÇC]ENEK\s*:\s*([A-E]){suffix}[\s.!]*$",
            line,
            re.IGNORECASE,
        )
        if dogru_match:
            exact_candidates.append((dogru_match.group(1).upper(), "dogru_secenek_line"))
    distinct_exact = {candidate for candidate, _method in exact_candidates}
    if len(distinct_exact) > 1:
        return _parse_failure("conflicting_choices")
    if exact_candidates:
        option, method = exact_candidates[0]
        return _parse_success(option, method)

    standalone: list[str] = []
    for line in head:
        match = re.match(r"^([A-E])(?:[\).:\-]|$)(?:\s|$)", line, re.IGNORECASE)
        if match:
            standalone.append(match.group(1).upper())
    if len(set(standalone)) == 1 and len(standalone) == 1:
        return _parse_success(standalone[0], "first_standalone_option_marker", 0.5)
    if len(set(standalone)) > 1 or len(standalone) > 1:
        return _parse_failure("conflicting_choices")
    return _parse_failure()


def parse_exam_year(question_name: str) -> int | None:
    match = YEAR_RE.search(question_name or "")
    return int(match.group(1)) if match else None


def classify_question_source(question_name: str) -> str:
    normalized = (question_name or "").lower()
    ascii_normalized = normalized.translate(str.maketrans({"ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u"}))
    if "hmgs" in normalized:
        return "hmgs"
    if "iyös" in normalized or "iyos" in normalized:
        return "iyos"
    if "adalet bakanl" in ascii_normalized:
        return "adalet_bakanligi"
    return "unknown"


def law_numbers_mentioned(question: dict[str, Any]) -> list[str]:
    text = " ".join(
        [
            str(question.get("question_name", "")),
            str(question.get("question", "")),
            " ".join(str(value) for value in (question.get("options") or {}).values()),
        ]
    )
    return sorted(set(LAW_NUMBER_RE.findall(text)))


def classify_domain(question: dict[str, Any]) -> str:
    text = (
        str(question.get("question_name", ""))
        + " "
        + str(question.get("question", ""))
        + " "
        + " ".join(str(value) for value in (question.get("options") or {}).values())
    ).lower()
    rules: list[tuple[str, tuple[str, ...]]] = [
        ("iktisat_or_non_legal", ("iktisat", "fayda", "maliyet", "enflasyon", "arz", "talep")),
        ("ceza_muhakemesi", ("ceza muhakemesi", "5271", "soruşturma", "kovuşturma", "tutukluluk")),
        ("ceza", ("türk ceza", "5237", "suç", "ceza", "kasten", "hapis")),
        ("borçlar", ("borçlar", "6098", "sözleşme", "haksız fiil", "zamanaşımı", "eser sözleşmesi")),
        ("iş", ("iş kanunu", "4857", "sendika", "işçi", "çalışma", "analık")),
        ("ticaret", ("ticaret", "6102", "anonim şirket", "kollektif", "marka")),
        ("icra_iflas", ("icra", "iflas", "haciz", "kambiyo", "istirdat")),
        ("vergi", ("vergi", "213", "mükellef", "tarh")),
        ("anayasa", ("anayasa", "milletvekili", "tbmm", "kanun teklifi")),
        ("idare", ("idari", "idare", "idari yargı")),
        ("medeni", ("medeni", "miras", "eş", "soybağı", "velayet")),
        ("avukatlık", ("avukat", "avukatlık")),
        ("fikri_sınai", ("fikri", "sınai", "marka", "patent", "telif")),
    ]
    for domain, needles in rules:
        if any(needle in text for needle in needles):
            return domain
    return "unknown"


def _compact_excerpt(text: str, limit: int = 500) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _post_json(url: str, payload: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_stream(url: str, payload: dict[str, Any], timeout_seconds: float) -> tuple[str, dict[str, Any]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    answer_parts: list[str] = []
    metadata: dict[str, Any] = {}
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            item = line.removeprefix("data: ")
            if item == "[DONE]":
                break
            payload_item = json.loads(item)
            if payload_item.get("object") == "chat.completion.metadata":
                metadata = payload_item
            else:
                choices = payload_item.get("choices") or []
                if choices:
                    answer_parts.append(str((choices[0].get("delta") or {}).get("content") or ""))
    return "".join(answer_parts), metadata


def fetch_health(api_base: str, timeout_seconds: float) -> dict[str, Any]:
    request = urllib.request.Request(api_base.rstrip("/") + "/v1/health", method="GET")
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _source_types(source_cards: list[dict[str, Any]]) -> list[str]:
    return sorted({str(card.get("source_type") or card.get("type") or "") for card in source_cards if card})


def _retrieval_lanes(payload: dict[str, Any], source_cards: list[dict[str, Any]]) -> list[str]:
    lanes = set(str(item) for item in payload.get("retrieval_lanes") or [] if item)
    for card in source_cards:
        lane = card.get("retrieval_lane")
        if lane:
            lanes.add(str(lane))
    return sorted(lanes)


def _current_law_state_present(source_cards: list[dict[str, Any]]) -> bool:
    state_keys = ("current", "effective", "valid", "end_date", "start_date", "yururluk", "state")
    for card in source_cards:
        metadata = card.get("metadata") if isinstance(card.get("metadata"), dict) else {}
        merged = {**card, **metadata}
        if any(key in str(candidate).lower() for candidate in merged for key in state_keys):
            return True
    return False


def _choice_evidence_status(payload: dict[str, Any], answer_text: str) -> str | None:
    answer_contract = payload.get("answer_contract") if isinstance(payload.get("answer_contract"), dict) else {}
    candidates = [
        payload.get("choice_evidence_status"),
        payload.get("evidence_status"),
        answer_contract.get("choice_evidence_status"),
        answer_contract.get("evidence_status"),
    ]
    for candidate in candidates:
        value = str(candidate or "").strip().lower()
        if value in MCQ_EVIDENCE_STATUSES:
            return value
    match = re.search(r"(?im)^KAYNAK\s+DURUMU\s*:\s*([a-z_]+)\s*$", answer_text)
    if match and match.group(1).lower() in MCQ_EVIDENCE_STATUSES:
        return match.group(1).lower()
    return None


def _mcq_outcome(row: dict[str, Any]) -> str:
    if row.get("error_type"):
        return "api_error"
    if row.get("blocked") and not row.get("predicted_answer"):
        return "blocked_no_choice"
    if row.get("unparseable"):
        return "unparseable"
    status = str(row.get("choice_evidence_status") or "")
    if status == "evidence_used" and row.get("verification_status") == "pass":
        return "verified_choice"
    if status == "limited_evidence":
        return "limited_evidence_choice"
    if status == "blocked" and row.get("blocked"):
        return "blocked_no_choice"
    return "unsupported_best_effort_choice"


def _failure_bucket(row: dict[str, Any]) -> str:
    if row.get("error_type"):
        return "timeout_or_api_error" if "timeout" in row["error_type"] or "url" in row["error_type"] else "unknown"
    if row.get("mcq_outcome") == "blocked_no_choice":
        return "blocked_no_choice"
    if row.get("unparseable"):
        return "unparseable"
    if row.get("is_correct") is True:
        return "none"
    if row.get("domain") == "iktisat_or_non_legal":
        return "non_legal_or_iktisat"
    if row.get("mcq_outcome") == "verified_choice":
        return "wrong_option_verified"
    if row.get("mcq_outcome") in {"limited_evidence_choice", "unsupported_best_effort_choice"}:
        return "wrong_option_limited_evidence"
    if row.get("source_card_count", 0) == 0:
        if any("judicial" in lane or "yargi" in lane for lane in row.get("retrieval_lanes") or []):
            return "retrieval_missing_judicial"
        return "retrieval_missing_mevzuat"
    if row.get("source_type_confusion"):
        return "source_type_confusion"
    if row.get("verification_status") == "fail":
        return "citation_mismatch"
    if row.get("possible_current_law_conflict"):
        return "current_law_possible_conflict"
    if row.get("source_card_count", 0) > 0 and row.get("is_correct") is False:
        return "wrong_legal_rule"
    return "llm_reasoning_error"


def run_question(
    question: dict[str, Any],
    *,
    api_base: str,
    llm_base: str | None,
    model: str,
    mode: str,
    streaming: bool,
    judicial_enabled: bool,
    temperature: float,
    timeout_seconds: float,
) -> dict[str, Any]:
    prompt = build_strict_advisor_prompt(question) if mode in {"app", "app_rag_strict_advisor"} else build_prompt(question)
    request_payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": streaming,
        "temperature": temperature,
        "include_trace": mode in APP_MODES,
    }
    if mode == "app_rag_mcq":
        request_payload["legal_task_type"] = "multiple_choice"
    started = time.perf_counter()
    error_type: str | None = None
    payload: dict[str, Any] = {}
    answer_text = ""
    try:
        if mode == "llm_direct_mcq":
            if not llm_base:
                raise ValueError("--llm-base or DGX_BASE_URL is required for llm_direct_mcq")
            url = llm_base.rstrip("/") + "/chat/completions"
            direct_payload = dict(request_payload)
            direct_payload["stream"] = False
            direct_payload["messages"] = [
                {
                    "role": "system",
                    "content": (
                        "Türk hukuku çoktan seçmeli sınav sorularını cevapla. "
                        "İlk satır tam olarak SEÇENEK: <A|B|C|D|E> olsun. "
                        "Cevap anahtarına erişimin yoktur."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            payload = _post_json(url, direct_payload, timeout_seconds)
            choices = payload.get("choices") or []
            if choices:
                answer_text = str(((choices[0].get("message") or {}).get("content")) or "")
        else:
            url = api_base.rstrip("/") + "/v1/chat/completions"
            if streaming:
                answer_text, metadata = _post_stream(url, request_payload, timeout_seconds)
                payload = dict(metadata)
                payload.setdefault("choices", [{"message": {"content": answer_text}}])
            else:
                payload = _post_json(url, request_payload, timeout_seconds)
                choices = payload.get("choices") or []
                if choices:
                    answer_text = str(((choices[0].get("message") or {}).get("content")) or "")
    except TimeoutError:
        error_type = "timeout"
    except urllib.error.URLError as exc:
        error_type = f"url_error:{exc.__class__.__name__}"
    except Exception as exc:  # noqa: BLE001 - compact benchmark error capture.
        error_type = f"api_error:{exc.__class__.__name__}"
    latency_ms = round((time.perf_counter() - started) * 1000, 3)

    parsed = extract_selected_option(answer_text, payload)
    expected = str(question.get("answer", "")).upper()
    source_cards = payload.get("source_cards") if isinstance(payload.get("source_cards"), list) else []
    source_types = _source_types(source_cards)
    final_reason = payload.get("final_reason")
    choice_evidence_status = _choice_evidence_status(payload, answer_text)
    blocked = bool(payload.get("blocked", False))
    if blocked and parsed["unparseable"]:
        parsed = {**parsed, "unparseable": False, "answer_parse_method": "blocked_no_choice"}
    current_law_metadata = _current_law_state_present(source_cards)
    verification = payload.get("verification") if isinstance(payload.get("verification"), dict) else {}
    answer_contract = payload.get("answer_contract") if isinstance(payload.get("answer_contract"), dict) else {}
    verification_metadata = (
        answer_contract.get("verification_metadata")
        if isinstance(answer_contract.get("verification_metadata"), dict)
        else {}
    )
    blocked_due_to_stale_or_unsupported = bool(
        payload.get("blocked") and final_reason and re.search(r"stale|current|unsupported|evidence", str(final_reason), re.I)
    )
    possible_current_law_conflict = bool(current_law_metadata or blocked_due_to_stale_or_unsupported)
    row: dict[str, Any] = {
        "id": question["id"],
        "question_name": question["question_name"],
        "exam_year": parse_exam_year(str(question.get("question_name", ""))),
        "question_source": classify_question_source(str(question.get("question_name", ""))),
        "domain": classify_domain(question),
        "law_numbers_mentioned": law_numbers_mentioned(question),
        "expected_answer": expected,
        "predicted_answer": parsed["predicted_answer"],
        "is_correct": (parsed["predicted_answer"] == expected if not blocked and not parsed["unparseable"] else False),
        "answer_parse_method": parsed["answer_parse_method"],
        "answer_parse_confidence": parsed["answer_parse_confidence"],
        "unparseable": parsed["unparseable"],
        "raw_answer_excerpt": _compact_excerpt(answer_text),
        "blocked": blocked,
        "final_reason": final_reason,
        "legal_rag_runtime_mode": payload.get("legal_rag_runtime_mode"),
        "judicial_runtime_enabled": payload.get("judicial_runtime_enabled", judicial_enabled),
        "judicial_ready": payload.get("judicial_ready"),
        "verification_status": payload.get("verification_status"),
        "choice_evidence_status": choice_evidence_status,
        "source_card_count": len(source_cards),
        "source_types_used": source_types,
        "retrieval_lanes": _retrieval_lanes(payload, source_cards),
        "current_law_state_metadata_present": current_law_metadata,
        "possible_current_law_conflict": possible_current_law_conflict,
        "source_type_confusion": bool(
            verification.get("source_type_confusion") or verification_metadata.get("source_type_confusion")
        ),
        "review_needed": False,
        "runtime_mode": mode,
        "latency_ms": latency_ms,
        "error_type": error_type,
    }
    row["mcq_outcome"] = _mcq_outcome(row)
    row["failure_bucket"] = _failure_bucket(row)
    row["review_needed"] = bool(
        row["error_type"]
        or row["blocked"]
        or row["unparseable"]
        or row["possible_current_law_conflict"]
        or row["is_correct"] is False
    )
    return row


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return round(ordered[index], 3)


def _accuracy_group(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(key) or "unknown"), []).append(row)
    return {
        group: {
            "count": len(items),
            "correct": sum(1 for item in items if item.get("is_correct") is True),
            "accuracy": _rate(sum(1 for item in items if item.get("is_correct") is True), len(items)),
        }
        for group, items in sorted(grouped.items())
    }


def build_summary(
    rows: list[dict[str, Any]],
    *,
    dataset_count: int,
    mode: str = "app_rag_mcq",
    health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    attempted = len(rows)
    correct = sum(1 for row in rows if row.get("is_correct") is True)
    unparseable = sum(1 for row in rows if row.get("unparseable"))
    blocked = sum(1 for row in rows if row.get("blocked"))
    latencies = [float(row["latency_ms"]) for row in rows if row.get("latency_ms") is not None and not row.get("error_type")]
    verification_known = [row for row in rows if row.get("verification_status")]
    source_present = sum(1 for row in rows if int(row.get("source_card_count") or 0) > 0)
    legislation_usage = sum(1 for row in rows if any(t in {"mevzuat", "legislation"} for t in row.get("source_types_used") or []))
    judicial_usage = sum(1 for row in rows if any("judicial" in t or "yargi" in t for t in row.get("source_types_used") or []))
    mixed_usage = sum(
        1
        for row in rows
        if any(t in {"mevzuat", "legislation"} for t in row.get("source_types_used") or [])
        and any("judicial" in t or "yargi" in t for t in row.get("source_types_used") or [])
    )
    buckets: dict[str, int] = {bucket: 0 for bucket in FAILURE_BUCKETS}
    for row in rows:
        bucket = str(row.get("failure_bucket") or "unknown")
        if bucket != "none":
            buckets[bucket if bucket in buckets else "unknown"] += 1
    return {
        "mode": mode,
        "dataset_count": dataset_count,
        "attempted_count": attempted,
        "correct_count": correct,
        "incorrect_count": attempted - correct,
        "unparseable_count": unparseable,
        "blocked_count": blocked,
        "raw_accuracy": _rate(correct, attempted),
        "raw_accuracy_against_answer_key": _rate(correct, attempted),
        "accuracy_by_domain": _accuracy_group(rows, "domain"),
        "accuracy_by_exam_year": _accuracy_group(rows, "exam_year"),
        "accuracy_by_question_source": _accuracy_group(rows, "question_source"),
        "accuracy_by_runtime_mode": _accuracy_group(rows, "runtime_mode"),
        "average_latency_ms": round(statistics.fmean(latencies), 3) if latencies else None,
        "p50_latency_ms": _percentile(latencies, 0.50),
        "p95_latency_ms": _percentile(latencies, 0.95),
        "verification_pass_rate": _rate(sum(1 for row in verification_known if row.get("verification_status") == "pass"), len(verification_known)),
        "source_card_presence_rate": _rate(source_present, attempted),
        "legislation_source_usage_rate": _rate(legislation_usage, attempted),
        "judicial_source_usage_rate": _rate(judicial_usage, attempted),
        "mixed_source_usage_rate": _rate(mixed_usage, attempted),
        "limited_evidence_count": sum(1 for row in rows if row.get("choice_evidence_status") == "limited_evidence"),
        "unsupported_best_effort_count": sum(
            1 for row in rows if row.get("choice_evidence_status") == "unsupported_best_effort"
        ),
        "possible_current_law_conflict_count": sum(1 for row in rows if row.get("possible_current_law_conflict")),
        "manual_review_ids": [
            row.get("id")
            for row in rows
            if row.get("review_needed") or row.get("possible_current_law_conflict") or row.get("blocked")
        ],
        "review_needed_count": sum(1 for row in rows if row.get("review_needed")),
        "failure_buckets": dict(sorted(buckets.items(), key=lambda item: (-item[1], item[0]))),
        "health": health or {},
    }


def _select_questions(questions: list[dict[str, Any]], *, ids: str | None, limit: int | None) -> list[dict[str, Any]]:
    selected = questions
    if ids:
        wanted = {item.strip() for item in ids.split(",") if item.strip()}
        selected = [question for question in selected if str(question["id"]) in wanted]
    if limit is not None:
        selected = selected[: max(0, limit)]
    return selected


def run_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data, source = load_dataset(data_url=args.data_url, data_path=Path(args.data_path) if args.data_path else None)
    preflight = preflight_dataset(data)
    preflight_payload = dict(preflight.payload)
    preflight_payload["source"] = source
    (output_dir / "preflight.json").write_text(
        json.dumps(preflight_payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    if not preflight.passed:
        raise SystemExit("dataset preflight failed")

    selected = _select_questions(preflight.questions, ids=args.ids, limit=args.limit)
    health: dict[str, Any] | None = None
    if args.mode in APP_MODES:
        health = fetch_health(args.api_base, args.timeout_seconds)
        expected_judicial = bool(args.judicial_enabled)
        actual_judicial = bool(health.get("judicial_runtime_enabled"))
        if actual_judicial != expected_judicial:
            raise SystemExit(
                f"API judicial_runtime_enabled={actual_judicial} does not match --judicial-enabled={expected_judicial}"
            )
        if expected_judicial and not health.get("judicial_ready"):
            raise SystemExit("API judicial runtime is enabled but not ready")

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.max_concurrency)) as executor:
        futures = [
            executor.submit(
                run_question,
                question,
                api_base=args.api_base,
                llm_base=args.llm_base or os.getenv("DGX_BASE_URL"),
                model=args.model,
                mode=args.mode,
                streaming=args.streaming,
                judicial_enabled=args.judicial_enabled,
                temperature=args.temperature,
                timeout_seconds=args.timeout_seconds,
            )
            for question in selected
        ]
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: int(row["id"]) if str(row["id"]).isdigit() else str(row["id"]))

    with (output_dir / "results.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    summary = build_summary(rows, dataset_count=preflight.payload["question_count"], mode=args.mode, health=health)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Hukuk-AI against TRLawBench OSYM questions.")
    parser.add_argument("--data-url", default=DEFAULT_DATA_URL)
    parser.add_argument("--data-path", default=None)
    parser.add_argument("--output-dir", default=".local_eval/trlawbench_osym")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--llm-base", default=None)
    parser.add_argument("--model", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--ids", default=None)
    parser.add_argument(
        "--mode",
        choices=["app_rag_mcq", "app_rag_strict_advisor", "llm_direct_mcq", "app"],
        default="app_rag_mcq",
    )
    parser.add_argument("--streaming", type=str_to_bool, default=False)
    parser.add_argument("--judicial-enabled", type=str_to_bool, default=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-concurrency", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_benchmark(args)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
