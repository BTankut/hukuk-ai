from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

from data_pipeline.indexing import HashingEmbedder, MilvusVectorStore, TBKIngestPipeline
from data_pipeline.loaders import TBKMevzuatLoader
from data_pipeline.processing import LegalChunker


class MilvusRuntimeError(RuntimeError):
    """Milvus smoke path runtime hatası."""


@dataclass(slots=True)
class MilvusSmokeResult:
    milvus_uri: str
    collection: str
    collection_created: bool
    source_kind: str
    article_count: int
    chunk_count: int
    indexed_count: int
    count_after_upsert: int
    search_hit_count: int
    top_hit_id: str | None
    warnings: list[str]


def _import_pymilvus() -> tuple[Any, Any]:
    try:
        from pymilvus import DataType, MilvusClient
    except ModuleNotFoundError as exc:  # pragma: no cover - ortam bağımlı
        raise MilvusRuntimeError(
            "pymilvus kurulu değil. Önce `pip install -e '.[milvus]'` (veya eşdeğeri) çalıştırın."
        ) from exc
    return MilvusClient, DataType


def create_milvus_client(*, uri: str, token: str | None = None):
    MilvusClient, _ = _import_pymilvus()
    kwargs: dict[str, Any] = {"uri": uri}
    if token:
        kwargs["token"] = token
    return MilvusClient(**kwargs)


def ensure_tbk_collection(
    *,
    client: Any,
    collection: str,
    embedding_dim: int,
    drop_if_exists: bool = False,
    create_retries: int = 3,
    retry_backoff_seconds: float = 2.0,
) -> bool:
    """TBK pipeline payload'ı ile uyumlu collection'ı hazırlar.

    Dönen değer:
    - True: collection bu çağrıda oluşturuldu
    - False: collection zaten vardı
    """

    _, data_type = _import_pymilvus()

    exists = bool(client.has_collection(collection_name=collection))
    if exists and drop_if_exists:
        client.drop_collection(collection_name=collection)
        exists = False

    if exists:
        return False

    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field(field_name="id", datatype=data_type.VARCHAR, is_primary=True, max_length=128)
    schema.add_field(field_name="text", datatype=data_type.VARCHAR, max_length=8192)
    schema.add_field(field_name="embedding", datatype=data_type.FLOAT_VECTOR, dim=embedding_dim)
    schema.add_field(field_name="metadata", datatype=data_type.JSON)

    index_params = client.prepare_index_params()
    index_params.add_index(field_name="embedding", metric_type="COSINE", index_type="AUTOINDEX")

    last_error: Exception | None = None
    for attempt in range(1, create_retries + 1):
        try:
            client.create_collection(collection_name=collection, schema=schema, index_params=index_params)
            return True
        except Exception as exc:  # pragma: no cover - gerçek Milvus runtime davranışı
            last_error = exc
            if attempt >= create_retries:
                break
            time.sleep(retry_backoff_seconds * attempt)

    raise MilvusRuntimeError(
        f"Milvus collection oluşturulamadı ({collection}) after {create_retries} deneme: {last_error}"
    )


def _extract_top_hit_id(search_result: Any) -> str | None:
    """Milvus search response format'larını toleranslı şekilde parse eder."""

    if not search_result:
        return None

    first_batch = search_result[0] if isinstance(search_result, list) else None
    if not first_batch:
        return None

    top_hit = first_batch[0]
    if isinstance(top_hit, dict):
        if "id" in top_hit:
            return str(top_hit["id"])

        entity = top_hit.get("entity")
        if isinstance(entity, dict) and "id" in entity:
            return str(entity["id"])

    return None


def run_tbk_milvus_smoke(
    *,
    milvus_uri: str,
    milvus_token: str | None,
    collection: str,
    embedding_dim: int,
    prefer_online: bool,
    fixture_path: Path | None,
    query: str,
    recreate_collection: bool,
    drop_collection_after: bool,
) -> MilvusSmokeResult:
    client = create_milvus_client(uri=milvus_uri, token=milvus_token)
    collection_created = ensure_tbk_collection(
        client=client,
        collection=collection,
        embedding_dim=embedding_dim,
        drop_if_exists=recreate_collection,
    )

    embedder = HashingEmbedder(dimension=embedding_dim)
    pipeline = TBKIngestPipeline(
        loader=TBKMevzuatLoader(),
        chunker=LegalChunker(),
        embedder=embedder,
        vector_store=MilvusVectorStore(client=client),
        collection_name=collection,
    )

    summary, _ = pipeline.run(prefer_online=prefer_online, fixture_path=fixture_path)

    if hasattr(client, "flush"):
        client.flush(collection_name=collection)

    count_after_upsert = MilvusVectorStore(client=client).count(collection=collection)

    if hasattr(client, "load_collection"):
        client.load_collection(collection_name=collection)

    query_vector = embedder.embed_texts([query])[0]
    search_result = client.search(
        collection_name=collection,
        data=[query_vector],
        limit=3,
        output_fields=["id", "text"],
    )
    top_hit_id = _extract_top_hit_id(search_result)

    if drop_collection_after:
        client.drop_collection(collection_name=collection)

    return MilvusSmokeResult(
        milvus_uri=milvus_uri,
        collection=collection,
        collection_created=collection_created,
        source_kind=summary.source_kind,
        article_count=summary.article_count,
        chunk_count=summary.chunk_count,
        indexed_count=summary.indexed_count,
        count_after_upsert=count_after_upsert,
        search_hit_count=len(search_result[0]) if search_result and search_result[0] else 0,
        top_hit_id=top_hit_id,
        warnings=summary.warnings,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TBK -> Milvus canlı bağlantı smoke testi")
    parser.add_argument("--milvus-uri", default="http://localhost:19530", help="Milvus URI")
    parser.add_argument("--milvus-token", default=None, help="Milvus token (opsiyonel)")
    parser.add_argument("--collection", default="mevzuat_tbk_smoke", help="Smoke collection adı")
    parser.add_argument("--embedding-dim", type=int, default=16, help="Hashing embedder vektör boyutu")
    parser.add_argument("--query", default="haksız fiil tazminatı", help="Smoke search sorgusu")
    parser.add_argument("--fixture", type=Path, default=None, help="Offline fixture dosya yolu")
    parser.add_argument("--online", action="store_true", help="Önce online TBK kaynağını dene")
    parser.add_argument("--recreate-collection", action="store_true", help="Collection varsa drop edip yeniden oluştur")
    parser.add_argument("--drop-after", action="store_true", help="Smoke sonrası collection'ı sil")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    result = run_tbk_milvus_smoke(
        milvus_uri=args.milvus_uri,
        milvus_token=args.milvus_token,
        collection=args.collection,
        embedding_dim=args.embedding_dim,
        prefer_online=args.online,
        fixture_path=args.fixture,
        query=args.query,
        recreate_collection=args.recreate_collection,
        drop_collection_after=args.drop_after,
    )

    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
