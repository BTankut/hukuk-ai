#!/usr/bin/env python3
import sys
from pathlib import Path

# Add api-gateway/src to python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api-gateway" / "src"))

import os
from dotenv import load_dotenv

# Load env
load_dotenv(PROJECT_ROOT / "api-gateway" / ".env")

from data_pipeline.indexing import TBKIngestPipeline, MilvusVectorStore
from data_pipeline.loaders import TBKMevzuatLoader
from data_pipeline.processing import LegalChunker
from rag.embedding import get_default_embedder

from pymilvus import MilvusClient, DataType

def ensure_collection(client, collection_name, dim):
    exists = client.has_collection(collection_name)
    if exists:
        print(f"Dropping existing collection: {collection_name}")
        client.drop_collection(collection_name)

    print(f"Creating collection {collection_name} with dim {dim}...")
    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=128)
    schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=8192)
    schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=dim)
    schema.add_field(field_name="metadata", datatype=DataType.JSON)

    index_params = client.prepare_index_params()
    index_params.add_index(field_name="embedding", metric_type="COSINE", index_type="AUTOINDEX")
    
    client.create_collection(collection_name=collection_name, schema=schema, index_params=index_params)
    print("Collection created.")

def main():
    embedder = get_default_embedder()
    dim = embedder.dimension
    print(f"Using embedder: {embedder.__class__.__name__}, dim: {dim}")

    milvus_uri = os.getenv("MILVUS_URI", "http://localhost:19530")
    collection_name = os.getenv("MILVUS_COLLECTION", "mevzuat")
    
    client = MilvusClient(uri=milvus_uri)
    ensure_collection(client, collection_name, dim)

    pipeline = TBKIngestPipeline(
        loader=TBKMevzuatLoader(),
        chunker=LegalChunker(),
        embedder=embedder,
        vector_store=MilvusVectorStore(client=client),
        collection_name=collection_name,
    )

    print("Starting ingestion pipeline...")
    # Öncelik: HTML cache (fixtures/tbk_detail.html) → online → metin fixture
    # --online argümanı verilmedikçe network'e çıkmaz; geçici /tmp bağımlılığı yok.
    use_online = "--online" in sys.argv
    html_cache = PROJECT_ROOT / "api-gateway" / "src" / "data_pipeline" / "fixtures" / "tbk_detail.html"
    summary, _ = pipeline.run(prefer_online=use_online, html_cache_path=html_cache if html_cache.exists() else None)
    
    print("Ingestion Summary:")
    print(f"  Article Count: {summary.article_count}")
    print(f"  Chunk Count: {summary.chunk_count}")
    print(f"  Indexed Count: {summary.indexed_count}")
    
    client.flush(collection_name)
    count = MilvusVectorStore(client=client).count(collection=collection_name)
    print(f"Milvus verified count: {count}")

if __name__ == "__main__":
    main()
