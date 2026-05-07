"""
AWS OpenSearch Serverless Vector Service
==========================================
Replaces Qdrant as the vector database for patient memory embeddings.
Uses AWS SigV4 authentication — no API keys needed, uses CLI credentials.

Collection: medgraph-vectors (VECTORSEARCH type)
Index: patient-memories (knn_vector, 1024-dim, cosine similarity)
"""
import structlog
from typing import List, Optional
from datetime import datetime
from functools import lru_cache

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

from app.config import get_settings

logger = structlog.get_logger()


class OpenSearchVectorService:
    def __init__(self):
        settings = get_settings()
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, settings.aws_region, "aoss")

        self.client = OpenSearch(
            hosts=[{"host": settings.opensearch_endpoint, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_maxsize=20,
        )
        self.index = settings.opensearch_index
        self.dim = settings.embedding_dim
        logger.info(
            "opensearch_initialized",
            endpoint=settings.opensearch_endpoint,
            index=self.index,
        )

    async def index_document(
        self,
        patient_id: str,
        entry_id: str,
        text: str,
        embedding: List[float],
        source: str,
        encounter_date: Optional[str],
        entities: Optional[dict],
    ) -> str:
        """Index a patient memory document with its embedding vector."""
        entities = entities or {}
        doc = {
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
            "embedding": embedding,
        }

        self.client.index(index=self.index, body=doc)
        logger.info("opensearch_indexed", entry_id=entry_id, patient_id=patient_id[:8])
        return entry_id

    async def search(
        self,
        patient_id: str,
        query_embedding: List[float],
        scope: str,
        filters: dict,
        top_k: int = 10,
    ) -> List[dict]:
        """
        KNN vector search filtered by patient_id and consent scope.
        Returns ranked results with content and metadata.
        """
        # Build filter based on consent scope
        must_filters = [{"term": {"patient_id": patient_id}}]

        if scope == "medication_only":
            must_filters.append({"term": {"has_medications": True}})
        elif scope == "disease_specific":
            diseases = [d.lower() for d in filters.get("diseases", [])]
            if diseases:
                must_filters.append({"terms": {"condition_names": diseases}})
        elif scope == "time_bound":
            date_start = filters.get("date_start")
            date_end = filters.get("date_end", datetime.utcnow().isoformat())
            if date_start:
                must_filters.append({
                    "range": {"encounter_date": {"gte": date_start, "lte": date_end}}
                })

        query = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": must_filters,
                    "should": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_embedding,
                                    "k": top_k,
                                }
                            }
                        }
                    ],
                }
            },
            "_source": {
                "excludes": ["embedding"]
            },
        }

        response = self.client.search(index=self.index, body=query)

        results = []
        for hit in response["hits"]["hits"]:
            src = hit["_source"]
            results.append({
                "id": hit["_id"],
                "type": "vector_entry",
                "content": src.get("text", ""),
                "score": hit["_score"],
                "date": src.get("encounter_date", ""),
                "medication_names": src.get("medication_names", []),
                "condition_names": src.get("condition_names", []),
            })

        return results

    async def delete_patient_data(self, patient_id: str) -> int:
        """Delete all vectors for a patient (consent revocation)."""
        # OpenSearch Serverless: search then delete individually
        search_body = {
            "size": 1000,
            "query": {"term": {"patient_id": patient_id}},
            "_source": False,
        }
        response = self.client.search(index=self.index, body=search_body)
        hits = response["hits"]["hits"]
        for hit in hits:
            self.client.delete(index=self.index, id=hit["_id"])
        logger.info("opensearch_patient_deleted", patient_id=patient_id[:8], deleted=len(hits))
        return len(hits)


@lru_cache()
def get_opensearch_service() -> OpenSearchVectorService:
    return OpenSearchVectorService()
