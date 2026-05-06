from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class MemoryIngestRequest(BaseModel):
    patient_id: str
    text: str = Field(min_length=10)
    source: str = Field(default="patient_input")
    encounter_date: Optional[str] = None


class MemoryIngestResponse(BaseModel):
    request_id: str
    status: str
    entities: dict
    graph_nodes_created: int
    vector_entry_id: Optional[str]
    processing_time_ms: int


class ChatRequest(BaseModel):
    patient_id: str
    query: str = Field(min_length=3)
    requester_id: str
    requester_role: str
    session_id: Optional[str] = None   # If None, a new session is created automatically


class ChatResponse(BaseModel):
    request_id: str
    session_id: str
    response: str
    citations: List[dict]
    graph_nodes_used: int
    vector_entries_used: int
    retrieval_time_ms: int
    llm_time_ms: int
    total_time_ms: int
    cache_hit: bool = False
    history_turns: int = 0


class FHIRExchangeRequest(BaseModel):
    patient_id: str
    doctor_id: str
    consent_id: str
    include_summary: bool = True


class FHIRExchangeResponse(BaseModel):
    bundle_id: str
    fhir_bundle: dict
    clinical_summary: str
    resource_count: int
