from __future__ import annotations

from dataclasses import dataclass

import pytest

from data_pipeline.milvus_smoke import _extract_top_hit_id, ensure_tbk_collection


@dataclass
class _FakeDataType:
    VARCHAR: str = "VARCHAR"
    FLOAT_VECTOR: str = "FLOAT_VECTOR"
    JSON: str = "JSON"


class _FakeSchema:
    def __init__(self) -> None:
        self.fields: list[dict] = []

    def add_field(self, **kwargs) -> None:
        self.fields.append(kwargs)


class _FakeIndexParams:
    def __init__(self) -> None:
        self.indexes: list[dict] = []

    def add_index(self, **kwargs) -> None:
        self.indexes.append(kwargs)


class _FakeMilvusClient:
    def __init__(self, *, exists: bool = False) -> None:
        self.exists = exists
        self.dropped = False
        self.created = False
        self.schema = None
        self.index_params = None

    def has_collection(self, *, collection_name: str) -> bool:
        return self.exists

    def drop_collection(self, *, collection_name: str) -> None:
        self.dropped = True
        self.exists = False

    def create_schema(self, **kwargs):
        self.schema = _FakeSchema()
        return self.schema

    def prepare_index_params(self):
        self.index_params = _FakeIndexParams()
        return self.index_params

    def create_collection(self, *, collection_name: str, schema, index_params) -> None:
        self.created = True
        self.schema = schema
        self.index_params = index_params
        self.exists = True


@pytest.fixture
def patch_pymilvus_import(monkeypatch):
    monkeypatch.setattr(
        "data_pipeline.milvus_smoke._import_pymilvus",
        lambda: (object, _FakeDataType),
    )


def test_ensure_collection_creates_when_missing(patch_pymilvus_import):
    client = _FakeMilvusClient(exists=False)

    created = ensure_tbk_collection(client=client, collection="mevzuat_tbk_smoke", embedding_dim=16)

    assert created is True
    assert client.created is True
    assert client.schema is not None
    field_names = {field["field_name"] for field in client.schema.fields}
    assert field_names == {"id", "text", "embedding", "metadata"}


def test_ensure_collection_drops_and_recreates_when_requested(patch_pymilvus_import):
    client = _FakeMilvusClient(exists=True)

    created = ensure_tbk_collection(
        client=client,
        collection="mevzuat_tbk_smoke",
        embedding_dim=24,
        drop_if_exists=True,
    )

    assert created is True
    assert client.dropped is True
    assert client.created is True


def test_ensure_collection_skips_when_exists_and_no_drop(patch_pymilvus_import):
    client = _FakeMilvusClient(exists=True)

    created = ensure_tbk_collection(
        client=client,
        collection="mevzuat_tbk_smoke",
        embedding_dim=24,
        drop_if_exists=False,
    )

    assert created is False
    assert client.created is False


def test_extract_top_hit_id_tolerates_multiple_payload_shapes():
    assert _extract_top_hit_id([[{"id": "TBK_m72_f1"}]]) == "TBK_m72_f1"
    assert _extract_top_hit_id([[{"entity": {"id": "TBK_m49_f1"}}]]) == "TBK_m49_f1"
    assert _extract_top_hit_id([]) is None
    assert _extract_top_hit_id([[]]) is None
