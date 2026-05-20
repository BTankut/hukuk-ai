from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from data_pipeline.judicial import (
    build_judicial_chunks_stream,
    build_judicial_exact_lookup_index,
    build_judicial_lexical_index,
    build_judicial_manifest_record,
)
from rag.legal_rag_orchestrator import LegalRagOrchestrator, LegalRuntimeConfig
from rag.retriever import RetrievalResult, RetrievalStats
from routers.chat import ConversationStore, get_conversation_store, router as chat_router


JUDICIAL_TEXT = """T. C. Yargıtay 9. Hukuk Dairesi

Davacı işçilik alacağı ve fazla mesai ücreti istemiştir.

Mahkemece verilen karar temyiz edilmiştir.

Yargıtay, TBK m.49 bakımından tazminat koşullarını ve işçilik alacağı ispatını değerlendirmiştir.

Sonuç olarak hükmün bozulmasına karar verilmiştir."""

TRIAL_COURT_TEXT = """İSTANBUL 3. ASLİYE TİCARET MAHKEMESİ

Davacı, haksız fiil nedeniyle uğradığı zararın tazminini istemiştir.

Mahkeme, TBK m.49 kapsamında kusur, zarar ve illiyet bağı koşullarını değerlendirmiştir.

Talebin somut deliller kapsamında kısmen kabulüne karar verilmiştir."""


class FakeMevzuatRetriever:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def retrieve(self, *, query: str, top_k: int, metadata_filter: Any | None = None):
        self.calls.append({"query": query, "top_k": top_k, "metadata_filter": metadata_filter})
        result = RetrievalResult(
            chunk_id="tbk-49",
            text="Haksız fiilden doğan zararın tazmini için kusur, zarar ve uygun illiyet bağı aranır.",
            score=0.92,
            metadata={
                "source_type": "legislation",
                "law_short_name": "TBK",
                "law_no": "6098",
                "madde_no": "49",
                "source_title": "Türk Borçlar Kanunu",
                "source_url": "https://mevzuat.gov.tr/tbk-49",
            },
        )
        return [result], RetrievalStats(
            collection="mevzuat",
            query_preview=query[:80],
            top_k=top_k,
            filter_expr=None,
            hit_count=1,
            latency_ms=1.0,
        )


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _build_runtime(tmp_path: Path, *, judicial_enabled: bool) -> LegalRagOrchestrator:
    processed = tmp_path / "processed"
    processed.mkdir()
    record = build_judicial_manifest_record(
        text=JUDICIAL_TEXT,
        source_authority="Yargıtay",
        court="Yargıtay",
        chamber="9HD",
        decision_date="2024-05-10",
        esas_no="2024/12345",
        karar_no="2024/6789",
        source_url="https://karararama.yargitay.gov.tr/runtime",
        download_timestamp="2026-05-20T00:00:00+00:00",
        related_law_refs=["TBK m.49"],
    )
    manifest_path = processed / "judicial_manifest.jsonl"
    _write_jsonl(manifest_path, [record])
    build_judicial_chunks_stream(manifest_path, processed, max_paragraphs_per_chunk=2)
    build_judicial_exact_lookup_index(
        manifest_path,
        processed,
        chunks_path=processed / "judicial_chunks.jsonl",
    )
    build_judicial_lexical_index(processed / "judicial_chunks.jsonl", processed)
    return LegalRagOrchestrator(
        config=LegalRuntimeConfig(
            judicial_runtime_enabled=judicial_enabled,
            processed_dir=processed,
            exact_lookup_path=processed / "judicial_exact_lookup.sqlite",
            lexical_index_path=processed / "judicial_lexical_index.sqlite",
        ),
        mevzuat_retriever=FakeMevzuatRetriever(),
    )


def _build_trial_court_runtime(tmp_path: Path, *, judicial_enabled: bool) -> LegalRagOrchestrator:
    processed = tmp_path / "processed"
    processed.mkdir()
    record = build_judicial_manifest_record(
        text=TRIAL_COURT_TEXT,
        source_authority="Yerel Mahkeme",
        court="İSTANBUL\n3. ASLİYE TİCARET MAHKEMESİ",
        chamber="GENEL",
        decision_date="2023-10-31",
        esas_no="2022/140",
        karar_no="2023/521",
        source_url="https://example.invalid/istanbul-3-atm",
        download_timestamp="2026-05-20T00:00:00+00:00",
        related_law_refs=["TBK m.49"],
    )
    manifest_path = processed / "judicial_manifest.jsonl"
    _write_jsonl(manifest_path, [record])
    build_judicial_chunks_stream(manifest_path, processed, max_paragraphs_per_chunk=2)
    build_judicial_exact_lookup_index(
        manifest_path,
        processed,
        chunks_path=processed / "judicial_chunks.jsonl",
    )
    build_judicial_lexical_index(processed / "judicial_chunks.jsonl", processed)
    return LegalRagOrchestrator(
        config=LegalRuntimeConfig(
            judicial_runtime_enabled=judicial_enabled,
            processed_dir=processed,
            exact_lookup_path=processed / "judicial_exact_lookup.sqlite",
            lexical_index_path=processed / "judicial_lexical_index.sqlite",
        ),
        mevzuat_retriever=FakeMevzuatRetriever(),
    )


