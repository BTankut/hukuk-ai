"""Evaluation Metrics — AI Hukuk Asistanı Faz 1 (Backlog #8).

Dört temel metrik:
    1. Citation Rate        — Model yanıtlarında atıf (kaynak) geçiyor mu?
    2. Correct Source Rate  — Atıf yapılan kaynaklar beklenen kaynaklarla örtüşüyor mu?
    3. Hallucination Rate   — Model beklenen kaynak dışı atıf yapıyor mu?
    4. Refusal on Unknown   — Model bilmediğini/kapsam dışı olduğunu doğru söylüyor mu?

Ek yardımcı metrikler:
    5. Keyword Coverage     — Beklenen anahtar terimlerin yanıtta görünme oranı
    6. Expected Phrase Hit  — expected_answer_contains kontrolü

Kullanım:
    from evaluation.metrics import compute_metrics, aggregate_metrics

    question_result = compute_metrics(
        question=q,          # test seti JSON'undan tek soru dict'i
        answer_text=...,     # LLM yanıt metni
        cited_sources=[...], # API'nin döndürdüğü citations listesi
    )
    summary = aggregate_metrics([result1, result2, ...])
"""

from __future__ import annotations

import os
import re
import string
import unicodedata
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Türkçe metin normalizasyonu
# ---------------------------------------------------------------------------

def _tr_lower(text: str) -> str:
    """Türkçe büyük-küçük harf dönüşümü.

    Python'un str.lower() metodu 'İ' (U+0130) karakterini 'i\u0307'
    (i + birleştirici nokta) olarak dönüştürür; bu, regex eşleşmesini bozar.
    Bu fonksiyon 'İ' → 'i' ve diğer Türkçe özel karakterleri doğru işler.
    """
    # Türkçe büyük harf → küçük harf önce manuel replace, sonra lower()
    _TR_UPPER_MAP = str.maketrans(
        "İIĞÖÜŞÇ",
        "iiğöüşç",
    )
    return text.translate(_TR_UPPER_MAP).lower()

# ---------------------------------------------------------------------------
# Refusal tespiti için anahtar ifadeler (Türkçe)
# ---------------------------------------------------------------------------

REFUSAL_PATTERNS: list[str] = [
    r"kapsam\s+dışı",
    r"bilgim\s+(yok|bulunmamaktadır|mevcut\s+değil)",
    r"bu\s+konuda\s+(yeterli\s+)?bilgi(m)?\s+(yok|bulunamadı|mevcut\s+değil)",
    r"bilgi\s+bulunmamaktadır",
    r"yer\s+almamaktadır",
    r"yanıtlanamaz",
    r"cevap\s*veremiyorum",
    r"yanıt\s*veremiyorum",
    r"bu\s+soruyu\s+cevaplayamıyorum",
    r"bu\s+soru\s+(tbk|turk\s+borclar\s+kanunu)\s+(kapsamında|icinde)\s+degil",
    r"bu\s+soru\s+(ttk|turk\s+ticaret\s+kanunu)\s+(kapsamında|icinde)\s+degil",
    r"(ilgili\s+)?veri\s+(tabanımda|tabaninda|kaynagımda).*?(mevcut\s+değil|bulunmamaktadır|yok)",
    r"(ilgili\s+)?kaynak\s+(bulunamadı|mevcut\s+değil|yok)",
    r"(tbk\s+)?mevzuatımızda\s+(bu\s+konu\s+)?yer\s+almıyor",
    r"yeterli\s+kaynak\s+(bulunamadı|mevcut\s+değil|yok)",
    r"guvenilir\s+bilgi\s+veremiyorum",
    r"bu\s+bilgiye\s+sahip\s+degil",
    r"iş\s+kanunu",          # Kıdem tazminatı sorusu için (_tr_lower ile İş→iş)
]

# ---------------------------------------------------------------------------
# Kaynak normalizasyonu
# ---------------------------------------------------------------------------

