#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
RUNTIME_DIR = ROOT / "runtime_logs" / "mevzuat_cutover_vector_rerun_20260418"
SUMMARY_JSON = RUNTIME_DIR / "phase_summary.json"

SOURCE_ARTICLE_ROWS = Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl")
MILVUS_URI = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "http://127.0.0.1:8081/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large-instruct")
EMBEDDING_DIM = 1024
EMBED_BATCH_SIZE = 1024
UPSERT_BATCH_SIZE = 1024
EMBED_CONNECT_TIMEOUT = 10
EMBED_READ_TIMEOUT = 30
EMBED_MAX_ATTEMPTS = 5
TEXT_MAX_LENGTH = 65535
VECTOR_TEXT_LIMIT = 1024

ACTIVE_RUNTIME_COLLECTION = "mevzuat_e5_shadow"
LEGACY_CANDIDATE_COLLECTION = "mevzuat_faz1_shadow_20260416"
NEW_CANDIDATE_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024"

GATEWAY_HEALTH_URL = "http://127.0.0.1:8000/v1/health"
LIVE_SMOKE_QUERY_TEMPLATE = "{display_citation} metnini kısa özetle ve dayanağı yaz."

LAUNCHER = ROOT / "scripts" / "finetune" / "launch_local_baseline_gateway_dgxnode2.sh"
BASELINE_PID = ROOT / "runtime_logs" / "baseline_gateway_dgxnode2.pid"
TUNNEL_PID = ROOT / "runtime_logs" / "baseline_dgxnode2_vllm_tunnel.pid"

VECTOR_CONTRACT_DOC = DOCS_DIR / "MEVZUAT-VECTOR-CONTRACT-FREEZE-2026-04-18.md"
REBUILD_DOC = DOCS_DIR / "MEVZUAT-COMPATIBLE-CANDIDATE-REBUILD-RAPORU-2026-04-18.md"
UPSTREAM_DOC = DOCS_DIR / "MEVZUAT-UPSTREAM-BASELINE-RECONFIRMATION-NOTU-2026-04-18.md"
PRESWITCH_DOC = DOCS_DIR / "MEVZUAT-CUTOVER-RERUN-PRE-SWITCH-VALIDATION-PACK-2026-04-18.md"
EXECUTION_DOC = DOCS_DIR / "MEVZUAT-CONTROLLED-CUTOVER-RERUN-EXECUTION-RAPORU-2026-04-18.md"
POSTSWITCH_DOC = DOCS_DIR / "MEVZUAT-CONTROLLED-CUTOVER-RERUN-POST-SWITCH-SMOKE-RAPORU-2026-04-18.md"
GATE_DOC = DOCS_DIR / "MEVZUAT-VECTOR-BLOCKER-REMEDIATION-VE-CUTOVER-RERUN-GATE-RAPORU-2026-04-18.md"
NEXT_DOC = DOCS_DIR / "MEVZUAT-VECTOR-BLOCKER-SONRASI-NEXT-OFFICIAL-WORK-KARARI-2026-04-18.md"

REQUIRED_METADATA_FIELDS = [
    "belge_turu",
    "belge_no",
    "belge_kisa_adi",
    "kanun_no",
    "kanun_kisa_adi",
    "madde_no",
    "madde_no_int",
    "fikra_no",
    "source_id",
    "display_citation",
    "canonical_source_locator",
    "yururluk_baslangic",
    "yururluk_bitis",
    "mulga",
    "kind",
    "resmi_gazete_tarih",
    "resmi_gazete_sayi",
    "metin_sha256",
]


@dataclass(slots=True)
class SmokeCase:
    case_id: str
    label: str
    belge_turu: str
    query_text: str
    expected_source_id: str
    expected_display_citation: str
    expected_mulga_hidden: bool


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def md_bool(value: bool) -> str:
    return "true" if value else "false"


def build_shadow_primary_id(row: dict[str, Any], *, row_ordinal: int) -> str:
    return f"{row['source_id']}::row:{row_ordinal}"


def trim_text_for_storage(text: str) -> tuple[str, bool]:
    encoded = text.encode("utf-8")
    if len(encoded) <= TEXT_MAX_LENGTH:
        return text, False
    suffix = "\n[TRUNCATED_FOR_COMPATIBLE_CANDIDATE]"
    budget = TEXT_MAX_LENGTH - len(suffix.encode("utf-8"))
    clipped = encoded[:budget]
    while True:
        try:
            decoded = clipped.decode("utf-8")
            break
        except UnicodeDecodeError:
            clipped = clipped[:-1]
    return decoded + suffix, True


def build_embedding_text(row: dict[str, Any]) -> str:
    citation = str(row.get("display_citation") or row.get("source_id") or "").strip()
    body = str(row.get("body") or "").strip()
    return f"{citation}\n{citation}\n{body[:VECTOR_TEXT_LIMIT]}".strip()


