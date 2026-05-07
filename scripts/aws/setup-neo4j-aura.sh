#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MedGraph AI — Neo4j Aura Setup & Verification
# ═══════════════════════════════════════════════════════════════════════════════
# Verifies connectivity to Neo4j Aura and creates graph schema constraints.
#
# Prerequisites:
#   - Python with neo4j driver installed (pip install neo4j)
#   - .env file with NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
#
# Run: bash scripts/aws/setup-neo4j-aura.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   MedGraph AI — Neo4j Aura Setup                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "✓ Loaded .env"
else
    echo "ERROR: No .env file found"
    exit 1
fi

echo ""
echo "  URI:      $NEO4J_URI"
echo "  User:     $NEO4J_USER"
echo "  Database: $NEO4J_DATABASE"
echo ""

# Test connection and create schema
python -c "
from neo4j import GraphDatabase
import os

uri = os.environ['NEO4J_URI']
user = os.environ['NEO4J_USER']
password = os.environ['NEO4J_PASSWORD']
database = os.environ.get('NEO4J_DATABASE', 'neo4j')

print('[1/3] Connecting to Neo4j Aura...')
driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session(database=database) as session:
    result = session.run('RETURN 1 AS n')
    record = result.single()
    assert record['n'] == 1
    print('  ✓ Connection successful')

print('[2/3] Creating uniqueness constraints...')
with driver.session(database=database) as session:
    constraints = [
        'CREATE CONSTRAINT patient_id IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE',
        'CREATE CONSTRAINT symptom_id IF NOT EXISTS FOR (n:Symptom) REQUIRE n.node_id IS UNIQUE',
        'CREATE CONSTRAINT medication_id IF NOT EXISTS FOR (n:Medication) REQUIRE n.node_id IS UNIQUE',
        'CREATE CONSTRAINT condition_id IF NOT EXISTS FOR (n:Condition) REQUIRE n.node_id IS UNIQUE',
        'CREATE CONSTRAINT vital_id IF NOT EXISTS FOR (n:Vital) REQUIRE n.node_id IS UNIQUE',
        'CREATE CONSTRAINT allergy_id IF NOT EXISTS FOR (n:Allergy) REQUIRE n.node_id IS UNIQUE',
        'CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE',
    ]
    for cypher in constraints:
        try:
            session.run(cypher)
        except Exception as e:
            if 'already exists' in str(e).lower() or 'equivalent' in str(e).lower():
                pass
            else:
                print(f'  Warning: {e}')
    print('  ✓ Constraints created')

print('[3/3] Creating indexes...')
with driver.session(database=database) as session:
    indexes = [
        'CREATE INDEX patient_id_idx IF NOT EXISTS FOR (p:Patient) ON (p.patient_id)',
        'CREATE INDEX symptom_patient IF NOT EXISTS FOR (n:Symptom) ON (n.patient_id)',
        'CREATE INDEX medication_patient IF NOT EXISTS FOR (n:Medication) ON (n.patient_id)',
        'CREATE INDEX condition_patient IF NOT EXISTS FOR (n:Condition) ON (n.patient_id)',
        'CREATE INDEX vital_patient IF NOT EXISTS FOR (n:Vital) ON (n.patient_id)',
        'CREATE INDEX allergy_patient IF NOT EXISTS FOR (n:Allergy) ON (n.patient_id)',
        'CREATE INDEX event_patient IF NOT EXISTS FOR (e:Event) ON (e.patient_id)',
    ]
    for cypher in indexes:
        try:
            session.run(cypher)
        except Exception as e:
            if 'already exists' in str(e).lower() or 'equivalent' in str(e).lower():
                pass
            else:
                print(f'  Warning: {e}')
    print('  ✓ Indexes created')

driver.close()
print('')
print('╔══════════════════════════════════════════════════════════╗')
print('║   ✓ Neo4j Aura fully configured                         ║')
print('║                                                          ║')
print('║   Instance: medgraph_Neo4j                               ║')
print('║   Schema:   7 constraints + 7 indexes                    ║')
print('║   Ready for patient entity storage                       ║')
print('╚══════════════════════════════════════════════════════════╝')
"
