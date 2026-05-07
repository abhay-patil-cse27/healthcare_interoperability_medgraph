"""
AWS Bedrock Embedding Service
==============================
Replaces local sentence-transformers with Amazon Titan Text Embeddings v2.
Uses boto3 with the user's configured AWS CLI credentials.
"""
import json
import structlog
from functools import lru_cache
from typing import List
import boto3
from app.config import get_settings

logger = structlog.get_logger()


class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
        )
        self.model_id = settings.bedrock_embedding_model_id
        self.dim = settings.embedding_dim
        logger.info(
            "embedding_service_initialized",
            model=self.model_id,
            dim=self.dim,
        )

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "inputText": text,
                "dimensions": self.dim,
                "normalize": True,
            }),
        )
        result = json.loads(response["body"].read())
        return result["embedding"]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (sequential calls to Bedrock)."""
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