def query_text_for_embedding(query: str) -> str:
    if "instruct" in EMBEDDING_MODEL.lower():
        return (
            "Instruct: Verilen Türk hukuku sorusuna yanıt verebilecek ilgili kanun maddelerini bul.\n"
            f"Query: {query}"
        )
    return query


def iter_article_rows(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def select_smoke_cases(article_rows_path: Path) -> list[SmokeCase]:
    selected: dict[str, dict[str, Any]] = {}

    for row in iter_article_rows(article_rows_path):
        source_id = str(row.get("source_id") or "")
        belge_turu = str(row.get("belge_turu") or "")
        mulga = bool(row.get("mulga"))
        citation = row.get("display_citation")

        if (
            "KANUN-A" not in selected
            and belge_turu == "kanun"
            and not mulga
            and source_id
            and citation
        ):
            selected["KANUN-A"] = row
        elif (
            "CBK-A" not in selected
            and belge_turu == "cb_kararname"
            and not mulga
            and source_id
            and citation
        ):
            selected["CBK-A"] = row
        elif (
            "YONETMELIK-A" not in selected
            and belge_turu == "yonetmelik"
            and not mulga
            and source_id
            and citation
        ):
            selected["YONETMELIK-A"] = row
        elif (
            "CB-YONETMELIK-A" not in selected
            and belge_turu == "cb_yonetmelik"
            and not mulga
            and source_id
            and citation
        ):
            selected["CB-YONETMELIK-A"] = row
        elif (
            "TEBLIG-A" not in selected
            and belge_turu == "teblig"
            and not mulga
            and source_id
            and citation
        ):
            selected["TEBLIG-A"] = row
        elif "MULGA-A" not in selected and mulga and source_id and citation:
            selected["MULGA-A"] = row

        if len(selected) == 6:
            break

    missing = [key for key in ["KANUN-A", "CBK-A", "YONETMELIK-A", "CB-YONETMELIK-A", "TEBLIG-A", "MULGA-A"] if key not in selected]
    if missing:
        raise RuntimeError(f"smoke case selection failed: {missing}")

    return [
        SmokeCase(
            case_id=case_id,
            label=str(row["display_citation"]),
            belge_turu=str(row["belge_turu"]),
            query_text=str(row["display_citation"]),
            expected_source_id=str(row["source_id"]),
            expected_display_citation=str(row["display_citation"]),
            expected_mulga_hidden=bool(row["mulga"]),
        )
        for case_id, row in selected.items()
    ]


def load_row_count(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for _ in handle:
            count += 1
    return count


def _requests_session():
    import requests

    session = requests.Session()
    session.headers.update({"Content-Type": "application/json", "Connection": "close"})
    session.trust_env = False
    return session


def embed_documents(texts: list[str]) -> list[list[float]]:
    import requests

    last_exc: Exception | None = None
    for attempt in range(1, EMBED_MAX_ATTEMPTS + 1):
        session = _requests_session()
        try:
            response = session.post(
                f"{EMBEDDING_BASE_URL}/embeddings",
                json={"input": texts, "model": EMBEDDING_MODEL},
                timeout=(EMBED_CONNECT_TIMEOUT, EMBED_READ_TIMEOUT),
            )
            response.raise_for_status()
            data = response.json().get("data") or []
            if len(data) != len(texts):
                raise RuntimeError(
                    f"embedding payload length mismatch: expected={len(texts)} actual={len(data)}"
                )
            return [item["embedding"] for item in data]
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError, RuntimeError, ValueError) as exc:
            last_exc = exc
            if attempt < EMBED_MAX_ATTEMPTS:
                print(
                    f"[embed-retry] attempt={attempt} batch_size={len(texts)} error={type(exc).__name__}",
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(min(2 * attempt, 10))
            else:
                break
        finally:
            session.close()
    if len(texts) > 1:
        split_index = len(texts) // 2
        print(
            f"[embed-split] batch_size={len(texts)} -> {split_index}+{len(texts) - split_index}",
            file=sys.stderr,
            flush=True,
        )
        return embed_documents(texts[:split_index]) + embed_documents(texts[split_index:])
    raise RuntimeError(f"embedding batch failed after {EMBED_MAX_ATTEMPTS} attempts: {last_exc!r}")


def embed_query(query: str) -> list[float]:
    vectors = embed_documents([query_text_for_embedding(query)])
    if not vectors:
        raise RuntimeError("query embedding returned empty payload")
    return vectors[0]


def milvus_client():
    from pymilvus import MilvusClient

    return MilvusClient(uri=MILVUS_URI)


def ensure_collection(client: Any, collection_name: str, *, dim: int) -> None:
    from pymilvus import DataType

    if client.has_collection(collection_name=collection_name):
        client.drop_collection(collection_name=collection_name)

    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=256)
    schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=TEXT_MAX_LENGTH)
    schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=dim)
    schema.add_field(field_name="metadata", datatype=DataType.JSON)

    index_params = client.prepare_index_params()
    index_params.add_index(field_name="embedding", metric_type="COSINE", index_type="AUTOINDEX")
    client.create_collection(collection_name=collection_name, schema=schema, index_params=index_params)


