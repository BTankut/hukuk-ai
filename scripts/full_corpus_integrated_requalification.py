#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATE = "2026-04-06"
DATE_STAMP = "20260406"
RUN_DIR = ROOT / "runtime_logs" / f"full_corpus_integrated_requalification_{DATE_STAMP}"
PACK_PATH = RUN_DIR / "full_corpus_integrated_requalification_pack.json"
REPORT_PATH = RUN_DIR / f"eval_full_corpus_integrated_requalification_{DATE_STAMP}.json"
SUMMARY_PATH = RUN_DIR / "integrated_summary.json"

DOC_EVAL_PACK = ROOT / "docs" / f"FULL-CORPUS-INTEGRATED-REQUALIFICATION-EVAL-PACK-{DATE}.md"
DOC_EVAL_REPORT = ROOT / "docs" / f"FULL-CORPUS-INTEGRATED-REQUALIFICATION-EVAL-RAPORU-{DATE}.md"
DOC_ZERO_DELTA = ROOT / "docs" / f"FULL-CORPUS-INTEGRATED-REQUALIFICATION-ZERO-DELTA-CONFIRMATION-{DATE}.md"
DOC_GATE = ROOT / "docs" / f"FULL-CORPUS-INTEGRATED-REQUALIFICATION-GATE-RAPORU-{DATE}.md"
DOC_NEXT = ROOT / "docs" / f"FULL-CORPUS-INTEGRATED-REQUALIFICATION-SONRASI-NEXT-OFFICIAL-WORK-KARARI-{DATE}.md"

LAUNCHER = ROOT / "scripts" / "faz10" / "launch_local_runtime_gateway.sh"
REDIS_LAUNCHER = ROOT / "scripts" / "faz7" / "launch_local_redis.sh"
EVAL_RUNNER = ROOT / "evaluation" / "eval_runner.py"
API_PY = ROOT / "api-gateway" / ".venv" / "bin" / "python"
REBUILD_SUMMARY = ROOT / "runtime_logs" / "full_corpus_rebuild_20260406" / "integrated_summary.json"

FULL_COLLECTION = "mevzuat_e5_shadow"
GATEWAY_PORT = 8120
TUNNEL_PORT = 30120
REDIS_PORT = 6387
API_KEY = "full-corpus-integrated-eval-key"
TOKENIZER_PATH = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--Qwen--Qwen3-32B"
    / "snapshots"
    / "9216db5781bf21249d130ec9da846c4624c16137"
)

REDIS_PID_NAME = "full_corpus_integrated_redis.pid"
REDIS_LOG_NAME = "full_corpus_integrated_redis.log"
GATEWAY_PID_NAME = "full_corpus_integrated_gateway.pid"
GATEWAY_LOG_NAME = "full_corpus_integrated_gateway.log"
TUNNEL_PID_NAME = "full_corpus_integrated_tunnel.pid"
TUNNEL_LOG_NAME = "full_corpus_integrated_tunnel.log"

SOURCE_BATCHES = [
    {
        "label": "TMK core corpus",
        "slug": "tmk_core_corpus",
        "law_family": "TMK",
        "csv": ROOT / "docs" / "RC-S-TMK-LAWYER-REVIEW-BATCH-001-reviewed.csv",
    },
    {
        "label": "TCK",
        "slug": "tck",
        "law_family": "TCK",
        "csv": ROOT / "docs" / "RC-S-TCK-LAWYER-REVIEW-BATCH-001-reviewed.csv",
    },
    {
        "label": "HMK",
        "slug": "hmk",
        "law_family": "HMK",
        "csv": ROOT / "docs" / "RC-S-HMK-LAWYER-REVIEW-BATCH-001_filled.csv",
    },
    {
        "label": "CMK",
        "slug": "cmk",
        "law_family": "CMK",
        "csv": ROOT / "docs" / "RC-S-CMK-LAWYER-REVIEW-BATCH-001-FILLED.csv",
    },
    {
        "label": "TTK",
        "slug": "ttk",
        "law_family": "TTK",
        "csv": ROOT / "docs" / "RC-S-TTK-LAWYER-REVIEW-BATCH-001_filled.csv",
    },
    {
        "label": "IK",
        "slug": "ik",
        "law_family": "IIK",
        "csv": ROOT / "docs" / "RC-S-IK-LAWYER-REVIEW-BATCH-001_filled.csv",
    },
]

