#!/usr/bin/env python3
"""Faz 1 Reranker A/B Evaluation Script.

Kullanım:
    # Tüm modeller, tüm threshold'lar:
    python evaluation/reranker_ab_eval.py

    # Sadece belirli model:
    python evaluation/reranker_ab_eval.py --models mmarco

    # Threshold grid override:
    python evaluation/reranker_ab_eval.py --thresholds 0.4 0.5 0.6 0.7

    # Rapor çıktısını farklı dosyaya yaz:
    python evaluation/reranker_ab_eval.py --output evaluation/reports/my_run.json

Bağımlılıklar (pyproject.toml dev extras):
    sentence-transformers>=3.0.0
    numpy>=1.26.0

Frozen scope referansları:
    - docs/faz1-poc-plan.md §8 (başarı kriterleri)
    - coordination/decision-freeze-faz1.md D-2, U-1
    - api-gateway/src/rag/reranker.py (üretim reranker sınıfı)

Kabul kriteri (U-1):
    Reranking sonrası top-5 precision ≥ reranking öncesi top-20 precision
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_PATH = PROJECT_ROOT / "evaluation" / "fixtures" / "reranker_queries.json"
REPORTS_DIR = PROJECT_ROOT / "evaluation" / "reports"

# ---------------------------------------------------------------------------
# Faz 1 frozen model shortlist
# ---------------------------------------------------------------------------

MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "mmarco": {
        "model_id": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        "description": "D-2 primary — çok dilli mMiniLM, mMARCO 42 dil",
        "params_m": 117,
        "language_support": "multilingual (TR dahil)",
        "cpu_latency_estimate_ms_per_10": 200,
        "faz1_status": "PRIMARY",
    },
    "msmarco_en": {
        "model_id": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "description": "İngilizce baseline kontrol grubu",
        "params_m": 22,
        "language_support": "en-only",
        "cpu_latency_estimate_ms_per_10": 100,
        "faz1_status": "CONTROL",
    },
    "bge_m3": {
        "model_id": "BAAI/bge-reranker-v2-m3",
        "description": "Yedek — mmarco başarısız olursa değerlendirilen güçlü alternatif",
        "params_m": 568,
        "language_support": "multilingual (TR dahil)",
        "cpu_latency_estimate_ms_per_10": 1200,
        "faz1_status": "FALLBACK",
    },
}

FAZ1_MODELS = ["mmarco", "msmarco_en"]          # DEFAULT: primary + control
FAZ1_THRESHOLD_GRID = [0.5, 0.6, 0.7]          # U-1 grid search
FAZ1_TOP_K = 5

# Faz 1 kabul kriteri eşiği:
MIN_PRECISION_GAIN = 0.0   # top-5 precision ≥ baseline (top-20 precision)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("reranker_ab_eval")


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def precision_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Precision@k: ilk k sonuçta kaçı relevant?"""
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / k


def reciprocal_rank(ranked_ids: list[str], relevant_ids: set[str]) -> float:
    """MRR için tek sorgu reciprocal rank."""
    for i, rid in enumerate(ranked_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / i
    return 0.0


def dcg_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """DCG@k (binary relevance)."""
    total = 0.0
    for i, rid in enumerate(ranked_ids[:k], start=1):
        import math
        rel = 1.0 if rid in relevant_ids else 0.0
        total += rel / math.log2(i + 1)
    return total


def ndcg_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """nDCG@k."""
    ideal = sorted(
        [1.0 if rid in relevant_ids else 0.0 for rid in ranked_ids],
        reverse=True,
    )[:k]
    import math
    ideal_dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal))
    if ideal_dcg == 0:
        return 1.0
    return dcg_at_k(ranked_ids, relevant_ids, k) / ideal_dcg