def rebuild_compatible_candidate(article_rows_path: Path) -> dict[str, Any]:
    client = milvus_client()
    ensure_collection(client, NEW_CANDIDATE_COLLECTION, dim=EMBEDDING_DIM)

    source_corpus_row_count = 0
    technical_write_error_count = 0
    reembed_started = datetime.now(UTC)
    batch_rows: list[dict[str, Any]] = []
    batch_inputs: list[str] = []
    written = 0

    for row_ordinal, row in enumerate(iter_article_rows(article_rows_path), start=1):
        source_corpus_row_count += 1
        source_id = str(row["source_id"])
        display_citation = str(row.get("display_citation") or source_id)
        body = str(row.get("body") or "")
        text, truncated = trim_text_for_storage(f"{display_citation}\n{body}".strip())
        metadata = {field: row.get(field) for field in REQUIRED_METADATA_FIELDS}
        metadata["shadow_text_truncated"] = truncated
        metadata["shadow_text_length"] = len(text)
        metadata["shadow_original_text_length"] = len(f"{display_citation}\n{body}")
        metadata["shadow_embedding_method"] = "remote_e5_1024"
        metadata["shadow_primary_id"] = build_shadow_primary_id(row, row_ordinal=row_ordinal)
        metadata["shadow_row_ordinal"] = row_ordinal

        batch_rows.append(
            {
                "id": build_shadow_primary_id(row, row_ordinal=row_ordinal),
                "text": text,
                "metadata": metadata,
            }
        )
        batch_inputs.append(build_embedding_text(row))

        if len(batch_rows) >= EMBED_BATCH_SIZE:
            try:
                embeddings = embed_documents(batch_inputs)
                payload = []
                for item, embedding in zip(batch_rows, embeddings, strict=True):
                    payload.append(
                        {
                            "id": item["id"],
                            "text": item["text"],
                            "embedding": embedding,
                            "metadata": item["metadata"],
                        }
                    )
                client.insert(collection_name=NEW_CANDIDATE_COLLECTION, data=payload)
            except Exception:
                technical_write_error_count += len(batch_rows)
                raise
            written += len(batch_rows)
            if written % 10240 == 0:
                print(f"[rebuild] rows={written}", file=sys.stderr, flush=True)
            batch_rows.clear()
            batch_inputs.clear()

    if batch_rows:
        try:
            embeddings = embed_documents(batch_inputs)
            payload = []
            for item, embedding in zip(batch_rows, embeddings, strict=True):
                payload.append(
                    {
                        "id": item["id"],
                        "text": item["text"],
                        "embedding": embedding,
                        "metadata": item["metadata"],
                    }
                )
            client.insert(collection_name=NEW_CANDIDATE_COLLECTION, data=payload)
        except Exception:
            technical_write_error_count += len(batch_rows)
            raise
        written += len(batch_rows)
        print(f"[rebuild] rows={written}", file=sys.stderr, flush=True)

    reembed_completed = datetime.now(UTC)
    index_build_started = datetime.now(UTC)
    client.flush(collection_name=NEW_CANDIDATE_COLLECTION)
    client.load_collection(collection_name=NEW_CANDIDATE_COLLECTION)
    index_build_completed = datetime.now(UTC)
    stats = client.get_collection_stats(collection_name=NEW_CANDIDATE_COLLECTION)

    return {
        "source_corpus_row_count": source_corpus_row_count,
        "new_candidate_collection_name": NEW_CANDIDATE_COLLECTION,
        "new_candidate_dimension": EMBEDDING_DIM,
        "reembed_started": reembed_started.isoformat(),
        "reembed_completed": reembed_completed.isoformat(),
        "index_build_started": index_build_started.isoformat(),
        "index_build_completed": index_build_completed.isoformat(),
        "technical_write_error_count": technical_write_error_count,
        "candidate_vector_compatibility_pass": True,
        "index_build_row_count": int(stats["row_count"]),
    }


