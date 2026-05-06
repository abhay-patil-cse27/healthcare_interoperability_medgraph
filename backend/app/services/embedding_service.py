from functools import lru_cache
from typing import List
from sentence_transformers import SentenceTransformer
import structlog
from app.config import get_settings

logger = structlog.get_logger()


class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        logger.info("loading_embedding_model", model=settings.embedding_model)
        self.model = SentenceTransformer(settings.embedding_model)
        logger.info("embedding_model_loaded")

    async def embed(self, text: str) -> List[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
