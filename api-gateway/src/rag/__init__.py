from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORT_MODULES = {
    # orchestrator
    "RAGOrchestrator": "rag.orchestrator",
    "RetrievedChunk": "rag.orchestrator",
    "OrchestratorResponse": "rag.orchestrator",
    # retriever
    "MilvusRetriever": "rag.retriever",
    "MockRetriever": "rag.retriever",
    "MetadataFilter": "rag.retriever",
    "RetrievalResult": "rag.retriever",
    "RetrievalStats": "rag.retriever",
    # prompt builder
    "BuiltPrompt": "rag.prompt_builder",
    "PromptBuilder": "rag.prompt_builder",
    "get_prompt_builder": "rag.prompt_builder",
    # token manager
    "TokenBudget": "rag.token_manager",
    "TokenLimitManager": "rag.token_manager",
    "TokenLimitResult": "rag.token_manager",
    "estimate_tokens": "rag.token_manager",
    # verification engine (Backlog #6)
    "CitationSpan": "rag.verification_engine",
    "ClaimSpan": "rag.verification_engine",
    "GroundingResult": "rag.verification_engine",
    "VerificationEngine": "rag.verification_engine",
    "VerificationResult": "rag.verification_engine",
    "get_verification_engine": "rag.verification_engine",
    # embedding
    "EmbeddingService": "rag.embedding",
    "HashingEmbedder": "rag.embedding",
    "RemoteEmbeddingService": "rag.embedding",
    "SentenceTransformerEmbedder": "rag.embedding",
    "get_default_embedder": "rag.embedding",
}

__all__ = list(_EXPORT_MODULES)


def __getattr__(name: str) -> Any:
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module 'rag' has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