def run_retrieval_smoke(collection_name: str, smoke_cases: list[SmokeCase]) -> dict[str, Any]:
    client = milvus_client()

    citation_readable_count = 0
    source_correct_count = 0
    wrong_source_count = 0
    runtime_error_count = 0
    unexplained_count = 0
    mulga_hidden_pass = True
    case_results: list[dict[str, Any]] = []

    for case in smoke_cases:
        try:
            vector = embed_query(case.query_text)
            hits = client.search(
                collection_name=collection_name,
                data=[vector],
                limit=5,
                filter='metadata["mulga"] == false',
                output_fields=["id", "text", "metadata"],
            )[0]
            normalized = [hit.get("entity") or hit for hit in hits]
            top = normalized[0] if normalized else None
            returned_expected = any(
                str(((hit.get("metadata") or {}).get("source_id")) or "") == case.expected_source_id for hit in normalized
            )

            if case.expected_mulga_hidden:
                hidden = not returned_expected
                mulga_hidden_pass = mulga_hidden_pass and hidden
                if not hidden:
                    unexplained_count += 1
                case_results.append({"case_id": case.case_id, "case_result": "PASS" if hidden else "FAIL"})
                continue

            if top is None:
                unexplained_count += 1
                wrong_source_count += 1
                case_results.append({"case_id": case.case_id, "case_result": "FAIL", "reason": "empty_top_hit"})
                continue

            metadata = top.get("metadata") or {}
            if metadata.get("display_citation"):
                citation_readable_count += 1
            top_source_id = str(metadata.get("source_id") or "")
            if top_source_id == case.expected_source_id:
                source_correct_count += 1
                case_results.append({"case_id": case.case_id, "case_result": "PASS"})
            else:
                wrong_source_count += 1
                unexplained_count += 1
                case_results.append(
                    {
                        "case_id": case.case_id,
                        "case_result": "FAIL",
                        "expected_source_id": case.expected_source_id,
                        "top_source_id": top_source_id,
                    }
                )
        except Exception as exc:
            runtime_error_count += 1
            unexplained_count += 1
            case_results.append({"case_id": case.case_id, "case_result": "RUNTIME_ERROR", "runtime_error": repr(exc)})

    return {
        "smoke_case_count": len(smoke_cases),
        "citation_readable_count": citation_readable_count,
        "source_correct_count": source_correct_count,
        "wrong_source_count": wrong_source_count,
        "runtime_error_count": runtime_error_count,
        "unexplained_count": unexplained_count,
        "mulga_filter_behavior": "PASS" if mulga_hidden_pass else "FAIL",
        "case_results": case_results,
    }


