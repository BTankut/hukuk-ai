from __future__ import annotations

import os
from pathlib import Path

import pytest

from data_pipeline.milvus_smoke import MilvusRuntimeError, run_tbk_milvus_smoke


@pytest.mark.integration
def test_milvus_live_smoke_runs_when_env_is_ready():
    milvus_uri = os.getenv("MILVUS_URI")
    if not milvus_uri:
        pytest.skip("MILVUS_URI tanımlı değil; canlı Milvus integration testi atlandı.")

    fixture_path = Path(__file__).resolve().parents[1] / "src" / "data_pipeline" / "fixtures" / "tbk_fixture.txt"

    try:
        result = run_tbk_milvus_smoke(
            milvus_uri=milvus_uri,
            milvus_token=os.getenv("MILVUS_TOKEN"),
            collection="mevzuat_tbk_smoke_it",
            embedding_dim=16,
            prefer_online=False,
            fixture_path=fixture_path,
            query="haksız fiil",
            recreate_collection=True,
            drop_collection_after=True,
        )
    except MilvusRuntimeError as exc:
        pytest.skip(f"Milvus runtime hazır değil: {exc}")

    assert result.indexed_count >= 1
    assert result.search_hit_count >= 1
    assert result.top_hit_id is not None
