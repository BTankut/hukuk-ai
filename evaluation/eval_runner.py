#!/usr/bin/env python3
"""Evaluation Runner — AI Hukuk Asistanı Faz 1 (Backlog #8).

Chat API üzerinden test soruları gönderir, yanıtları değerlendirir ve
Faz 1 kabul kriterlerine göre rapor üretir.

Değerlendirilen metrikler:
    1. Citation Rate        — Yanıtta kaynak atıfı var mı?
    2. Correct Source Rate  — Atıf yapılan kaynaklar beklenenlerle örtüşüyor mu?
    3. Hallucination Rate   — Model, beklenen dışı kaynak üretiyor mu?
    4. Refusal on Unknown   — Model kapsam dışı soruları doğru reddediyor mu?
    5. Keyword Coverage     — Beklenen anahtar terimler yanıtta geçiyor mu?

Kullanım (CLI):
    # Mock mod (API gerektirmez, uygulanabilir değerlendirme izler):
    python evaluation/eval_runner.py --mock

    # Gerçek API:
    python evaluation/eval_runner.py --api-url http://localhost:8000

    # Özel sorgu seti:
    python evaluation/eval_runner.py --questions configs/evaluation/test_questions.json

    # Tek kategori:
    python evaluation/eval_runner.py --category tbk_kira --mock

    # Rapor çıktısı:
    python evaluation/eval_runner.py --output evaluation/reports/eval_run.json

Faz 1 Kabul Kriterleri:
    Citation Rate ≥ 0.80, Correct Source Rate ≥ 0.70,
    Hallucination Rate ≤ 0.10, Refusal Accuracy ≥ 0.80
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_QUESTIONS_PATH = PROJECT_ROOT / "configs" / "evaluation" / "test_questions.json"
REPORTS_DIR = PROJECT_ROOT / "evaluation" / "reports"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("eval_runner")

# ---------------------------------------------------------------------------
# Metrics import (proje içi — sys.path eklentisiyle)
# ---------------------------------------------------------------------------

# eval_runner.py → evaluation/ → project_root/
# metrics.py aynı dizinde olduğu için relative import kullanmaya gerek yok
# (script doğrudan çalıştırıldığında sys.path'e evaluation/ eklenir)
sys.path.insert(0, str(Path(__file__).parent))

from metrics import (  # noqa: E402
    QuestionResult,
    AggregatedMetrics,
    compute_metrics,
    aggregate_metrics,
)

# ---------------------------------------------------------------------------
# Chat API Client
# ---------------------------------------------------------------------------


class ChatAPIClient:
    """Minimal Chat API istemcisi (stdlib urllib, bağımlılık yok).

    /v1/chat/completions endpoint'ine POST atar ve yanıtı döner.
    Streaming desteği: Faz 1 eval için stream=False kullanılır.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 180.0,
        law_filter: str | None = None,  # Recall fix: None → TBK+TMK her ikisi de retrieve edilir
        use_verification: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.law_filter = law_filter
        self.use_verification = use_verification

    def chat(
        self,
        question: str,
        *,
        session_id: str | None = None,
        law_filter: str | None = None,
    ) -> dict[str, Any]:
        """Tek soru için chat API çağrısı.

        Returns:
            dict with keys: answer_text, citations, blocked, verification, error
        """
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": "hukuk-lora",
            "messages": [{"role": "user", "content": question}],
            "stream": False,
            "use_verification": self.use_verification,
            "max_tokens": 512,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        if session_id:
            payload["session_id"] = session_id
        if law_filter or self.law_filter:
            payload["law_filter"] = law_filter or self.law_filter

        data = json.dumps(payload).encode("utf-8")

        try:
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            t0 = time.perf_counter()
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                body = json.loads(resp.read().decode("utf-8"))

            # Yanıtı parse et
            choices = body.get("choices", [])
            answer_text = choices[0]["message"]["content"] if choices else ""
            citations = body.get("citations", [])
            blocked = body.get("blocked", False)
            verification = body.get("verification")

            return {
                "answer_text": answer_text,
                "citations": citations,
                "blocked": blocked,
                "verification": verification,
                "response_time_ms": elapsed_ms,
                "error": None,
            }

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            logger.error("HTTP %d — %s: %s", e.code, url, err_body[:200])
            return {
                "answer_text": "",
                "citations": [],
                "blocked": False,
                "verification": None,
                "response_time_ms": 0.0,
                "error": f"HTTP {e.code}: {err_body[:100]}",
            }
        except Exception as exc:
            logger.error("API hatası: %s", exc)
            return {
                "answer_text": "",
                "citations": [],
                "blocked": False,
                "verification": None,
                "response_time_ms": 0.0,
                "error": str(exc),
            }


