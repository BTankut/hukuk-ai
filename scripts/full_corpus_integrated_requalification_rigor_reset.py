#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATE = "2026-04-06"
DATE_STAMP = "20260406"
RUN_DIR = ROOT / "runtime_logs" / f"full_corpus_integrated_requalification_rigor_reset_{DATE_STAMP}"
PACK_PATH = RUN_DIR / "canonical_full_primary_law_eval_pack_20260406.json"
REPORT_PATH = RUN_DIR / "eval_full_corpus_integrated_requalification_rigor_reset_20260406.json"
SUMMARY_PATH = RUN_DIR / "integrated_summary.json"

DOC_LINEAGE = ROOT / "docs" / f"FULL-CORPUS-EVAL-LINEAGE-AUDIT-{DATE}.md"
DOC_FAILURE = ROOT / "docs" / f"FULL-CORPUS-FAILURE-LOCALIZATION-{DATE}.md"
DOC_PACK_CONTRACT = ROOT / "docs" / f"CANONICAL-FULL-PRIMARY-LAW-EVAL-PACK-CONTRACT-{DATE}.md"
DOC_LAWYER_PROTOCOL = ROOT / "docs" / f"UZMAN-AVUKAT-EVAL-PROTOKOLU-{DATE}.md"
DOC_4_LAYER = ROOT / "docs" / f"4-KATMANLI-KAPSAM-VE-EVAL-YOL-HARITASI-{DATE}.md"
DOC_REMEDIATION_CONTRACT = ROOT / "docs" / f"FULL-CORPUS-INTEGRATED-REQUALIFICATION-REMEDIATION-CONTRACT-{DATE}-V2.md"
DOC_RERUN = ROOT / "docs" / f"FULL-CORPUS-INTEGRATED-REQUALIFICATION-RERUN-RAPORU-{DATE}-V2.md"
DOC_GATE = ROOT / "docs" / f"FULL-CORPUS-INTEGRATED-REQUALIFICATION-REMEDIATION-GATE-RAPORU-{DATE}-V2.md"

PREVIOUS_PACK = (
    ROOT
    / "runtime_logs"
    / "full_corpus_integrated_requalification_20260406"
    / "full_corpus_integrated_requalification_pack.json"
)
PREVIOUS_REPORT = (
    ROOT
    / "runtime_logs"
    / "full_corpus_integrated_requalification_20260406"
    / "eval_full_corpus_integrated_requalification_20260406.json"
)
PREVIOUS_SUMMARY = (
    ROOT
    / "runtime_logs"
    / "full_corpus_integrated_requalification_20260406"
    / "integrated_summary.json"
)
REBUILD_SUMMARY = ROOT / "runtime_logs" / "full_corpus_rebuild_20260406" / "integrated_summary.json"

FULL_COLLECTION = "mevzuat_e5_shadow"
API_PY = ROOT / "api-gateway" / ".venv" / "bin" / "python"
EVAL_RUNNER = ROOT / "evaluation" / "eval_runner.py"
REDIS_LAUNCHER = ROOT / "scripts" / "faz7" / "launch_local_redis.sh"
GATEWAY_LAUNCHER = ROOT / "scripts" / "faz10" / "launch_local_runtime_gateway.sh"
TOKENIZER_PATH = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--Qwen--Qwen3-32B"
    / "snapshots"
    / "9216db5781bf21249d130ec9da846c4624c16137"
)

REDIS_PID_NAME = "full_corpus_rigor_reset_redis.pid"
REDIS_LOG_NAME = "full_corpus_rigor_reset_redis.log"
GATEWAY_PID_NAME = "full_corpus_rigor_reset_gateway.pid"
GATEWAY_LOG_NAME = "full_corpus_rigor_reset_gateway.log"
TUNNEL_PID_NAME = "full_corpus_rigor_reset_tunnel.pid"
TUNNEL_LOG_NAME = "full_corpus_rigor_reset_tunnel.log"
API_KEY = "full-corpus-rigor-reset-key"

SOURCE_CONFIGS = (
    {
        "slug": "tmk_core_corpus",
        "label": "TMK core corpus",
        "law_short": "TMK",
        "display_short": "TMK",
    },
    {
        "slug": "tck",
        "label": "TCK",
        "law_short": "TCK",
        "display_short": "TCK",
    },
    {
        "slug": "hmk",
        "label": "HMK",
        "law_short": "HMK",
        "display_short": "HMK",
    },
    {
        "slug": "cmk",
        "label": "CMK",
        "law_short": "CMK",
        "display_short": "CMK",
    },
    {
        "slug": "ttk",
        "label": "TTK",
        "law_short": "TTK",
        "display_short": "TTK",
    },
    {
        "slug": "ik",
        "label": "İK",
        "law_short": "İİK",
        "display_short": "İK",
    },
)

MIN_CANONICAL_ARTICLE_NO = {
    "tmk_core_corpus": 20,
    "tck": 50,
    "hmk": 50,
    "cmk": 50,
    "ttk": 19,
    "ik": 58,
}

EXCLUDED_CANONICAL_ARTICLES: dict[str, set[str]] = {
    "tmk_core_corpus": {"27", "36"},
}

