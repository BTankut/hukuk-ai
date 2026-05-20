from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import main
from data_pipeline.judicial import (
    build_judicial_chunks_stream,
    build_judicial_exact_lookup_index,
    build_judicial_lexical_index,
    build_judicial_manifest_record,
)
from rag.legal_rag_orchestrator import LegalRagOrchestrator, LegalRuntimeConfig
from rag.retriever import RetrievalResult, RetrievalStats


PROCESSED_REAL = Path("/Users/btmacstudio/Projects/yargi/_work/final_package/processed")
JUDICIAL_TEXT = """T. C. Yargıtay 9. Hukuk Dairesi

Davacı işçilik alacağı ve fazla mesai ücreti istemiştir.

Yargıtay, TBK m.49 bakımından tazminat koşullarını ve işçilik alacağı ispatını değerlendirmiştir.

Sonuç olarak hükmün bozulmasına karar verilmiştir."""


class FakeMevzuatRetriever:
    def retrieve(self, *, query: str, top_k: int, metadata_filter: Any | None = None):
        result = RetrievalResult(
            chunk_id="tbk-49",
            text="TBK m.49 haksız fiil sorumluluğunda kusur, zarar ve uygun illiyet bağı koşullarını düzenler.",
            score=0.91,
            metadata={
                "source_type": "legislation",
                "law_short_name": "TBK",
                "law_no": "6098",
                "madde_no": "49",
                "source_title": "Türk Borçlar Kanunu",
                "source_url": "https://mevzuat.gov.tr/tbk-49",
                "current_law_state": "current",
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


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_passing_coverage_audit(processed: Path) -> None:
    (processed / "judicial_processed_coverage_audit.json").write_text(
        json.dumps({"pass": True, "failures": []}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _build_synthetic_runtime(tmp_path: Path, *, judicial_enabled: bool) -> LegalRagOrchestrator:
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
    build_judicial_exact_lookup_index(manifest_path, processed, chunks_path=processed / "judicial_chunks.jsonl")
    build_judicial_lexical_index(processed / "judicial_chunks.jsonl", processed)
    _write_passing_coverage_audit(processed)
    return LegalRagOrchestrator(
        config=LegalRuntimeConfig(
            judicial_runtime_enabled=judicial_enabled,
            processed_dir=processed,
            exact_lookup_path=processed / "judicial_exact_lookup.sqlite",
            lexical_index_path=processed / "judicial_lexical_index.sqlite",
            legal_advisor_llm_enabled=False,
        ),
        mevzuat_retriever=FakeMevzuatRetriever(),
    )


@pytest.fixture()
def app_state_restore():
    original_runtime = getattr(main.app.state, "legal_rag_orchestrator", None)
    original_retriever = getattr(main.app.state, "retriever", None)
    yield
    main.app.state.legal_rag_orchestrator = original_runtime
    main.app.state.retriever = original_retriever


def _install_runtime(runtime: LegalRagOrchestrator) -> None:
    main.app.state.legal_rag_orchestrator = runtime
    main.app.state.retriever = runtime.mevzuat_retriever


def _post(client: TestClient, content: str, *, stream: bool = False) -> dict[str, Any]:
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": content}], "include_trace": True, "stream": stream},
    )
    assert response.status_code == 200
    return response.json()


def _stream_post(client: TestClient, content: str) -> tuple[str, dict[str, Any]]:
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": content}], "include_trace": True, "stream": True},
    ) as response:
        assert response.status_code == 200
        answer_parts: list[str] = []
        metadata: dict[str, Any] = {}
        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            payload = line.removeprefix("data: ")
            if payload == "[DONE]":
                break
            item = json.loads(payload)
            if item.get("object") == "chat.completion.metadata":
                metadata = item
                continue
            answer_parts.append(item["choices"][0]["delta"].get("content", ""))
        return "".join(answer_parts), metadata


def _assert_turkish_answer(text: str) -> None:
    assert any(token in text for token in ("Kaynaklar", "Mevzuat", "Yargı", "Somut", "Sınırlar"))


def test_actual_app_disabled_mode_health_legislation_and_judicial_refusal(tmp_path, app_state_restore) -> None:
    runtime = _build_synthetic_runtime(tmp_path, judicial_enabled=False)
    _install_runtime(runtime)

    with TestClient(main.app) as client:
        health = client.get("/v1/health").json()
        assert health["judicial_runtime_enabled"] == "disabled"
        assert health["judicial_ready"] == "false"
        assert health["judicial_readiness_status"] == "disabled"
        assert health["exact_lookup_available"] == "true"
        assert health["lexical_index_available"] == "true"
        assert health["verifier_enabled"] == "true"
        assert health["processed_corpus_dir_configured"] == "true"
        assert health["retrieval_timeout_ms"]

        legislation = _post(client, "TBK m.49 haksız fiil şartları nelerdir?")
        assert legislation["blocked"] is False
        _assert_turkish_answer(legislation["choices"][0]["message"]["content"])
        assert {card["source_type"] for card in legislation["source_cards"]} == {"legislation"}
        assert legislation["verification"]["pass"] is True

        judicial = _post(client, "Yargıtay 9HD E. 2024/12345 K. 2024/6789 kararını açıkla")
        assert judicial["blocked"] is True
        assert judicial["final_reason"] == "judicial_runtime_disabled"
        assert judicial["source_cards"] == []


def test_actual_app_missing_enabled_index_fails_readiness_and_refuses(tmp_path, app_state_restore) -> None:
    missing = tmp_path / "missing"
    runtime = LegalRagOrchestrator(
        config=LegalRuntimeConfig(
            judicial_runtime_enabled=True,
            processed_dir=missing,
            exact_lookup_path=missing / "judicial_exact_lookup.sqlite",
            lexical_index_path=missing / "judicial_lexical_index.sqlite",
            legal_advisor_llm_enabled=False,
        ),
        mevzuat_retriever=FakeMevzuatRetriever(),
    )
    _install_runtime(runtime)

    with TestClient(main.app) as client:
        health = client.get("/v1/health").json()
        assert health["judicial_runtime_enabled"] == "enabled"
        assert health["judicial_ready"] == "false"
        assert health["judicial_readiness_status"] == "failed"
        assert "processed_corpus_dir_missing" in health["judicial_readiness_failures"]

        payload = _post(client, "Yargıtay içtihadı nedir?")
        assert payload["blocked"] is True
        assert payload["final_reason"] == "judicial_indexes_unavailable"
        assert payload["answer_contract"]["runtime_health"]["judicial_readiness_status"] == "failed"


def _readonly_conn(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA query_only=ON")
    return conn


def _select_real_decision(processed: Path) -> dict[str, Any]:
    with _readonly_conn(processed / "judicial_exact_lookup.sqlite") as conn:
        row = conn.execute(
            "SELECT canonical_decision_id, court, chamber, decision_date, esas_no, karar_no "
            "FROM decisions "
            "WHERE court = 'Yargıtay' AND chamber LIKE '%HD' AND esas_no != '' AND karar_no != '' "
            "LIMIT 1"
        ).fetchone()
        if row is None:
            row = conn.execute(
                "SELECT canonical_decision_id, court, chamber, decision_date, esas_no, karar_no "
                "FROM decisions WHERE esas_no != '' AND karar_no != '' LIMIT 1"
            ).fetchone()
    assert row is not None
    return dict(row)


def _select_real_lexical_term(processed: Path, canonical_decision_id: str) -> str:
    with _readonly_conn(processed / "judicial_lexical_index.sqlite") as conn:
        row = conn.execute(
            "SELECT text FROM chunks WHERE canonical_decision_id = ? AND paragraph_start >= 1 "
            "ORDER BY length(text) DESC LIMIT 1",
            (canonical_decision_id,),
        ).fetchone()
    assert row is not None
    stopwords = {
        "mahkeme",
        "mahkemesi",
        "asliye",
        "ticaret",
        "karar",
        "davaci",
        "davali",
        "sonuc",
        "olarak",
        "istanbul",
        "ankara",
        "izmir",
        "esas",
        "gerekceli",
    }
    tokens = [
        token
        for token in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]{5,}", str(row["text"]))
        if unicodedata.normalize("NFKD", token.lower()).encode("ascii", "ignore").decode("ascii") not in stopwords
    ]
    return tokens[0].lower() if tokens else "tazminat"


def test_actual_app_real_index_enabled_exact_lexical_mixed_streaming_smoke(app_state_restore) -> None:
    required = [
        PROCESSED_REAL / "judicial_exact_lookup.sqlite",
        PROCESSED_REAL / "judicial_lexical_index.sqlite",
        PROCESSED_REAL / "judicial_processed_coverage_audit.json",
    ]
    if not all(path.exists() for path in required):
        pytest.skip("real judicial processed indexes are not available")

    decision = _select_real_decision(PROCESSED_REAL)
    lexical_term = _select_real_lexical_term(PROCESSED_REAL, str(decision["canonical_decision_id"]))
    runtime = LegalRagOrchestrator(
        config=LegalRuntimeConfig(
            judicial_runtime_enabled=True,
            processed_dir=PROCESSED_REAL,
            exact_lookup_path=PROCESSED_REAL / "judicial_exact_lookup.sqlite",
            lexical_index_path=PROCESSED_REAL / "judicial_lexical_index.sqlite",
            legal_advisor_llm_enabled=False,
        ),
        mevzuat_retriever=FakeMevzuatRetriever(),
    )
    _install_runtime(runtime)

    court = str(decision["court"]).replace("\n", " ")
    chamber = str(decision["chamber"])
    exact_query = f"{court} {chamber} E. {decision['esas_no']} K. {decision['karar_no']} kararını açıkla"
    lexical_query = f"{court} {lexical_term} hakkında mahkeme kararı var mı?"
    mixed_query = f"{court} {lexical_term} için TBK m.49 kapsamında mahkeme kararı nedir?"

    with TestClient(main.app) as client:
        health = client.get("/v1/health").json()
        assert health["judicial_runtime_enabled"] == "enabled"
        assert health["judicial_ready"] == "true"
        assert health["exact_lookup_available"] == "true"
        assert health["lexical_index_available"] == "true"
        assert health["verifier_enabled"] == "true"

        exact = _post(client, exact_query)
        assert exact["blocked"] is False
        _assert_turkish_answer(exact["choices"][0]["message"]["content"])
        assert any(card["source_type"] == "judicial_decision" for card in exact["source_cards"])
        assert exact["verification"]["pass"] is True

        lexical = _post(client, lexical_query)
        assert lexical["blocked"] is False
        assert any(card["source_type"] == "judicial_decision" for card in lexical["source_cards"])
        assert lexical["verification"]["pass"] is True

        mixed = _post(client, mixed_query)
        assert mixed["blocked"] is False
        assert {card["source_type"] for card in mixed["source_cards"]} == {"legislation", "judicial_decision"}
        assert mixed["verification"]["source_type_confusion"] is False

        streamed_answer, metadata = _stream_post(client, mixed_query)
        assert streamed_answer == mixed["choices"][0]["message"]["content"]
        assert metadata["answer_contract"]["source_cards"] == mixed["source_cards"]
        assert metadata["verification"]["pass"] is True

        unsupported = _post(client, "Yargıtay 9HD E. 1900/1 K. 1900/2 karar sonucu nedir?")
        assert unsupported["blocked"] is True
        assert unsupported["final_reason"] == "judicial_evidence_not_found"

        ambiguous = _post(client, "Tazminat olur mu?")
        assert ambiguous["blocked"] is False
        _assert_turkish_answer(ambiguous["choices"][0]["message"]["content"])
        assert ambiguous["verification"]["pass"] is True
