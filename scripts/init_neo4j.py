"""
Run this once after Docker services are up to create Neo4j constraints and indexes.
Usage: python scripts/init_neo4j.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from neo4j import AsyncGraphDatabase
from app.config import get_settings


async def init():
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    constraints = [
        ("Patient", "patient_id"),
        ("Symptom", "node_id"),
        ("Medication", "node_id"),
        ("Condition", "node_id"),
        ("Vital", "node_id"),
        ("Allergy", "node_id"),
        ("Event", "event_id"),
    ]

    async with driver.session() as session:
        for label, prop in constraints:
            cypher = (
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) "
                f"REQUIRE n.{prop} IS UNIQUE"
            )
            await session.run(cypher)
            print(f"✅ Constraint: {label}.{prop} IS UNIQUE")

        # Indexes on patient_id for fast patient-scoped queries
        for label in ["Symptom", "Medication", "Condition", "Vital", "Allergy", "Event"]:
            await session.run(
                f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.patient_id)"
            )
            print(f"✅ Index: {label}(patient_id)")

    await driver.close()
    print("\n🎉 Neo4j initialization complete!")


if __name__ == "__main__":
    asyncio.run(init())
