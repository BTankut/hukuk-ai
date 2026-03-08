from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_pipeline.indexing import HashingEmbedder, InMemoryVectorStore, TBKIngestPipeline
from data_pipeline.loaders import TBKMevzuatLoader
from data_pipeline.processing import LegalChunker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TBK pilot scrape/chunk/index smoke zinciri")
    parser.add_argument("--fixture", type=Path, default=None, help="Offline fixture dosya yolu")
    parser.add_argument(
        "--online",
        action="store_true",
        help="Önce online mevzuat kaynağını dene (hata olursa fixture fallback).",
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=None,
        help="Chunk + metadata çıktısını JSONL olarak yaz.",
    )
    parser.add_argument("--embedding-dim", type=int, default=16, help="Smoke embedder vektör boyutu")
    return parser


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    args = build_parser().parse_args()

    pipeline = TBKIngestPipeline(
        loader=TBKMevzuatLoader(),
        chunker=LegalChunker(),
        embedder=HashingEmbedder(dimension=args.embedding_dim),
        vector_store=InMemoryVectorStore(),
    )

    summary, chunks = pipeline.run(prefer_online=args.online, fixture_path=args.fixture)

    if args.output_jsonl:
        rows = [{"chunk_id": chunk.chunk_id, "text": chunk.text, "metadata": chunk.metadata} for chunk in chunks]
        _write_jsonl(args.output_jsonl, rows)

    payload = {
        "source_kind": summary.source_kind,
        "law_no": summary.law_no,
        "article_count": summary.article_count,
        "chunk_count": summary.chunk_count,
        "indexed_count": summary.indexed_count,
        "warnings": summary.warnings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