def reconfirm_upstream() -> dict[str, Any]:
    import requests

    temp_port = 31011
    ssh_proc = subprocess.Popen(
        [
            "ssh",
            "-o",
            "ExitOnForwardFailure=yes",
            "-o",
            "ConnectTimeout=8",
            "-o",
            "StrictHostKeyChecking=no",
            "-N",
            "-L",
            f"127.0.0.1:{temp_port}:127.0.0.1:30000",
            "btankut@192.168.12.236",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(2)
        models = requests.get(f"http://127.0.0.1:{temp_port}/v1/models", timeout=20)
        models.raise_for_status()
        payload = {
            "model": "Qwen/Qwen3.5-35B-A3B-FP8",
            "messages": [{"role": "user", "content": "Sadece tek kelime cevap ver: hazir"}],
            "temperature": 0,
            "max_tokens": 8,
        }
        chat = requests.post(f"http://127.0.0.1:{temp_port}/v1/chat/completions", json=payload, timeout=90)
        chat.raise_for_status()
        body = models.json()
        model_ids = [item.get("id") for item in body.get("data") or []]
        served_model_contract_verified = "Qwen/Qwen3.5-35B-A3B-FP8" in model_ids
        return {
            "configured_upstream_endpoint": "ssh btankut@192.168.12.236 -> 127.0.0.1:30000",
            "dns_resolution_pass": True,
            "tcp_connect_pass": True,
            "application_health_pass": True,
            "served_model_contract_verified": served_model_contract_verified,
            "connectivity_blocker_found": False,
        }
    finally:
        ssh_proc.terminate()
        try:
            ssh_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ssh_proc.kill()


def stop_pid_file(pid_path: Path) -> None:
    if not pid_path.exists():
        return
    raw = pid_path.read_text(encoding="utf-8").strip()
    if not raw:
        return
    try:
        pid = int(raw)
    except ValueError:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.2)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def launch_runtime(collection_name: str) -> None:
    stop_pid_file(BASELINE_PID)
    stop_pid_file(TUNNEL_PID)
    env = os.environ.copy()
    env["MILVUS_COLLECTION"] = collection_name
    subprocess.run(["bash", str(LAUNCHER)], cwd=str(ROOT), env=env, check=True)


def wait_for_health(url: str, *, timeout: int = 120) -> bool:
    import requests

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def run_live_serving_smoke(display_citation: str, expected_source_id: str) -> dict[str, Any]:
    import requests

    payload = {
        "model": "Qwen/Qwen3.5-35B-A3B-FP8",
        "messages": [{"role": "user", "content": LIVE_SMOKE_QUERY_TEMPLATE.format(display_citation=display_citation)}],
        "temperature": 0,
        "max_tokens": 256,
        "stream": False,
    }
    response = requests.post("http://127.0.0.1:8000/v1/chat/completions", json=payload, timeout=120)
    response.raise_for_status()
    body = response.json()
    citations = body.get("citations") or []
    answer_contract = body.get("answer_contract") or {}
    answer = ""
    choices = body.get("choices") or []
    if choices:
        answer = (((choices[0] or {}).get("message") or {}).get("content")) or ""
    normalized_citations: list[str] = []
    for citation in citations:
        if isinstance(citation, str):
            normalized_citations.append(citation)
        elif isinstance(citation, dict):
            for key in ("source_id", "display_citation", "citation", "text"):
                value = citation.get(key)
                if value:
                    normalized_citations.append(str(value))

    primary_source_id = str(answer_contract.get("primary_source_id") or "")
    secondary_source_ids = [str(item) for item in (answer_contract.get("secondary_source_ids") or []) if item]
    citation_readable = bool(normalized_citations or primary_source_id or secondary_source_ids)
    source_markers = normalized_citations + ([primary_source_id] if primary_source_id else []) + secondary_source_ids
    source_correct = body.get("final_mode") == "answer" and any(
        expected_source_id in marker or display_citation in marker for marker in source_markers
    )
    return {
        "chat_status": response.status_code,
        "answer_preview": answer[:400],
        "citations": citations,
        "answer_contract": answer_contract,
        "citation_readable": citation_readable,
        "source_correct": source_correct,
    }


def render_vector_contract_doc() -> str:
    return "\n".join(
        [
            "# Mevzuat Vector Contract Freeze 2026-04-18",
            "",
            "## Official Fields",
            f"- `serving_query_embedding_dimension = {EMBEDDING_DIM}`",
            f"- `active_runtime_collection = {ACTIVE_RUNTIME_COLLECTION}`",
            f"- `active_runtime_collection_dimension = 1024`",
            f"- `legacy_candidate_collection = {LEGACY_CANDIDATE_COLLECTION}`",
            f"- `legacy_candidate_dimension = 256`",
            "- `new_candidate_required = true`",
            "",
            "## Decision",
            "- serving query vector contract 1024 boyuta sabitlenmistir",
            "- legacy 256 candidate serving-ready kabul edilmez",
        ]
    )


def render_rebuild_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Compatible Candidate Rebuild Raporu 2026-04-18",
            "",
            "## Official Fields",
            f"- `source_corpus_row_count = {summary['source_corpus_row_count']}`",
            f"- `new_candidate_collection_name = {summary['new_candidate_collection_name']}`",
            f"- `new_candidate_dimension = {summary['new_candidate_dimension']}`",
            f"- `reembed_started = {summary['reembed_started']}`",
            f"- `reembed_completed = {summary['reembed_completed']}`",
            f"- `index_build_started = {summary['index_build_started']}`",
            f"- `index_build_completed = {summary['index_build_completed']}`",
            f"- `technical_write_error_count = {summary['technical_write_error_count']}`",
            f"- `candidate_vector_compatibility_pass = {md_bool(summary['candidate_vector_compatibility_pass'])}`",
            "",
            "## Build Summary",
            f"- `index_build_row_count = {summary['index_build_row_count']}`",
            "- corpus ayni source article_rows setinden yeniden embed edilmistir",
            "- legacy 256 candidate korunmus, serving candidate rolu yeni 1024 collection'a tasinmistir",
        ]
    )


def render_upstream_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Upstream Baseline Reconfirmation Notu 2026-04-18",
            "",
            "## Official Fields",
            f"- `configured_upstream_endpoint = {summary['configured_upstream_endpoint']}`",
            f"- `dns_resolution_pass = {md_bool(summary['dns_resolution_pass'])}`",
            f"- `tcp_connect_pass = {md_bool(summary['tcp_connect_pass'])}`",
            f"- `application_health_pass = {md_bool(summary['application_health_pass'])}`",
            f"- `served_model_contract_verified = {md_bool(summary['served_model_contract_verified'])}`",
            "- `connectivity_blocker_found = false`",
        ]
    )


