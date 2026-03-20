import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Orijinal plandaki model: intfloat/multilingual-e5-large-instruct
MODEL_NAME = "intfloat/multilingual-e5-large-instruct"
PREFERRED_DEVICE = "mps"
_MODEL_CACHE_DIRNAME = "models--intfloat--multilingual-e5-large-instruct"


def _env_flag(name: str) -> bool | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _hf_cache_root() -> Path:
    return Path(
        os.getenv("HF_HUB_CACHE")
        or os.getenv("HUGGINGFACE_HUB_CACHE")
        or (Path.home() / ".cache" / "huggingface" / "hub")
    )


def _model_cache_exists() -> bool:
    return (_hf_cache_root() / _MODEL_CACHE_DIRNAME).exists()


def _resolve_local_files_only() -> bool:
    explicit = _env_flag("HF_LOCAL_FILES_ONLY")
    if explicit is not None:
        return explicit
    return _model_cache_exists()


def _torch_supports_mps() -> bool:
    try:
        import torch
    except Exception:
        return False
    return bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())


def _resolve_device() -> str:
    explicit = os.getenv("EMBEDDING_DEVICE")
    if explicit:
        return explicit.strip().lower()
    return PREFERRED_DEVICE if _torch_supports_mps() else "cpu"


if _resolve_local_files_only():
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    def __init__(self):
        local_files_only = _resolve_local_files_only()
        device = _resolve_device()
        logger.info(
            "Loading model %s on %s (local_files_only=%s)...",
            MODEL_NAME,
            device,
            local_files_only,
        )
        self.model = SentenceTransformer(
            MODEL_NAME,
            device=device,
            local_files_only=local_files_only,
        )
        self.device = device
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Dimension: {self.dimension}")

    def embed(self, texts: list[str], instruction: str = "") -> list[list[float]]:
        # e5 modelleri sorgular için "Instruct: {instruction}\nQuery: {text}" formatını kullanabilir
        # Ancak basit kullanımda metinlerin doğrudan verilmesi de yaygındır.
        # Bu API'de instruction prefix'i destekleyeceğiz.
        formatted_texts = []
        for t in texts:
            if instruction:
                formatted_texts.append(f"Instruct: {instruction}\nQuery: {t}")
            else:
                formatted_texts.append(t)

        # normalize_embeddings=True (e5 modelleri genellikle cosine similarity için normalize edilmelidir)
        embeddings = self.model.encode(formatted_texts, normalize_embeddings=True)
        return embeddings.tolist()
