# MedGraph AI — Codebase Handoff

> **Project:** Healthcare Interoperability Platform  
> **Team:** TLE_Eliminators | KIT's College of Engineering, Kolhapur  
> **Hackathon:** Cognizant Technoverse 2026  
> **Stack:** AWS Bedrock + LangGraph + Neo4j Aura + OpenSearch Serverless + DynamoDB + FastAPI + React

---

## What This Project Does

MedGraph AI is a HIPAA-compliant healthcare interoperability platform with four core flows:

### Flow 1 — Patient Record Ingestion
```
Patient submits health text or uploads PDF
  → PHI redacted (HIPAA Safe Harbor — 18 identifier types)
  → Bedrock Claude extracts clinical entities (symptoms, meds, conditions, vitals, allergies)
  → Entities stored as Neo4j Aura graph nodes + relationships
  → Redacted text embedded via Bedrock Titan (1024-dim)
  → Embedding stored in OpenSearch Serverless
  → Audit log written to DynamoDB
```

### Flow 2 — Consent-Gated Clinical RAG
```
Doctor submits clinical query about a patient
  → Consent check: active approved consent? (DynamoDB)
  → If yes: parallel search — Neo4j graph + OpenSearch vectors
  → Hybrid ranking: Graph×0.5 + Vector×0.3 + Recency×0.2
  → Top results → context → Bedrock Claude → clinical response with citations
  → Bedrock Guardrails validate output (PHI leakage, hallucination)
```

### Flow 3 — FHIR R4 Exchange
```
Doctor requests patient record bundle
  → Consent validated + scope enforced
  → Neo4j graph data retrieved
  → Bedrock Claude generates clinical summary
  → fhir.resources builds FHIR R4 Bundle (Patient, Condition, MedicationStatement, DocumentReference)
  → Bundle stored in DynamoDB + returned
```

### Flow 4 — Responsible AI Screening
```
Lab report uploaded → AI screening generated
  → HITL validator reviews (accept/edit/reject/escalate)
  → If accepted: forwarded to doctor with time-bound consent
  → Doctor reviews and marks complete
```

---

## Quick Start

### Prerequisites
- AWS CLI configured with valid credentials
- Python 3.11+
- Node.js 18+
- Neo4j Aura account (free tier works)

### Setup

```bash
# 1. Configure environment
cp .env.example .env
# Fill in: Neo4j Aura credentials, JWT secret, AWS region
# AWS credentials come from CLI profile (no keys in .env)

# 2. Create DynamoDB tables
cd backend
pip install -r requirements.txt
python scripts/create_dynamodb_tables.py

# 3. Seed initial data
python scripts/seed_super_admin.py
python scripts/seed_test_users.py

# 4. Start backend
uvicorn app.main:app --reload --port 8000

# 5. Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000 (Swagger: http://localhost:8000/docs)  
Frontend: http://localhost:5173

---

## Architecture

```
React 19 (Vite + TailwindCSS)
  ↓ Axios + JWT
FastAPI (Uvicorn)
  ├── DynamoDB (users, consents, audit, documents, chat)
  ├── Neo4j Aura (clinical entity graph)
  ├── OpenSearch Serverless (vector search)
  ├── S3 (encrypted PDF storage)
  └── Bedrock (Claude LLM + Titan Embeddings + Guardrails)
```

---

## Key Design Decisions

1. **PHI never reaches the knowledge base** — All text is redacted before LLM/vector/graph storage
2. **Consent-gated access** — Doctors cannot access patient data without explicit patient consent
3. **HITL validation** — AI outputs are never sent directly to doctors; human validators gate the flow
4. **Hybrid search** — Combines graph traversal (relationship-aware) with vector search (semantic)
5. **Bedrock Guardrails** — Runtime content filtering prevents PHI leakage and hallucinations
6. **Permission-based RBAC** — 50+ granular permissions, not just role checks

---

## Documentation

| File | Content |
|------|---------|
| `docs/API_REFERENCE.md` | Complete REST API (80+ endpoints) |
| `docs/BACKEND.md` | Backend architecture, services, pipelines |
| `docs/FRONTEND.md` | React app structure, routing, components |
| `docs/INFRASTRUCTURE.md` | AWS setup, environment config, deployment |
| `docs/RBAC.md` | 17 roles, 50+ permissions, access control |
| `docs/RESPONSIBLE_AI.md` | HIPAA, guardrails, HITL, audit trail |
| `TECH_STACK.md` | Full technology inventory |
| `ARCHITECTURE_DIAGRAM.mmd` | Mermaid architecture diagram |
