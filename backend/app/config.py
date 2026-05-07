from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

# .env lives at the project root (one level above backend/)
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # AWS Bedrock — RAG / Clinical pipeline
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    bedrock_model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-6", env="BEDROCK_MODEL_ID"
    )
    # AWS Bedrock — Vaidya Guide Bot (can be a different / newer model)
    vaidya_model_id: str = Field(
        default="us.anthropic.claude-3-7-sonnet-20250219-v1:0", env="VAIDYA_MODEL_ID"
    )
    bedrock_embedding_model_id: str = Field(
        default="amazon.titan-embed-text-v2:0", env="BEDROCK_EMBEDDING_MODEL_ID"
    )
    embedding_dim: int = Field(default=1024, env="EMBEDDING_DIM")

    # Bedrock Guardrails
    bedrock_guardrail_id: str = Field(default="", env="BEDROCK_GUARDRAIL_ID")
    bedrock_guardrail_version: str = Field(default="", env="BEDROCK_GUARDRAIL_VERSION")

    # DynamoDB
    dynamodb_table_prefix: str = Field(default="medgraph", env="DYNAMODB_TABLE_PREFIX")

    # OpenSearch Serverless (Vector DB)
    opensearch_endpoint: str = Field(env="OPENSEARCH_ENDPOINT")
    opensearch_index: str = Field(default="patient-memories", env="OPENSEARCH_INDEX")

    # S3 (Patient Documents — PDF storage, replaces GridFS)
    s3_documents_bucket: str = Field(
        default="medgraph-patient-documents-344759721711", env="S3_DOCUMENTS_BUCKET"
    )

    # Neo4j Aura
    neo4j_uri: str = Field(env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(env="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", env="NEO4J_DATABASE")

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
