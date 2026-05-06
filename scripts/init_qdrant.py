"""
Run this once after Docker services are up to create Qdrant collection and indexes.
Usage: python scripts/init_qdrant.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PayloadSchemaType,
)
from app.config import get_settings


def init():
    settings = get_settings()
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    existing = [c.name for c in client.get_collections().collections]

    if settings.qdrant_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dim, distance=Distance.COSINE
            ),
        )
        print(f"✅ Collection '{settings.qdrant_collection}' created")
    else:
        print(f"ℹ️  Collection '{settings.qdrant_collection}' already exists")

    # Payload indexes for fast filtered search
    indexes = [
        ("patient_id", PayloadSchemaType.KEYWORD),
        ("has_medications", PayloadSchemaType.BOOL),
        ("has_conditions", PayloadSchemaType.BOOL),
        ("has_symptoms", PayloadSchemaType.BOOL),
        ("encounter_date", PayloadSchemaType.DATETIME),
    ]

    for field, schema_type in indexes:
        client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name=field,
            field_schema=schema_type,
        )
        print(f"✅ Payload index: {field} ({schema_type})")

    info = client.get_collection(settings.qdrant_collection)
    print(f"\n📊 Collection info: {info}")
    print("\n🎉 Qdrant initialization complete!")


if __name__ == "__main__":
    init()
