# MedGraph AI

**HIPAA-Compliant Healthcare Interoperability Platform**  
Team TLE_Eliminators | KIT's College of Engineering, Kolhapur  
Cognizant Technoverse 2026

---

## Overview

MedGraph AI enables secure, consent-gated sharing of patient health records using AI-powered clinical intelligence and FHIR R4 standards.

- **Patients** upload health records → AI extracts entities → stored in knowledge graph + vector index
- **Doctors** request consent → query patient data with RAG-powered clinical answers
- **HITL Validators** review AI outputs before they reach doctors (anti-hallucination)
- **FHIR Exchange** generates R4 bundles shareable across any healthcare system

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, TailwindCSS, Zustand |
| Backend | FastAPI, Python 3.11+, LangGraph |
| LLM | AWS Bedrock (Claude Sonnet + Titan Embeddings) |
| Graph DB | Neo4j Aura |
| Vector DB | AWS OpenSearch Serverless |
| Primary DB | AWS DynamoDB |
| Storage | AWS S3 (encrypted PDFs) |
| Auth | JWT (HS256) + bcrypt |
| Standards | FHIR R4, HIPAA Safe Harbor |

---

## Quick Start

### Prerequisites
- AWS CLI configured with valid credentials
- Python 3.11+
- Node.js 18+
- Neo4j Aura account

### Setup

```bash
# Configure environment
cp .env.example .env
# Fill in: Neo4j credentials, JWT secret

# Backend
cd backend
pip install -r requirements.txt
python -m scripts.create_dynamodb_tables
python -m scripts.seed_pregnancy_demo
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000 (Swagger: http://localhost:8000/docs)  
Frontend: http://localhost:5173

---

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/API_REFERENCE.md) | 80+ REST endpoints |
| [Backend](docs/BACKEND.md) | Architecture, services, pipelines |
| [Frontend](docs/FRONTEND.md) | React app structure, routing |
| [Infrastructure](docs/INFRASTRUCTURE.md) | AWS setup, deployment |
| [RBAC](docs/RBAC.md) | 17 roles, 50+ permissions |
| [Responsible AI](docs/RESPONSIBLE_AI.md) | HIPAA, guardrails, HITL |
| [Tech Stack](TECH_STACK.md) | Full technology inventory |
| [Developer Guide](DEVELOPER_GUIDE.md) | Setup & contribution guide |

---

## Architecture

```
React 19 (Vite)
  ↓ Axios + JWT
FastAPI (Uvicorn)
  ├── DynamoDB (users, consents, audit)
  ├── Neo4j Aura (clinical entity graph)
  ├── OpenSearch Serverless (vector search)
  ├── S3 (encrypted PDFs)
  └── Bedrock (Claude + Titan + Guardrails)
```

---

## Key Features

- **Consent-Gated Access** — Doctors cannot access patient data without explicit consent
- **PHI Redaction** — HIPAA Safe Harbor de-identification before any LLM processing
- **Hybrid RAG** — Graph traversal + vector search with weighted ranking
- **HITL Validation** — Human review gates all AI-generated clinical summaries
- **Bedrock Guardrails** — Runtime content filtering for safety
- **17 User Roles** — From patient to super admin with granular permissions
- **FHIR R4** — Standards-compliant health data exchange

---

## License

Hackathon project — Cognizant Technoverse 2026