# ---------------------------------------------------------------------------
# Mock Client (API gerektirmez — offline test için)
# ---------------------------------------------------------------------------


class MockChatClient:
    """Offline mock client — gerçek API olmadan değerlendirme iskeletini test eder.

    Yanıt şablonları sorunun expected_sources ve expected_keywords'ünden türetilir.
    out_of_scope kategorisindeki sorulara refusal yanıtı verir.
    """

    def chat(
        self,
        question: str,
        *,
        session_id: str | None = None,
        law_filter: str | None = None,
        _question_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Mock yanıt üret."""
        meta = _question_meta or {}
        category = meta.get("category", "")
        expected_sources = meta.get("expected_sources", [])
        expected_keywords = meta.get("expected_keywords", [])
        refusal_expected = meta.get("refusal_expected", False)

        # Refusal beklenen soru → refusal yanıtı
        if refusal_expected or category == "out_of_scope":
            if "tbk-018" in meta.get("id", "").lower() or "kıdem" in question.lower():
                answer = (
                    "Bu soru Türk Borçlar Kanunu kapsamında değildir. "
                    "Kıdem tazminatı İş Kanunu (4857 sayılı Kanun) çerçevesinde "
                    "düzenlenmektedir. İlgili mevzuat kaynaklarımda bu konuda "
                    "yeterli bilgi bulunmamaktadır; bir iş hukuku uzmanına "
                    "başvurmanızı tavsiye ederim."
                )
            else:
                answer = (
                    f"Bu konuya ilişkin veri tabanımda yeterli kaynak bulunmamaktadır. "
                    f"Sorunuz mevcut TBK mevzuat kapsamımız dışında kalıyor olabilir. "
                    f"Lütfen ilgili uzman bir avukata danışınız."
                )
            return {
                "answer_text": answer,
                "citations": [],
                "blocked": False,
                "verification": {"verdict": "pass", "hallucination_risk": 0.0},
                "response_time_ms": 12.5,
                "error": None,
            }

        # Normal soru → mock yanıt (beklenen kaynak ve keyword'leri içerir)
        source_text = ", ".join(expected_sources[:3]) if expected_sources else "TBK"
        keyword_text = " ve ".join(expected_keywords[:4]) if expected_keywords else ""
        answer = (
            f"Türk Borçlar Kanunu'na göre bu konuda ilgili düzenlemeler "
            f"{source_text} maddelerinde yer almaktadır. "
            f"Bu kapsamda {keyword_text} kavramları önem taşımaktadır. "
            f"İlgili hükümler uyarınca söz konusu durum değerlendirilmelidir. "
            f"Detaylı bilgi için {source_text} hükümlerini incelemenizi öneririm."
        )

        # Yarı doğru atıf simülasyonu (%70 doğru, %30 yanlış)
        import random
        rng = random.Random(hash(question) % 1000)
        if expected_sources and rng.random() > 0.3:
            citations = expected_sources[:2]
        else:
            citations = expected_sources[:1] if expected_sources else []

        return {
            "answer_text": answer,
            "citations": citations,
            "blocked": False,
            "verification": {
                "verdict": "pass" if citations else "warn",
                "hallucination_risk": 0.1,
            },
            "response_time_ms": rng.uniform(80, 350),
            "error": None,
        }


# ---------------------------------------------------------------------------
# Core evaluation loop
# ---------------------------------------------------------------------------


def run_evaluation(
    questions: list[dict[str, Any]],
    client: ChatAPIClient | MockChatClient,
    *,
    category_filter: str | None = None,
    delay_between_requests: float = 0.5,
    mock_mode: bool = False,
) -> list[QuestionResult]:
    """Tüm sorular için eval döngüsü.

    Args:
        questions: test_questions.json'dan soru listesi
        client: ChatAPIClient veya MockChatClient
        category_filter: sadece bu kategoriyi değerlendir (None = hepsi)
        delay_between_requests: API çağrıları arası bekleme (saniye)
        mock_mode: MockChatClient kullanılıyorsa True

    Returns:
        QuestionResult listesi
    """
    results: list[QuestionResult] = []

    filtered = questions
    if category_filter:
        filtered = [q for q in questions if q.get("category") == category_filter]
        logger.info("Kategori filtresi: '%s' → %d soru", category_filter, len(filtered))

    total = len(filtered)
    logger.info("Değerlendirme başlıyor: %d soru", total)

    for idx, q in enumerate(filtered, start=1):
        q_id = q.get("id", f"Q{idx}")
        q_text = q.get("question", "")
        logger.info("[%d/%d] %s — %s...", idx, total, q_id, q_text[:60])

        try:
            if mock_mode and isinstance(client, MockChatClient):
                api_result = client.chat(
                    q_text,
                    _question_meta=q,
                )
            else:
                # Kapsam dışı sorular için law_filter kaldır (doğal refusal testi)
                lf = None if q.get("refusal_expected") else None
                api_result = client.chat(q_text, law_filter=lf)

        except Exception as exc:
            logger.error("  Soru %s için beklenmedik hata: %s", q_id, exc)
            api_result = {
                "answer_text": "",
                "citations": [],
                "blocked": False,
                "verification": None,
                "response_time_ms": 0.0,
                "error": str(exc),
            }

        result = compute_metrics(
            question=q,
            answer_text=api_result["answer_text"],
            cited_sources=api_result["citations"],
            response_time_ms=api_result["response_time_ms"],
            blocked=api_result["blocked"],
            verification=api_result["verification"],
            error=api_result["error"],
        )
        results.append(result)

        # Durum log'u
        status_icons = []
        if result.error:
            status_icons.append("💥 HATA")
        else:
            status_icons.append("📎" if result.has_citation else "🚫")
            status_icons.append(f"src={result.correct_source_rate:.2f}")
            status_icons.append(f"kw={result.kw_coverage:.2f}")
            if result.refusal_expected:
                status_icons.append("↩️REFUSAL_OK" if result.refusal_correct else "❌REFUSAL_MISS")
            if result.is_hallucination:
                status_icons.append("⚠️HAL")
        logger.info("  → %s", " | ".join(status_icons))

        if delay_between_requests > 0 and idx < total:
            time.sleep(delay_between_requests)

    return results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def build_report(
    results: list[QuestionResult],
    summary: AggregatedMetrics,
    *,
    questions_path: Path,
    api_url: str,
    mock_mode: bool,
) -> dict[str, Any]:
    """Değerlendirme raporu oluştur."""

    def result_to_dict(r: QuestionResult) -> dict[str, Any]:
        d = asdict(r)
        # None değerleri temizle (JSON boyutunu küçültur)
        return {k: v for k, v in d.items() if v is not None}

    return {
        "report_meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "questions_source": str(questions_path),
            "api_url": api_url if not mock_mode else "MOCK",
            "mock_mode": mock_mode,
            "total_questions": summary.total_questions,
            "error_count": summary.error_count,
        },
        "summary": {
            "citation_rate": summary.citation_rate,
            "correct_source_rate": summary.correct_source_rate,
            "hallucination_rate": summary.hallucination_rate,
            "refusal_accuracy": summary.refusal_accuracy,
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


def print_summary(summary: AggregatedMetrics) -> None:
    """Terminale okunabilir özet yazdır."""
    print("\n" + "=" * 65)
    print("  AI HUKUK ASISTANI — FAZ 1 DEĞERLENDİRME SONUCU")
    print("=" * 65)
    print(f"  Toplam Soru      : {summary.total_questions}")
    print(f"  Hata Sayısı      : {summary.error_count}")
    print()
    print("  ─── Temel Metrikler ───────────────────────────────────────")
    print(f"  Citation Rate        : {summary.citation_rate:.1%}")
    print(f"  Correct Source Rate  : {summary.correct_source_rate:.1%}")
    print(f"  Hallucination Rate   : {summary.hallucination_rate:.1%}")
    print(f"  Refusal Accuracy     : {summary.refusal_accuracy:.1%}")
    print()
    print("  ─── Ek Metrikler ──────────────────────────────────────────")
    print(f"  Avg Keyword Coverage : {summary.avg_keyword_coverage:.1%}")
    print(f"  Phrase Hit Rate      : {summary.phrase_hit_rate:.1%}")
    print(f"  Avg Response Time    : {summary.avg_response_time_ms:.0f} ms")
    print(f"  Blocked Rate         : {summary.blocked_rate:.1%}")
    print()
    print("  ─── Faz 1 Kabul Kriterleri ────────────────────────────────")
    for metric, data in summary.faz1_criteria.items():
        if metric == "overall":
            continue
        op = data["operator"]
        thr = data["threshold"]
        actual = data["actual"]
        status = data["status"]
        print(f"  {metric:<24} {op} {thr:.0%}   actual={actual:.1%}   {status}")
    print()
    overall = summary.faz1_criteria.get("overall", {})
    print(f"  ► {overall.get('status', 'N/A')}")
    print()
    if summary.by_category:
        print("  ─── Kategori Bazlı ────────────────────────────────────────")
        for cat, cat_data in summary.by_category.items():
            csr = cat_data.get("correct_source_rate", 0)
            halr = cat_data.get("hallucination_rate", 0)
            n = cat_data.get("count", 0)
            print(f"  {cat:<22} n={n}  src_rate={csr:.1%}  hal_rate={halr:.1%}")
    print("=" * 65)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI Hukuk Asistanı Faz 1 — Evaluation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Chat API base URL (varsayılan: http://localhost:8000)",
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=DEFAULT_QUESTIONS_PATH,
        help=f"Test soruları JSON dosyası (varsayılan: {DEFAULT_QUESTIONS_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Rapor çıktı yolu (varsayılan: evaluation/reports/eval_<timestamp>.json)",
    )
    parser.add_argument(
        "--category",
        default=None,
        help="Sadece bu kategoriyi değerlendir (ör: tbk_kira, out_of_scope)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Gerçek API yerine mock client kullan (API gerektirmez)",
    )
    parser.add_argument(
        "--law-filter",
        default=None,
        help="Retrieval metadata filtresi (varsayılan: None = tüm kanunlar)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="API çağrıları arası bekleme süresi saniye (varsayılan: 0.5)",
    )
    parser.add_argument(
        "--no-verification",
        action="store_true",
        help="Verification Engine'i devre dışı bırak",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="API zaman aşımı süresi saniye (varsayılan: 60.0)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # ── Soruları yükle ────────────────────────────────────────────────────────
    if not args.questions.exists():
        logger.error("Soru dosyası bulunamadı: %s", args.questions)
        return 1

    with open(args.questions, encoding="utf-8") as f:
        data = json.load(f)

    questions = data.get("questions", [])
    if not questions:
        logger.error("Soru listesi boş! Dosya: %s", args.questions)
        return 1

    logger.info(
        "Soru seti yüklendi: %d soru (%s)",
        len(questions),
        args.questions.name,
    )

    # ── Client seç ───────────────────────────────────────────────────────────
    if args.mock:
        logger.info("MOCK MOD: Gerçek API kullanılmayacak.")
        client = MockChatClient()
    else:
        logger.info("API MOD: %s", args.api_url)
        client = ChatAPIClient(
            base_url=args.api_url,
            timeout=args.timeout,
            law_filter=args.law_filter,
            use_verification=not args.no_verification,
        )

    # ── Değerlendirme ─────────────────────────────────────────────────────────
    results = run_evaluation(
        questions=questions,
        client=client,
        category_filter=args.category,
        delay_between_requests=args.delay if not args.mock else 0.0,
        mock_mode=args.mock,
    )

    # ── Agregasyon ────────────────────────────────────────────────────────────
    summary = aggregate_metrics(results)

    # ── Rapor ─────────────────────────────────────────────────────────────────
    report = build_report(
        results=results,
        summary=summary,
        questions_path=args.questions,
        api_url=args.api_url,
        mock_mode=args.mock,
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output:
        out_path = args.output
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = "mock" if args.mock else "live"
        out_path = REPORTS_DIR / f"eval_{mode}_{ts}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info("Rapor yazıldı: %s", out_path)

    # ── Terminal özeti ────────────────────────────────────────────────────────
    print_summary(summary)

    # Çıkış kodu: tüm Faz 1 kriterleri geçtiyse 0
    overall_pass = summary.faz1_criteria.get("overall", {}).get("passes", False)
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
