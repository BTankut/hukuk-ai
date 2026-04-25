from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


_TR_ASCII_TRANS = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
    }
)


def _dedupe(values: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def normalize_slot_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip().casefold().translate(_TR_ASCII_TRANS)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _contains_any(normalized_query: str, terms: tuple[str, ...]) -> bool:
    return any(term in normalized_query for term in terms)


@lru_cache(maxsize=1)
def load_required_slot_matrix() -> dict[str, Any]:
    path = Path(__file__).with_name("required_slot_matrix.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _task_type_from_template(answer_template: str) -> str:
    template = str(answer_template or "").strip()
    if template == "procedure":
        return "compliance_checklist"
    if template == "exception":
        return "exception_analysis"
    if template == "condition":
        return "scenario_applicability"
    if template == "comparison_or_temporal":
        return "temporal_validity"
    return "precise_retrieval"


def _query_matrix_slots(query: str) -> list[str]:
    normalized = normalize_slot_text(query)
    slots: list[str] = []
    if _contains_any(
        normalized,
        (
            "hangi mevzuat",
            "hangi duzenleme",
            "hangi belge",
            "hangi kaynak",
            "tuzuk",
            "yonetmelik",
            "teblig",
            "karar",
            "genelge",
            "kararname",
        ),
    ):
        slots.extend(["selected_primary_source", "identifier", "why_this_source"])
    if _contains_any(normalized, ("madde", "fikra", "bent", "paragraf", "hukum")):
        slots.append("article_or_span")
    if _contains_any(normalized, ("istisna", "muaf", "haric", "sakli", "uygulanmaz")):
        slots.append("exception_or_limitation")
    if _contains_any(normalized, ("kosul", "sart", "hangi hallerde", "aranir", "gerekir")):
        slots.append("facts_applied")
    if _contains_any(normalized, ("yeterli midir", "yeterli mi", "tescil", "ilan", "noter", "noterce")):
        slots.extend(["facts_applied", "procedure"])
    if _contains_any(
        normalized,
        (
            "guncel",
            "guncellik",
            "hala",
            "halen yururlukte",
            "yururlukte mi",
            "yururluk",
            "mulga",
            "eski",
            "gecici",
            "son durum",
            "ne zaman yururluge",
            "dogrudan uygulan",
            "dogrudan hukum",
            "guvenli midir",
            "riskli",
            "hatali",
        ),
    ):
        slots.extend(["effective_state", "effective_period"])
    if query_needs_historical_transition_slots(normalized):
        slots.extend(
            [
                "source_is_repealed_or_historical",
                "applicable_period",
                "current_applicability",
                "replacement_or_current_law_relation",
                "transition_rule",
            ]
        )
    elif query_needs_current_applicability_slot(normalized):
        slots.append("current_applicability")
    if _contains_any(
        normalized,
        (
            "ust norm",
            "alt norm",
            "kanun mu",
            "yonetmelik mi",
            "hangisi uygulanir",
            "normlar hiyerarsisi",
            "kanuna aykiri",
        ),
    ) or (
        "yoksa" in normalized
        and _contains_any(normalized, ("kanun", "yonetmelik", "teblig", "tuzuk", "genelge", "karar"))
    ):
        slots.extend(["conflict_rule", "applicable_priority"])
    return _dedupe(slots)


def query_needs_historical_transition_slots(normalized_query: str) -> bool:
    historical_or_repealed = _contains_any(
        normalized_query,
        (
            "mulga",
            "mülga",
            "ilga",
            "yururlukten kaldir",
            "yururlukten kalk",
            "eski metin",
            "eski khk",
            "eski tuzuk",
            "eski tüzük",
            "eski yonetmelik",
            "eski yönetmelik",
            "eski yonetmeligi",
            "eski yönetmeliği",
            "eski duzenleme",
            "eski düzenleme",
            "onceki duzenleme",
            "tarihsel",
            "o tarihte",
            "gecis hukmu",
            "gecici madde",
            "yerine gecen",
            "yerini alan",
        ),
    )
    direct_risk = _contains_any(
        normalized_query,
        (
            "dogrudan uygulan",
            "dogrudan hukum",
            "esas almak",
            "guvenli midir",
            "riskli",
            "hatali",
            "hata",
            "guncellik hatasi",
        ),
    )
    historical_year = bool(re.search(r"(?<!\d)(?:19\d{2}|200\d|201\d)(?!\d)", normalized_query))
    return bool(historical_or_repealed or (historical_year and direct_risk))


def query_needs_current_applicability_slot(normalized_query: str) -> bool:
    return _contains_any(
        normalized_query,
        (
            "bugun",
            "guncel",
            "guncellik",
            "halen",
            "hala",
            "yururlukte mi",
            "gecerli mi",
            "son durum",
            "2026'da dogrudan",
            "2026 da dogrudan",
        ),
    )


def _family_matrix_slots(source_families: list[str] | tuple[str, ...] | set[str] | None) -> tuple[list[str], list[str]]:
    matrix = load_required_slot_matrix()
    requested = {normalize_slot_text(family) for family in (source_families or []) if str(family or "").strip()}
    labels: list[str] = []
    slots: list[str] = []
    if not requested:
        return labels, slots
    for label, config in (matrix.get("family_specific") or {}).items():
        aliases = {normalize_slot_text(alias) for alias in config.get("families") or []}
        if requested & aliases:
            labels.append(str(label))
            slots.extend(str(slot) for slot in config.get("required_slots") or [])
    return _dedupe(labels), _dedupe(slots)


def runtime_slots_for_matrix_slot(matrix_slot: str) -> list[str]:
    matrix = load_required_slot_matrix()
    runtime_map = matrix.get("runtime_slot_map") or {}
    mapped = runtime_map.get(str(matrix_slot or ""))
    if isinstance(mapped, list):
        return _dedupe([str(item) for item in mapped])
    if isinstance(mapped, str):
        return [mapped]
    return []


def _runtime_slots_for_matrix_slots(matrix_slots: list[str]) -> list[str]:
    runtime_slots: list[str] = []
    for slot in matrix_slots:
        runtime_slots.extend(runtime_slots_for_matrix_slot(slot))
    return _dedupe(runtime_slots)


@dataclass(frozen=True)
class RequiredSlotResolution:
    matrix_version: str
    task_type: str
    answer_template: str
    source_families: list[str]
    family_labels: list[str]
    task_slots: list[str]
    family_slots: list[str]
    query_slots: list[str]
    matrix_slots: list[str]
    runtime_slots: list[str]
    critical_slots: list[str]
    resolution_reason: list[str]

    def to_trace_dict(self) -> dict[str, Any]:
        return {
            "required_slot_matrix_version": self.matrix_version,
            "required_slot_task_type": self.task_type,
            "required_slot_answer_template": self.answer_template,
            "required_slot_source_families": self.source_families,
            "required_slot_family_labels": self.family_labels,
            "required_slot_task_slots": self.task_slots,
            "required_slot_family_additions": self.family_slots,
            "required_slot_query_additions": self.query_slots,
            "required_slot_matrix_slots": self.matrix_slots,
            "required_slot_runtime_slots": self.runtime_slots,
            "required_slot_critical_slots": self.critical_slots,
            "required_slot_resolution_reason": self.resolution_reason,
        }


def resolve_required_slot_matrix(
    *,
    query: str,
    answer_template: str,
    source_families: list[str] | tuple[str, ...] | set[str] | None = None,
    task_type: str | None = None,
) -> RequiredSlotResolution:
    matrix = load_required_slot_matrix()
    resolved_task_type = str(task_type or "").strip() or _task_type_from_template(answer_template)
    task_config = (matrix.get("task_types") or {}).get(resolved_task_type) or {}
    task_slots = [str(slot) for slot in task_config.get("required_slots") or []]
    family_labels, family_slots = _family_matrix_slots(source_families)
    query_slots = _query_matrix_slots(query)
    matrix_slots = _dedupe([*task_slots, *family_slots, *query_slots])
    runtime_slots = _runtime_slots_for_matrix_slots(matrix_slots)

    # Preserve the Phase 17 runtime contract: every answer must expose a direct
    # conclusion and a governing source even when the matrix is only advisory.
    runtime_slots = _dedupe(["result_or_holding", "governing_source", *runtime_slots])
    critical_config = {str(slot) for slot in matrix.get("critical_runtime_slots") or []}
    critical_slots = [slot for slot in runtime_slots if slot in critical_config]

    reasons = [f"task_type:{resolved_task_type}"]
    if family_labels:
        reasons.append("family_additions:" + ",".join(family_labels))
    if query_slots:
        reasons.append("query_additions")

    return RequiredSlotResolution(
        matrix_version=str(matrix.get("version") or "unknown"),
        task_type=resolved_task_type,
        answer_template=str(answer_template or ""),
        source_families=_dedupe([normalize_slot_text(family) for family in (source_families or [])]),
        family_labels=family_labels,
        task_slots=_dedupe(task_slots),
        family_slots=family_slots,
        query_slots=query_slots,
        matrix_slots=matrix_slots,
        runtime_slots=runtime_slots,
        critical_slots=critical_slots,
        resolution_reason=reasons,
    )