def baseline_precision(candidates: list[dict], k: int = 20) -> float:
    """Reranking öncesi ham sıra (retrieval sırası) precision@k.

    Retrieval'ı simüle eder: candidates listesinin ilk k'sı.
    """
    relevant_ids = {c["id"] for c in candidates if c["relevance"] == 1}
    ordered_ids = [c["id"] for c in candidates]
    return precision_at_k(ordered_ids, relevant_ids, min(k, len(ordered_ids)))


# ---------------------------------------------------------------------------
# Reranker runner
# ---------------------------------------------------------------------------

def run_reranker_on_fixtures(
    model_key: str,
    queries: list[dict],
    thresholds: list[float],
    top_k: int = FAZ1_TOP_K,
) -> dict[str, Any]:
    """Bir model için tüm threshold'larda fixture değerlendirmesi yap."""
    model_info = MODEL_REGISTRY[model_key]
    model_id = model_info["model_id"]

    logger.info("Model yükleniyor: %s (%s)", model_key, model_id)

    try:
        from sentence_transformers import CrossEncoder  # type: ignore[import]
    except ImportError:
        logger.error(
            "sentence-transformers kurulu değil! "
            "pip install 'sentence-transformers>=3.0.0'"
        )
        return _mock_result(model_key, model_info, queries, thresholds, top_k)

    t_load = time.perf_counter()
    model = CrossEncoder(model_id, device="cpu")
    load_ms = (time.perf_counter() - t_load) * 1000
    logger.info("Model yüklendi: %.0fms", load_ms)

    per_threshold_results: dict[str, Any] = {}

    for thr in thresholds:
        thr_key = str(thr)
        precision_scores: list[float] = []
        mrr_scores: list[float] = []
        ndcg_scores: list[float] = []
        baseline_precisions: list[float] = []
        per_query_stats: list[dict] = []

        t_eval = time.perf_counter()

        for q in queries:
            candidates = q["candidates"]
            relevant_ids = {c["id"] for c in candidates if c["relevance"] == 1}
            query_text = q["query"]

            pairs = [[query_text, c["text"]] for c in candidates]
            scores: list[float] = model.predict(pairs).tolist()

            scored = sorted(
                zip(scores, candidates),
                key=lambda x: x[0],
                reverse=True,
            )

            # threshold filtrele
            above = [(s, c) for s, c in scored if s >= thr]
            final = above[:top_k]
            ranked_ids = [c["id"] for _, c in final]
            all_ranked_ids = [c["id"] for _, c in scored]

            p5 = precision_at_k(ranked_ids, relevant_ids, top_k)
            rr = reciprocal_rank(ranked_ids, relevant_ids)
            nd = ndcg_at_k(ranked_ids, relevant_ids, top_k)
            bp = baseline_precision(candidates)

            precision_scores.append(p5)
            mrr_scores.append(rr)
            ndcg_scores.append(nd)
            baseline_precisions.append(bp)

            per_query_stats.append({
                "query_id": q["id"],
                "query": query_text,
                "law_domain": q.get("law_domain"),
                "precision_at_5": round(p5, 4),
                "mrr_at_5": round(rr, 4),
                "ndcg_at_5": round(nd, 4),
                "baseline_precision": round(bp, 4),
                "above_threshold_count": len(above),
                "top_k_returned": len(final),
                "top_1_citation": final[0][1]["citation"] if final else None,
                "top_1_score": round(final[0][0], 4) if final else None,
                "relevant_count": len(relevant_ids),
            })

        eval_ms = (time.perf_counter() - t_eval) * 1000

        def mean(lst: list[float]) -> float:
            return sum(lst) / len(lst) if lst else 0.0

        avg_p5 = mean(precision_scores)
        avg_bp = mean(baseline_precisions)
        precision_gain = avg_p5 - avg_bp

        per_threshold_results[thr_key] = {
            "threshold": thr,
            "avg_precision_at_5": round(avg_p5, 4),
            "avg_mrr_at_5": round(mean(mrr_scores), 4),
            "avg_ndcg_at_5": round(mean(ndcg_scores), 4),
            "avg_baseline_precision": round(avg_bp, 4),
            "precision_gain_vs_baseline": round(precision_gain, 4),
            "passes_faz1_criterion": precision_gain >= MIN_PRECISION_GAIN,
            "eval_latency_ms": round(eval_ms, 1),
            "per_query": per_query_stats,
        }

        status = "✅ GEÇTİ" if precision_gain >= MIN_PRECISION_GAIN else "❌ BAŞARISIZ"
        logger.info(
            "  thr=%.1f | P@5=%.3f | baseline=%.3f | gain=%.3f | %s",
            thr, avg_p5, avg_bp, precision_gain, status,
        )

    return {
        "model_key": model_key,
        "model_id": model_id,
        "model_info": model_info,
        "model_load_ms": round(load_ms, 1),
        "per_threshold": per_threshold_results,
    }