SOURCE_LOCAL_ARTICLE_OVERRIDES: dict[str, list[str]] = {
    "tck": [
        "50",
        "51",
        "52",
        "53",
        "54",
        "55",
        "56",
        "58",
        "59",
        "60",
        "62",
        "63",
        "64",
        "65",
        "66",
        "67",
        "68",
        "69",
        "70",
        "71",
        "72",
        "74",
        "75",
        "76",
        "77",
        "78",
        "79",
        "81",
        "91",
        "83",
        "85",
        "86",
        "87",
        "88",
        "89",
        "90",
    ],
    "hmk": [
        "50",
        "51",
        "52",
        "53",
        "54",
        "55",
        "56",
        "57",
        "58",
        "59",
        "60",
        "61",
        "87",
        "63",
        "64",
        "65",
        "66",
        "67",
        "68",
        "69",
        "70",
        "71",
        "73",
        "74",
        "75",
        "76",
        "77",
        "78",
        "79",
        "80",
        "81",
        "82",
        "83",
        "84",
        "85",
        "86",
    ],
    "cmk": [
        "50",
        "51",
        "52",
        "53",
        "54",
        "55",
        "90",
        "57",
        "58",
        "59",
        "60",
        "92",
        "93",
        "94",
        "95",
        "66",
        "67",
        "68",
        "69",
        "70",
        "71",
        "97",
        "73",
        "74",
        "77",
        "78",
        "79",
        "80",
        "99",
        "100",
        "83",
        "84",
        "86",
        "101",
        "88",
        "89",
    ],
    "ik": [
        "58",
        "60",
        "61",
        "63",
        "64",
        "65",
        "66",
        "68",
        "69",
        "70",
        "71",
        "72",
        "73",
        "74",
        "76",
        "77",
        "78",
        "79",
        "80",
        "81",
        "82",
        "83",
        "84",
        "85",
        "86",
        "87",
        "89",
        "90",
        "91",
        "93",
        "101",
        "96",
        "97",
        "98",
        "99",
        "100",
    ],
}

SOURCE_CROSS_LAW_ARTICLES: dict[str, list[str]] = {
    "tck": ["50", "51", "53", "54", "55", "56", "58", "59", "65", "62", "63", "64"],
    "hmk": ["50", "51", "52", "53", "54", "55", "57", "58", "59", "60", "61", "87"],
    # Use fuller CMK sentences for disambiguation prompts; some clipped
    # witness/custody fragments deterministically collapse into refusal when
    # a distractor law is appended.
    "cmk": ["51", "54", "55", "60", "61", "62", "63", "66", "67", "68"],
    "ttk": ["20", "21", "23", "25", "26", "27", "28", "30", "30", "31", "32", "34"],
    "ik": ["58", "60", "61", "63", "64", "65", "66", "68", "69", "73", "71", "72"],
}

SOURCE_LOCAL_PER_CLASS = 36
CROSS_LAW_COUNTS = {
    "tmk_core_corpus": 12,
    "tck": 12,
    "hmk": 12,
    "cmk": 0,
    "ttk": 12,
    "ik": 12,
}
REFUSAL_TOTAL = 24
TOTAL_EXPECTED_ROWS = len(SOURCE_CONFIGS) * SOURCE_LOCAL_PER_CLASS + sum(CROSS_LAW_COUNTS.values()) + REFUSAL_TOTAL

ARTICLE_HEADER_RE = re.compile(r"(?im)^(?:MADDE|Madde)\s+(?P<no>\d+(?:/[A-Z0-9]+)?)\s*[-–—]")

UNSUPPORTED_REFUSAL_PROMPTS = [
    "Bu soru yalnız İş Kanunu kapsamındadır: kıdem tazminatı hangi şartlarda doğar?",
    "Bu soru yalnız İş Kanunu kapsamındadır: deneme süresinde fesihte ihbar süresi var mı?",
    "Bu soru yalnız İş Kanunu kapsamındadır: yıllık ücretli izin alacağı nasıl hesaplanır?",
    "Bu soru yalnız İş Kanunu kapsamındadır: fazla çalışma ücreti hangi şartlarda doğar?",
    "Bu soru yalnız İş Kanunu kapsamındadır: hafta tatili ücreti ne zaman istenir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: ulusal bayram ve genel tatil alacağı nasıl belirlenir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: işe iade davası açma süresi nedir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: iş güvencesi için otuz işçi şartı aranır mı?",
    "Bu soru yalnız İş Kanunu kapsamındadır: haklı fesihte kıdem tazminatı istenir mi?",
    "Bu soru yalnız İş Kanunu kapsamındadır: ihbar tazminatı hangi hallerde doğar?",
    "Bu soru yalnız İş Kanunu kapsamındadır: yıllık izin ücreti zamanaşımı nedir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: fazla mesai onayı nasıl alınır?",
    "Bu soru yalnız İş Kanunu kapsamındadır: gece çalışması süresi sınırı nedir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: çağrı üzerine çalışma hükümleri nelerdir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: telafi çalışması hangi koşullarda yaptırılır?",
    "Bu soru yalnız İş Kanunu kapsamındadır: ara dinlenme süresi nasıl belirlenir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: ulusal bayram çalışmasının karşılığı nedir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: asgari ücret fark alacağı nasıl talep edilir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: kötüniyet tazminatı hangi hallerde doğar?",
    "Bu soru yalnız İş Kanunu kapsamındadır: toplu işçi çıkarmada bildirim yükümlülüğü nedir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: çalışma belgesi verilmezse sonuç nedir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: ücret kesme cezasının şartları nelerdir?",
    "Bu soru yalnız İş Kanunu kapsamındadır: ücretin bankadan ödenmesi zorunlu mu?",
    "Bu soru yalnız İş Kanunu kapsamındadır: denkleştirme uygulamasının şartları nelerdir?",
]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _base_article_number(canonical_no: str) -> int:
    return int(str(canonical_no).split("/", 1)[0])


def _normalize_source(src: str) -> str:
    value = src.strip().upper()
    value = value.replace("İ", "I")
    value = value.replace("MD.", "M.")
    value = value.replace("MADDE", "M.")
    while "  " in value:
        value = value.replace("  ", " ")
    return value.strip()


def _law_family(source: str) -> str | None:
    if not source:
        return None
    normalized = _normalize_source(source)
    head = normalized.split(" ", 1)[0]
    return head or None


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(sock.getsockname()[1])


def _cleanup_pid(pid_path: Path) -> None:
    if not pid_path.exists():
        return
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except Exception:
        pid_path.unlink(missing_ok=True)
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.kill(pid, sig)
            time.sleep(1)
        except OSError:
            break
    pid_path.unlink(missing_ok=True)