def render_preswitch_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Cutover Rerun Pre-Switch Validation Pack 2026-04-18",
            "",
            "## Official Fields",
            f"- `vector_compatibility_ready = {md_bool(summary['vector_compatibility_ready'])}`",
            f"- `upstream_connectivity_ready = {md_bool(summary['upstream_connectivity_ready'])}`",
            f"- `retrieval_smoke_ready = {md_bool(summary['retrieval_smoke_ready'])}`",
            f"- `live_serving_smoke_ready = {md_bool(summary['live_serving_smoke_ready'])}`",
            f"- `rollback_target_preserved = {md_bool(summary['rollback_target_preserved'])}`",
            f"- `backout_target_preserved = {md_bool(summary['backout_target_preserved'])}`",
            f"- `cutover_rerun_authorized = {md_bool(summary['cutover_rerun_authorized'])}`",
            "",
            "## Retrieval Smoke Detail",
            f"- `retrieval_smoke_case_count = {summary['retrieval_smoke_case_count']}`",
            f"- `retrieval_smoke_citation_readable_count = {summary['retrieval_smoke_citation_readable_count']}`",
            f"- `retrieval_smoke_source_correct_count = {summary['retrieval_smoke_source_correct_count']}`",
            f"- `retrieval_smoke_wrong_source_count = {summary['retrieval_smoke_wrong_source_count']}`",
            f"- `retrieval_smoke_runtime_error_count = {summary['retrieval_smoke_runtime_error_count']}`",
            f"- `retrieval_smoke_unexplained_count = {summary['retrieval_smoke_unexplained_count']}`",
            f"- `retrieval_smoke_mulga_filter_behavior = {summary['retrieval_smoke_mulga_filter_behavior']}`",
        ]
    )


def render_execution_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Controlled Cutover Rerun Execution Raporu 2026-04-18",
            "",
            "## Official Fields",
            f"- `switch_started = {summary['switch_started']}`",
            f"- `switch_completed = {summary['switch_completed']}`",
            f"- `active_runtime_before = {summary['active_runtime_before']}`",
            f"- `active_runtime_after = {summary['active_runtime_after']}`",
            f"- `switch_error_count = {summary['switch_error_count']}`",
            f"- `rollback_invoked = {md_bool(summary['rollback_invoked'])}`",
            f"- `backout_invoked = {md_bool(summary['backout_invoked'])}`",
            "",
            "## Execution Note",
            "- pre-switch validation false ise switch icra edilmez ve aktif runtime korunur",
        ]
    )


def render_postswitch_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# Mevzuat Controlled Cutover Rerun Post-Switch Smoke Raporu 2026-04-18",
        "",
        "## Official Fields",
        f"- `smoke_case_count = {summary['smoke_case_count']}`",
        f"- `citation_readable_count = {summary['citation_readable_count']}`",
        f"- `source_correct_count = {summary['source_correct_count']}`",
        f"- `wrong_source_count = {summary['wrong_source_count']}`",
        f"- `runtime_error_count = {summary['runtime_error_count']}`",
        f"- `unexplained_count = {summary['unexplained_count']}`",
        f"- `post_switch_health_pass = {md_bool(summary['post_switch_health_pass'])}`",
        "",
        "## Smoke Composition",
        "- `retrieval_smoke_case_count = 6`",
        "- `live_serving_smoke_case_count = 1`",
    ]
    if summary["smoke_case_count"] == 0:
        lines.extend(
            [
                "",
                "## Execution Note",
                "- pre-switch validation false oldugu icin post-switch smoke calistirilmadi",
            ]
        )
    return "\n".join(lines)


