from __future__ import annotations

from datetime import datetime
from pathlib import Path

from data_pipeline.indexing import HashingEmbedder, InMemoryVectorStore, MilvusVectorStore, TBKIngestPipeline
from data_pipeline.indexing.interfaces import VectorRecord
from data_pipeline.loaders import TBKMevzuatLoader
from data_pipeline.models import LawArticle, LawDocument
from data_pipeline.processing import LegalChunker, LegalMetadataExtractor


def _fixture_path() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "data_pipeline" / "fixtures" / "tbk_fixture.txt"


def test_tbk_loader_fixture_fallback_builds_articles():
    loader = TBKMevzuatLoader()

    result = loader.load(prefer_online=False, fixture_path=_fixture_path())

    assert result.source_kind == "fixture"
    assert result.document.law_no == "6098"
    assert len(result.document.articles) >= 3
    assert any(article.madde_no == "49" for article in result.document.articles)


def test_tbk_loader_online_iframe_path_parses_articles(monkeypatch):
    loader = TBKMevzuatLoader()

    shell_html = """
    <html>
      <body>
        <iframe id=\"mevzuatDetayIframe\" src=\"/anasayfa/MevzuatFihristDetayIframe?MevzuatNo=6098\"></iframe>
      </body>
    </html>
    """
    iframe_html = """
    <html>
      <body>
        <p><b>TÜRK BORÇLAR KANUNU</b></p>
        <p>Kanun Numarası : 6098</p>
        <p><b>MADDE 49-</b> Kusurlu ve hukuka aykırı bir fiille başkasına zarar veren, bu zararı gidermekle yükümlüdür.</p>
      </body>
    </html>
    """

    def fake_get_with_retries(*, client, url: str, label: str):
        if "mevzuat?" in url:
            return shell_html, "https://mevzuat.gov.tr/mevzuat?MevzuatNo=6098"
        if "MevzuatFihristDetayIframe" in url:
            return iframe_html, "https://mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatNo=6098"
        raise AssertionError(f"Beklenmeyen URL: {url}")

    monkeypatch.setattr(loader, "_get_with_retries", fake_get_with_retries)

    result = loader.load(prefer_online=True, fixture_path=_fixture_path())

    assert result.source_kind == "online"
    assert result.document.law_no == "6098"
    assert result.document.law_name == "Türk Borçlar Kanunu"
    assert any(article.madde_no == "49" for article in result.document.articles)
    assert any("iframe" in warning.lower() for warning in result.warnings)


def test_chunker_produces_madde_fikra_metadata_and_id_format():
    loader = TBKMevzuatLoader()
    chunker = LegalChunker(max_words=40, overlap_words=10)
    result = loader.load(prefer_online=False, fixture_path=_fixture_path())

    chunks = chunker.chunk_document(result.document)

    assert chunks
    sample = chunks[0]
    assert sample.chunk_id.startswith("TBK_m")
    assert "_f" in sample.chunk_id
    assert sample.metadata["law_no"] == "6098"
    assert sample.metadata["law_short_name"] == "TBK"
    assert sample.metadata["kanun_no"] == "6098"
    assert sample.metadata["kanun_kisa_adi"] == "TBK"
    assert sample.metadata["source_id"].startswith("TBK m.")
    assert sample.metadata["chunk_id"] == sample.chunk_id
    assert sample.metadata["yururluk_baslangic"] is None
    assert sample.metadata["yururluk_bitis"] is None
    assert sample.metadata["mulga"] is None
    assert sample.metadata["hukuk_dali"] == "borclar_hukuku"

    parsed = LegalMetadataExtractor.parse_madde_no_from_text("TBK Madde 72 zamanaşımı")
    assert parsed == "72"


def test_chunker_keeps_source_id_stable_across_split_parts():
    document = LawDocument(
        law_no="6098",
        law_short_name="TBK",
        law_name="Türk Borçlar Kanunu",
        source_url=None,
        fetched_at=datetime(2026, 3, 22, 12, 0, 0),
        raw_text="",
        articles=[
            LawArticle(
                madde_no="49",
                heading="Haksız fiil",
                body="(1) " + " ".join(["kelime"] * 120) + " (2) " + " ".join(["ikinci"] * 120),
            )
        ],
    )
    chunker = LegalChunker(max_words=30, overlap_words=5)

    chunks = chunker.chunk_document(document)

    assert len(chunks) > 1
    assert len({chunk.metadata["source_id"] for chunk in chunks}) == 1
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
    assert all(chunk.metadata["chunk_id"] == chunk.chunk_id for chunk in chunks)
    assert all(chunk.metadata["yururluk_baslangic"] is None for chunk in chunks)
    assert all(chunk.metadata["yururluk_bitis"] is None for chunk in chunks)
    assert all(chunk.metadata["mulga"] is None for chunk in chunks)


def test_tbk_ingest_pipeline_smoke_chunk_count_matches_index_count():
    pipeline = TBKIngestPipeline(
        loader=TBKMevzuatLoader(),
        chunker=LegalChunker(),
        embedder=HashingEmbedder(dimension=24),
        vector_store=InMemoryVectorStore(),
    )

    summary, chunks = pipeline.run(prefer_online=False, fixture_path=_fixture_path())

    assert summary.source_kind == "fixture"
    assert summary.chunk_count == summary.indexed_count
    assert summary.chunk_count == len(chunks)
    assert summary.chunk_count >= 6
    assert any("offline fixture" in warning.lower() for warning in summary.warnings)


class _FakeMilvusClient:
    def __init__(self) -> None:
        self.last_collection = None
        self.last_data = None

    def upsert(self, *, collection_name: str, data: list[dict]) -> None:
        self.last_collection = collection_name
        self.last_data = data

    def count(self, *, collection_name: str) -> int:
        assert collection_name == self.last_collection
        return len(self.last_data or [])


def test_milvus_store_interface_contract_with_fake_client():
    client = _FakeMilvusClient()
    store = MilvusVectorStore(client=client)

    records = [
        VectorRecord(
            id="TBK_m49_f1",
            text="örnek",
            embedding=[0.1, 0.2],
            metadata={
                "source_id": "TBK m.49",
                "law_no": "6098",
                "law_short_name": "TBK",
                "kanun_no": "6098",
                "kanun_kisa_adi": "TBK",
                "madde_no": "49",
                "fikra_no": "1",
                "yururluk_baslangic": None,
                "yururluk_bitis": None,
                "mulga": None,
            },
        )
    ]

    inserted = store.upsert(collection="mevzuat", records=records)

    assert inserted == 1
    assert client.last_collection == "mevzuat"
    assert client.last_data[0]["id"] == "TBK_m49_f1"
    assert client.last_data[0]["metadata"]["source_id"] == "TBK m.49"
    assert store.count(collection="mevzuat") == 1
