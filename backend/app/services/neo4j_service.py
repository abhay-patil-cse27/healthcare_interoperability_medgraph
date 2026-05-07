import uuid
import structlog
from datetime import datetime
from typing import Optional, List
from neo4j import AsyncGraphDatabase
from app.config import get_settings

logger = structlog.get_logger()


class Neo4jService:
    """
    Neo4j Aura Service.
    Connects to Neo4j Aura (cloud) via neo4j+s:// protocol.
    Uses the configured database name for all sessions.
    """

    def __init__(self):
        settings = get_settings()
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        self.database = settings.neo4j_database

    async def close(self):
        await self.driver.close()

    def _session(self):
        """Create a session with the configured database."""
        return self.driver.session(database=self.database)

    async def store_entities(
        self,
        patient_id: str,
        entities: dict,
        source: str,
        encounter_date: str,
    ) -> int:
        nodes_created = 0
        timestamp = encounter_date or datetime.utcnow().isoformat()

        async with self._session() as session:
            # Merge Patient node
            await session.run(
                "MERGE (p:Patient {patient_id: $pid}) "
                "ON CREATE SET p.created_at = $now",
                pid=patient_id,
                now=datetime.utcnow().isoformat(),
            )

            # Symptoms
            for s in entities.get("symptoms", []):
                node_id = str(
                    uuid.uuid5(uuid.NAMESPACE_DNS, f"{patient_id}:symptom:{s['name']}")
                )
                await session.run(
                    """
                    MERGE (n:Symptom {node_id: $nid})
                    ON CREATE SET n.name=$name, n.severity=$sev, n.duration=$dur,
                                  n.patient_id=$pid, n.timestamp=$ts, n.source=$src
                    WITH n
                    MATCH (p:Patient {patient_id: $pid})
                    MERGE (p)-[:HAS_SYMPTOM]->(n)
                    """,
                    nid=node_id,
                    name=s["name"].lower(),
                    sev=s.get("severity", "unknown"),
                    dur=s.get("duration", ""),
                    pid=patient_id,
                    ts=timestamp,
                    src=source,
                )
                nodes_created += 1

            # Medications
            for m in entities.get("medications", []):
                node_id = str(
                    uuid.uuid5(uuid.NAMESPACE_DNS, f"{patient_id}:med:{m['name']}")
                )
                await session.run(
                    """
                    MERGE (n:Medication {node_id: $nid})
                    ON CREATE SET n.name=$name, n.dosage=$dos, n.frequency=$freq,
                                  n.patient_id=$pid, n.timestamp=$ts, n.source=$src
                    WITH n
                    MATCH (p:Patient {patient_id: $pid})
                    MERGE (p)-[:TAKES_MEDICATION]->(n)
                    """,
                    nid=node_id,
                    name=m["name"].lower(),
                    dos=m.get("dosage", ""),
                    freq=m.get("frequency", ""),
                    pid=patient_id,
                    ts=timestamp,
                    src=source,
                )
                nodes_created += 1

            # Conditions
            for c in entities.get("conditions", []):
                node_id = str(
                    uuid.uuid5(uuid.NAMESPACE_DNS, f"{patient_id}:cond:{c['name']}")
                )
                await session.run(
                    """
                    MERGE (n:Condition {node_id: $nid})
                    ON CREATE SET n.name=$name, n.icd10=$icd, n.status=$stat,
                                  n.patient_id=$pid, n.timestamp=$ts
                    WITH n
                    MATCH (p:Patient {patient_id: $pid})
                    MERGE (p)-[:HAS_CONDITION]->(n)
                    """,
                    nid=node_id,
                    name=c["name"].lower(),
                    icd=c.get("icd10_code", ""),
                    stat=c.get("status", "active"),
                    pid=patient_id,
                    ts=timestamp,
                )
                nodes_created += 1

            # Vitals
            for v in entities.get("vitals", []):
                node_id = str(
                    uuid.uuid5(
                        uuid.NAMESPACE_DNS,
                        f"{patient_id}:vital:{v['type']}:{timestamp}",
                    )
                )
                await session.run(
                    """
                    MERGE (n:Vital {node_id: $nid})
                    ON CREATE SET n.type=$type, n.value=$val, n.unit=$unit,
                                  n.status=$stat, n.patient_id=$pid, n.timestamp=$ts
                    WITH n
                    MATCH (p:Patient {patient_id: $pid})
                    MERGE (p)-[:HAS_VITAL]->(n)
                    """,
                    nid=node_id,
                    type=v.get("type", ""),
                    val=v.get("value", ""),
                    unit=v.get("unit", ""),
                    stat=v.get("status", "normal"),
                    pid=patient_id,
                    ts=timestamp,
                )
                nodes_created += 1

            # Allergies
            for a in entities.get("allergies", []):
                node_id = str(
                    uuid.uuid5(
                        uuid.NAMESPACE_DNS,
                        f"{patient_id}:allergy:{a['substance']}",
                    )
                )
                await session.run(
                    """
                    MERGE (n:Allergy {node_id: $nid})
                    ON CREATE SET n.substance=$sub, n.reaction=$react, n.severity=$sev,
                                  n.patient_id=$pid, n.timestamp=$ts
                    WITH n
                    MATCH (p:Patient {patient_id: $pid})
                    MERGE (p)-[:HAS_ALLERGY]->(n)
                    """,
                    nid=node_id,
                    sub=a.get("substance", ""),
                    react=a.get("reaction", ""),
                    sev=a.get("severity", ""),
                    pid=patient_id,
                    ts=timestamp,
                )
                nodes_created += 1

        logger.info("neo4j_entities_stored", patient_id=patient_id, nodes=nodes_created)
        return nodes_created

    async def search(
        self,
        patient_id: str,
        query: str,
        scope: str,
        filters: dict,
        top_k: int = 10,
    ) -> List[dict]:
        results = []

        async with self._session() as session:
            if scope == "medication_only":
                records = await session.run(
                    "MATCH (p:Patient {patient_id: $pid})-[:TAKES_MEDICATION]->(n:Medication) "
                    "RETURN n, 'Medication' as label LIMIT $k",
                    pid=patient_id,
                    k=top_k,
                )
            elif scope == "disease_specific":
                diseases = filters.get("diseases", [])
                records = await session.run(
                    "MATCH (p:Patient {patient_id: $pid})-[:HAS_CONDITION]->(n:Condition) "
                    "WHERE n.name IN $diseases OR $diseases = [] "
                    "RETURN n, 'Condition' as label LIMIT $k",
                    pid=patient_id,
                    diseases=[d.lower() for d in diseases],
                    k=top_k,
                )
            elif scope == "time_bound":
                date_start = filters.get("date_start", "")
                date_end = filters.get("date_end", datetime.utcnow().isoformat())
                records = await session.run(
                    "MATCH (p:Patient {patient_id: $pid})-[]->(n) "
                    "WHERE n.timestamp >= $ds AND n.timestamp <= $de "
                    "RETURN n, labels(n)[0] as label LIMIT $k",
                    pid=patient_id,
                    ds=date_start,
                    de=date_end,
                    k=top_k,
                )
            else:  # full — fetch from every node type to ensure balanced coverage
                per_label_k = max(top_k // 5, 3)
                queries = [
                    ("MATCH (p:Patient {patient_id: $pid})-[:TAKES_MEDICATION]->(n:Medication) "
                     "RETURN n, 'Medication' as label LIMIT $k", per_label_k),
                    ("MATCH (p:Patient {patient_id: $pid})-[:HAS_CONDITION]->(n:Condition) "
                     "RETURN n, 'Condition' as label LIMIT $k", per_label_k),
                    ("MATCH (p:Patient {patient_id: $pid})-[:HAS_SYMPTOM]->(n:Symptom) "
                     "RETURN n, 'Symptom' as label LIMIT $k", per_label_k),
                    ("MATCH (p:Patient {patient_id: $pid})-[:HAS_ALLERGY]->(n:Allergy) "
                     "RETURN n, 'Allergy' as label LIMIT $k", per_label_k),
                    ("MATCH (p:Patient {patient_id: $pid})-[:HAS_VITAL]->(n:Vital) "
                     "RETURN n, 'Vital' as label LIMIT $k", per_label_k),
                ]
                for cypher, k in queries:
                    recs = await session.run(cypher, pid=patient_id, k=k)
                    async for record in recs:
                        node = dict(record["n"])
                        label = record["label"]
                        content = self._node_to_text(node, label)
                        results.append({
                            "id": node.get("node_id", str(uuid.uuid4())),
                            "type": "graph_node",
                            "vertex_label": label,
                            "content": content,
                            "score": 1.0,
                            "date": node.get("timestamp", ""),
                        })

        return results

    async def get_patient_summary(self, patient_id: str) -> dict:
        summary = {
            "conditions": [],
            "medications": [],
            "symptoms": [],
            "allergies": [],
            "vitals": [],
        }
        async with self._session() as session:
            for rel, key in [
                ("HAS_CONDITION", "conditions"),
                ("TAKES_MEDICATION", "medications"),
                ("HAS_SYMPTOM", "symptoms"),
                ("HAS_ALLERGY", "allergies"),
                ("HAS_VITAL", "vitals"),
            ]:
                records = await session.run(
                    f"MATCH (p:Patient {{patient_id: $pid}})-[:{rel}]->(n) RETURN n",
                    pid=patient_id,
                )
                async for r in records:
                    summary[key].append(dict(r["n"]))
        return summary

    async def create_event_node(
        self, patient_id: str, request_id: str, source: str, encounter_date: str
    ) -> str:
        event_id = str(uuid.uuid4())
        async with self._session() as session:
            await session.run(
                """
                CREATE (e:Event {event_id: $eid, patient_id: $pid, request_id: $rid,
                                 source: $src, timestamp: $ts})
                WITH e
                MATCH (p:Patient {patient_id: $pid})
                CREATE (e)-[:PART_OF_EVENT]->(p)
                """,
                eid=event_id,
                pid=patient_id,
                rid=request_id,
                src=source,
                ts=encounter_date or datetime.utcnow().isoformat(),
            )
        return event_id

    def _node_to_text(self, node: dict, label: str) -> str:
        parts = [f"[{label}]"]
        skip = {"node_id", "patient_id"}
        for k, v in node.items():
            if k not in skip and v:
                parts.append(f"{k}: {v}")
        return " | ".join(parts)
