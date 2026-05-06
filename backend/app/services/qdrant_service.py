import structlog
from typing import List, Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    Range,
)
from app.config import get_settings

logger = structlog.get_logger()


class QdrantService:
    def __init__(self):
        settings = get_settings()
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection = settings.qdrant_collection
        self.dim = settings.embedding_dim
        self._ensure_collection()

    def _ensure_collection(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
            )
            logger.info("qdrant_collection_created", collection=self.collection)

    async def index(
        self,
        patient_id: str,
        entry_id: str,
        text: str,
        embedding: List[float],
        source: str,
        encounter_date: Optional[str],
        entities: Optional[dict],
    ) -> str:
        entities = entities or {}
        payload = {
            "patient_id": patient_id,
            "entry_id": entry_id,
            "text": text,
            "source": source,
            "encounter_date": encounter_date or datetime.utcnow().isoformat(),
            "has_medications": bool(entities.get("medications")),
            "has_conditions": bool(entities.get("conditions")),
            "has_symptoms": bool(entities.get("symptoms")),
            "medication_names": [
                m["name"].lower() for m in entities.get("medications", [])
            ],
            "condition_names": [
                c["name"].lower() for c in entities.get("conditions", [])
            ],
            "symptom_names": [
                s["name"].lower() for s in entities.get("symptoms", [])
            ],
        }

        self.client.upsert(
            collection_name=self.collection,
            points=[PointStruct(id=entry_id, vector=embedding, payload=payload)],
        )
        logger.info("qdrant_entry_indexed", entry_id=entry_id)
        return entry_id

    async def search(
        self,
        patient_id: str,
        query_embedding: List[float],
        scope: str,
        filters: dict,
        top_k: int = 10,
    ) -> List[dict]:
        must_conditions = [
            FieldCondition(key="patient_id", match=MatchValue(value=patient_id))
        ]

        if scope == "medication_only":
            must_conditions.append(
                FieldCondition(key="has_medications", match=MatchValue(value=True))
            )
        elif scope == "disease_specific":
            diseases = [d.lower() for d in filters.get("diseases", [])]
            if diseases:
                must_conditions.append(
                    FieldCondition(key="condition_names", match=MatchAny(any=diseases))
                )
        elif scope == "time_bound":
            date_start = filters.get("date_start")
            date_end = filters.get("date_end", datetime.utcnow().isoformat())
            if date_start:
                must_conditions.append(
                    FieldCondition(
                        key="encounter_date",
                        range=Range(gte=date_start, lte=date_end),
                    )
                )

        search_filter = Filter(must=must_conditions)
        hits = self.client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "id": str(hit.id),
                "type": "vector_entry",
                "content": hit.payload.get("text", ""),
                "score": hit.score,
                "date": hit.payload.get("encounter_date", ""),
                "medication_names": hit.payload.get("medication_names", []),
                "condition_names": hit.payload.get("condition_names", []),
            }
            for hit in hits
        ]

    async def delete_patient_data(self, patient_id: str) -> int:
        result = self.client.delete(
            collection_name=self.collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="patient_id", match=MatchValue(value=patient_id)
                    )
                ]
            ),
        )
        return result.result if result else 0
