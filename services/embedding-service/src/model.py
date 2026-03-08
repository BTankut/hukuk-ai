import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Orijinal plandaki model: intfloat/multilingual-e5-large-instruct
MODEL_NAME = "intfloat/multilingual-e5-large-instruct"
# M4 Max üzerinde "mps" veya "cpu" kullanılabilir. mps daha hızlıdır.
DEVICE = "mps" 

class EmbeddingModel:
    def __init__(self):
        logger.info(f"Loading model {MODEL_NAME} on {DEVICE}...")
        self.model = SentenceTransformer(MODEL_NAME, device=DEVICE)
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
