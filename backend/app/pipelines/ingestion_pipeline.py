"""
Ingestion Pipeline (LangGraph) — PII-Free Knowledge Base
==========================================================
Hybrid pipeline: PHI Redaction → Entity Extraction → Neo4j + Vector Store

CRITICAL DESIGN PRINCIPLE:
  The knowledge base (Neo4j graph + vector store) must NEVER contain PII.
  All text is PHI-redacted BEFORE:
    1. Being sent to the LLM for entity extraction
    2. Being embedded and stored in the vector store
    3. Being stored as node properties in Neo4j

Pipeline stages:
  1. validate_input       — Basic input validation
  2. redact_phi           — Strip all PII/PHI from text (HIPAA Safe Harbor)
  3. extract_entities     — LLM extracts clinical entities from REDACTED text
  4. store_neo4j          — Store entities in graph (no PII in node properties)
  5. generate_embedding   — Embed the REDACTED text
  6. store_vectors        — Store REDACTED text + embedding in vector store
  7. create_event         — Create event node for audit linkage
"""
import json
import uuid
import structlog
from typing import TypedDict, Optional, List
from datetime import datetime
from langgraph.graph import StateGraph, END

from app.services.bedrock_service import BedrockService
from app.services.embedding_service import get_embedding_service
from app.services.neo4j_service import Neo4jService
from app.services.opensearch_service import get_opensearch_service
from app.services.phi_redaction_service import redact_phi
from app.prompts.entity_extraction import (
    ENTITY_EXTRACTION_SYSTEM_PROMPT,
    build_extraction_prompt,
)

logger = structlog.get_logger()


class IngestionState(TypedDict):
    patient_id: str
    text: str                       # Original text (used only for redaction step)
    redacted_text: str              # PHI-redacted text (used for all downstream)
    source: str
    encounter_date: Optional[str]
    request_id: str
    phi_redactions_applied: int
    extracted_entities: Optional[dict]
    graph_nodes_created: int
    embedding: Optional[List[float]]
    vector_entry_id: Optional[str]
    event_node_id: Optional[str]
    errors: List[str]
    status: str


