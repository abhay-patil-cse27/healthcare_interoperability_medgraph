"""
Integration tests for the full ingestion flow.
Requires external services: MongoDB Atlas, Neo4j Aura, AWS Bedrock.

Run: python -m pytest tests/integration/ -v -s
"""
import sys
import os
import asyncio
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_check():
    """Verify all services are reachable."""
    from app.config import get_settings
    settings = get_settings()

    # MongoDB
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    await client[settings.mongodb_db].command("ping")

    # Neo4j
    from neo4j import AsyncGraphDatabase
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    async with driver.session() as session:
        result = await session.run("RETURN 1 AS n")
        record = await result.single()
        assert record["n"] == 1
    await driver.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_embedding_service():
    """Verify Bedrock Titan embedding model produces 1024-dim vectors."""
    from app.services.embedding_service import EmbeddingService
    svc = EmbeddingService()

    embedding = await svc.embed("Patient has diabetes and takes metformin")
    assert isinstance(embedding, list)
    assert len(embedding) == 1024


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bedrock_service():
    """Verify AWS Bedrock Claude is reachable and returns text."""
    from app.services.bedrock_service import BedrockService
    svc = BedrockService()
    result = await svc.invoke(
        system_prompt="You are a test assistant. Reply with exactly: PONG",
        user_message="PING",
        max_tokens=10,
    )
    assert "text" in result
    assert len(result["text"]) > 0
    assert result["input_tokens"] > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_ingestion_pipeline():
    """
    Full end-to-end ingestion: text → entities → Neo4j.
    Uses a test patient ID that won't conflict with real data.
    """
    from app.pipelines.ingestion_pipeline import IngestionPipeline

    pipeline = IngestionPipeline()
    test_patient_id = "test-integration-patient-001"

    result = await pipeline.run(
        patient_id=test_patient_id,
        text="Patient has Type 2 Diabetes (E11.9). Taking Metformin 500mg twice daily. Allergic to penicillin. Blood pressure 140/90 mmHg.",
        source="integration_test",
    )

    assert result["status"] in ("success", "partial")
    assert result["graph_nodes_created"] >= 1
    assert len(result["errors"]) == 0 or result["status"] == "partial"

    # Verify entities were extracted
    entities = result["entities"]
    assert "conditions" in entities or "medications" in entities or "allergies" in entities


@pytest.mark.asyncio
@pytest.mark.integration
async def test_neo4j_store_and_retrieve():
    """Verify Neo4j stores entities and retrieves them correctly."""
    from app.services.neo4j_service import Neo4jService

    svc = Neo4jService()
    test_patient_id = "test-neo4j-patient-001"

    entities = {
        "conditions": [{"name": "hypertension", "icd10_code": "I10", "status": "active"}],
        "medications": [{"name": "lisinopril", "dosage": "10mg", "frequency": "daily", "route": "oral"}],
        "symptoms": [],
        "vitals": [],
        "allergies": [],
    }

    nodes_created = await svc.store_entities(
        patient_id=test_patient_id,
        entities=entities,
        source="integration_test",
        encounter_date="2026-05-04T00:00:00",
    )
    assert nodes_created == 2  # 1 condition + 1 medication

    # Retrieve and verify
    summary = await svc.get_patient_summary(test_patient_id)
    assert len(summary["conditions"]) >= 1
    assert len(summary["medications"]) >= 1

    condition_names = [c["name"] for c in summary["conditions"]]
    assert "hypertension" in condition_names

    await svc.close()