def _make_client(runtime: LegalRagOrchestrator) -> TestClient:
    app = FastAPI()
    app.state.legal_rag_orchestrator = runtime
    app.include_router(chat_router)
    app.dependency_overrides[get_conversation_store] = lambda: ConversationStore()
    return TestClient(app)


def _post(client: TestClient, content: str) -> dict[str, Any]:
    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": content}],
            "include_trace": True,
            "stream": False,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_runtime_config_judicial_disabled_fails_closed_before_generation(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("JUDICIAL_RUNTIME_ENABLED", raising=False)
    runtime = _build_runtime(tmp_path, judicial_enabled=False)
    with _make_client(runtime) as client:
        payload = _post(client, "Yargıtay 9HD E. 2024/12345 K. 2024/6789 kararını açıkla")

    assert payload["blocked"] is True
    assert payload["final_reason"] == "judicial_runtime_disabled"
    assert payload["citations"] == []
    assert payload["trace"]["decision_lane"] == "legal_rag_runtime"


def test_runtime_config_judicial_enabled_exact_lookup_chat_path(tmp_path) -> None:
    runtime = _build_runtime(tmp_path, judicial_enabled=True)
    with _make_client(runtime) as client:
        payload = _post(client, "Yargıtay 9HD E. 2024/12345 K. 2024/6789 kararını açıkla")

    answer = payload["choices"][0]["message"]["content"]
    assert payload["blocked"] is False
    assert payload["final_mode"] == "answer"
    assert any("E. 2024/12345 K. 2024/6789" in citation for citation in payload["citations"])
    assert "Yargı kararları / içtihat değerlendirmesi" in answer
    assert "judicial_decision" in payload["trace"]["answer_contract"]["source_types"]


def test_sqlite_fts5_lexical_runtime_path_has_judicial_citation_contract(tmp_path) -> None:
    runtime = _build_runtime(tmp_path, judicial_enabled=True)
    with _make_client(runtime) as client:
        payload = _post(client, "işçilik alacağı hakkında Yargıtay içtihadı var mı?")

    assert payload["blocked"] is False
    assert payload["trace"]["answer_contract"]["judicial_evidence_count"] >= 1
    assert any("Yargıtay 9HD" in citation for citation in payload["citations"])
    assert any("YARGITAY_9HD_2024_12345E_2024_6789K_2024-05-10" in citation for citation in payload["citations"])


def test_trial_court_exact_lookup_falls_back_to_case_number_metadata_for_turkish_case_drift(tmp_path) -> None:
    runtime = _build_trial_court_runtime(tmp_path, judicial_enabled=True)
    with _make_client(runtime) as client:
        payload = _post(client, "İstanbul 3. Asliye Ticaret Mahkemesi E. 2022/140 K. 2023/521 kararını açıkla")

    assert payload["blocked"] is False
    assert any("E. 2022/140 K. 2023/521" in citation for citation in payload["citations"])
    evidence = payload["trace"]["evidence"]
    assert evidence
    assert any("exact_metadata" in item["score_components"] for item in evidence)


def test_mixed_legislation_and_judicial_answer_separates_source_types(tmp_path) -> None:
    runtime = _build_runtime(tmp_path, judicial_enabled=True)
    with _make_client(runtime) as client:
        payload = _post(client, "TBK m.49 kapsamında işçilik alacağı ve Yargıtay içtihadı nedir?")

    answer = payload["choices"][0]["message"]["content"]
    assert payload["blocked"] is False
    assert "Mevzuat dayanağı" in answer
    assert "Yargı kararları / içtihat değerlendirmesi" in answer
    assert any(citation.startswith("TBK m.49") for citation in payload["citations"])
    assert any("Yargıtay 9HD" in citation for citation in payload["citations"])
    assert payload["verification"]["source_type_confusion"] is False


def test_legislation_only_runtime_uses_mevzuat_and_has_no_judicial_leakage_when_enabled(tmp_path) -> None:
    runtime = _build_runtime(tmp_path, judicial_enabled=True)
    with _make_client(runtime) as client:
        payload = _post(client, "TBK m.49 haksız fiil şartları nelerdir?")

    answer = payload["choices"][0]["message"]["content"]
    assert payload["blocked"] is False
    assert "Mevzuat dayanağı" in answer
    assert "Yargı kararları / içtihat değerlendirmesi" not in answer
    assert payload["trace"]["answer_contract"]["source_types"] == ["legislation"]
    assert all("Yargıtay" not in citation for citation in payload["citations"])


def test_unsupported_exact_judicial_query_does_not_fallback_to_unrelated_lexical(tmp_path) -> None:
    runtime = _build_runtime(tmp_path, judicial_enabled=True)
    with _make_client(runtime) as client:
        payload = _post(client, "Yargıtay 9HD E. 1999/1 K. 1999/2 karar sonucu nedir?")

    assert payload["blocked"] is True
    assert payload["final_reason"] == "judicial_evidence_not_found"
    assert "karar dayanaklı yanıt vermiyorum" in payload["choices"][0]["message"]["content"] or "kanıt bulunamadı" in payload["choices"][0]["message"]["content"]
