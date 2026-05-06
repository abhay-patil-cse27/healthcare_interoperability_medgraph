# MedGraph AI

**Healthcare Interoperability Platform** — Cognizant Technoverse 2026  
Team: TLE_Eliminators | KIT's College of Engineering, Kolhapur

---

## What It Does

MedGraph AI enables secure, consent-based sharing of patient records across providers using FHIR R4 standards.

- **Patients** submit health records in plain text → AI extracts structured entities → stored in a knowledge graph + vector index
- **Doctors** request consent → patients approve → doctors query patient data with AI-powered clinical answers
- **FHIR Exchange** → generate standards-compliant R4 bundles shareable across any healthcare system

---

## Quick Start

### Prerequisites
- Docker Desktop (with WSL2 on Windows)
- Python 3.12+
- Node.js 22+

### 1. Clone and configure
```bash
git clone <repo>
cd medgraph-ai
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Start databases
```bash
docker compose up -d mongodb neo4j qdrant
```

### 3. Set up Python environment
```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

pip install -r backend/requirements.txt
```

### 4. Initialize database schemas (first time only)
```bash
python scripts/init_neo4j.py
python scripts/init_qdrant.py
```

### 5. Start the backend
```bash
# From project root, with venv active
cd backend
uvicorn app.main:app --reload --port 8000
```

### 6. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## Full Docker Deployment

To run everything in containers:
```bash
docker compose up --build
```
Frontend available at **http://localhost:80**  
Backend API at **http://localhost:8000**

---

## API Reference

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/health` | GET | — | Service health check |
| `/auth/register` | POST | — | Create account (patient or doctor) |
| `/auth/login` | POST | — | Get JWT token |
| `/auth/me` | GET | Bearer | Current user profile |
| `/memory/ingest` | POST | Bearer | Ingest health text |
| `/memory/history/{id}` | GET | Bearer | Ingestion history |
| `/chat/` | POST | Bearer | Consent-gated RAG query |
| `/consent/request` | POST | Bearer (doctor) | Request patient access |
| `/consent/grant` | POST | Bearer (patient) | Approve/deny consent |
| `/consent/active/{id}` | GET | Bearer | List consents |
| `/consent/{id}` | DELETE | Bearer (patient) | Revoke consent |
| `/fhir/exchange` | POST | Bearer (doctor) | Generate FHIR R4 bundle |
| `/fhir/bundle/{id}` | GET | Bearer (doctor) | Retrieve stored bundle |

Interactive docs: **http://localhost:8000/docs**

---

## Running Tests

```bash
# Unit tests (no Docker needed)
venv\Scripts\python.exe -m pytest tests/unit/ -v

# Integration tests (requires Docker services running)
venv\Scripts\python.exe -m pytest tests/integration/ -v -s -m integration
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq Cloud — llama-3.3-70b-versatile |
| Embeddings | HuggingFace all-MiniLM-L6-v2 (local, 384-dim) |
| Orchestration | LangGraph + LangChain |
| FHIR | fhir.resources (R4) |
| Graph DB | Neo4j 5.18 |
| Vector DB | Qdrant |
| Primary DB | MongoDB 7.0 |
| Backend | FastAPI + Python 3.12 |
| Auth | JWT (HS256) + bcrypt |
| Frontend | React 19 + Vite + TailwindCSS |
| State | Zustand |

---

## Project Structure

```
medgraph-ai/
├── backend/app/
│   ├── routers/        # API endpoints
│   ├── services/       # Groq, Neo4j, Qdrant, MongoDB, FHIR, Consent, Audit
│   ├── pipelines/      # LangGraph ingestion + retrieval state machines
│   ├── models/         # Pydantic models
│   ├── prompts/        # LLM system prompts
│   └── utils/          # JWT handler, hybrid ranker
├── frontend/src/
│   ├── pages/          # Patient portal + Doctor dashboard
│   ├── components/     # Layout, UI primitives
│   ├── services/       # Axios API client
│   └── store/          # Zustand auth store
├── scripts/            # DB initialization
└── tests/              # Unit + integration tests
```

---

*MedGraph AI v1.0 — TLE_Eliminators — Cognizant Technoverse 2026*