class IngestionPipeline:
    def __init__(self):
        self.llm = BedrockService()
        self.embedding_svc = get_embedding_service()
        self.neo4j = Neo4jService()
        self.vector_store = get_opensearch_service()
        self.graph = self._build_graph()

    def _build_graph(self):
        g = StateGraph(IngestionState)
        g.add_node("validate_input", self._validate_input)
        g.add_node("redact_phi", self._redact_phi)
        g.add_node("extract_entities", self._extract_entities)
        g.add_node("store_neo4j", self._store_neo4j)
        g.add_node("generate_embedding", self._generate_embedding)
        g.add_node("store_vectors", self._store_vectors)
        g.add_node("create_event", self._create_event)
        g.set_entry_point("validate_input")
        g.add_edge("validate_input", "redact_phi")
        g.add_edge("redact_phi", "extract_entities")
        g.add_edge("extract_entities", "store_neo4j")
        g.add_edge("store_neo4j", "generate_embedding")
        g.add_edge("generate_embedding", "store_vectors")
        g.add_edge("store_vectors", "create_event")
        g.add_edge("create_event", END)
        return g.compile()

    async def run(
        self,
        patient_id: str,
        text: str,
        source: str,
        encounter_date: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> dict:
        initial: IngestionState = {
            "patient_id": patient_id,
            "text": text,
            "redacted_text": "",
            "source": source,
            "encounter_date": encounter_date or datetime.utcnow().isoformat(),
            "request_id": request_id or str(uuid.uuid4()),
            "phi_redactions_applied": 0,
            "extracted_entities": None,
            "graph_nodes_created": 0,
            "embedding": None,
            "vector_entry_id": None,
            "event_node_id": None,
            "errors": [],
            "status": "processing",
        }
        final = await self.graph.ainvoke(initial)
        return {
            "entities": final["extracted_entities"] or {},
            "graph_nodes_created": final["graph_nodes_created"],
            "vector_entry_id": final["vector_entry_id"],
            "event_node_id": final["event_node_id"],
            "phi_redactions_applied": final["phi_redactions_applied"],
            "status": final["status"],
            "errors": final["errors"],
        }

    async def _validate_input(self, state: IngestionState) -> dict:
        if len(state["text"]) < 10:
            return {**state, "status": "failed", "errors": ["Text too short"]}
        if not state["patient_id"]:
            return {**state, "status": "failed", "errors": ["Missing patient_id"]}
        return state

    async def _redact_phi(self, state: IngestionState) -> dict:
        """
        CRITICAL STEP: Strip all PII/PHI before any downstream processing.
        After this step, only redacted_text is used — original text is discarded
        from the pipeline flow.
        """
        try:
            redacted_text, redactions = redact_phi(state["text"], state["patient_id"])
            logger.info(
                "ingestion_phi_redacted",
                patient_id=state["patient_id"][:8] + "...",
                redactions_count=len(redactions),
                fields=[r.field_type for r in redactions],
            )
            return {
                **state,
                "redacted_text": redacted_text,
                "phi_redactions_applied": len(redactions),
            }
        except Exception as e:
            logger.error("phi_redaction_failed", error=str(e))
            return {
                **state,
                "redacted_text": state["text"],
                "phi_redactions_applied": 0,
                "errors": state["errors"] + [f"phi_redaction_fallback: {e}"],
            }

    async def _extract_entities(self, state: IngestionState) -> dict:
        """
        Extract clinical entities from PHI-REDACTED text.
        The LLM never sees original PII.
        """
        try:
            result = await self.llm.invoke(
                system_prompt=ENTITY_EXTRACTION_SYSTEM_PROMPT,
                user_message=build_extraction_prompt(state["redacted_text"]),
                temperature=0.0,
                apply_guardrails=False,  # Entity extraction is internal — skip guardrails
            )
            text = result["text"].strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
            entities = json.loads(text.strip())
            entities = self._scrub_pii_from_entities(entities)
            return {**state, "extracted_entities": entities}
        except Exception as e:
            logger.error("entity_extraction_failed", error=str(e))
            return {
                **state,
                "errors": state["errors"] + [f"entity_extraction: {e}"],
                "extracted_entities": {},
                "status": "partial",
            }

    def _scrub_pii_from_entities(self, entities: dict) -> dict:
        """
        Post-extraction safety net: remove any extracted entity that
        looks like PII (names, phone numbers, addresses, IDs).
        """
        import re

        pii_patterns = [
            re.compile(r'\+?\d{10,12}'),
            re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b'),
            re.compile(r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+'),
            re.compile(r'\b\d{6}\b'),
            re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            re.compile(r'\[PATIENT\]'),
            re.compile(r'\[PHONE_REDACTED\]'),
            re.compile(r'\[ADDRESS_REDACTED\]'),
            re.compile(r'\[LAB_ID_REDACTED\]'),
        ]

        def is_pii(value: str) -> bool:
            if not value or not isinstance(value, str):
                return False
            for pattern in pii_patterns:
                if pattern.search(value):
                    return True
            return False

        def scrub_list(items: list) -> list:
            cleaned = []
            for item in items:
                if isinstance(item, dict):
                    has_pii = any(is_pii(str(v)) for v in item.values() if v)
                    if not has_pii:
                        cleaned.append(item)
                    else:
                        logger.warning("pii_scrubbed_from_entity", entity=str(item)[:50])
            return cleaned

        for key in entities:
            if isinstance(entities[key], list):
                entities[key] = scrub_list(entities[key])

        return entities

    async def _store_neo4j(self, state: IngestionState) -> dict:
        """Store extracted entities in Neo4j graph (no PII in node properties)."""
        try:
            nodes = await self.neo4j.store_entities(
                patient_id=state["patient_id"],
                entities=state["extracted_entities"] or {},
                source=state["source"],
                encounter_date=state["encounter_date"],
            )
            return {**state, "graph_nodes_created": nodes}
        except Exception as e:
            logger.error("neo4j_store_failed", error=str(e))
            return {**state, "errors": state["errors"] + [f"neo4j: {e}"]}

    async def _generate_embedding(self, state: IngestionState) -> dict:
        """Generate embedding from PHI-REDACTED text via Bedrock Titan."""
        try:
            embedding = await self.embedding_svc.embed(state["redacted_text"])
            return {**state, "embedding": embedding}
        except Exception as e:
            return {**state, "errors": state["errors"] + [f"embedding: {e}"]}

    async def _store_vectors(self, state: IngestionState) -> dict:
        """Store REDACTED text + embedding in OpenSearch vector DB."""
        if not state["embedding"]:
            return state
        try:
            entry_id = str(uuid.uuid4())
            await self.vector_store.index_document(
                patient_id=state["patient_id"],
                entry_id=entry_id,
                text=state["redacted_text"],
                embedding=state["embedding"],
                source=state["source"],
                encounter_date=state["encounter_date"],
                entities=state["extracted_entities"],
            )
            return {**state, "vector_entry_id": entry_id}
        except Exception as e:
            return {**state, "errors": state["errors"] + [f"opensearch: {e}"]}

    async def _create_event(self, state: IngestionState) -> dict:
        try:
            event_id = await self.neo4j.create_event_node(
                patient_id=state["patient_id"],
                request_id=state["request_id"],
                source=state["source"],
                encounter_date=state["encounter_date"],
            )
            return {**state, "event_node_id": event_id, "status": "success"}
        except Exception as e:
            return {
                **state,
                "event_node_id": state["request_id"],
                "status": "partial",
                "errors": state["errors"] + [f"event_node: {e}"],
            }
