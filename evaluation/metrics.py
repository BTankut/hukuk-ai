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
    r"(ilgili\s+)?veri\s+(tabanımda|tabaninda|kaynagımda).*?(mevcut\s+değil|bulunmamaktadır|yok)",
    r"(ilgili\s+)?kaynak\s+(bulunamadı|mevcut\s+değil|yok)",
    r"(tbk\s+)?mevzuatımızda\s+(bu\s+konu\s+)?yer\s+almıyor",
    r"yeterli\s+kaynak\s+(bulunamadı|mevcut\s+değil|yok)",
    r"guvenilir\s+bilgi\s+veremiyorum",
    r"bu\s+bilgiye\s+sahip\s+degil",
    r"iş\s+kanunu",          # Kıdem tazminatı sorusu için (_tr_lower ile İş→iş)
    r"ticaret\s+kanunu",     # TTK sorusu için
    r"ttk",
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
    s = re.sub(r"(tbk|tmk|tck|ik)\s*[-–]\s*(\d+)", r"\1 m.\2", s)
    # Normalize whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


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

    # Kategori bazlı
    by_category: dict[str, dict[str, float]] = field(default_factory=dict)
    by_difficulty: dict[str, dict[str, float]] = field(default_factory=dict)

    # Faz 1 başarı kriterleri
    faz1_criteria: dict[str, Any] = field(default_factory=dict)


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
    blocked_rate = _safe_mean([1.0 if r.blocked else 0.0 for r in non_error])

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
        by_category=cat_summary,
        by_difficulty=diff_summary,
        faz1_criteria=faz1_criteria,
    )