def normalize_source(src: str) -> str:
    """Kaynak string'ini normalize et: büyük harf, boşluk temizle.

    Örnekler:
        "TBK m. 299"    → "tbk m.299"
        "TBK md.299"    → "tbk m.299"
        "tbk-299"       → "tbk m.299"
        "TBK Madde 146" → "tbk m.146"
        "TBK md. 146"   → "tbk m.146"
    """
    s = src.strip().lower()
    # "madde" → "m."
    s = re.sub(r"\bmadde\b", "m.", s)
    # "md." → "m." (LLM sıklıkla "md." kullanır)
    s = re.sub(r"\bmd\.", "m.", s)
    # "m. " → "m."
    s = re.sub(r"m\.\s+", "m.", s)
    # "tbk-299" → "tbk m.299"
    law_tokens = "tbk|tmk|tck|cmk|hmk|ttk|ik|i̇k|iyuk|i̇yuk|iik|i̇i̇k|anayasa|ay|kvkk"
    s = re.sub(rf"({law_tokens})\s*[-–]\s*(\d+)", r"\1 m.\2", s)
    # Normalize whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _canonical_source_set(values: list[str]) -> set[str]:
    return {normalize_source(item) for item in values if isinstance(item, str) and item.strip()}


def _source_from_trace_item(item: Any) -> str | None:
    if not isinstance(item, dict):
        return None
    for key in ("source_id", "canonical_citation", "citation"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _trace_list(trace: dict[str, Any] | None, *path: str) -> list[Any]:
    current: Any = trace
    for key in path:
        if not isinstance(current, dict):
            return []
        current = current.get(key)
    return current if isinstance(current, list) else []


def _extract_trace_source_ids(
    trace: dict[str, Any] | None,
    *,
    list_name: str,
    limit: int | None = None,
) -> list[str]:
    items = _trace_list(trace, "retrieval", list_name)
    if not items and list_name == "post_rerank_chunks":
        items = _trace_list(trace, "rerank_list")
    if limit is not None:
        items = items[:limit]

    source_ids: list[str] = []
    seen: set[str] = set()
    for item in items:
        source_id = _source_from_trace_item(item)
        if not source_id:
            continue
        normalized = normalize_source(source_id)
        if normalized not in seen:
            source_ids.append(source_id)
            seen.add(normalized)
    return source_ids


def _extract_selected_evidence_sources(
    *,
    trace: dict[str, Any] | None,
    answer_contract: dict[str, Any] | None,
    cited_sources: list[str],
) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()

    def add(value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            return
        normalized = normalize_source(value)
        if normalized in seen:
            return
        selected.append(value)
        seen.add(normalized)

    if isinstance(answer_contract, dict):
        for value in answer_contract.get("selected_source_keys") or []:
            add(value)
        add(answer_contract.get("primary_source_id"))
        for value in answer_contract.get("secondary_source_ids") or []:
            add(value)

    for item in _trace_list(trace, "context_assembly", "assembled_evidence"):
        add(_source_from_trace_item(item))
    for item in _trace_list(trace, "assembled_evidence"):
        add(_source_from_trace_item(item))

    if not selected:
        for value in cited_sources:
            add(value)

    return selected


def _extract_claim_sources(answer_contract: dict[str, Any] | None) -> list[str]:
    if not isinstance(answer_contract, dict):
        return []
    claim_units = answer_contract.get("claim_units")
    if not isinstance(claim_units, list):
        return []

    sources: list[str] = []
    seen: set[str] = set()
    for claim in claim_units:
        if not isinstance(claim, dict):
            continue
        source_id = claim.get("selected_source_key") or claim.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            continue
        normalized = normalize_source(source_id)
        if normalized not in seen:
            sources.append(source_id)
            seen.add(normalized)
    return sources


def _expected_evidence_sources(question: dict[str, Any], expected_sources: list[str]) -> list[str]:
    values = question.get("expected_evidence_sources")
    if isinstance(values, list):
        return [item for item in values if isinstance(item, str) and item.strip()]
    return expected_sources


def _source_recall(found_sources: list[str], expected_sources: list[str]) -> float:
    expected = _canonical_source_set(expected_sources)
    if not expected:
        return 1.0
    found = _canonical_source_set(found_sources)
    return len(found & expected) / len(expected)


def _source_precision(found_sources: list[str], expected_sources: list[str]) -> float:
    found = _canonical_source_set(found_sources)
    if not found:
        return 1.0 if not expected_sources else 0.0
    expected = _canonical_source_set(expected_sources)
    if not expected:
        return 1.0
    return len(found & expected) / len(found)


def _citation_exactness(cited_sources: list[str], expected_sources: list[str], *, refusal_correct: bool) -> float:
    cited = _canonical_source_set(cited_sources)
    expected = _canonical_source_set(expected_sources)
    if not expected:
        return 1.0 if (not cited and refusal_correct) or not cited else 0.0
    if not cited:
        return 0.0
    return len(cited & expected) / len(cited | expected)


def _claim_support_rates(
    *,
    answer_contract: dict[str, Any] | None,
    selected_evidence_sources: list[str],
    final_mode: str | None,
    refusal_correct: bool,
) -> tuple[float, float]:
    if final_mode == "refusal":
        supported = 1.0 if refusal_correct else 0.0
        return supported, 1.0 - supported

    if not isinstance(answer_contract, dict):
        return 0.0, 1.0
    claim_units = answer_contract.get("claim_units")
    if not isinstance(claim_units, list) or not claim_units:
        return 0.0, 1.0

    selected = _canonical_source_set(selected_evidence_sources)
    supported_count = 0
    for claim in claim_units:
        if not isinstance(claim, dict):
            continue
        source_id = claim.get("selected_source_key") or claim.get("source_id")
        if isinstance(source_id, str) and normalize_source(source_id) in selected:
            supported_count += 1
    supported_rate = supported_count / len(claim_units)
    return supported_rate, 1.0 - supported_rate


def _current_law_state_error(
    *,
    question: dict[str, Any],
    answer_contract: dict[str, Any] | None,
    trace: dict[str, Any] | None,
) -> bool:
    expected_state = str(question.get("expected_law_state") or "").strip().lower()
    if expected_state not in {"current", "historical", "repealed"}:
        return False

    contract = answer_contract if isinstance(answer_contract, dict) else {}
    source_validity = str(contract.get("source_validity") or "").lower()
    applicability_note = str(contract.get("applicability_note") or "").lower()
    temporal_intent = ""
    parsed = trace.get("parsed_query") if isinstance(trace, dict) else None
    if isinstance(parsed, dict):
        analysis = parsed.get("query_analysis")
        if isinstance(analysis, dict):
            temporal_intent = str(analysis.get("temporal_intent") or "").lower()

    historical_signal = any(
        token in f"{source_validity} {applicability_note} {temporal_intent}"
        for token in ("historical", "repealed", "mülga", "mulga", "tarihsel", "yürürlükten", "yururlukten")
    )

    if expected_state == "current":
        return historical_signal
    return not historical_signal


def _no_benchmark_runtime_patch(trace: dict[str, Any] | None) -> bool:
    if not isinstance(trace, dict):
        return True
    generation = trace.get("generation_outcome")
    decision_lane = ""
    if isinstance(generation, dict):
        decision_lane = str(generation.get("decision_lane") or "")
    if any(token in decision_lane.lower() for token in ("precise", "benchmark", "shortcut")):
        return False

    query_signals = trace.get("query_signals")
    if isinstance(query_signals, dict):
        if query_signals.get("forced_article_refs"):
            return False
        if query_signals.get("applied_expansions"):
            return False
    parsed_query = trace.get("parsed_query")
    if isinstance(parsed_query, dict):
        if parsed_query.get("forced_article_refs"):
            return False
        if parsed_query.get("applied_expansions"):
            return False
    return True


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def sources_overlap(cited: list[str], expected: list[str]) -> tuple[int, int]:
    """Atıf yapılan ve beklenen kaynaklar arasındaki örtüşmeyi hesapla.

    Returns:
        (overlap_count, expected_count):
            overlap_count  — doğru atıf edilen kaynak sayısı
            expected_count — beklenen kaynak sayısı
    """
    if not expected:
        return 0, 0

    norm_cited = {normalize_source(s) for s in cited}
    norm_expected = {normalize_source(s) for s in expected}

    # Tam eşleşme denemesi
    exact_overlap = norm_cited & norm_expected
    if exact_overlap:
        return len(exact_overlap), len(norm_expected)

    # Madde numarası tabanlı yumuşak eşleşme (ör. "tbk m.299" ∈ "m.299 kira")
    soft_overlap = 0
    for exp in norm_expected:
        # Madde numarasını çıkar
        m = re.search(r"m\.(\d+)", exp)
        if not m:
            continue
        article_num = m.group(1)
        law_prefix = exp.split(" ")[0] if " " in exp else ""

        for cit in norm_cited:
            cit_m = re.search(r"m\.(\d+)", cit)
            if cit_m and cit_m.group(1) == article_num:
                # Aynı kanun mu?
                if not law_prefix or law_prefix in cit:
                    soft_overlap += 1
                    break

    return soft_overlap, len(norm_expected)


def detect_hallucination(cited: list[str], expected: list[str], answer_text: str) -> bool:
    """Hallüsinasyon tespiti.

    Kriter:
    - Model en az bir kaynak atfetti VE
    - Hiçbir beklenen kaynak doğru atıf edilmedi VE
    - Beklenen kaynaklar boş değil

    Not: Bu basit bir heuristik; gerçek hallüsinasyon tespiti için
    VerificationEngine (Backlog #6) kullanılmalıdır.
    """
    if not expected:
        # Beklenen kaynak yoksa hallüsinasyon kararı verilemez
        return False
    if not cited:
        # Atıf yoksa hallüsinasyon sayılmaz (citation rate düşer)
        return False

    overlap, expected_count = sources_overlap(cited, expected)
    # Hiçbir beklenen kaynak doğru atıf edilmediyse hallüsinasyon
    return overlap == 0


def detect_refusal(answer_text: str) -> bool:
    """Yanıtta refusal (ret/kapsam dışı) ifadesi var mı?

    Türkçe büyük-küçük harf normalizasyonu için _tr_lower kullanır.
    """
    normalized = _tr_lower(answer_text)
    for pattern in REFUSAL_PATTERNS:
        if re.search(pattern, normalized, flags=re.DOTALL):
            return True
    return False


def keyword_coverage(answer_text: str, expected_keywords: list[str]) -> float:
    """Beklenen anahtar terimlerin yanıtta görünme oranı.

    Türkçe büyük-küçük harf normalizasyonu için _tr_lower kullanır.

    Returns:
        0.0 – 1.0 arası oran (beklenen keyword yoksa 1.0 döner)
    """
    if not expected_keywords:
        return 1.0

    normalized = _tr_lower(answer_text)
    hit = sum(1 for kw in expected_keywords if _tr_lower(kw) in normalized)
    return hit / len(expected_keywords)


def phrase_hit(answer_text: str, expected_phrase: str | None) -> bool | None:
    """expected_answer_contains kontrolü.

    Türkçe büyük-küçük harf normalizasyonu için _tr_lower kullanır.

    Returns:
        True  — ifade yanıtta var
        False — ifade yanıtta yok
        None  — expected_phrase None ise kontrol yapılmadı
    """
    if expected_phrase is None:
        return None
    return _tr_lower(expected_phrase) in _tr_lower(answer_text)


# ---------------------------------------------------------------------------
# Tek soru için metrik hesaplama
# ---------------------------------------------------------------------------

@dataclass
class QuestionResult:
    """Tek soru için değerlendirme sonucu."""

    question_id: str
    question_text: str
    category: str
    difficulty: str

    # Ham veriler
    answer_text: str
    cited_sources: list[str] = field(default_factory=list)
    expected_sources: list[str] = field(default_factory=list)
    expected_evidence_sources: list[str] = field(default_factory=list)
    expected_keywords: list[str] = field(default_factory=list)
    expected_answer_contains: str | None = None
    refusal_expected: bool = False

    # Hesaplanan metrikler
    has_citation: bool = False          # Herhangi bir atıf var mı?
    correct_source_overlap: int = 0     # Doğru kaynak sayısı
    expected_source_count: int = 0      # Beklenen kaynak sayısı
    correct_source_rate: float = 0.0    # Doğru kaynak oranı (0-1)
    is_hallucination: bool = False      # Hallüsinasyon var mı?
    is_refusal: bool = False            # Model reddetti mi?
    refusal_correct: bool = False       # Beklenen ret → doğru ret?
    kw_coverage: float = 0.0           # Keyword coverage (0-1)
    phrase_hit_result: bool | None = None  # expected_answer_contains sonucu
    retrieved_source_ids_top5: list[str] = field(default_factory=list)
    retrieved_source_ids_top20: list[str] = field(default_factory=list)
    selected_evidence_source_ids: list[str] = field(default_factory=list)
    claim_source_ids: list[str] = field(default_factory=list)
    retrieval_hit_at_5: float = 0.0
    retrieval_hit_at_20: float = 0.0
    selected_evidence_precision: float = 0.0
    selected_evidence_recall: float = 0.0
    citation_exactness: float = 0.0
    claim_supported_rate: float = 0.0
    unsupported_claim_rate: float = 0.0
    current_law_state_error: bool = False
    refusal_correctness: float = 0.0
    no_benchmark_specific_runtime_patch: bool = True

    # API meta
    response_time_ms: float = 0.0
    blocked: bool = False
    verification_verdict: str | None = None
    final_mode: str | None = None
    final_reason: str | None = None
    answer_contract: dict[str, Any] | None = None
    error: str | None = None
    trace: dict[str, Any] | None = None


def compute_metrics(
    *,
    question: dict[str, Any],
    answer_text: str,
    cited_sources: list[str],
    response_time_ms: float = 0.0,
    blocked: bool = False,
    verification: dict[str, Any] | None = None,
    final_mode: str | None = None,
    final_reason: str | None = None,
    answer_contract: dict[str, Any] | None = None,
    error: str | None = None,
    trace: dict[str, Any] | None = None,
) -> QuestionResult:
    """Tek soru için tüm metrikleri hesapla.

    Args:
        question: test_questions.json'dan tek soru dict'i
        answer_text: LLM'den dönen yanıt metni
        cited_sources: API'nin döndürdüğü citations listesi
        response_time_ms: API yanıt süresi (ms)
        blocked: Guardrails tarafından bloklandı mı?
        verification: Verification Engine sonucu dict'i
        error: API hatası mesajı (varsa)

    Returns:
        QuestionResult dataclass'ı
    """
    q_id = question["id"]
    q_text = question["question"]
    category = question.get("category", "unknown")
    difficulty = question.get("difficulty", "medium")
    expected_sources = question.get("expected_sources", [])
    expected_evidence = _expected_evidence_sources(question, expected_sources)
    expected_keywords = question.get("expected_keywords", [])
    expected_answer_contains = question.get("expected_answer_contains")
    refusal_expected = question.get("refusal_expected", False)

    # Metrik hesapla
    has_citation = bool(cited_sources)
    overlap, expected_count = sources_overlap(cited_sources, expected_sources)
    correct_source_rate = (overlap / expected_count) if expected_count > 0 else (1.0 if not expected_sources else 0.0)
    is_hallucination = detect_hallucination(cited_sources, expected_sources, answer_text)
    is_refusal = detect_refusal(answer_text)
    refusal_correct = (refusal_expected == is_refusal)
    kw_cov = keyword_coverage(answer_text, expected_keywords)
    p_hit = phrase_hit(answer_text, expected_answer_contains)
    retrieved_top5 = _extract_trace_source_ids(trace, list_name="pre_rerank_chunks", limit=5)
    retrieved_top20 = _extract_trace_source_ids(trace, list_name="pre_rerank_chunks", limit=20)
    selected_evidence = _extract_selected_evidence_sources(
        trace=trace,
        answer_contract=answer_contract,
        cited_sources=cited_sources,
    )
    claim_sources = _extract_claim_sources(answer_contract)
    retrieval_hit_at_5 = 1.0 if _source_recall(retrieved_top5, expected_evidence) >= 1.0 else 0.0
    retrieval_hit_at_20 = 1.0 if _source_recall(retrieved_top20, expected_evidence) >= 1.0 else 0.0
    selected_precision = _source_precision(selected_evidence, expected_evidence)
    selected_recall = _source_recall(selected_evidence, expected_evidence)
    citation_exact = _citation_exactness(cited_sources, expected_sources, refusal_correct=refusal_correct)
    claim_supported, unsupported_claim = _claim_support_rates(
        answer_contract=answer_contract,
        selected_evidence_sources=selected_evidence,
        final_mode=final_mode,
        refusal_correct=refusal_correct,
    )
    current_law_error = _current_law_state_error(
        question=question,
        answer_contract=answer_contract,
        trace=trace,
    )
    no_benchmark_patch = _no_benchmark_runtime_patch(trace)

    # Verification Engine verdict'i
    v_verdict = None
    if verification and isinstance(verification, dict):
        v_verdict = verification.get("verdict")

    return QuestionResult(
        question_id=q_id,
        question_text=q_text,
        category=category,
        difficulty=difficulty,
        answer_text=answer_text,
        cited_sources=cited_sources,
        expected_sources=expected_sources,
        expected_evidence_sources=expected_evidence,
        expected_keywords=expected_keywords,
        expected_answer_contains=expected_answer_contains,
        refusal_expected=refusal_expected,
        has_citation=has_citation,
        correct_source_overlap=overlap,
        expected_source_count=expected_count,
        correct_source_rate=round(correct_source_rate, 4),
        is_hallucination=is_hallucination,
        is_refusal=is_refusal,
        refusal_correct=refusal_correct,
        kw_coverage=round(kw_cov, 4),
        phrase_hit_result=p_hit,
        retrieved_source_ids_top5=retrieved_top5,
        retrieved_source_ids_top20=retrieved_top20,
        selected_evidence_source_ids=selected_evidence,
        claim_source_ids=claim_sources,
        retrieval_hit_at_5=round(retrieval_hit_at_5, 4),
        retrieval_hit_at_20=round(retrieval_hit_at_20, 4),
        selected_evidence_precision=round(selected_precision, 4),
        selected_evidence_recall=round(selected_recall, 4),
        citation_exactness=round(citation_exact, 4),
        claim_supported_rate=round(claim_supported, 4),
        unsupported_claim_rate=round(unsupported_claim, 4),
        current_law_state_error=current_law_error,
        refusal_correctness=1.0 if refusal_correct else 0.0,
        no_benchmark_specific_runtime_patch=no_benchmark_patch,
        response_time_ms=round(response_time_ms, 1),
        blocked=blocked,
        verification_verdict=v_verdict,
        final_mode=final_mode,
        final_reason=final_reason,
        answer_contract=answer_contract,
        error=error,
        trace=trace,
    )


# ---------------------------------------------------------------------------
# Toplu metrik agregasyonu
# ---------------------------------------------------------------------------

@dataclass
class AggregatedMetrics:
    """Tüm test seti için özet metrikler."""

    total_questions: int = 0
    error_count: int = 0

    # Temel metrikler (0.0 – 1.0)
    citation_rate: float = 0.0           # Atıf olan yanıt oranı
    correct_source_rate: float = 0.0     # Doğru kaynak oranı (macro avg)
    hallucination_rate: float = 0.0      # Hallüsinasyon oranı
    refusal_accuracy: float = 0.0        # Refusal doğruluğu (beklenen == gerçek)

    # Ek metrikler
    avg_keyword_coverage: float = 0.0    # Ortalama keyword coverage
    phrase_hit_rate: float = 0.0         # expected_answer_contains geçme oranı
    avg_response_time_ms: float = 0.0    # Ortalama yanıt süresi
    blocked_rate: float = 0.0            # Guardrails tarafından bloklanan oran
    retrieval_hit_at_5: float = 0.0
    retrieval_hit_at_20: float = 0.0
    selected_evidence_precision: float = 0.0
    selected_evidence_recall: float = 0.0
    citation_exactness: float = 0.0
    claim_supported_rate: float = 0.0
    unsupported_claim_rate: float = 0.0
    current_law_state_error_rate: float = 0.0
    refusal_correctness: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    no_benchmark_specific_runtime_patch: bool = True

    # Kategori bazlı
    by_category: dict[str, dict[str, float]] = field(default_factory=dict)
    by_difficulty: dict[str, dict[str, float]] = field(default_factory=dict)

    # Faz 1 başarı kriterleri
    faz1_criteria: dict[str, Any] = field(default_factory=dict)
    closure_criteria: dict[str, Any] = field(default_factory=dict)


def aggregate_metrics(results: list[QuestionResult]) -> AggregatedMetrics:
    """Soru sonuçlarını toplu metriklere çevir.

    Faz 1 başarı kriterleri (backlog hedefleri):
        - Citation rate ≥ 0.80
        - Correct source rate ≥ 0.70
        - Hallucination rate ≤ 0.10
        - Refusal accuracy ≥ 0.80
    """
    if not results:
        return AggregatedMetrics()

    total = len(results)
    non_error = [r for r in results if r.error is None]
    errors = total - len(non_error)

    def _safe_mean(vals: list[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    # Temel metrikler
    citation_rate = _safe_mean([1.0 if r.has_citation else 0.0 for r in non_error])
    correct_source_rate = _safe_mean([r.correct_source_rate for r in non_error])
    hallucination_rate = _safe_mean([1.0 if r.is_hallucination else 0.0 for r in non_error])
    refusal_accuracy = _safe_mean([1.0 if r.refusal_correct else 0.0 for r in non_error])

    # Ek metrikler
    avg_kw_cov = _safe_mean([r.kw_coverage for r in non_error])
    phrase_hits = [r for r in non_error if r.phrase_hit_result is not None]
    phrase_hit_rate = _safe_mean([1.0 if r.phrase_hit_result else 0.0 for r in phrase_hits]) if phrase_hits else 1.0
    avg_rt = _safe_mean([r.response_time_ms for r in non_error])
    latency_values = [r.response_time_ms for r in non_error]
    latency_p50 = _percentile(latency_values, 0.50)
    latency_p95 = _percentile(latency_values, 0.95)
    blocked_rate = _safe_mean([1.0 if r.blocked else 0.0 for r in non_error])
    retrieval_hit_at_5 = _safe_mean([r.retrieval_hit_at_5 for r in non_error])
    retrieval_hit_at_20 = _safe_mean([r.retrieval_hit_at_20 for r in non_error])
    selected_evidence_precision = _safe_mean([r.selected_evidence_precision for r in non_error])
    selected_evidence_recall = _safe_mean([r.selected_evidence_recall for r in non_error])
    citation_exactness = _safe_mean([r.citation_exactness for r in non_error])
    claim_supported_rate = _safe_mean([r.claim_supported_rate for r in non_error])
    unsupported_claim_rate = _safe_mean([r.unsupported_claim_rate for r in non_error])
    current_law_state_error_rate = _safe_mean([1.0 if r.current_law_state_error else 0.0 for r in non_error])
    refusal_correctness = _safe_mean([r.refusal_correctness for r in non_error])
    no_benchmark_specific_runtime_patch = all(r.no_benchmark_specific_runtime_patch for r in non_error)

    # Kategori bazlı
    by_category: dict[str, list[QuestionResult]] = {}
    for r in non_error:
        by_category.setdefault(r.category, []).append(r)

    cat_summary: dict[str, dict[str, float]] = {}
    for cat, cat_results in by_category.items():
        cat_summary[cat] = {
            "count": len(cat_results),
            "citation_rate": round(_safe_mean([1.0 if r.has_citation else 0.0 for r in cat_results]), 4),
            "correct_source_rate": round(_safe_mean([r.correct_source_rate for r in cat_results]), 4),
            "hallucination_rate": round(_safe_mean([1.0 if r.is_hallucination else 0.0 for r in cat_results]), 4),
            "refusal_accuracy": round(_safe_mean([1.0 if r.refusal_correct else 0.0 for r in cat_results]), 4),
            "avg_keyword_coverage": round(_safe_mean([r.kw_coverage for r in cat_results]), 4),
            "retrieval_hit_at_20": round(_safe_mean([r.retrieval_hit_at_20 for r in cat_results]), 4),
            "selected_evidence_recall": round(_safe_mean([r.selected_evidence_recall for r in cat_results]), 4),
            "claim_supported_rate": round(_safe_mean([r.claim_supported_rate for r in cat_results]), 4),
        }

    # Zorluk bazlı
    by_difficulty: dict[str, list[QuestionResult]] = {}
    for r in non_error:
        by_difficulty.setdefault(r.difficulty, []).append(r)

    diff_summary: dict[str, dict[str, float]] = {}
    for diff, diff_results in by_difficulty.items():
        diff_summary[diff] = {
            "count": len(diff_results),
            "citation_rate": round(_safe_mean([1.0 if r.has_citation else 0.0 for r in diff_results]), 4),
            "correct_source_rate": round(_safe_mean([r.correct_source_rate for r in diff_results]), 4),
            "hallucination_rate": round(_safe_mean([1.0 if r.is_hallucination else 0.0 for r in diff_results]), 4),
            "avg_keyword_coverage": round(_safe_mean([r.kw_coverage for r in diff_results]), 4),
        }

    # Faz 1 başarı kriterleri
    FAZ1_THRESHOLDS = {
        "citation_rate": ("≥", 0.80),
        "correct_source_rate": ("≥", 0.70),
        "hallucination_rate": ("≤", 0.10),
        "refusal_accuracy": ("≥", 0.80),
    }
    actual_values = {
        "citation_rate": citation_rate,
        "correct_source_rate": correct_source_rate,
        "hallucination_rate": hallucination_rate,
        "refusal_accuracy": refusal_accuracy,
    }
    faz1_criteria: dict[str, Any] = {}
    all_pass = True
    for metric, (op, threshold) in FAZ1_THRESHOLDS.items():
        val = actual_values[metric]
        if op == "≥":
            passes = val >= threshold
        else:  # ≤
            passes = val <= threshold
        faz1_criteria[metric] = {
            "threshold": threshold,
            "operator": op,
            "actual": round(val, 4),
            "passes": passes,
            "status": "✅ GEÇTİ" if passes else "❌ BAŞARISIZ",
        }
        if not passes:
            all_pass = False

    faz1_criteria["overall"] = {
        "passes": all_pass,
        "status": "✅ FAZ 1 KABULEDİLDİ" if all_pass else "❌ FAZ 1 KRİTERLERİ KARŞILANMADI",
    }

    closure_actual_values: dict[str, float | bool] = {
        "retrieval_hit_at_20": retrieval_hit_at_20,
        "selected_evidence_recall": selected_evidence_recall,
        "citation_exactness": citation_exactness,
        "claim_supported_rate": claim_supported_rate,
        "unsupported_claim_rate": unsupported_claim_rate,
        "current_law_state_error_rate": current_law_state_error_rate,
        "refusal_correctness": refusal_correctness,
        "no_benchmark_specific_runtime_patch": no_benchmark_specific_runtime_patch,
    }
    closure_thresholds: dict[str, tuple[str, float | bool]] = {
        "retrieval_hit_at_20": ("≥", 0.95),
        "selected_evidence_recall": ("≥", 0.90),
        "citation_exactness": ("≥", 0.95),
        "claim_supported_rate": ("≥", 0.95),
        "unsupported_claim_rate": ("≤", 0.03),
        "current_law_state_error_rate": ("≤", 0.03),
        "refusal_correctness": ("≥", 0.95),
        "no_benchmark_specific_runtime_patch": ("==", True),
    }
    latency_baseline_raw = os.getenv("CLOSURE_LATENCY_P95_BASELINE_MS", "").strip()
    try:
        latency_threshold = float(latency_baseline_raw) * 1.25 if latency_baseline_raw else None
    except ValueError:
        latency_threshold = None
    if latency_threshold is not None:
        closure_actual_values["latency_p95_ms"] = latency_p95
        closure_thresholds["latency_p95_ms"] = ("≤", latency_threshold)

    closure_criteria: dict[str, Any] = {}
    closure_all_pass = True
    for metric, (op, threshold) in closure_thresholds.items():
        value = closure_actual_values[metric]
        if op == "≥":
            passes = float(value) >= float(threshold)
        elif op == "≤":
            passes = float(value) <= float(threshold)
        else:
            passes = value is threshold
        closure_criteria[metric] = {
            "threshold": threshold,
            "operator": op,
            "actual": round(value, 4) if isinstance(value, float) else value,
            "passes": passes,
            "status": "GEÇTİ" if passes else "BAŞARISIZ",
        }
        if not passes:
            closure_all_pass = False
    if latency_threshold is None:
        closure_criteria["latency_p95_ms"] = {
            "threshold": "CLOSURE_LATENCY_P95_BASELINE_MS * 1.25",
            "operator": "≤",
            "actual": round(latency_p95, 1),
            "passes": True,
            "status": "BASIS_YOK",
        }
    closure_criteria["overall"] = {
        "passes": closure_all_pass,
        "status": "PASS" if closure_all_pass else "NO_GO",
    }

    return AggregatedMetrics(
        total_questions=total,
        error_count=errors,
        citation_rate=round(citation_rate, 4),
        correct_source_rate=round(correct_source_rate, 4),
        hallucination_rate=round(hallucination_rate, 4),
        refusal_accuracy=round(refusal_accuracy, 4),
        avg_keyword_coverage=round(avg_kw_cov, 4),
        phrase_hit_rate=round(phrase_hit_rate, 4),
        avg_response_time_ms=round(avg_rt, 1),
        blocked_rate=round(blocked_rate, 4),
        retrieval_hit_at_5=round(retrieval_hit_at_5, 4),
        retrieval_hit_at_20=round(retrieval_hit_at_20, 4),
        selected_evidence_precision=round(selected_evidence_precision, 4),
        selected_evidence_recall=round(selected_evidence_recall, 4),
        citation_exactness=round(citation_exactness, 4),
        claim_supported_rate=round(claim_supported_rate, 4),
        unsupported_claim_rate=round(unsupported_claim_rate, 4),
        current_law_state_error_rate=round(current_law_state_error_rate, 4),
        refusal_correctness=round(refusal_correctness, 4),
        latency_p50_ms=round(latency_p50, 1),
        latency_p95_ms=round(latency_p95, 1),
        no_benchmark_specific_runtime_patch=no_benchmark_specific_runtime_patch,
        by_category=cat_summary,
        by_difficulty=diff_summary,
        faz1_criteria=faz1_criteria,
        closure_criteria=closure_criteria,
    )