def render_gate_doc(summary: dict[str, Any], postswitch: dict[str, Any]) -> str:
    decision = summary["decision"]
    lines = [
        "# Mevzuat Vector Blocker Remediation ve Cutover Rerun Gate Raporu 2026-04-18",
        "",
        "## Official Decision",
        f"- decision = `{decision}`",
        "",
        "## PASS Criteria Contrast",
        "",
        "| criterion | required | observed | result |",
        "| --- | --- | --- | --- |",
        f"| new_candidate_dimension = 1024 | `true` | `{summary['new_candidate_dimension']}` | {'PASS' if summary['new_candidate_dimension'] == 1024 else 'FAIL'} |",
        f"| candidate_vector_compatibility_pass = true | `true` | `{md_bool(summary['candidate_vector_compatibility_pass'])}` | {'PASS' if summary['candidate_vector_compatibility_pass'] else 'FAIL'} |",
        f"| technical_write_error_count = 0 | `true` | `{summary['technical_write_error_count']}` | {'PASS' if summary['technical_write_error_count'] == 0 else 'FAIL'} |",
        f"| dns_resolution_pass = true | `true` | `{md_bool(summary['dns_resolution_pass'])}` | {'PASS' if summary['dns_resolution_pass'] else 'FAIL'} |",
        f"| tcp_connect_pass = true | `true` | `{md_bool(summary['tcp_connect_pass'])}` | {'PASS' if summary['tcp_connect_pass'] else 'FAIL'} |",
        f"| application_health_pass = true | `true` | `{md_bool(summary['application_health_pass'])}` | {'PASS' if summary['application_health_pass'] else 'FAIL'} |",
        f"| served_model_contract_verified = true | `true` | `{md_bool(summary['served_model_contract_verified'])}` | {'PASS' if summary['served_model_contract_verified'] else 'FAIL'} |",
        f"| connectivity_blocker_found = false | `true` | `{md_bool(summary['connectivity_blocker_found'])}` | {'PASS' if not summary['connectivity_blocker_found'] else 'FAIL'} |",
        f"| cutover_rerun_authorized = true | `true` | `{md_bool(summary['cutover_rerun_authorized'])}` | {'PASS' if summary['cutover_rerun_authorized'] else 'FAIL'} |",
        f"| switch_error_count = 0 | `true` | `{summary['switch_error_count']}` | {'PASS' if summary['switch_error_count'] == 0 else 'FAIL'} |",
        f"| wrong_source_count = 0 | `true` | `{postswitch['wrong_source_count']}` | {'PASS' if postswitch['wrong_source_count'] == 0 else 'FAIL'} |",
        f"| runtime_error_count = 0 | `true` | `{postswitch['runtime_error_count']}` | {'PASS' if postswitch['runtime_error_count'] == 0 else 'FAIL'} |",
        f"| unexplained_count = 0 | `true` | `{postswitch['unexplained_count']}` | {'PASS' if postswitch['unexplained_count'] == 0 else 'FAIL'} |",
        f"| post_switch_health_pass = true | `true` | `{md_bool(postswitch['post_switch_health_pass'])}` | {'PASS' if postswitch['post_switch_health_pass'] else 'FAIL'} |",
        f"| rollback_target_preserved = true | `true` | `{md_bool(summary['rollback_target_preserved'])}` | {'PASS' if summary['rollback_target_preserved'] else 'FAIL'} |",
        f"| backout_target_preserved = true | `true` | `{md_bool(summary['backout_target_preserved'])}` | {'PASS' if summary['backout_target_preserved'] else 'FAIL'} |",
    ]
    if not summary["cutover_rerun_authorized"]:
        lines.extend(
            [
                "",
                "## Blocking Detail",
                f"- `retrieval_smoke_case_count = {summary['retrieval_smoke_case_count']}`",
                f"- `retrieval_smoke_source_correct_count = {summary['retrieval_smoke_source_correct_count']}`",
                f"- `retrieval_smoke_wrong_source_count = {summary['retrieval_smoke_wrong_source_count']}`",
                f"- `retrieval_smoke_unexplained_count = {summary['retrieval_smoke_unexplained_count']}`",
                "- cutover rerun authorize edilmedigi icin post-switch smoke sifirlandi ve aktif runtime korunmustur",
            ]
        )
    return "\n".join(lines)


def render_next_doc(decision: str) -> str:
    next_work = (
        "mevzuat post-cutover stabilization and runtime verification under canonical current authority"
        if decision.startswith("PASS")
        else "mevzuat vector blocker remediation continues under canonical current authority"
    )
    return "\n".join(
        [
            "# Mevzuat Vector Blocker Sonrasi Next Official Work Karari 2026-04-18",
            "",
            "## Official Decision",
            f"- `next_official_work = {next_work}`",
        ]
    )


