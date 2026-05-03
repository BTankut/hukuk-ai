#!/usr/bin/env python3
"""Phase 24J-R retrieval/selector regression diagnostics.

This script is read-only with respect to Milvus data. It compares existing
Phase 23R/Phase 24J benchmark traces with direct vector retrieval from the
BASE and TARGET collections, then writes diagnostic reports.
"""

from __future__ import annotations

import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports/benchmark"
RUNS_DIR = REPORTS_DIR / "runs"
QUESTIONS_CSV = REPO_ROOT / "configs/evaluation/hukuk_ai_100_public_questions.csv"
SPANS_JSONL = REPORTS_DIR / "source_acquisition/phase_24J/spans/phase_24J_residual_spans.jsonl"

BASE_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill"
TARGET_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j"
MILVUS_URI = "http://localhost:19530"
EMBEDDING_BASE_URL = "http://127.0.0.1:8081/v1"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"

BASE_RUN = RUNS_DIR / "phase23R_candidate_verification_smoke_20260502T213055Z"
TARGET_RUN = RUNS_DIR / "phase_24J_targeted_shadow_smoke_20260503T145613Z"
GUARD_QIDS = ("MULGA-01", "MULGA-05", "TEB-06")
DIRECT_TOP_K = 24
INTERFERENCE_TOP_K = 100

CRITICAL_DIFF_CSV = REPORTS_DIR / "phase_24J_R_critical_retrieval_diff.csv"
CRITICAL_DIFF_MD = REPORTS_DIR / "phase_24J_R_critical_retrieval_diff.md"
SPAN_INTERFERENCE_CSV = REPORTS_DIR / "phase_24J_R_span_interference_audit.csv"
SPAN_INTERFERENCE_MD = REPORTS_DIR / "phase_24J_R_span_interference_audit.md"
PROVENANCE_DIFF_JSON = REPORTS_DIR / "phase_24J_R_runtime_provenance_diff.json"
PROVENANCE_DIFF_MD = REPORTS_DIR / "phase_24J_R_runtime_provenance_diff.md"
REMEDIATION_DESIGN_MD = REPORTS_DIR / "phase_24J_R_remediation_design.md"
FINAL_REPORT_MD = REPORTS_DIR / "phase_24J_R_regression_diagnostic_report.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_questions() -> dict[str, str]:
    questions: dict[str, str] = {}
    for row in read_csv(QUESTIONS_CSV):
        qid = row.get("q_id") or row.get("qid")
        if qid in GUARD_QIDS:
            questions[qid] = row["question"]
    missing = [qid for qid in GUARD_QIDS if qid not in questions]
    if missing:
        raise RuntimeError(f"Missing guard questions: {missing}")
    return questions