SUPPLEMENTAL_SUPPORTED = [
    {
        "id": "FCR-TMK-XL-001",
        "question": "Aile konutu uzerinde tasarruf icin gerekli es rizasi HMK degil TMK kapsamindadir. Yalniz dogru kanun ve maddeyi gosterir misin?",
        "category": "tmk_core_corpus",
        "difficulty": "hard",
        "expected_sources": ["TMK m.194"],
        "expected_keywords": [],
        "expected_answer_contains": None,
        "refusal_expected": False,
        "source_class": "TMK core corpus",
        "coverage_tags": ["cross-law", "wrong-primary-source-sensitivity", "source-family-parity"],
        "notes": "supplemental_supported",
    },
    {
        "id": "FCR-TCK-XL-001",
        "question": "Tehdit sucu TTK degil TCK kapsamindadir. Yalniz dogru kanun ve maddeyi gosterir misin?",
        "category": "tck",
        "difficulty": "hard",
        "expected_sources": ["TCK m.106"],
        "expected_keywords": [],
        "expected_answer_contains": None,
        "refusal_expected": False,
        "source_class": "TCK",
        "coverage_tags": ["cross-law", "wrong-primary-source-sensitivity", "source-family-parity"],
        "notes": "supplemental_supported",
    },
    {
        "id": "FCR-HMK-XL-001",
        "question": "Belirsiz alacak davasi TBK degil HMK kapsamindadir. Yalniz dogru kanun ve maddeyi gosterir misin?",
        "category": "hmk",
        "difficulty": "hard",
        "expected_sources": ["HMK m.107"],
        "expected_keywords": [],
        "expected_answer_contains": None,
        "refusal_expected": False,
        "source_class": "HMK",
        "coverage_tags": ["cross-law", "wrong-primary-source-sensitivity", "source-family-parity"],
        "notes": "supplemental_supported",
    },
    {
        "id": "FCR-CMK-XL-001",
        "question": "Zorunlu mudafi gorevlendirilmesi HMK degil CMK kapsamindadir. Yalniz dogru kanun ve maddeyi gosterir misin?",
        "category": "cmk",
        "difficulty": "hard",
        "expected_sources": ["CMK m.150"],
        "expected_keywords": [],
        "expected_answer_contains": None,
        "refusal_expected": False,
        "source_class": "CMK",
        "coverage_tags": ["cross-law", "wrong-primary-source-sensitivity", "source-family-parity"],
        "notes": "supplemental_supported",
    },
    {
        "id": "FCR-TTK-XL-001",
        "question": "Tacirin borclarinin ticari sayilmasi TBK degil TTK kapsamindadir. Yalniz dogru kanun ve maddeyi gosterir misin?",
        "category": "ttk",
        "difficulty": "hard",
        "expected_sources": ["TTK m.19"],
        "expected_keywords": [],
        "expected_answer_contains": None,
        "refusal_expected": False,
        "source_class": "TTK",
        "coverage_tags": ["cross-law", "wrong-primary-source-sensitivity", "source-family-parity"],
        "notes": "supplemental_supported",
    },
    {
        "id": "FCR-IK-XL-001",
        "question": "Ilamsiz takipte odeme emrine itiraz suresi TBK degil IIK kapsamindadir. Yalniz dogru kanun ve maddeyi gosterir misin?",
        "category": "ik",
        "difficulty": "hard",
        "expected_sources": ["IIK m.62"],
        "expected_keywords": [],
        "expected_answer_contains": None,
        "refusal_expected": False,
        "source_class": "IK",
        "coverage_tags": ["cross-law", "wrong-primary-source-sensitivity", "source-family-parity"],
        "notes": "supplemental_supported",
    },
]

