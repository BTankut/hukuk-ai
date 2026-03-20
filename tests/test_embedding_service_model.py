from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module():
    fake_sentence_transformers = types.ModuleType("sentence_transformers")
    fake_sentence_transformers.SentenceTransformer = object
    sys.modules["sentence_transformers"] = fake_sentence_transformers
    module_path = Path("services/embedding-service/src/model.py").resolve()
    spec = importlib.util.spec_from_file_location("embedding_service_model", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_resolve_local_files_only_uses_explicit_env(monkeypatch):
    module = _load_module()
    monkeypatch.setenv("HF_LOCAL_FILES_ONLY", "true")
    assert module._resolve_local_files_only() is True


def test_resolve_local_files_only_uses_cache_presence(monkeypatch, tmp_path: Path):
    module = _load_module()
    monkeypatch.delenv("HF_LOCAL_FILES_ONLY", raising=False)
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path))
    (tmp_path / "models--intfloat--multilingual-e5-large-instruct").mkdir()
    assert module._resolve_local_files_only() is True


def test_resolve_local_files_only_false_without_env_or_cache(monkeypatch, tmp_path: Path):
    module = _load_module()
    monkeypatch.delenv("HF_LOCAL_FILES_ONLY", raising=False)
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path))
    assert module._resolve_local_files_only() is False


def test_resolve_device_prefers_cpu_when_mps_unavailable(monkeypatch):
    module = _load_module()
    monkeypatch.delenv("EMBEDDING_DEVICE", raising=False)
    monkeypatch.setattr(module, "_torch_supports_mps", lambda: False)
    assert module._resolve_device() == "cpu"


def test_resolve_device_uses_explicit_env(monkeypatch):
    module = _load_module()
    monkeypatch.setenv("EMBEDDING_DEVICE", "cpu")
    assert module._resolve_device() == "cpu"


def test_local_files_mode_sets_offline_env(monkeypatch):
    monkeypatch.setenv("HF_LOCAL_FILES_ONLY", "true")
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    monkeypatch.delenv("TRANSFORMERS_OFFLINE", raising=False)
    module = _load_module()
    monkeypatch.setenv("EMBEDDING_DEVICE", "cpu")

    class DummySentenceTransformer:
        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs

        def get_sentence_embedding_dimension(self):
            return 1024

    monkeypatch.setattr(module, "SentenceTransformer", DummySentenceTransformer)
    model = module.EmbeddingModel()
    assert model.dimension == 1024
    assert model.device == "cpu"
    assert module.os.environ["HF_HUB_OFFLINE"] == "1"
    assert module.os.environ["TRANSFORMERS_OFFLINE"] == "1"