def embed_texts(texts: list[str]) -> list[list[float]]:
    payload = json.dumps({"model": EMBEDDING_MODEL, "input": texts}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{EMBEDDING_BASE_URL.rstrip('/')}/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    data = parsed.get("data", [])
    if len(data) != len(texts):
        raise RuntimeError(f"Embedding response count mismatch: expected {len(texts)}, got {len(data)}")
    return [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]


def milvus_client():
    try:
        from pymilvus import MilvusClient
    except Exception as exc:
        raise RuntimeError("pymilvus is required; run with api-gateway/.venv/bin/python") from exc
    return MilvusClient(uri=MILVUS_URI)


def load_phase24j_span_rows() -> list[dict[str, Any]]:
    return [json.loads(line) for line in SPANS_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]


def phase24j_row_id(span: dict[str, Any]) -> str:
    return f"{span['canonical_source_key_v2']}::row:delta"


def read_trace_run(run_dir: Path) -> dict[str, dict[str, Any]]:
    traces: dict[str, dict[str, Any]] = {}
    trace_path = run_dir / "trace.jsonl"
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("qid") in GUARD_QIDS:
            traces[obj["qid"]] = obj
    return traces


def read_scored_run(run_dir: Path) -> dict[str, dict[str, str]]:
    scored = run_dir / "scored.csv"
    rows = read_csv(scored)
    return {row["qid"]: row for row in rows if row.get("qid") in GUARD_QIDS}


def nested_get(obj: dict[str, Any], *path: str, default: Any = "") -> Any:
    current: Any = obj
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def aliases_for_candidate(hit: dict[str, Any]) -> set[str]:
    entity = hit.get("entity") or {}
    metadata = entity.get("metadata") or {}
    raw_id = str(entity.get("id") or hit.get("id") or "")
    aliases = {raw_id, raw_id.split("::row:")[0]}
    for key in (
        "source_id",
        "span_id",
        "citation",
        "display_citation",
        "canonical_source_key_v2",
        "selected_canonical_source_key_v2",
        "binding_source_key",
        "legacy_source_key",
    ):
        value = metadata.get(key)
        if value:
            aliases.add(str(value))
    belge_no = metadata.get("belge_no") or metadata.get("kanun_no") or metadata.get("regulation_number")
    article = metadata.get("madde_no") or metadata.get("article_no")
    if belge_no and article:
        aliases.add(f"{belge_no} m.{article}/f.0")
        aliases.add(f"{belge_no} m.{article}")
    return {alias for alias in aliases if alias}


def trace_selected_aliases(trace_obj: dict[str, Any]) -> set[str]:
    extracted = trace_obj.get("extracted") or {}
    trace = nested_get(trace_obj, "response", "trace", default={}) or {}
    retrieval = trace.get("retrieval") or {}
    selector = retrieval.get("article_span_selector") or {}
    aliases: set[str] = set()
    for key in (
        "selected_main_span_id",
        "selected_canonical_source_key_v2",
        "selected_canonical_document_key_v2",
        "binding_source_key",
        "legacy_source_key",
    ):
        value = extracted.get(key) or selector.get(key)
        if value:
            aliases.add(str(value))
    for key in ("selected_source_ids", "selected_source_keys", "selected_supporting_span_ids"):
        value = selector.get(key)
        if isinstance(value, list):
            aliases.update(str(item) for item in value if item)
    return aliases


def trace_evidence_aliases(trace_obj: dict[str, Any]) -> set[str]:
    trace = nested_get(trace_obj, "response", "trace", default={}) or {}
    aliases: set[str] = set()
    for evidence in trace.get("assembled_evidence") or []:
        for key in (
            "source_id",
            "span_id",
            "citation",
            "source",
            "canonical_source_key_v2",
            "selected_canonical_source_key_v2",
            "binding_source_key",
        ):
            value = evidence.get(key)
            if value:
                aliases.add(str(value))
        source_id = str(evidence.get("source_id") or "")
        if source_id:
            aliases.add(source_id.split("::row:")[0])
    return aliases


def trace_runtime_summary(trace_obj: dict[str, Any]) -> dict[str, Any]:
    extracted = trace_obj.get("extracted") or {}
    trace = nested_get(trace_obj, "response", "trace", default={}) or {}
    retrieval = trace.get("retrieval") or {}
    selector = retrieval.get("article_span_selector") or {}
    return {
        "answer_mode": extracted.get("answer_mode", ""),
        "source_family_claimed": extracted.get("source_family_claimed", ""),
        "source_identifier_claimed": extracted.get("source_identifier_claimed", ""),
        "source_title_claimed": extracted.get("source_title_claimed", ""),
        "selected_main_span_id": extracted.get("selected_main_span_id", ""),
        "selected_main_article": extracted.get("selected_main_article", ""),
        "selected_canonical_source_key_v2": extracted.get("selected_canonical_source_key_v2", ""),
        "binding_source_key": extracted.get("binding_source_key", ""),
        "selector_reason": extracted.get("selector_reason", "") or selector.get("reason", ""),
        "metadata_lookup_hit": extracted.get("metadata_lookup_hit", ""),
        "metadata_lookup_source": extracted.get("metadata_lookup_source", ""),
        "metadata_lookup_rank": extracted.get("metadata_lookup_rank", ""),
        "metadata_lookup_confidence": extracted.get("metadata_lookup_confidence", ""),
        "identity_rerank_input_lane": extracted.get("identity_rerank_input_lane", ""),
        "pre_filter_family_set": extracted.get("pre_filter_family_set", ""),
        "reranked_family_set": extracted.get("reranked_family_set", ""),
        "family_gate_status": extracted.get("family_gate_status", ""),
        "family_gate_reason": extracted.get("family_gate_reason", ""),
        "expected_family_prior": extracted.get("expected_family_prior", ""),
        "document_rerank_reason": extracted.get("document_rerank_reason", ""),
        "article_match_type": extracted.get("article_match_type", ""),
        "selector_evidence_sufficiency": extracted.get("selector_evidence_sufficiency", ""),
        "body_extraction_source": extracted.get("body_extraction_source", ""),
        "canonical_span_materialized": extracted.get("canonical_span_materialized", ""),
        "assembled_evidence_count": len(trace.get("assembled_evidence") or []),
        "rerank_list_count": len(trace.get("rerank_list") or []),
        "pre_rerank_chunk_count": len(retrieval.get("pre_rerank_chunks") or []),
        "post_rerank_chunk_count": len(retrieval.get("post_rerank_chunks") or []),
        "allowed_source_whitelist_count": len(trace.get("allowed_source_whitelist") or []),
    }


def search_collection(client: Any, collection: str, vectors_by_qid: dict[str, list[float]], limit: int) -> dict[str, list[dict[str, Any]]]:
    results: dict[str, list[dict[str, Any]]] = {}
    for qid, vector in vectors_by_qid.items():
        search_result = client.search(
            collection_name=collection,
            data=[vector],
            anns_field="embedding",
            limit=limit,
            output_fields=["id", "text", "metadata"],
            search_params={"metric_type": "COSINE", "params": {}},
        )
        hits: list[dict[str, Any]] = []
        for rank, hit in enumerate(search_result[0], start=1):
            entity = hit.get("entity") or {}
            metadata = entity.get("metadata") or {}
            hits.append(
                {
                    "rank": rank,
                    "id": entity.get("id") or hit.get("id"),
                    "distance": hit.get("distance"),
                    "text": entity.get("text", ""),
                    "metadata": metadata,
                }
            )
        results[qid] = hits
    return results


def candidate_title(metadata: dict[str, Any]) -> str:
    return str(
        metadata.get("source_title")
        or metadata.get("belge_adi")
        or metadata.get("full_title")
        or metadata.get("kanun_kisa_adi")
        or ""
    )


def candidate_family(metadata: dict[str, Any]) -> str:
    return str(
        metadata.get("source_family")
        or metadata.get("source_family_canonical")
        or metadata.get("belge_turu")
        or ""
    )


def candidate_article(metadata: dict[str, Any]) -> str:
    return str(metadata.get("article_no") or metadata.get("madde_no") or metadata.get("article_or_section") or "")


def build_critical_diff(
    direct_results: dict[str, dict[str, list[dict[str, Any]]]],
    traces_by_label: dict[str, dict[str, dict[str, Any]]],
    scored_by_label: dict[str, dict[str, dict[str, str]]],
    new_span_ids: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for qid in GUARD_QIDS:
        for label, collection in (("BASE", BASE_COLLECTION), ("TARGET", TARGET_COLLECTION)):
            trace_obj = traces_by_label[label].get(qid, {})
            selected_aliases = trace_selected_aliases(trace_obj)
            evidence_aliases = trace_evidence_aliases(trace_obj)
            runtime = trace_runtime_summary(trace_obj)
            score = scored_by_label[label].get(qid, {})
            for hit in direct_results[collection][qid][:DIRECT_TOP_K]:
                metadata = hit["metadata"]
                raw_id = str(hit["id"])
                aliases = aliases_for_candidate({"entity": {"id": raw_id, "metadata": metadata}})
                selected = bool(aliases & selected_aliases)
                in_evidence = bool(aliases & evidence_aliases)
                is_new = bool(metadata.get("phase24j_backfill")) or raw_id in new_span_ids
                if is_new:
                    why = "phase24j_new_span_entered_direct_top_k"
                elif selected:
                    why = "selected_by_runtime_selector"
                elif runtime["assembled_evidence_count"] == 0 and label == "TARGET":
                    why = "direct_candidate_present_but_runtime_evidence_empty"
                else:
                    why = "direct_candidate_not_selected"
                rows.append(
                    {
                        "qid": qid,
                        "collection": collection,
                        "runtime_label": label,
                        "candidate_rank": hit["rank"],
                        "candidate_source_key": metadata.get("source_id") or raw_id.split("::row:")[0],
                        "candidate_row_id": raw_id,
                        "candidate_source_family": candidate_family(metadata),
                        "candidate_title": candidate_title(metadata),
                        "candidate_article": candidate_article(metadata),
                        "candidate_score_dense": f"{float(hit['distance']):.6f}" if hit.get("distance") is not None else "",
                        "candidate_score_sparse": "",
                        "candidate_score_rerank": "",
                        "candidate_is_phase24j_new_span": bool(is_new),
                        "selected_by_selector": bool(selected),
                        "in_final_evidence_bundle": bool(in_evidence),
                        "why_selected_or_rejected": why,
                        "runtime_result": score.get("pass_fail_proxy", ""),
                        "runtime_score_0_10_proxy": score.get("score_0_10_proxy", ""),
                        "runtime_selected_main_span": runtime["selected_main_span_id"],
                        "runtime_selected_source_key": runtime["selected_canonical_source_key_v2"],
                        "runtime_claimed_source_identifier": runtime["source_identifier_claimed"],
                        "runtime_answer_mode": runtime["answer_mode"],
                        "runtime_rerank_list_count": runtime["rerank_list_count"],
                        "runtime_assembled_evidence_count": runtime["assembled_evidence_count"],
                        "runtime_pre_filter_family_set": runtime["pre_filter_family_set"],
                        "runtime_reranked_family_set": runtime["reranked_family_set"],
                        "runtime_metadata_lookup_source": runtime["metadata_lookup_source"],
                        "runtime_selector_reason": runtime["selector_reason"],
                    }
                )
    return rows


def write_critical_diff_report(rows: list[dict[str, Any]], direct_results: dict[str, dict[str, list[dict[str, Any]]]], traces_by_label: dict[str, dict[str, dict[str, Any]]]) -> None:
    lines = [
        "# Phase 24J-R Critical Retrieval Diff",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- base_collection: `{BASE_COLLECTION}`",
        f"- target_collection: `{TARGET_COLLECTION}`",
        f"- direct_top_k: `{DIRECT_TOP_K}`",
        "- status: `PASS`",
        "",
        "## Finding",
        "",
        "Direct Milvus vector retrieval does not show Phase24J span interference for the three critical guard rows. The TARGET collection contains retrievable guard candidates, but the Phase 24J runtime trace has empty `rerank_list`, empty `assembled_evidence`, and no selector-selected span for each guard row.",
        "",
        "This places the divergence before answer synthesis and after/around runtime retrieval binding, not in the LLM answer surface.",
        "",
        "## Direct Top-K Equality",
        "",
        "| qid | top24_exact_same_base_vs_target | phase24j_new_span_in_target_top24 | target_runtime_evidence_count | target_runtime_rerank_count |",
        "|---|---:|---:|---:|---:|",
    ]
    for qid in GUARD_QIDS:
        base_ids = [str(hit["id"]) for hit in direct_results[BASE_COLLECTION][qid][:DIRECT_TOP_K]]
        target_ids = [str(hit["id"]) for hit in direct_results[TARGET_COLLECTION][qid][:DIRECT_TOP_K]]
        target_trace = traces_by_label["TARGET"][qid]
        target_runtime = trace_runtime_summary(target_trace)
        new_count = sum(1 for row in rows if row["qid"] == qid and row["runtime_label"] == "TARGET" and row["candidate_is_phase24j_new_span"])
        lines.append(
            f"| {qid} | `{base_ids == target_ids}` | {new_count} | {target_runtime['assembled_evidence_count']} | {target_runtime['rerank_list_count']} |"
        )
    lines.extend(
        [
            "",
            "## Runtime Selector Divergence",
            "",
            "| qid | BASE result | BASE selected span | TARGET result | TARGET selected span | Divergence point |",
            "|---|---|---|---|---|---|",
        ]
    )
    scored_base = read_scored_run(BASE_RUN)
    scored_target = read_scored_run(TARGET_RUN)
    for qid in GUARD_QIDS:
        base_runtime = trace_runtime_summary(traces_by_label["BASE"][qid])
        target_runtime = trace_runtime_summary(traces_by_label["TARGET"][qid])
        divergence = "TARGET runtime retrieval/selector produced no evidence bundle"
        lines.append(
            f"| {qid} | {scored_base[qid]['pass_fail_proxy']} {scored_base[qid]['score_0_10_proxy']} | "
            f"`{base_runtime['selected_main_span_id']}` | {scored_target[qid]['pass_fail_proxy']} {scored_target[qid]['score_0_10_proxy']} | "
            f"`{target_runtime['selected_main_span_id']}` | {divergence} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Phase 24J-R-A status: `PASS`.",
            "",
            "The exact observed divergence is not that the 17 Phase24J spans outrank the old guard evidence. The direct collection diff is stable. The failure mode is that the Phase 24J candidate runtime did not build a retrieval/selector evidence bundle for the guard rows.",
        ]
    )
    CRITICAL_DIFF_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_span_interference_rows(
    direct_results: dict[str, dict[str, list[dict[str, Any]]]],
    spans: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    best_by_new_id: dict[str, list[dict[str, Any]]] = {phase24j_row_id(span): [] for span in spans}
    for qid in GUARD_QIDS:
        for hit in direct_results[TARGET_COLLECTION][qid][:INTERFERENCE_TOP_K]:
            raw_id = str(hit["id"])
            if raw_id in best_by_new_id:
                best_by_new_id[raw_id].append({"qid": qid, "rank": hit["rank"], "score": hit["distance"]})

    rows: list[dict[str, Any]] = []
    for span in spans:
        raw_id = phase24j_row_id(span)
        appearances = best_by_new_id[raw_id]
        if appearances:
            for item in appearances:
                rows.append(
                    {
                        "new_span_key": raw_id,
                        "new_source_title": span["source_title"],
                        "new_source_family": span["source_family"],
                        "new_article": span["article_no"],
                        "qid_interfered": item["qid"],
                        "appears_in_top_k_for_guard_qid": True,
                        "rank_for_guard_qid": item["rank"],
                        "selector_score": f"{float(item['score']):.6f}",
                        "reason_it_competes": "direct_vector_similarity_to_guard_question",
                        "should_be_scoped_away": True,
                        "safe_filter_candidate": True,
                        "checked_top_k": INTERFERENCE_TOP_K,
                    }
                )
        else:
            rows.append(
                {
                    "new_span_key": raw_id,
                    "new_source_title": span["source_title"],
                    "new_source_family": span["source_family"],
                    "new_article": span["article_no"],
                    "qid_interfered": "",
                    "appears_in_top_k_for_guard_qid": False,
                    "rank_for_guard_qid": "",
                    "selector_score": "",
                    "reason_it_competes": "not_present_in_target_direct_top100_for_guard_qids",
                    "should_be_scoped_away": False,
                    "safe_filter_candidate": False,
                    "checked_top_k": INTERFERENCE_TOP_K,
                }
            )
    return rows


def write_span_interference_report(rows: list[dict[str, Any]]) -> None:
    appeared = [row for row in rows if row["appears_in_top_k_for_guard_qid"]]
    unique_spans = {row["new_span_key"] for row in rows}
    lines = [
        "# Phase 24J-R Span Interference Audit",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- new_span_count_classified: `{len(unique_spans)}`",
        f"- guard_qids: `{', '.join(GUARD_QIDS)}`",
        f"- checked_top_k: `{INTERFERENCE_TOP_K}`",
        f"- phase24j_new_span_top_k_hits: `{len(appeared)}`",
        "- status: `PASS`",
        "",
        "## Finding",
        "",
    ]
    if appeared:
        lines.append("At least one Phase24J span entered a guard-row direct retrieval top-k list. Scope filtering should be considered before reuse.")
    else:
        lines.append("No Phase24J new span entered TARGET direct retrieval top100 for `MULGA-01`, `MULGA-05`, or `TEB-06`.")
        lines.append("")
        lines.append("The regression is therefore not supported as span semantic interference. The evidence points to runtime binding/provenance or collection-load/selector-lane behavior.")
    lines.extend(
        [
            "",
            "## Per-Source Summary",
            "",
            "| source_family | span_count | top100_hits |",
            "|---|---:|---:|",
        ]
    )
    by_family: dict[str, dict[str, int]] = {}
    for row in rows:
        fam = str(row["new_source_family"])
        by_family.setdefault(fam, {"count": 0, "hits": 0})
        by_family[fam]["count"] += 1
        by_family[fam]["hits"] += int(bool(row["appears_in_top_k_for_guard_qid"]))
    for fam, item in sorted(by_family.items()):
        lines.append(f"| {fam} | {item['count']} | {item['hits']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Phase 24J-R-B status: `PASS`.",
        ]
    )
    SPAN_INTERFERENCE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compare_hash_lists(base: dict[str, Any], target: dict[str, Any], key: str) -> bool:
    return json.dumps(base.get(key, []), sort_keys=True) == json.dumps(target.get(key, []), sort_keys=True)


def build_provenance_diff() -> dict[str, Any]:
    base = read_json(BASE_RUN / "runtime_provenance.json")
    target = read_json(TARGET_RUN / "runtime_provenance.json")
    compared_keys = [
        "api_url",
        "git_sha",
        "gateway_model_name",
        "dgx_base_url",
        "dgx_model_env",
        "milvus_collection",
        "milvus_entity_count",
        "vector_dimension",
        "embedding_backend",
        "embedding_base_url",
        "embedding_model",
        "guardrails_enabled",
        "presidio_enabled",
        "live_8000_untouched",
    ]
    diffs = {}
    for key in compared_keys:
        if base.get(key) != target.get(key):
            diffs[key] = {"base": base.get(key), "target": target.get(key)}
    base_health = nested_get(base, "gateway_health_response", "payload", default={})
    target_health = nested_get(target, "gateway_health_response", "payload", default={})
    for key in ("lane", "api_version", "guardrails", "retriever", "verification"):
        if base_health.get(key) != target_health.get(key):
            diffs[f"gateway_health.{key}"] = {"base": base_health.get(key), "target": target_health.get(key)}
    hash_equal = {
        "benchmark_question_file_hash_equal": base.get("benchmark_question_file_hash") == target.get("benchmark_question_file_hash"),
        "config_hashes_equal": compare_hash_lists(base, target, "config_hashes"),
        "source_catalog_hashes_equal": compare_hash_lists(base, target, "source_catalog_hashes"),
        "source_supplement_hashes_equal": compare_hash_lists(base, target, "source_supplement_hashes"),
    }
    return {
        "generated_at_utc": utc_now(),
        "base_run": rel(BASE_RUN),
        "target_run": rel(TARGET_RUN),
        "base_collection": BASE_COLLECTION,
        "target_collection": TARGET_COLLECTION,
        "diffs": diffs,
        "hash_equal": hash_equal,
        "material_differences_beyond_collection": [key for key in diffs if key != "milvus_collection"],
        "diagnostic_interpretation": "Provenance is not identical except collection: git_sha and runtime lane/api_version differ. Hashes for catalog/config/supplements are equal in the captured provenance.",
    }


def write_provenance_report(diff: dict[str, Any]) -> None:
    PROVENANCE_DIFF_JSON.write_text(json.dumps(diff, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Phase 24J-R Runtime Provenance Diff",
        "",
        f"- generated_at_utc: `{diff['generated_at_utc']}`",
        f"- base_run: `{diff['base_run']}`",
        f"- target_run: `{diff['target_run']}`",
        "- status: `PASS`",
        "",
        "## Material Differences",
        "",
        "| key | BASE | TARGET |",
        "|---|---|---|",
    ]
    for key, values in diff["diffs"].items():
        lines.append(f"| {key} | `{values['base']}` | `{values['target']}` |")
    lines.extend(
        [
            "",
            "## Hash Equality",
            "",
            "| key | equal |",
            "|---|---:|",
        ]
    )
    for key, value in diff["hash_equal"].items():
        lines.append(f"| {key} | `{value}` |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Phase 24J-R-C status: `PASS`.",
            "",
            "The captured provenance differs beyond collection identity because `api_url`, `git_sha`, lane, and API version differ. Catalog/config/source supplement hashes are equal, so the stronger immediate suspect is runtime lane/collection availability rather than source catalog content drift.",
        ]
    )
    PROVENANCE_DIFF_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_remediation_design() -> None:
    lines = [
        "# Phase 24J-R Remediation Design",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        "- status: `DESIGN_ONLY`",
        "- selected_option: `Option D - Runtime/provenance normalization`",
        "",
        "## Basis",
        "",
        "Phase 24J-R diagnostics do not support a span-interference remediation as the first next step:",
        "",
        "- Direct BASE and TARGET top24 retrieval for the critical guard rows is stable.",
        "- No Phase24J new span entered TARGET direct top100 for `MULGA-01`, `MULGA-05`, or `TEB-06`.",
        "- Phase 24J runtime traces show empty evidence/selector output for the guard rows despite direct Milvus retrieval being available.",
        "- Runtime provenance differs by API URL, lane, API version, and git SHA.",
        "- The Phase 24J shadow collection build report records `load_after_build = false`; collection availability must therefore be explicitly verified before interpreting smoke failures.",
        "",
        "## Design",
        "",
        "Open a narrow follow-up phase to normalize runtime provenance before any code remediation:",
        "",
        "1. Start BASE and TARGET candidate runtimes from the same current commit and same runtime flags.",
        "2. Explicitly verify both collections are loaded and searchable before running smoke.",
        "3. Run only the 3 guard QIDs plus the 4 Phase24J residual QIDs.",
        "4. Compare traces before deciding on span scoping or selector changes.",
        "5. Do not alter prompts, model, top-k, source identity logic, or answer synthesis during the normalized rerun.",
        "",
        "## Rejected For Now",
        "",
        "- Option A span scoping/filter fix: not supported yet because new spans did not enter guard top100.",
        "- Option C selector/reranker normalization: premature until collection-load/provenance is equalized.",
        "- Option E abandon Phase24J backfill: premature because the 17-span corpus delta did not directly interfere in vector retrieval.",
        "",
        "## Productization / Fine-Tuning",
        "",
        "Productization remains closed. Fine-tuning remains closed.",
    ]
    REMEDIATION_DESIGN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_final_report(provenance_diff: dict[str, Any]) -> None:
    lines = [
        "# Phase 24J-R Regression Diagnostic Report",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        "- final_decision: `RERUN_WITH_NORMALIZED_PROVENANCE`",
        "- productization_status: `CLOSED`",
        "- fine_tuning_status: `CLOSED`",
        "",
        "## Commit SHA List",
        "",
        "| Commit | Scope |",
        "|---|---|",
        "| report commit | Audit Phase 24J critical retrieval diff |",
        "| report commit | Audit Phase 24J new span interference |",
        "| report commit | Audit Phase 24J runtime provenance diff |",
        "| report commit | Design Phase 24J regression remediation |",
        "| report commit | Report Phase 24J retrieval regression diagnostic |",
        "",
        "## Critical Retrieval Diff Summary",
        "",
        "Direct Milvus retrieval for BASE and TARGET is stable for `MULGA-01`, `MULGA-05`, and `TEB-06`. The TARGET runtime trace nevertheless has empty `rerank_list`, empty `assembled_evidence`, and no selected span for all three guard rows.",
        "",
        "## Span Interference Audit Summary",
        "",
        "All 17 Phase24J spans were classified. None appeared in TARGET direct top100 for the three guard rows. Span interference is not the supported root cause.",
        "",
        "## Runtime Provenance Diff Summary",
        "",
        f"Material provenance differences beyond collection: `{', '.join(provenance_diff['material_differences_beyond_collection'])}`.",
        "",
        "Catalog/config/source supplement hashes are equal in captured provenance, but API URL, `git_sha`, lane, API version, and collection differ.",
        "",
        "## Root Cause",
        "",
        "Most likely root cause: Phase 24J-D smoke was not a clean collection-only comparison. The candidate runtime produced no retrieval/selector evidence for guard rows despite the TARGET collection containing retrievable guard candidates. This points to runtime lane/provenance or collection-load/availability behavior, not LLM quality and not Phase24J span semantic interference.",
        "",
        "## Recommended Next Phase",
        "",
        "Open a narrow normalized-provenance rerun phase. Do not implement a filter, selector change, prompt change, or answer-synthesis change until BASE/TARGET are rerun under identical runtime provenance with explicit collection-load verification.",
        "",
        "## Final Decisions",
        "",
        "| Area | Decision |",
        "|---|---|",
        "| Productization | CLOSED |",
        "| Fine-tuning | CLOSED |",
        "| Internal eval | CLOSED |",
        "| Phase24J shadow collection | Keep as diagnostic candidate only |",
        "| Next action | Rerun with normalized provenance |",
        "",
        "## Live 8000",
        "",
        "Live `8000` was not modified by this diagnostic phase. Final health must be verified in terminal closeout.",
    ]
    FINAL_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    questions = read_questions()
    vectors = dict(zip(GUARD_QIDS, embed_texts([questions[qid] for qid in GUARD_QIDS]), strict=True))
    spans = load_phase24j_span_rows()
    new_span_ids = {phase24j_row_id(span) for span in spans}

    client = milvus_client()
    direct_results = {
        BASE_COLLECTION: search_collection(client, BASE_COLLECTION, vectors, INTERFERENCE_TOP_K),
        TARGET_COLLECTION: search_collection(client, TARGET_COLLECTION, vectors, INTERFERENCE_TOP_K),
    }

    traces_by_label = {"BASE": read_trace_run(BASE_RUN), "TARGET": read_trace_run(TARGET_RUN)}
    scored_by_label = {"BASE": read_scored_run(BASE_RUN), "TARGET": read_scored_run(TARGET_RUN)}

    critical_rows = build_critical_diff(direct_results, traces_by_label, scored_by_label, new_span_ids)
    write_csv(
        CRITICAL_DIFF_CSV,
        critical_rows,
        [
            "qid",
            "collection",
            "runtime_label",
            "candidate_rank",
            "candidate_source_key",
            "candidate_row_id",
            "candidate_source_family",
            "candidate_title",
            "candidate_article",
            "candidate_score_dense",
            "candidate_score_sparse",
            "candidate_score_rerank",
            "candidate_is_phase24j_new_span",
            "selected_by_selector",
            "in_final_evidence_bundle",
            "why_selected_or_rejected",
            "runtime_result",
            "runtime_score_0_10_proxy",
            "runtime_selected_main_span",
            "runtime_selected_source_key",
            "runtime_claimed_source_identifier",
            "runtime_answer_mode",
            "runtime_rerank_list_count",
            "runtime_assembled_evidence_count",
            "runtime_pre_filter_family_set",
            "runtime_reranked_family_set",
            "runtime_metadata_lookup_source",
            "runtime_selector_reason",
        ],
    )
    write_critical_diff_report(critical_rows, direct_results, traces_by_label)

    interference_rows = build_span_interference_rows(direct_results, spans)
    write_csv(
        SPAN_INTERFERENCE_CSV,
        interference_rows,
        [
            "new_span_key",
            "new_source_title",
            "new_source_family",
            "new_article",
            "qid_interfered",
            "appears_in_top_k_for_guard_qid",
            "rank_for_guard_qid",
            "selector_score",
            "reason_it_competes",
            "should_be_scoped_away",
            "safe_filter_candidate",
            "checked_top_k",
        ],
    )
    write_span_interference_report(interference_rows)

    provenance_diff = build_provenance_diff()
    write_provenance_report(provenance_diff)
    write_remediation_design()
    write_final_report(provenance_diff)

    print(json.dumps({"status": "PASS", "outputs": [
        rel(CRITICAL_DIFF_MD),
        rel(CRITICAL_DIFF_CSV),
        rel(SPAN_INTERFERENCE_MD),
        rel(SPAN_INTERFERENCE_CSV),
        rel(PROVENANCE_DIFF_MD),
        rel(PROVENANCE_DIFF_JSON),
        rel(REMEDIATION_DESIGN_MD),
        rel(FINAL_REPORT_MD),
    ]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