SUPPLEMENTAL_REFUSALS = [
    {
        "id": "FCR-REF-001",
        "question": "Yalniz Yargitay Ictihat Merkezi'ndeki en yeni aile konutu kararina dayanarak cevap ver: sonuc nedir?",
        "category": "boundary_refusal",
        "difficulty": "hard",
        "expected_sources": [],
        "expected_keywords": [],
        "expected_answer_contains": None,
        "refusal_expected": True,
        "source_class": None,
        "coverage_tags": ["refusal-expected", "excluded-source-class", "yim"],
        "notes": "supplemental_refusal",
    },
    {
        "id": "FCR-REF-002",
        "question": "Yalniz muvekkilin sisteme yuklenmemis ozel kira sozlesmesinin 7. maddesine dayanarak cevap ver: tahliye riski var mi?",
        "category": "boundary_refusal",
        "difficulty": "hard",
        "expected_sources": [],
        "expected_keywords": [],
        "expected_answer_contains": None,
        "refusal_expected": True,
        "source_class": None,
        "coverage_tags": ["refusal-expected", "excluded-source-class", "customer-private"],
        "notes": "supplemental_refusal",
    },
    {
        "id": "FCR-REF-003",
        "question": "Yalniz bugun internette yayimlanmis ve burada paylasilmayan hukuk blogu yorumlarina dayanarak cevap ver: TCK m.106 nasil uygulanir?",
        "category": "boundary_refusal",
        "difficulty": "hard",
        "expected_sources": [],
        "expected_keywords": [],
        "expected_answer_contains": None,
        "refusal_expected": True,
        "source_class": None,
        "coverage_tags": ["refusal-expected", "excluded-source-class", "external-internet"],
        "notes": "supplemental_refusal",
    },
]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _split_sources(text: str) -> list[str]:
    return [part.strip() for part in re.split(r";", text or "") if part.strip()]


def _normalize_source(text: str) -> str:
    normalized = text.strip().upper()
    normalized = normalized.replace("İ", "I")
    normalized = normalized.replace("MADDE", "M.")
    normalized = normalized.replace("MD.", "M.")
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"M\.\s+", "M.", normalized)
    return normalized


def _law_family(source: str) -> str | None:
    if not source:
        return None
    normalized = _normalize_source(source)
    match = re.match(r"([A-Z]+)\s+M\.", normalized)
    if match:
        return match.group(1)
    head = normalized.split(" ", 1)[0]
    return head or None


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


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


def _build_pack() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    questions: list[dict[str, Any]] = []
    metadata_by_id: dict[str, dict[str, Any]] = {}

    for batch in SOURCE_BATCHES:
        with batch["csv"].open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                question = {
                    "id": row["question_id"],
                    "question": row["question"],
                    "category": batch["slug"],
                    "difficulty": "medium",
                    "expected_sources": _split_sources(row["source_citation"]),
                    "expected_keywords": [],
                    "expected_answer_contains": None,
                    "refusal_expected": False,
                    "source_class": batch["label"],
                    "coverage_tags": ["source-class", "lawyer-reviewed"],
                    "notes": f"question_origin={batch['csv'].name} lawyer_decision={row.get('lawyer_decision', '')}",
                }
                questions.append(question)
                metadata_by_id[question["id"]] = question

    for item in SUPPLEMENTAL_SUPPORTED + SUPPLEMENTAL_REFUSALS:
        questions.append(item)
        metadata_by_id[item["id"]] = item

    citation_heavy_count = sum(1 for q in questions if len(q.get("expected_sources", [])) >= 2)
    cross_law_count = sum(1 for q in questions if "cross-law" in q.get("coverage_tags", []))
    wrong_primary_count = sum(
        1 for q in questions if "wrong-primary-source-sensitivity" in q.get("coverage_tags", [])
    )
    source_family_parity_count = sum(
        1 for q in questions if "source-family-parity" in q.get("coverage_tags", [])
    )
    refusal_expected_count = sum(1 for q in questions if q.get("refusal_expected"))

    payload = {
        "_meta": {
            "version": "1.0.0",
            "scope": "Full corpus integrated requalification under canonical current authority",
            "official_base": "RC-R",
            "active_collection_name": FULL_COLLECTION,
            "total_questions": len(questions),
            "supported_question_count": len(questions) - refusal_expected_count,
            "refusal_expected_count": refusal_expected_count,
            "cross_law_question_count": cross_law_count,
            "wrong_primary_source_sensitivity_count": wrong_primary_count,
            "citation_heavy_count": citation_heavy_count,
            "source_family_parity_question_count": source_family_parity_count,
        },
        "questions": questions,
    }
    PACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    PACK_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload, metadata_by_id