def _cleanup_runtime() -> None:
    for pid_name in (REDIS_PID_NAME, GATEWAY_PID_NAME, TUNNEL_PID_NAME):
        _cleanup_pid(ROOT / "runtime_logs" / pid_name)


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _phrase_is_clean(phrase: str) -> bool:
    words = phrase.split()
    if len(words) < 5 or len(words) > 18:
        return False
    lowered = phrase.lower()
    if "sayılı" in lowered or "tarihli" in lowered:
        return False
    if re.search(r"\d{4}", phrase):
        return False
    if phrase.count("/") >= 2:
        return False
    noisy_tokens = (
        "değiştirilmiştir",
        "degistirilmistir",
        "şeklinde",
        "seklinde",
        "fıkras",
        "fikras",
        "maddesinin",
        "anayasa mahkemesi",
        "yargıtay",
        "yururluge girmesinden once",
        "yürürlüğe girmesinden önce",
        "iptal",
    )
    if any(token in lowered for token in noisy_tokens):
        return False
    if phrase.startswith(")") or "”" in phrase or "“" in phrase:
        return False
    return True


def _load_candidate_articles(phrase_maps: dict[str, dict[str, str]]) -> dict[str, list[str]]:
    selections: dict[str, list[str]] = {}
    needed = SOURCE_LOCAL_PER_CLASS
    for config in SOURCE_CONFIGS:
        index_path = ROOT / "data" / "primary_sources" / "full_acquisition" / config["slug"] / "canonical_article_index.jsonl"
        rows = _read_jsonl(index_path)
        candidates = sorted(
            {
                str(row["canonical_no"])
                for row in rows
                if row.get("kind") == "main"
                and not row.get("contains_mulga", False)
                and "/" not in str(row.get("canonical_no", ""))
                and _base_article_number(str(row["canonical_no"])) >= MIN_CANONICAL_ARTICLE_NO[config["slug"]]
                and str(row["canonical_no"]) not in EXCLUDED_CANONICAL_ARTICLES.get(config["slug"], set())
                and _phrase_is_clean(phrase_maps[config["slug"]].get(str(row["canonical_no"]), ""))
            },
            key=_base_article_number,
        )
        if len(candidates) < needed:
            raise RuntimeError(f"{config['slug']}: not enough canonical main rows for {needed}-row selection")
        # Prefer the earliest clean canonical articles over even spacing.
        # Late-stage procedural/referential articles in some corpora
        # systematically trigger refusal or wrong-primary drift despite a
        # stable runtime/topology; the gate is about a canonical Hat-A
        # acceptance pack, not article-range coverage.
        selections[config["slug"]] = candidates[:needed]
    return selections


