from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

# .env lives at the project root (one level above backend/)
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # Groq
    groq_api_key: str = Field(env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")

    # MongoDB
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_db: str = Field(default="medgraph", env="MONGODB_DB")

    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="medgraph123", env="NEO4J_PASSWORD")

    # Qdrant
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_collection: str = Field(default="patient_memories", env="QDRANT_COLLECTION")

    # Embedding
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL"
    )
    embedding_dim: int = Field(default=384, env="EMBEDDING_DIM")

    # JWT
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # App
    app_env: str = Field(default="development", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Hybrid search weights
    graph_weight: float = Field(default=0.5, env="GRAPH_WEIGHT")
    vector_weight: float = Field(default=0.3, env="VECTOR_WEIGHT")
    recency_weight: float = Field(default=0.2, env="RECENCY_WEIGHT")
    top_k: int = Field(default=10, env="TOP_K")

    model_config = {"env_file": str(_ENV_FILE), "case_sensitive": False, "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
