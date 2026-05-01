from __future__ import annotations

from typing import Any

from rag.orchestrator import RetrievedChunk
from rag.retrieval_orchestration import _retrieve_relation_chain_chunks


class _FakeMilvusClient:
    def __init__(self) -> None:
        self.filters: list[str] = []

    def query(
        self,
        *,
        collection_name: str,
        filter: str,
        output_fields: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        del collection_name, output_fields
        self.filters.append(filter)
        if 'metadata["relation_metadata"]["repeal_source_id"] == "yok_disc_2023_repeal"' in filter:
            return [
                {
                    "id": "current-2547-54",
                    "text": "Yükseköğretim kurumlarında disiplin işlemlerine ilişkin esaslar 2547 sayılı Kanun m.54 kapsamındadır.",
                    "metadata": {
                        "source_identifier": "2547",
                        "law_no": "2547",
                        "law_short_name": "2547",
                        "madde_no": "54",
                        "fikra_no": "0",
                        "belge_turu": "kanun",
                        "source_family": "kanun",
                        "effective_state": "active",
                        "bridge_role": "current_law_basis",
                        "relation_metadata": {
                            "relation_type": "current_law_basis_for_repealed_discipline_regulation",
                            "historical_source_id": "yok_disc_2012_regulation",
                            "repeal_source_id": "yok_disc_2023_repeal",
                        },
                    },
                }
            ][:limit]
        if 'metadata["relation_metadata"]["repealed_source_id"] == "yok_disc_2012_regulation"' in filter:
            return [
                {
                    "id": "repeal-rg20230311-4-m1",
                    "text": "Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği yürürlükten kaldırılmıştır.",
                    "metadata": {
                        "source_identifier": "rg20230311-4",
                        "madde_no": "1",
                        "fikra_no": "0",
                        "belge_turu": "yonetmelik",
                        "source_family": "yonetmelik_repeal",
                        "effective_state": "repeal_instrument",
                        "bridge_role": "repeal_instrument",
                        "relation_metadata": {
                            "relation_type": "repeals_historical_regulation",
                            "repealed_source_id": "yok_disc_2012_regulation",
                        },
                    },
                }
            ][:limit]
        return []


class _StrictNoQueryClient:
    def query(self, **_: Any) -> list[dict[str, Any]]:
        raise AssertionError("relation-chain lookup must not run without relation metadata")


class _FakeRetriever:
    def __init__(self, client: Any) -> None:
        self.client = client
        self.collection = "shadow_relation_chain_test"


def _historical_anchor() -> RetrievedChunk:
    return RetrievedChunk(
        text="2012 tarihli YÖK disiplin yönetmeliği m.22 disiplin cezasına ilişkin eski hükmü içerir.",
        citation="YOK_DISIPLIN_2012 m.22",
        source="YOK_DISIPLIN_2012",
        score=0.72,
        metadata={
            "source_identifier": "16532",
            "madde_no": "22",
            "fikra_no": "0",
            "belge_turu": "yonetmelik",
            "source_family": "yonetmelik",
            "effective_state": "historical_repealed",
            "bridge_role": "historical_repealed_source",
            "relation_metadata": {
                "relation_type": "historical_repealed_to_current_bridge",
                "repealed_by_source_id": "yok_disc_2023_repeal",
                "current_law_basis_source_id": "law_2547_current",
            },
        },
    )


def test_historical_repealed_source_adds_repeal_and_current_basis_spans() -> None:
    client = _FakeMilvusClient()
    retriever = _FakeRetriever(client)
    anchor = _historical_anchor()

    added, policy = _retrieve_relation_chain_chunks(
        retriever=retriever,
        query="Eski YÖK öğrenci disiplin yönetmeliğine bugün hâlâ dayanılabilir mi?",
        chunks=[anchor],
    )

    identifiers = {str((chunk.metadata or {}).get("source_identifier")) for chunk in added}
    assert {"rg20230311-4", "2547"} <= identifiers
    assert policy["relation_chain_expansion_applied"] is True
    assert policy["repeal_instrument_added"] is True
    assert policy["current_law_basis_added"] is True
    assert anchor.metadata["relation_chain_role"] == "historical_rule"
    assert anchor.metadata["relation_chain_source_key"] == "16532"


def test_relation_chain_does_not_mark_repealed_source_active() -> None:
    anchor = _historical_anchor()

    _added, policy = _retrieve_relation_chain_chunks(
        retriever=_FakeRetriever(_FakeMilvusClient()),
        query="Bu eski yönetmelik bugün uygulanır mı?",
        chunks=[anchor],
    )

    assert anchor.metadata["effective_state"] == "historical_repealed"
    assert anchor.metadata["historical_source_effective_state"] == "historical_repealed"
    assert policy["historical_source_not_marked_active"] is True
    assert policy["repealed_as_active_count"] == 0


def test_relation_chain_requires_metadata_not_qid() -> None:
    ordinary_chunk = RetrievedChunk(
        text="Sıradan bir kanun maddesi.",
        citation="TEST m.1",
        source="TEST",
        score=0.5,
        metadata={"source_identifier": "TEST", "effective_state": "active"},
    )

    added, policy = _retrieve_relation_chain_chunks(
        retriever=_FakeRetriever(_StrictNoQueryClient()),
        query="MULGA-01 için cevap ver",
        chunks=[ordinary_chunk],
    )

    assert added == []
    assert policy["relation_chain_expansion_applied"] is False
    assert policy["relation_chain_missing_reason"] == "no_relation_metadata_anchor"


def test_relation_chain_preserves_teblig_and_yonetmelik_guard_rows() -> None:
    teblig_chunk = RetrievedChunk(
        text="Tebliğ hükmü.",
        citation="TEB m.1",
        source="TEB",
        score=0.6,
        metadata={"source_identifier": "TEB", "belge_turu": "teblig", "effective_state": "active"},
    )
    yonetmelik_chunk = RetrievedChunk(
        text="Yönetmelik hükmü.",
        citation="YON m.2",
        source="YON",
        score=0.5,
        metadata={"source_identifier": "YON", "belge_turu": "yonetmelik", "effective_state": "active"},
    )
    chunks = [teblig_chunk, yonetmelik_chunk]

    added, policy = _retrieve_relation_chain_chunks(
        retriever=_FakeRetriever(_StrictNoQueryClient()),
        query="Tebliğ ve yönetmelik ilişkisini açıkla",
        chunks=chunks,
    )

    assert added == []
    assert chunks == [teblig_chunk, yonetmelik_chunk]
    assert "relation_chain_role" not in teblig_chunk.metadata
    assert "relation_chain_role" not in yonetmelik_chunk.metadata
    assert policy["relation_chain_expansion_applied"] is False
