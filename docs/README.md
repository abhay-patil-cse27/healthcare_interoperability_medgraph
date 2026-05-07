# MedGraph AI — Documentation

> Healthcare Interoperability Platform | Team TLE_Eliminators | Cognizant Technoverse 2026

---

## Quick Links

| Document | Description |
|----------|-------------|
| [API Reference](./API_REFERENCE.md) | Complete REST API with all endpoints, request/response schemas |
| [Backend](./BACKEND.md) | Backend architecture, services, pipelines, database schemas |
| [Frontend](./FRONTEND.md) | React app structure, routing, state management, components |
| [Infrastructure](./INFRASTRUCTURE.md) | AWS services, deployment, environment configuration |
| [RBAC](./RBAC.md) | Role-Based Access Control — 17 roles, 50+ permissions |
| [Responsible AI](./RESPONSIBLE_AI.md) | HIPAA compliance, PHI redaction, Bedrock Guardrails, HITL pipeline |

---

## What is MedGraph AI?

MedGraph AI is a HIPAA-compliant healthcare interoperability platform that uses AI to structure, store, and retrieve patient health records. It connects patients, doctors, nurses, pharmacists, and administrators through a consent-gated system.

### Core Flows

**1. Patient Record Ingestion**
```
Patient submits health text / uploads PDF
  → PHI redacted (HIPAA Safe Harbor)
  → Bedrock Claude extracts clinical entities
  → Entities stored in Neo4j knowledge graph
  → Text embedded via Bedrock Titan (1024-dim)
  → Embedding stored in OpenSearch Serverless
```

**2. Consent-Gated Clinical RAG**
```
Doctor submits clinical query
  → Consent validated (DynamoDB)
  → Parallel search: Neo4j graph + OpenSearch vectors
  → Hybrid ranking (Graph 0.5 + Vector 0.3 + Recency 0.2)
  → Bedrock Claude generates response with citations
```

**3. FHIR R4 Exchange**
```
Doctor requests patient bundle
  → Consent validated
  → Graph data + LLM summary
  → FHIR R4 Bundle (Patient, Condition, MedicationStatement, DocumentReference)
```

**4. Responsible AI Screening**
```
Lab report uploaded → AI screening generated
  → HITL validator reviews/edits
  → Forwarded to doctor with time-bound consent
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, TailwindCSS, Zustand, React Router |
| Backend | FastAPI, Python 3.11+, Uvicorn |
| AI/ML | AWS Bedrock (Claude Sonnet + Titan Embeddings), LangGraph, LangChain |
| Graph DB | Neo4j Aura (cloud) |
| Vector DB | AWS OpenSearch Serverless |
| Primary DB | AWS DynamoDB |
| Storage | AWS S3 (encrypted PDFs) |
| Auth | JWT (HS256) + bcrypt |
| Standards | FHIR R4, HIPAA Safe Harbor, ABDM/ABHA |

---

## Getting Started

```bash
# 1. Clone and configure
cp .env.example .env
# Fill in: AWS credentials, Neo4j Aura URI, JWT secret

# 2. Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
npm run dev
```

See [Infrastructure](./INFRASTRUCTURE.md) for full environment setup.