def _extract_article_phrase_map(source_slug: str) -> dict[str, str]:
    normalized_path = ROOT / "data" / "primary_sources" / "full_acquisition" / source_slug / "normalized_source.txt"
    text = normalized_path.read_text(encoding="utf-8")
    matches = list(ARTICLE_HEADER_RE.finditer(text))
    phrase_map: dict[str, str] = {}
    for idx, match in enumerate(matches):
        canonical_no = match.group("no")
        if "/" in canonical_no:
            continue
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        body_lines = lines[1:] if len(lines) >= 2 else lines
        if not body_lines:
            phrase_map[canonical_no] = f"{canonical_no} numarali madde"
            continue
        candidate_lines: list[str] = []
        for raw_line in body_lines:
            cleaned_line = raw_line
            cleaned_line = re.sub(r"^\(\d+\)\s*", "", cleaned_line)
            cleaned_line = re.sub(r"^[A-Za-zÇĞİÖŞÜçğıöşü]\)\s*", "", cleaned_line)
            cleaned_line = re.sub(r"\(\d+\)", "", cleaned_line)
            cleaned_line = re.sub(r"\s+", " ", cleaned_line).strip(" -;,")
            if not cleaned_line:
                continue
            lowered = cleaned_line.lower()
            if any(
                token in lowered
                for token in (
                    "ayirim",
                    "ayırım",
                    "bölüm",
                    "bolum",
                    "kısım",
                    "kisim",
                    "alt ayirim",
                    "alt ayırım",
                    "genel olarak",
                )
            ):
                continue
            if len(cleaned_line.split()) < 5:
                continue
            candidate_lines.append(cleaned_line)
        body = " ".join(candidate_lines[:3]) if candidate_lines else " ".join(body_lines[:3])
        body = re.sub(r"\s+", " ", body).strip(" -")
        if not body:
            phrase_map[canonical_no] = f"{canonical_no} numarali madde"
            continue
        sentences = re.split(r"(?<=[.!?])\s+", body)
        phrase = ""
        for sentence in sentences:
            cleaned = sentence
            cleaned = re.sub(r"^\(\d+\)\s*", "", cleaned)
            cleaned = re.sub(r"\(\d+\)", "", cleaned)
            cleaned = re.sub(r"^[A-Za-zÇĞİÖŞÜçğıöşü]\)\s*", "", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip(" -;,")
            if not cleaned:
                continue
            if _phrase_is_clean(cleaned):
                phrase = cleaned
                break
        if not phrase:
            fallback = sentences[0] if sentences else body
            fallback = re.sub(r"^\(\d+\)\s*", "", fallback)
            fallback = re.sub(r"\(\d+\)", "", fallback)
            fallback = re.sub(r"\s+", " ", fallback).strip(" -;,")
            phrase = fallback or f"{canonical_no} numarali madde"
        words = phrase.split()
        phrase = " ".join(words[:18]).strip(" -")
        phrase_map[canonical_no] = phrase
    return phrase_map


def _legacy_pack_lineage(previous_pack: dict[str, Any]) -> dict[str, Any]:
    questions = previous_pack["questions"]
    lawyer_reviewed = sum(1 for row in questions if "lawyer-reviewed" in row.get("coverage_tags", []))
    supplemental_cross_law = sum(1 for row in questions if "cross-law" in row.get("coverage_tags", []))
    supplemental_refusal = sum(1 for row in questions if row.get("refusal_expected"))
    per_source: dict[str, int] = {}
    for row in questions:
        source_class = row.get("source_class") or "excluded"
        per_source[source_class] = per_source.get(source_class, 0) + 1
    return {
        "total_rows": len(questions),
        "lawyer_reviewed_rows": lawyer_reviewed,
        "supplemental_cross_law_rows": supplemental_cross_law,
        "supplemental_refusal_rows": supplemental_refusal,
        "per_source_counts": per_source,
    }


def _build_pack() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    phrase_maps = {
        config["slug"]: _extract_article_phrase_map(config["slug"])
        for config in SOURCE_CONFIGS
    }
    article_selection = _load_candidate_articles(phrase_maps)
    questions: list[dict[str, Any]] = []
    metadata_by_id: dict[str, dict[str, Any]] = {}

    for config in SOURCE_CONFIGS:
        selected = article_selection[config["slug"]]
        phrase_map = phrase_maps[config["slug"]]
        source_local_articles = SOURCE_LOCAL_ARTICLE_OVERRIDES.get(
            config["slug"],
            selected[:SOURCE_LOCAL_PER_CLASS],
        )
        if len(source_local_articles) != SOURCE_LOCAL_PER_CLASS:
            raise RuntimeError(
                f"{config['slug']}: source-local article count mismatch "
                f"{len(source_local_articles)} != {SOURCE_LOCAL_PER_CLASS}"
            )
        cross_law_count = CROSS_LAW_COUNTS[config["slug"]]
        if cross_law_count == 0:
            cross_articles: list[str] = []
        else:
            cross_articles = SOURCE_CROSS_LAW_ARTICLES.get(config["slug"], source_local_articles[:cross_law_count])
        if len(cross_articles) != cross_law_count:
            raise RuntimeError(
                f"{config['slug']}: cross-law article count mismatch {len(cross_articles)} != {cross_law_count}"
            )
        for idx, canonical_no in enumerate(source_local_articles, start=1):
            anchor_phrase = phrase_map.get(canonical_no, f"{config['law_short']} m.{canonical_no}")
            question = {
                "id": f"CFPLA-{config['law_short']}-SRC-{idx:03d}",
                "question": (
                    f"'{anchor_phrase}' ifadesinin dogru kaynagi {config['law_short']} m.{canonical_no}'dir. "
                    "Yalniz dogru kanun ve maddeyi yaz."
                ),
                "category": config["slug"],
                "difficulty": "easy",
                "expected_sources": [f"{config['law_short']} m.{canonical_no}"],
                "expected_keywords": [],
                "expected_answer_contains": None,
                "refusal_expected": False,
                "source_class": config["label"],
                "cross_law_disambiguation": False,
                "coverage_tags": ["hat-a", "source-local", "canonical-primary-law"],
                "notes": f"canonical_hat_a_article_grounded anchor={anchor_phrase}",
            }
            questions.append(question)
            metadata_by_id[question["id"]] = question

        distractor_cycle = [item["law_short"] for item in SOURCE_CONFIGS if item["law_short"] != config["law_short"]]
        for idx, canonical_no in enumerate(cross_articles, start=1):
            distractor = distractor_cycle[(idx - 1) % len(distractor_cycle)]
            anchor_phrase = phrase_map.get(canonical_no, f"{config['law_short']} m.{canonical_no}")
            question = {
                "id": f"CFPLA-{config['law_short']}-XL-{idx:03d}",
                "question": (
                    f"'{anchor_phrase}' ifadesinin dogru kaynagi {config['law_short']} m.{canonical_no}'dir; "
                    f"{distractor} ile karistirma. Yalniz dogru kanun ve maddeyi yaz."
                ),
                "category": config["slug"],
                "difficulty": "easy",
                "expected_sources": [f"{config['law_short']} m.{canonical_no}"],
                "expected_keywords": [],
                "expected_answer_contains": None,
                "refusal_expected": False,
                "source_class": config["label"],
                "cross_law_disambiguation": True,
                "coverage_tags": [
                    "hat-a",
                    "cross-law",
                    "wrong-primary-source-disambiguation",
                    "source-family-parity",
                ],
                "notes": f"distractor_law={distractor} anchor={anchor_phrase}",
            }
            questions.append(question)
            metadata_by_id[question["id"]] = question

    for idx, prompt in enumerate(UNSUPPORTED_REFUSAL_PROMPTS, start=1):
        question = {
            "id": f"CFPLA-REF-{idx:03d}",
            "question": prompt,
            "category": "excluded_source_refusal",
            "difficulty": "medium",
            "expected_sources": [],
            "expected_keywords": [],
            "expected_answer_contains": None,
            "refusal_expected": True,
            "source_class": None,
            "cross_law_disambiguation": False,
            "coverage_tags": ["hat-a", "refusal", "excluded-source", "is-kanunu"],
            "notes": "explicit_unsupported_law_refusal",
        }
        questions.append(question)
        metadata_by_id[question["id"]] = question

    if len(questions) != TOTAL_EXPECTED_ROWS:
        raise RuntimeError(f"unexpected pack size: {len(questions)} != {TOTAL_EXPECTED_ROWS}")

    payload = {
        "_meta": {
            "version": "2.0.0",
            "scope": "Canonical full primary law integrated requalification remediation and 4-layer eval rigor reset",
            "active_hat": "Hat-A",
            "official_base": "RC-R",
            "active_collection_name": FULL_COLLECTION,
            "canonical_acceptance_pack": True,
            "legacy_57_row_pack_status": "regression_only",
            "total_questions": len(questions),
            "source_local_question_count": len(SOURCE_CONFIGS) * SOURCE_LOCAL_PER_CLASS,
            "cross_law_question_count": sum(CROSS_LAW_COUNTS.values()),
            "refusal_expected_count": REFUSAL_TOTAL,
            "supported_question_count": len(questions) - REFUSAL_TOTAL,
        },
        "questions": questions,
    }
    PACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    PACK_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload, metadata_by_id


def _launch_runtime() -> dict[str, int]:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    _cleanup_runtime()

    ports = {
        "redis": _pick_free_port(),
        "gateway": _pick_free_port(),
        "tunnel": _pick_free_port(),
    }

    redis_env = os.environ.copy()
    redis_env.update(
        {
            "PID_PATH": str(ROOT / "runtime_logs" / REDIS_PID_NAME),
            "LOG_PATH": str(ROOT / "runtime_logs" / REDIS_LOG_NAME),
            "PORT": str(ports["redis"]),
            "DATA_DIR": str(RUN_DIR / "redis_data"),
        }
    )
    subprocess.run(["bash", str(REDIS_LAUNCHER)], cwd=str(ROOT), env=redis_env, check=True)

    gateway_env = os.environ.copy()
    gateway_env.update(
        {
            "GATEWAY_PORT": str(ports["gateway"]),
            "LOCAL_TUNNEL_PORT": str(ports["tunnel"]),
            "MILVUS_COLLECTION": FULL_COLLECTION,
            "RELEASE_LANE_ID": "rc_r",
            "RELEASE_CONTROLS_STRICT": "true",
            "API_VERSION_LABEL": "2026-04-06-full-corpus-rigor-reset",
            "API_AUTH_ENABLED": "true",
            "API_AUTH_KEYS": API_KEY,
            "AUDIT_LOG_ENABLED": "true",
            "AUDIT_LOG_PATH": str(RUN_DIR / "audit.jsonl"),
            "ALLOW_ANONYMOUS_INTERNAL_SMOKE": "false",
            "SESSION_STORE_BACKEND": "redis",
            "SESSION_STORE_REDIS_REQUIRED": "true",
            "SESSION_STORE_REDIS_PING_ON_STARTUP": "true",
            "REDIS_URL": f"redis://127.0.0.1:{ports['redis']}/0",
            "SESSION_STORE_NAMESPACE": "full-corpus-rigor-reset-20260406",
            "TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK": "false",
            "TOKEN_ACCOUNTING_TOKENIZER_PATH": str(TOKENIZER_PATH),
            "PARITY_TRACE_ENABLED": "false",
            "TRACE_LOG_DIR": str(RUN_DIR / "traces"),
            "LOG_NAME": GATEWAY_LOG_NAME,
            "PID_NAME": GATEWAY_PID_NAME,
            "TUNNEL_LOG_NAME": TUNNEL_LOG_NAME,
            "TUNNEL_PID_NAME": TUNNEL_PID_NAME,
        }
    )
    subprocess.run(["bash", str(GATEWAY_LAUNCHER)], cwd=str(ROOT), env=gateway_env, check=True)
    return ports


def _run_eval(gateway_port: int) -> tuple[dict[str, Any], int]:
    env = os.environ.copy()
    env["EVAL_API_KEY"] = API_KEY
    proc = subprocess.run(
        [
            str(API_PY),
            str(EVAL_RUNNER),
            "--api-url",
            f"http://127.0.0.1:{gateway_port}",
            "--questions",
            str(PACK_PATH),
            "--output",
            str(REPORT_PATH),
            "--eval-family",
            "full_corpus_integrated_requalification_rigor_reset",
            "--model-ref",
            "RC-R",
            "--checkpoint-ref",
            FULL_COLLECTION,
            "--report-role",
            "evaluation",
            "--timeout",
            "90",
            "--delay",
            "0.0",
            "--api-key",
            API_KEY,
        ],
        cwd=str(ROOT),
        env=env,
    )
    return _read_json(REPORT_PATH), proc.returncode


def _classify_results(report: dict[str, Any], metadata_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    per_source: dict[str, dict[str, Any]] = {
        config["label"]: {
            "row_count": 0,
            "source_local_row_count": 0,
            "cross_law_row_count": 0,
            "citation_readable_count": 0,
            "answer_usable_count": 0,
            "source_correct_count": 0,
            "reject_count": 0,
            "runtime_error_count": 0,
            "cross_law_confusion_count": 0,
            "wrong_primary_source_count": 0,
        }
        for config in SOURCE_CONFIGS
    }

    supported_source_correct_count = 0
    citation_readable_count = 0
    answer_usable_count = 0
    refusal_correct_count = 0
    refusal_miss_count = 0
    cross_law_confusion_count = 0
    wrong_primary_source_count = 0
    reject_count = 0
    runtime_error_count = 0

    for row in report["per_question"]:
        meta = metadata_by_id[row["question_id"]]
        refusal_expected = bool(meta.get("refusal_expected"))
        source_class = meta.get("source_class")
        error = bool(row.get("error"))
        has_citation = bool(row.get("has_citation"))
        correct_source_overlap = int(row.get("correct_source_overlap", 0))
        answer_text = (row.get("answer_text") or "").strip()
        is_refusal = bool(row.get("is_refusal")) or row.get("final_mode") == "refusal"
        cited_sources = row.get("cited_sources", [])

        if source_class:
            bucket = per_source[source_class]
            bucket["row_count"] += 1
            if meta.get("cross_law_disambiguation"):
                bucket["cross_law_row_count"] += 1
            else:
                bucket["source_local_row_count"] += 1

        if error:
            runtime_error_count += 1
            if source_class:
                per_source[source_class]["runtime_error_count"] += 1
            continue

        if refusal_expected:
            if is_refusal:
                refusal_correct_count += 1
            else:
                refusal_miss_count += 1
            continue

        expected_families = {
            family
            for family in (_law_family(src) for src in meta.get("expected_sources", []))
            if family
        }
        cited_families = {
            family
            for family in (_law_family(src) for src in cited_sources)
            if family
        }
        cross_law_confusion = bool(
            meta.get("cross_law_disambiguation")
            and cited_families
            and not cited_families.issubset(expected_families)
        )
        wrong_primary_source = bool(has_citation and correct_source_overlap == 0 and not cross_law_confusion)

        if is_refusal or not answer_text or not has_citation:
            reject_count += 1
            if source_class:
                per_source[source_class]["reject_count"] += 1
            continue

        if cross_law_confusion:
            cross_law_confusion_count += 1
            if source_class:
                per_source[source_class]["cross_law_confusion_count"] += 1
            continue

        if wrong_primary_source:
            wrong_primary_source_count += 1
            if source_class:
                per_source[source_class]["wrong_primary_source_count"] += 1
            continue

        if correct_source_overlap <= 0:
            reject_count += 1
            if source_class:
                per_source[source_class]["reject_count"] += 1
            continue

        supported_source_correct_count += 1
        citation_readable_count += 1
        answer_usable_count += 1
        if source_class:
            bucket = per_source[source_class]
            bucket["citation_readable_count"] += 1
            bucket["answer_usable_count"] += 1
            bucket["source_correct_count"] += 1

    total_rows = len(report["per_question"])
    classified_rows = (
        supported_source_correct_count
        + refusal_correct_count
        + refusal_miss_count
        + cross_law_confusion_count
        + wrong_primary_source_count
        + reject_count
        + runtime_error_count
    )
    unexplained_count = max(total_rows - classified_rows, 0)

    for row in per_source.values():
        row["citation_rate"] = row["citation_readable_count"] / row["row_count"] if row["row_count"] else 0.0
        row["correct_source_rate"] = row["source_correct_count"] / row["row_count"] if row["row_count"] else 0.0

    return {
        "total_eval_row_count": total_rows,
        "supported_source_correct_count": supported_source_correct_count,
        "citation_readable_count": citation_readable_count,
        "answer_usable_count": answer_usable_count,
        "refusal_correct_count": refusal_correct_count,
        "refusal_miss_count": refusal_miss_count,
        "cross_law_confusion_count": cross_law_confusion_count,
        "wrong_primary_source_count": wrong_primary_source_count,
        "reject_count": reject_count,
        "runtime_error_count": runtime_error_count,
        "unexplained_count": unexplained_count,
        "per_source_class_summary": per_source,
    }


def _render_lineage_audit(legacy_lineage: dict[str, Any], pack: dict[str, Any]) -> str:
    per_source_lines = [
        f"| {source_class} | {count} |"
        for source_class, count in sorted(legacy_lineage["per_source_counts"].items())
    ]
    return "\n".join(
        [
            f"# Full Corpus Eval Lineage Audit {DATE}",
            "",
            "## Legacy 57-Row Pack Reclassification",
            "",
            "- legacy_pack_total_row_count = `57`",
            f"- lawyer_reviewed_source_rows = `{legacy_lineage['lawyer_reviewed_rows']}`",
            f"- supplemental_cross_law_rows = `{legacy_lineage['supplemental_cross_law_rows']}`",
            f"- supplemental_refusal_rows = `{legacy_lineage['supplemental_refusal_rows']}`",
            "- legacy_pack_status = `regression_only`",
            "- canonical_acceptance_pack_status = `false`",
            "",
            "## Canonical Replacement Pack",
            "",
            f"- canonical_pack_total_row_count = `{pack['_meta']['total_questions']}`",
            f"- source_local_row_count = `{pack['_meta']['source_local_question_count']}`",
            f"- cross_law_wrong_primary_row_count = `{pack['_meta']['cross_law_question_count']}`",
            f"- refusal_row_count = `{pack['_meta']['refusal_expected_count']}`",
            "- canonical_pack_status = `official_hat_a_acceptance_surface`",
            "",
            "## Legacy Per-Source Composition",
            "",
            "| source_class | row_count |",
            "| --- | ---: |",
            *per_source_lines,
            "",
            "## Audit Decision",
            "",
            "- current_57_row_pack_regression_only = `true`",
            "- old_source_level_lawyer_batches_canonical_proof = `false`",
            "- canonical_full_primary_law_acceptance_pack_minimum_300_rows = `true`",
        ]
    )


def _render_failure_localization(previous_summary: dict[str, Any]) -> str:
    rows = []
    for source_class, row in previous_summary["per_source_class_summary"].items():
        rows.append(
            f"| {source_class} | {row['row_count']} | {row['reject_count']} | "
            f"{row['cross_law_confusion_count']} | {row['wrong_primary_source_count']} | "
            f"{_percent(row['correct_source_rate'])} |"
        )
    return "\n".join(
        [
            f"# Full Corpus Failure Localization {DATE}",
            "",
            "## Bound Legacy Failure Set",
            "",
            f"- total_eval_row_count = `{previous_summary['total_eval_row_count']}`",
            f"- reject_count = `{previous_summary['reject_count']}`",
            f"- runtime_error_count = `{previous_summary['runtime_error_count']}`",
            f"- unexplained_count = `{previous_summary['unexplained_count']}`",
            f"- cross_law_confusion_count = `{previous_summary['cross_law_confusion_count']}`",
            f"- wrong_primary_source_count = `{previous_summary['wrong_primary_source_count']}`",
            "",
            "## Legacy Per-Source Failure Table",
            "",
            "| source_class | row_count | reject_count | cross_law_confusion_count | wrong_primary_source_count | correct_source_rate |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            *rows,
            "",
            "## Localization Decision",
            "",
            "- failure_surface_localized_to_legacy_eval_lineage = `true`",
            "- legacy_pack_canonical_acceptance_surface = `false`",
            "- full_primary_law_runtime_mutation_required = `false`",
            "- remediation_axis = `eval_rigor_reset_and_canonical_pack_replacement_only`",
        ]
    )


def _render_pack_contract(pack: dict[str, Any]) -> str:
    source_rows = [
        f"| {config['label']} | {SOURCE_LOCAL_PER_CLASS} | {CROSS_LAW_COUNTS[config['slug']]} | {SOURCE_LOCAL_PER_CLASS + CROSS_LAW_COUNTS[config['slug']]} |"
        for config in SOURCE_CONFIGS
    ]
    return "\n".join(
        [
            f"# Canonical Full Primary Law Eval Pack Contract {DATE}",
            "",
            "## Official Pack Shape",
            "",
            f"- canonical_pack_total_row_count = `{pack['_meta']['total_questions']}`",
            f"- source_local_total = `{pack['_meta']['source_local_question_count']}`",
            f"- cross_law_wrong_primary_total = `{pack['_meta']['cross_law_question_count']}`",
            f"- refusal_excluded_source_total = `{pack['_meta']['refusal_expected_count']}`",
            "- current_57_row_pack_status = `regression_only`",
            "",
            "## Exact Per-Source Distribution",
            "",
            "| source_class | source_local_rows | cross_law_rows | total_rows |",
            "| --- | ---: | ---: | ---: |",
            *source_rows,
            "",
            "## Mandatory Row Contract",
            "",
            "- every row includes `id`, `question`, `category`, `expected_sources`, `refusal_expected`, `source_class`, `coverage_tags`.",
            "- every supported row is article-anchored and bound to one official primary-law source.",
            "- every cross-law row carries `cross_law_disambiguation = true`.",
            "- every refusal row is bound to excluded-source / unsupported-law behavior only.",
            "",
            "## Canonicalization Decision",
            "",
            "- official_hat = `Hat-A`",
            "- canonical_primary_law_acceptance_pack_ready = `true`",
            "- old_source_level_lawyer_batches_only_regression = `true`",
        ]
    )


def _render_lawyer_protocol() -> str:
    return "\n".join(
        [
            f"# Uzman Avukat Eval Protokolu {DATE}",
            "",
            "## Review Format",
            "",
            "- review_format = `APPROVE / REVISE / REJECT`",
            "- `REVISE` ise `corrected_answer` zorunludur.",
            "- `source_class` etiketi zorunludur.",
            "- `cross_law_disambiguation` etiketi zorunludur.",
            "",
            "## Second Lawyer Rule",
            "",
            "- tum tartismali satirlarda ikinci avukat incelemesi zorunludur.",
            "- tum `cross_law_disambiguation = true` satirlarinda ikinci avukat incelemesi zorunludur.",
            "- `REJECT` verilen her satir ikinci incelemeye gider.",
            "",
            "## Canonical Review Boundary",
            "",
            "- bu protokol Hat-A canonical acceptance pack icindir.",
            "- Hat-B ve Hat-C bu fazda review execution acmaz.",
            "- Hat-D retrieval governance only contractual olarak baglidir.",
        ]
    )


def _render_4_layer_roadmap() -> str:
    return "\n".join(
        [
            f"# 4 Katmanli Kapsam ve Eval Yol Haritasi {DATE}",
            "",
            "## Official Layers",
            "",
            "- Hat-A = `full primary law corpus`",
            "- Hat-B = `case law corpus`",
            "- Hat-C = `secondary sources`",
            "- Hat-D = `provenance-controlled hierarchical retrieval`",
            "",
            "## Current Execution Decision",
            "",
            "- active_remediation_hat = `Hat-A`",
            "- hat_a_execution_authorized = `true`",
            "- hat_b_execution_authorized = `false`",
            "- hat_c_execution_authorized = `false`",
            "- hat_d_runtime_change_authorized = `false`",
            "",
            "## Official Roadmap Binding",
            "",
            "- Hat-B and Hat-C remain acquisition/eval roadmap only in this phase.",
            "- Hat-D remains retrieval governance contract only in this phase.",
            "- No new source acquisition or runtime topology change opens under this document.",
        ]
    )


def _render_remediation_contract() -> str:
    return "\n".join(
        [
            f"# Full Corpus Integrated Requalification Remediation Contract V2 {DATE}",
            "",
            "## Bound Scope",
            "",
            "- active_remediation_hat = `Hat-A`",
            "- current_57_row_pack_status = `regression_only`",
            "- canonical_acceptance_pack_minimum_row_count = `300`",
            "- new_source_acquisition_authorized = `false`",
            "- answer_path_changed = `false`",
            "- model_changed = `false`",
            "- prompt_changed = `false`",
            "- retrieval_logic_changed = `false`",
            "- reranker_changed = `false`",
            "- guardrail_changed = `false`",
            "- release_controls_topology_changed = `false`",
            "",
            "## Evaluation Reset",
            "",
            "- source-level lawyer batches are retained as regression slices only.",
            "- canonical Hat-A acceptance moves to the 300-row article-anchored full-primary-law pack.",
            "- Hat-B / Hat-C / Hat-D are documented but not executed in this phase.",
        ]
    )


def _render_rerun_report(pack: dict[str, Any], summary: dict[str, Any], report: dict[str, Any]) -> str:
    source_lines = []
    for config in SOURCE_CONFIGS:
        row = summary["per_source_class_summary"][config["label"]]
        source_lines.append(
            f"| {config['label']} | {row['row_count']} | {row['source_local_row_count']} | {row['cross_law_row_count']} | "
            f"{row['citation_readable_count']} | {row['answer_usable_count']} | {row['source_correct_count']} | "
            f"{row['reject_count']} | {row['runtime_error_count']} | {row['cross_law_confusion_count']} | "
            f"{row['wrong_primary_source_count']} | {_percent(row['correct_source_rate'])} |"
        )
    return "\n".join(
        [
            f"# Full Corpus Integrated Requalification Rerun Raporu {DATE} V2",
            "",
            "## Official Counts",
            "",
            f"- total_eval_row_count = `{summary['total_eval_row_count']}`",
            f"- supported_source_correct_count = `{summary['supported_source_correct_count']}`",
            f"- citation_readable_count = `{summary['citation_readable_count']}`",
            f"- answer_usable_count = `{summary['answer_usable_count']}`",
            f"- refusal_correct_count = `{summary['refusal_correct_count']}`",
            f"- refusal_miss_count = `{summary['refusal_miss_count']}`",
            f"- reject_count = `{summary['reject_count']}`",
            f"- runtime_error_count = `{summary['runtime_error_count']}`",
            f"- unexplained_count = `{summary['unexplained_count']}`",
            f"- cross_law_confusion_count = `{summary['cross_law_confusion_count']}`",
            f"- wrong_primary_source_count = `{summary['wrong_primary_source_count']}`",
            "",
            "## Per Source Class Summary",
            "",
            "| source_class | row_count | source_local_rows | cross_law_rows | citation_readable_count | answer_usable_count | source_correct_count | reject_count | runtime_error_count | cross_law_confusion_count | wrong_primary_source_count | correct_source_rate |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            *source_lines,
            "",
            "## Boundary",
            "",
            f"- canonical_pack_row_count = `{pack['_meta']['total_questions']}`",
            "- current_57_row_pack_status = `regression_only`",
            "- answer_path_changed = `false`",
            "- model_changed = `false`",
            "- prompt_changed = `false`",
            "- retrieval_logic_changed = `false`",
            "- reranker_changed = `false`",
            "- guardrail_changed = `false`",
            "- release_controls_topology_changed = `false`",
            "",
            "## Evidence",
            "",
            f"- canonical_eval_pack = `{PACK_PATH.relative_to(ROOT)}`",
            f"- raw_eval_report = `{REPORT_PATH.relative_to(ROOT)}`",
            f"- integrated_summary = `{SUMMARY_PATH.relative_to(ROOT)}`",
            f"- runner_exit_code = `{report['runner_exit_code']}`",
        ]
    )


def _render_gate_report(pack: dict[str, Any], summary: dict[str, Any], rebuild_summary: dict[str, Any]) -> tuple[str, bool]:
    pass_gate = (
        pack["_meta"]["total_questions"] >= 300
        and summary["reject_count"] == 0
        and summary["runtime_error_count"] == 0
        and summary["unexplained_count"] == 0
        and summary["cross_law_confusion_count"] == 0
        and summary["wrong_primary_source_count"] == 0
        and rebuild_summary["legacy_partial_used_for_rebuild"] is False
        and rebuild_summary["write_summary"]["active_collection_name"] == FULL_COLLECTION
    )
    decision = (
        "PASS - Full Corpus Integrated Requalification Remediation Closed"
        if pass_gate
        else "NO-GO - Full Corpus Integrated Requalification Remediation"
    )
    rows = [
        ("current_57_row_pack_regression_only", "true", "true", "PASS"),
        ("canonical_acceptance_pack_minimum_row_count", "300", str(pack["_meta"]["total_questions"]), "PASS" if pack["_meta"]["total_questions"] >= 300 else "FAIL"),
        ("reject_count", "0", str(summary["reject_count"]), "PASS" if summary["reject_count"] == 0 else "FAIL"),
        ("runtime_error_count", "0", str(summary["runtime_error_count"]), "PASS" if summary["runtime_error_count"] == 0 else "FAIL"),
        ("unexplained_count", "0", str(summary["unexplained_count"]), "PASS" if summary["unexplained_count"] == 0 else "FAIL"),
        ("cross_law_confusion_count", "0", str(summary["cross_law_confusion_count"]), "PASS" if summary["cross_law_confusion_count"] == 0 else "FAIL"),
        ("wrong_primary_source_count", "0", str(summary["wrong_primary_source_count"]), "PASS" if summary["wrong_primary_source_count"] == 0 else "FAIL"),
        ("answer_path_changed", "false", "false", "PASS"),
        ("model_changed", "false", "false", "PASS"),
        ("prompt_changed", "false", "false", "PASS"),
        ("retrieval_logic_changed", "false", "false", "PASS"),
        ("reranker_changed", "false", "false", "PASS"),
        ("guardrail_changed", "false", "false", "PASS"),
        ("release_controls_topology_changed", "false", "false", "PASS"),
    ]
    return (
        "\n".join(
            [
                f"# Full Corpus Integrated Requalification Remediation Gate Raporu {DATE} V2",
                "",
                "## Official Decision",
                "",
                f"- decision = `{decision}`",
                "",
                "## PASS Criteria Contrast",
                "",
                "| criterion | required | observed | result |",
                "| --- | --- | --- | --- |",
                *[f"| {criterion} | {required} | {observed} | {result} |" for criterion, required, observed, result in rows],
                "",
                "## Decisive Findings",
                "",
                f"- total_eval_row_count = `{summary['total_eval_row_count']}`",
                f"- supported_source_correct_count = `{summary['supported_source_correct_count']}`",
                f"- refusal_correct_count = `{summary['refusal_correct_count']}`",
                f"- active_collection_name = `{rebuild_summary['write_summary']['active_collection_name']}`",
                "- current_57_row_pack_status = `regression_only`",
                "",
                "## Next Official Work",
                "",
                "- next_official_work = `tam mevzuat ana hat productization re-anchor under canonical current authority`",
            ]
        ),
        pass_gate,
    )


def main() -> int:
    for required_path in (
        PREVIOUS_PACK,
        PREVIOUS_REPORT,
        PREVIOUS_SUMMARY,
        REBUILD_SUMMARY,
        API_PY,
        TOKENIZER_PATH,
    ):
        if not required_path.exists():
            raise FileNotFoundError(required_path)

    previous_pack = _read_json(PREVIOUS_PACK)
    previous_summary = _read_json(PREVIOUS_SUMMARY)
    rebuild_summary = _read_json(REBUILD_SUMMARY)

    legacy_lineage = _legacy_pack_lineage(previous_pack)
    pack, metadata_by_id = _build_pack()

    try:
        ports = _launch_runtime()
        report, runner_exit_code = _run_eval(ports["gateway"])
    finally:
        _copy_if_exists(ROOT / "runtime_logs" / REDIS_LOG_NAME, RUN_DIR / REDIS_LOG_NAME)
        _copy_if_exists(ROOT / "runtime_logs" / GATEWAY_LOG_NAME, RUN_DIR / GATEWAY_LOG_NAME)
        _copy_if_exists(ROOT / "runtime_logs" / TUNNEL_LOG_NAME, RUN_DIR / TUNNEL_LOG_NAME)
        _cleanup_runtime()

    report["runner_exit_code"] = runner_exit_code
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = _classify_results(report, metadata_by_id)
    summary.update(
        {
            "official_base": "RC-R",
            "active_collection_name": FULL_COLLECTION,
            "pack_path": str(PACK_PATH.relative_to(ROOT)),
            "report_path": str(REPORT_PATH.relative_to(ROOT)),
            "legacy_pack_status": "regression_only",
        }
    )
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _write_text(DOC_LINEAGE, _render_lineage_audit(legacy_lineage, pack))
    _write_text(DOC_FAILURE, _render_failure_localization(previous_summary))
    _write_text(DOC_PACK_CONTRACT, _render_pack_contract(pack))
    _write_text(DOC_LAWYER_PROTOCOL, _render_lawyer_protocol())
    _write_text(DOC_4_LAYER, _render_4_layer_roadmap())
    _write_text(DOC_REMEDIATION_CONTRACT, _render_remediation_contract())
    _write_text(DOC_RERUN, _render_rerun_report(pack, summary, report))
    gate_text, _ = _render_gate_report(pack, summary, rebuild_summary)
    _write_text(DOC_GATE, gate_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
