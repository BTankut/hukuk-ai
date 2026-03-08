import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel, Field

from model import EmbeddingModel, MODEL_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Embedding Model...")
    ml_models["embedder"] = EmbeddingModel()
    yield
    # Shutdown
    ml_models.clear()

app = FastAPI(title="Hukuk AI Embedding Service", lifespan=lifespan)

class EmbedRequest(BaseModel):
    input: list[str] | str = Field(..., alias="input", description="Texts to embed")
    model: str | None = Field(default=MODEL_NAME)
    instruction: str = Field(default="")

class EmbedResponseItem(BaseModel):
    object: str = "embedding"
    embedding: list[float]
    index: int

class EmbedResponse(BaseModel):
    object: str = "list"
    data: list[EmbedResponseItem]
    model: str
    usage: dict[str, int] = {"prompt_tokens": 0, "total_tokens": 0}

@app.post("/v1/embeddings", response_model=EmbedResponse)
@app.post("/embed", response_model=EmbedResponse)
async def embed_endpoint(request: EmbedRequest):
    texts = [request.input] if isinstance(request.input, str) else request.input
    embedder = ml_models["embedder"]
    
    embeddings = embedder.embed(texts, instruction=request.instruction)
    
    data = [
        EmbedResponseItem(embedding=emb, index=i)
        for i, emb in enumerate(embeddings)
    ]
    
    return EmbedResponse(
        data=data,
        model=request.model or MODEL_NAME
    )

@app.get("/v1/models")
async def models_endpoint():
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": 1677610602,
                "owned_by": "hukuk-ai"
            }
        ]
    }

@app.get("/health")
async def health():
    embedder = ml_models.get("embedder")
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "dimension": getattr(embedder, "dimension", None)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=False)