def _mock_result(
    model_key: str,
    model_info: dict,
    queries: list[dict],
    thresholds: list[float],
    top_k: int,
) -> dict[str, Any]:
    """sentence-transformers yokken mock sonuç — iskelet testi için."""
    logger.warning("MOCK MOD: sentence-transformers kurulu değil, rastgele skorlar kullanılıyor.")
    import random
    per_threshold_results = {}
    for thr in thresholds:
        per_threshold_results[str(thr)] = {
            "threshold": thr,
            "avg_precision_at_5": 0.0,
            "avg_mrr_at_5": 0.0,
            "avg_ndcg_at_5": 0.0,
            "avg_baseline_precision": 0.0,
            "precision_gain_vs_baseline": 0.0,
            "passes_faz1_criterion": False,
            "eval_latency_ms": 0.0,
            "mock": True,
            "per_query": [],
        }
    return {
        "model_key": model_key,
        "model_id": model_info["model_id"],
        "model_info": model_info,
        "model_load_ms": 0.0,
        "mock": True,
        "per_threshold": per_threshold_results,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    model_results: list[dict],
    thresholds: list[float],
    fixture_path: Path,
    num_queries: int,
) -> dict[str, Any]:
    """Tüm model sonuçlarını birleştir ve öneri üret."""

    best_threshold_per_model: dict[str, dict] = {}
    for r in model_results:
        best_thr = None
        best_p5 = -1.0
        for thr_key, thr_data in r["per_threshold"].items():
            if thr_data["avg_precision_at_5"] > best_p5 and thr_data["passes_faz1_criterion"]:
                best_p5 = thr_data["avg_precision_at_5"]
                best_thr = thr_key
        best_threshold_per_model[r["model_key"]] = {
            "best_threshold": best_thr,
            "best_precision_at_5": round(best_p5, 4),
        }

    # Öneri mantığı
    primary_key = "mmarco"
    primary_result = next((r for r in model_results if r["model_key"] == primary_key), None)
    primary_passes = primary_result and any(
        td["passes_faz1_criterion"]
        for td in primary_result["per_threshold"].values()
    )

    if primary_passes:
        recommendation = (
            f"✅ PRIMARY MODEL ONAYLANDI: {MODEL_REGISTRY[primary_key]['model_id']} "
            f"(Faz 1 D-2 kararı doğrulandı). "
            f"Önerilen threshold: {best_threshold_per_model.get(primary_key, {}).get('best_threshold', '0.7')}"
        )
        chosen_model = primary_key
        faz1_decision = "CONFIRMED"
    else:
        recommendation = (
            "⚠️ PRIMARY MODEL YETERSİZ: mmarco Faz 1 kriterini geçemedi. "
            "Alternatif değerlendirme: BAAI/bge-reranker-v2-m3 (bge_m3) çalıştırın "
            "veya mmarco modelini Türkçe hukuki veriye fine-tune edin. "
            "Koordinatör onayı gerekir."
        )
        chosen_model = None
        faz1_decision = "NEEDS_REVIEW"

    results_by_model = {r["model_key"]: r for r in model_results}

    return {
        "report_meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "fixture_path": str(fixture_path),
            "num_queries": num_queries,
            "threshold_grid": thresholds,
            "top_k": FAZ1_TOP_K,
            "faz1_acceptance_criterion": (
                f"top-{FAZ1_TOP_K} precision ≥ baseline top-{num_queries} precision "
                f"(gain ≥ {MIN_PRECISION_GAIN})"
            ),
        },
        "models_evaluated": [
            {
                "key": r["model_key"],
                "model_id": r["model_id"],
                "faz1_status": r["model_info"]["faz1_status"],
                "mock": r.get("mock", False),
            }
            for r in model_results
        ],
        "results": results_by_model,
        "best_threshold_per_model": best_threshold_per_model,
        "faz1_decision": faz1_decision,
        "chosen_model": chosen_model,
        "recommendation": recommendation,
        "missing_metrics": [
            "Gerçek Milvus retrieval sıralaması (simüle edildi: fixture sırasıyla aynı)",
            "Avukat onaylı relevanslık etiketleri (mevcut: teknik ekip kestirimi)",
            "50+ soruluk tam eval seti (mevcut: 8 soruluk pilot)",
            "İçtihat/ictihat veri kategorisi (Faz 1 scope dışı, mevzuat-only)",
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Faz 1 Reranker A/B Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=FAZ1_MODELS,
        choices=list(MODEL_REGISTRY.keys()),
        help=f"Değerlendirilecek modeller (varsayılan: {FAZ1_MODELS})",
    )
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=float,
        default=FAZ1_THRESHOLD_GRID,
        help=f"Threshold grid (varsayılan: {FAZ1_THRESHOLD_GRID})",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=FIXTURES_PATH,
        help="Fixture JSON dosyası yolu",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Rapor çıktı yolu (varsayılan: evaluation/reports/reranker_ab_<timestamp>.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Sadece fixture'ları yükle, model inference yapmadan çalıştır",
    )
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Fixture yükle
    if not args.fixtures.exists():
        logger.error("Fixture dosyası bulunamadı: %s", args.fixtures)
        return 1

    with open(args.fixtures, encoding="utf-8") as f:
        fixture_data = json.load(f)

    queries = fixture_data["queries"]
    logger.info(
        "Fixture yüklendi: %d sorgu, toplam %d aday passage",
        len(queries),
        sum(len(q["candidates"]) for q in queries),
    )

    if args.dry_run:
        logger.info("DRY RUN: Fixture yükleme başarılı. Model inference atlandı.")
        print(json.dumps({"status": "dry_run_ok", "queries_loaded": len(queries)}, indent=2))
        return 0

    # Model değerlendirme
    model_results: list[dict] = []
    for model_key in args.models:
        logger.info("=" * 60)
        logger.info("Model: %s (%s)", model_key, MODEL_REGISTRY[model_key]["model_id"])
        logger.info("=" * 60)
        result = run_reranker_on_fixtures(
            model_key=model_key,
            queries=queries,
            thresholds=args.thresholds,
            top_k=FAZ1_TOP_K,
        )
        model_results.append(result)

    # Rapor oluştur
    report = generate_report(
        model_results=model_results,
        thresholds=args.thresholds,
        fixture_path=args.fixtures,
        num_queries=len(queries),
    )

    # Raporu yaz
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output:
        out_path = args.output
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = REPORTS_DIR / f"reranker_ab_{ts}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info("Rapor yazıldı: %s", out_path)

    # Özet çıktı
    print("\n" + "=" * 60)
    print("FAZ 1 RERANKER A/B DEĞERLENDİRME ÖZET")
    print("=" * 60)
    print(f"Faz 1 Kararı: {report['faz1_decision']}")
    print(f"Öneri       : {report['recommendation']}")
    print("\nEksik metrikler:")
    for m in report["missing_metrics"]:
        print(f"  - {m}")
    print("=" * 60)

    return 0 if report["faz1_decision"] == "CONFIRMED" else 1


if __name__ == "__main__":
    sys.exit(main())