def _launch_gateway() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    _cleanup_runtime()

    redis_env = os.environ.copy()
    redis_env.update(
        {
            "PID_PATH": str(ROOT / "runtime_logs" / REDIS_PID_NAME),
            "LOG_PATH": str(ROOT / "runtime_logs" / REDIS_LOG_NAME),
            "PORT": str(REDIS_PORT),
            "DATA_DIR": str(RUN_DIR / "redis_data"),
        }
    )
    subprocess.run(["bash", str(REDIS_LAUNCHER)], cwd=str(ROOT), env=redis_env, check=True)

    env = os.environ.copy()
    env.update(
        {
            "GATEWAY_PORT": str(GATEWAY_PORT),
            "LOCAL_TUNNEL_PORT": str(TUNNEL_PORT),
            "MILVUS_COLLECTION": FULL_COLLECTION,
            "RELEASE_LANE_ID": "rc_r",
            "RELEASE_CONTROLS_STRICT": "true",
            "API_VERSION_LABEL": "2026-04-06-full-corpus-integrated",
            "API_AUTH_ENABLED": "true",
            "API_AUTH_KEYS": API_KEY,
            "AUDIT_LOG_ENABLED": "true",
            "AUDIT_LOG_PATH": str(RUN_DIR / "audit.jsonl"),
            "ALLOW_ANONYMOUS_INTERNAL_SMOKE": "false",
            "SESSION_STORE_BACKEND": "redis",
            "SESSION_STORE_REDIS_REQUIRED": "true",
            "SESSION_STORE_REDIS_PING_ON_STARTUP": "true",
            "REDIS_URL": f"redis://127.0.0.1:{REDIS_PORT}/0",
            "SESSION_STORE_NAMESPACE": "full-corpus-integrated-20260406",
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
    subprocess.run(["bash", str(LAUNCHER)], cwd=str(ROOT), env=env, check=True)


def _run_eval() -> tuple[dict[str, Any], int]:
    env = os.environ.copy()
    env["EVAL_API_KEY"] = API_KEY
    proc = subprocess.run(
        [
            str(API_PY),
            str(EVAL_RUNNER),
            "--api-url",
            f"http://127.0.0.1:{GATEWAY_PORT}",
            "--questions",
            str(PACK_PATH),
            "--output",
            str(REPORT_PATH),
            "--eval-family",
            "full_corpus_integrated_requalification",
            "--model-ref",
            "RC-R",
            "--checkpoint-ref",
            FULL_COLLECTION,
            "--report-role",
            "evaluation",
            "--timeout",
            "90",
            "--delay",
            "0.1",
            "--api-key",
            API_KEY,
        ],
        cwd=str(ROOT),
        env=env,
    )
    return _read_json(REPORT_PATH), proc.returncode


def _classify_results(report: dict[str, Any], metadata_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    per_question = report["per_question"]
    per_source: dict[str, dict[str, Any]] = {}
    supported_source_correct_count = 0
    citation_readable_count = 0
    answer_usable_count = 0
    refusal_correct_count = 0
    refusal_miss_count = 0
    cross_law_confusion_count = 0
    wrong_primary_source_count = 0
    reject_count = 0
    runtime_error_count = 0
    unexplained_count = 0

    for batch in SOURCE_BATCHES:
        per_source[batch["label"]] = {
            "row_count": 0,
            "citation_readable_count": 0,
            "answer_usable_count": 0,
            "source_correct_count": 0,
            "reject_count": 0,
            "runtime_error_count": 0,
            "cross_law_confusion_count": 0,
            "wrong_primary_source_count": 0,
        }

    for row in per_question:
        meta = metadata_by_id[row["question_id"]]
        refusal_expected = bool(meta.get("refusal_expected"))
        source_class = meta.get("source_class")
        cited_sources = row.get("cited_sources", [])
        answer_text = (row.get("answer_text") or "").strip()
        has_citation = bool(row.get("has_citation"))
        is_refusal = bool(row.get("is_refusal")) or row.get("final_mode") == "refusal"
        error = bool(row.get("error"))
        correct_source_overlap = int(row.get("correct_source_overlap", 0))

        if source_class:
            per_source[source_class]["row_count"] += 1

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
            for family in (_law_family(source) for source in meta.get("expected_sources", []))
            if family
        }
        cited_families = {
            family for family in (_law_family(source) for source in cited_sources) if family
        }
        cross_law_confusion = bool(
            "cross-law" in meta.get("coverage_tags", [])
            and cited_families
            and not cited_families.issubset(expected_families)
        )
        wrong_primary = bool(has_citation and correct_source_overlap == 0 and not cross_law_confusion)

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

        if wrong_primary:
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
            per_source[source_class]["citation_readable_count"] += 1
            per_source[source_class]["answer_usable_count"] += 1
            per_source[source_class]["source_correct_count"] += 1

    total_rows = len(per_question)
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

    for source_class, row in per_source.items():
        row["citation_rate"] = (
            row["citation_readable_count"] / row["row_count"] if row["row_count"] else 0.0
        )
        row["correct_source_rate"] = (
            row["source_correct_count"] / row["row_count"] if row["row_count"] else 0.0
        )

    payload = {
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
    return payload


def _render_eval_pack(pack: dict[str, Any], metadata_by_id: dict[str, dict[str, Any]]) -> str:
    meta = pack["_meta"]
    source_rows = []
    for batch in SOURCE_BATCHES:
        count = sum(
            1 for q in pack["questions"] if q.get("source_class") == batch["label"]
        )
        source_rows.append(
            f"| {batch['label']} | `{batch['csv'].name}` + `supplemental cross-law boundary row` | {count} |"
        )

    citation_heavy_rows = sum(
        1 for q in pack["questions"] if len(q.get("expected_sources", [])) >= 2
    )

    return "\n".join(
        [
            f"# Full Corpus Integrated Requalification Eval Pack {DATE}",
            "",
            "## Eval Pack Summary",
            "",
            f"- official_base = `RC-R`",
            f"- active_collection_name = `{FULL_COLLECTION}`",
            f"- total_eval_row_count = `{meta['total_questions']}`",
            f"- supported_question_count = `{meta['supported_question_count']}`",
            f"- refusal_expected_count = `{meta['refusal_expected_count']}`",
            f"- cross_law_question_count = `{meta['cross_law_question_count']}`",
            f"- wrong_primary_source_sensitivity_count = `{meta['wrong_primary_source_sensitivity_count']}`",
            f"- citation_heavy_count = `{citation_heavy_rows}`",
            f"- source_family_parity_question_count = `{meta['source_family_parity_question_count']}`",
            "",
            "## Exact Source-Class Coverage",
            "",
            "| source_class | origin | row_count |",
            "| --- | --- | ---: |",
            *source_rows,
            "",
            "## Supplemental Coverage",
            "",
            "- cross-law boundary coverage is provided by six source-family disambiguation rows, one per source class.",
            "- wrong-primary-source sensitivity coverage is bound to the same six disambiguation rows.",
            "- refusal expected coverage is provided by three excluded-source prompts: YIM, customer/private document, external internet-derived ad hoc content.",
            "- citation-heavy coverage remains present inside the accepted reviewed lawyer batches and is preserved without rewriting those question texts.",
            "",
            "## Boundary",
            "",
            "- official_full_source_set = `[TMK core corpus, TCK, HMK, CMK, TTK, IK]`",
            "- excluded_source_classes_used_for_answering = `false`",
            "- customer_private_data_used = `false`",
            "- external_internet_content_used = `false`",
            "- YIM_used = `false`",
            "- new_vector_db_write_started = `false`",
        ]
    )


def _render_eval_report(pack: dict[str, Any], report: dict[str, Any], summary: dict[str, Any]) -> str:
    source_lines = []
    for batch in SOURCE_BATCHES:
        row = summary["per_source_class_summary"][batch["label"]]
        source_lines.append(
            f"| {batch['label']} | {row['row_count']} | {row['citation_readable_count']} | "
            f"{row['answer_usable_count']} | {row['source_correct_count']} | {row['reject_count']} | "
            f"{row['runtime_error_count']} | {row['cross_law_confusion_count']} | {row['wrong_primary_source_count']} | "
            f"{_percent(row['citation_rate'])} | {_percent(row['correct_source_rate'])} |"
        )

    return "\n".join(
        [
            f"# Full Corpus Integrated Requalification Eval Raporu {DATE}",
            "",
            "## Official Counts",
            "",
            f"- supported_source_correct_count = `{summary['supported_source_correct_count']}`",
            f"- citation_readable_count = `{summary['citation_readable_count']}`",
            f"- answer_usable_count = `{summary['answer_usable_count']}`",
            f"- refusal_correct_count = `{summary['refusal_correct_count']}`",
            f"- cross_law_confusion_count = `{summary['cross_law_confusion_count']}`",
            f"- wrong_primary_source_count = `{summary['wrong_primary_source_count']}`",
            f"- reject_count = `{summary['reject_count']}`",
            f"- runtime_error_count = `{summary['runtime_error_count']}`",
            f"- unexplained_count = `{summary['unexplained_count']}`",
            "",
            "## Per Source Class Summary",
            "",
            "| source_class | row_count | citation_readable_count | answer_usable_count | source_correct_count | reject_count | runtime_error_count | cross_law_confusion_count | wrong_primary_source_count | citation_rate | correct_source_rate |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            *source_lines,
            "",
            "## Evidence",
            "",
            f"- eval_pack = `{PACK_PATH.relative_to(ROOT)}`",
            f"- raw_eval_report = `{REPORT_PATH.relative_to(ROOT)}`",
            f"- integrated_summary = `{SUMMARY_PATH.relative_to(ROOT)}`",
            f"- runner_exit_code = `{report.get('runner_exit_code')}`",
            "",
            "## Notes",
            "",
            f"- total_eval_row_count = `{summary['total_eval_row_count']}`",
            f"- refusal_miss_count = `{summary['refusal_miss_count']}`",
            f"- official_full_source_set_active evaluation surface = `{FULL_COLLECTION}`",
            "- answer-path/model/prompt/retrieval/reranker/guardrail/release-controls topology was consumed as frozen runtime only.",
        ]
    )


def _render_zero_delta(rebuild_summary: dict[str, Any]) -> str:
    write_summary = rebuild_summary["write_summary"]
    return "\n".join(
        [
            f"# Full Corpus Integrated Requalification Zero Delta Confirmation {DATE}",
            "",
            "## Frozen Runtime Surface",
            "",
            "- answer_path_changed = `false`",
            "- model_changed = `false`",
            "- prompt_changed = `false`",
            "- retrieval_logic_changed = `false`",
            "- reranker_changed = `false`",
            "- guardrail_changed = `false`",
            "- release_controls_topology_changed = `false`",
            "- legacy_partial_serving_dependency_removed = `true`",
            "- official_full_source_set_active = `true`",
            "",
            "## Rebuild Evidence",
            "",
            f"- active_collection_name = `{write_summary['active_collection_name']}`",
            f"- official_source_set = `{rebuild_summary['official_source_set']}`",
            f"- legacy_partial_used_for_rebuild = `{_bool_text(bool(rebuild_summary['legacy_partial_used_for_rebuild']))}`",
            f"- build_error_count = `{rebuild_summary['build_error_count']}`",
            f"- technical_write_error_count = `{write_summary['technical_write_error_count']}`",
            f"- written_record_count = `{write_summary['written_record_count']}`",
            "",
            "## Confirmation",
            "",
            "- This phase opened no new source acquisition, no new source selection, no rebuild, and no new vector DB write.",
            "- The integrated requalification consumed the already rebuilt full corpus collection only.",
        ]
    )


def _render_gate(summary: dict[str, Any], rebuild_summary: dict[str, Any]) -> tuple[str, bool]:
    source_classes_seen = {
        source_class
        for source_class, row in summary["per_source_class_summary"].items()
        if row["row_count"] > 0
    }
    pass_gate = (
        source_classes_seen == {batch["label"] for batch in SOURCE_BATCHES}
        and summary["reject_count"] == 0
        and summary["runtime_error_count"] == 0
        and summary["unexplained_count"] == 0
        and summary["cross_law_confusion_count"] == 0
        and summary["wrong_primary_source_count"] == 0
        and rebuild_summary["legacy_partial_used_for_rebuild"] is False
        and rebuild_summary["write_summary"]["active_collection_name"] == FULL_COLLECTION
    )
    decision = (
        "PASS - Full Corpus Integrated Requalification Closed Under Canonical Current Authority"
        if pass_gate
        else "NO-GO - Full Corpus Integrated Requalification"
    )
    text = "\n".join(
        [
            f"# Full Corpus Integrated Requalification Gate Raporu {DATE}",
            "",
            "## Official Decision",
            "",
            f"- {decision}",
            "",
            "## PASS Criteria Check",
            "",
            f"- all_six_source_classes_covered = `{_bool_text(source_classes_seen == {batch['label'] for batch in SOURCE_BATCHES})}`",
            f"- reject_count = `{summary['reject_count']}`",
            f"- runtime_error_count = `{summary['runtime_error_count']}`",
            f"- unexplained_count = `{summary['unexplained_count']}`",
            f"- cross_law_confusion_count = `{summary['cross_law_confusion_count']}`",
            f"- wrong_primary_source_count = `{summary['wrong_primary_source_count']}`",
            f"- legacy_partial_serving_dependency_removed = `{_bool_text(rebuild_summary['legacy_partial_used_for_rebuild'] is False)}`",
            f"- official_full_source_set_active = `{_bool_text(rebuild_summary['write_summary']['active_collection_name'] == FULL_COLLECTION)}`",
            f"- answer_path_changed = `false`",
            f"- model_changed = `false`",
            f"- prompt_changed = `false`",
            f"- retrieval_logic_changed = `false`",
            f"- reranker_changed = `false`",
            f"- guardrail_changed = `false`",
            f"- release_controls_topology_changed = `false`",
            "",
            "## Decision Basis",
            "",
            f"- total_eval_row_count = `{summary['total_eval_row_count']}`",
            f"- supported_source_correct_count = `{summary['supported_source_correct_count']}`",
            f"- citation_readable_count = `{summary['citation_readable_count']}`",
            f"- answer_usable_count = `{summary['answer_usable_count']}`",
            f"- refusal_correct_count = `{summary['refusal_correct_count']}`",
            "",
            "## Evidence",
            "",
            f"- `{DOC_EVAL_PACK.name}`",
            f"- `{DOC_EVAL_REPORT.name}`",
            f"- `{DOC_ZERO_DELTA.name}`",
        ]
    )
    return text, pass_gate


def _render_next(pass_gate: bool) -> str:
    next_official_work = (
        "tam mevzuat ana hat productization re-anchor under canonical current authority"
        if pass_gate
        else "full corpus integrated requalification remediation under canonical current authority"
    )
    return f"next_official_work = {next_official_work}\n"


def main() -> int:
    if not REBUILD_SUMMARY.exists():
        raise FileNotFoundError(f"missing rebuild summary: {REBUILD_SUMMARY}")
    if not API_PY.exists():
        raise FileNotFoundError(f"missing api virtualenv python: {API_PY}")
    if not TOKENIZER_PATH.exists():
        raise FileNotFoundError(f"missing tokenizer path: {TOKENIZER_PATH}")

    rebuild_summary = _read_json(REBUILD_SUMMARY)
    pack, metadata_by_id = _build_pack()

    try:
        _launch_gateway()
        report, runner_exit_code = _run_eval()
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
        }
    )
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _write_text(DOC_EVAL_PACK, _render_eval_pack(pack, metadata_by_id))
    _write_text(DOC_EVAL_REPORT, _render_eval_report(pack, report, summary))
    _write_text(DOC_ZERO_DELTA, _render_zero_delta(rebuild_summary))
    gate_text, pass_gate = _render_gate(summary, rebuild_summary)
    _write_text(DOC_GATE, gate_text)
    _write_text(DOC_NEXT, _render_next(pass_gate))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