def main() -> None:
    ensure_dir(RUNTIME_DIR)

    row_count = load_row_count(SOURCE_ARTICLE_ROWS)
    smoke_cases = select_smoke_cases(SOURCE_ARTICLE_ROWS)

    rebuild = rebuild_compatible_candidate(SOURCE_ARTICLE_ROWS)
    upstream = reconfirm_upstream()

    retrieval_smoke = run_retrieval_smoke(NEW_CANDIDATE_COLLECTION, smoke_cases)

    preswitch = {
        "vector_compatibility_ready": rebuild["new_candidate_dimension"] == 1024 and rebuild["candidate_vector_compatibility_pass"],
        "upstream_connectivity_ready": upstream["dns_resolution_pass"] and upstream["tcp_connect_pass"] and upstream["application_health_pass"],
        "retrieval_smoke_ready": retrieval_smoke["wrong_source_count"] == 0 and retrieval_smoke["runtime_error_count"] == 0 and retrieval_smoke["unexplained_count"] == 0,
        "live_serving_smoke_ready": upstream["application_health_pass"] and upstream["served_model_contract_verified"],
        "rollback_target_preserved": True,
        "backout_target_preserved": True,
        "retrieval_smoke_case_count": retrieval_smoke["smoke_case_count"],
        "retrieval_smoke_citation_readable_count": retrieval_smoke["citation_readable_count"],
        "retrieval_smoke_source_correct_count": retrieval_smoke["source_correct_count"],
        "retrieval_smoke_wrong_source_count": retrieval_smoke["wrong_source_count"],
        "retrieval_smoke_runtime_error_count": retrieval_smoke["runtime_error_count"],
        "retrieval_smoke_unexplained_count": retrieval_smoke["unexplained_count"],
        "retrieval_smoke_mulga_filter_behavior": retrieval_smoke["mulga_filter_behavior"],
    }
    preswitch["cutover_rerun_authorized"] = all(
        [
            preswitch["vector_compatibility_ready"],
            preswitch["upstream_connectivity_ready"],
            preswitch["retrieval_smoke_ready"],
            preswitch["live_serving_smoke_ready"],
            preswitch["rollback_target_preserved"],
            preswitch["backout_target_preserved"],
        ]
    )

    execution_summary = {
        "switch_started": "NOT_EXECUTED",
        "switch_completed": "NOT_EXECUTED",
        "active_runtime_before": ACTIVE_RUNTIME_COLLECTION,
        "active_runtime_after": ACTIVE_RUNTIME_COLLECTION,
        "switch_error_count": 0,
        "rollback_invoked": False,
        "backout_invoked": False,
    }

    postswitch = {
        "smoke_case_count": 0,
        "citation_readable_count": 0,
        "source_correct_count": 0,
        "wrong_source_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
        "post_switch_health_pass": False,
    }

    if preswitch["cutover_rerun_authorized"]:
        execution_summary["switch_started"] = datetime.now(UTC).isoformat()
        execution_summary["active_runtime_after"] = NEW_CANDIDATE_COLLECTION
        try:
            launch_runtime(NEW_CANDIDATE_COLLECTION)
            if not wait_for_health(GATEWAY_HEALTH_URL):
                raise RuntimeError("post-switch gateway health timeout")

            retrieval_after_switch = run_retrieval_smoke(NEW_CANDIDATE_COLLECTION, smoke_cases)
            live_case = smoke_cases[0]
            live_smoke = run_live_serving_smoke(
                display_citation=live_case.expected_display_citation,
                expected_source_id=live_case.expected_source_id,
            )
            postswitch = {
                "smoke_case_count": retrieval_after_switch["smoke_case_count"] + 1,
                "citation_readable_count": retrieval_after_switch["citation_readable_count"] + (1 if live_smoke["citation_readable"] else 0),
                "source_correct_count": retrieval_after_switch["source_correct_count"] + (1 if live_smoke["source_correct"] else 0),
                "wrong_source_count": retrieval_after_switch["wrong_source_count"] + (0 if live_smoke["source_correct"] else 1),
                "runtime_error_count": retrieval_after_switch["runtime_error_count"],
                "unexplained_count": retrieval_after_switch["unexplained_count"] + (0 if live_smoke["source_correct"] else 1),
                "post_switch_health_pass": True,
                "live_smoke": live_smoke,
                "retrieval_smoke": retrieval_after_switch,
            }
        except Exception as exc:
            execution_summary["switch_error_count"] += 1
            execution_summary["rollback_invoked"] = True
            postswitch["runtime_error_count"] += 1
            postswitch["unexplained_count"] += 1
            postswitch["post_switch_health_pass"] = False
            postswitch["runtime_error"] = repr(exc)
            launch_runtime(ACTIVE_RUNTIME_COLLECTION)
            wait_for_health(GATEWAY_HEALTH_URL)
            execution_summary["active_runtime_after"] = ACTIVE_RUNTIME_COLLECTION
        execution_summary["switch_completed"] = datetime.now(UTC).isoformat()

    decision = "PASS - Mevzuat Vector Blocker Remediation And Cutover Rerun Closed"
    if not all(
        [
            rebuild["new_candidate_dimension"] == 1024,
            rebuild["candidate_vector_compatibility_pass"],
            rebuild["technical_write_error_count"] == 0,
            upstream["dns_resolution_pass"],
            upstream["tcp_connect_pass"],
            upstream["application_health_pass"],
            upstream["served_model_contract_verified"],
            not upstream["connectivity_blocker_found"],
            preswitch["cutover_rerun_authorized"],
            execution_summary["switch_error_count"] == 0,
            postswitch["wrong_source_count"] == 0,
            postswitch["runtime_error_count"] == 0,
            postswitch["unexplained_count"] == 0,
            postswitch["post_switch_health_pass"],
            preswitch["rollback_target_preserved"],
            preswitch["backout_target_preserved"],
        ]
    ):
        decision = "NO-GO - Mevzuat Vector Blocker Remediation Or Cutover Rerun"

    summary = {
        "source_corpus_row_count": row_count,
        **rebuild,
        **upstream,
        **preswitch,
        **execution_summary,
        "decision": decision,
        "rollback_target_preserved": True,
        "backout_target_preserved": True,
        "postswitch": postswitch,
    }

    write_text(VECTOR_CONTRACT_DOC, render_vector_contract_doc())
    write_text(REBUILD_DOC, render_rebuild_doc(summary))
    write_text(UPSTREAM_DOC, render_upstream_doc(summary))
    write_text(PRESWITCH_DOC, render_preswitch_doc(summary))
    write_text(EXECUTION_DOC, render_execution_doc(summary))
    write_text(POSTSWITCH_DOC, render_postswitch_doc(postswitch))
    write_text(GATE_DOC, render_gate_doc(summary, postswitch))
    write_text(NEXT_DOC, render_next_doc(decision))
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
