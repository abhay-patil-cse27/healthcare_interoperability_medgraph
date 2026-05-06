# MedGraph AI — Developer Guide

> **Project:** Healthcare Interoperability Platform
> **Team:** TLE_Eliminators | KIT's College of Engineering, Kolhapur
> **Hackathon:** Cognizant Technoverse 2026
> **Stack:** Groq + LangGraph + Neo4j + Qdrant + MongoDB + FastAPI + React

---

## Table of Contents

1. [What This Project Does](#1-what-this-project-does)
2. [Prerequisites](#2-prerequisites)
3. [Environment Setup](#3-environment-setup)
4. [Running the Project](#4-running-the-project)
5. [Project Structure](#5-project-structure)
6. [Architecture Overview](#6-architecture-overview)
7. [Backend Deep Dive](#7-backend-deep-dive)
8. [Frontend Deep Dive](#8-frontend-deep-dive)
9. [Database Schemas](#9-database-schemas)
10. [API Reference](#10-api-reference)
11. [Testing](#11-testing)
12. [Known Issues](#12-known-issues)
13. [Tech Stack Summary](#13-tech-stack-summary)

---

## 1. What This Project Does

MedGraph AI is a full-stack healthcare interoperability platform built around three core flows:

**Flow 1 — Patient Memory Ingestion**
A patient submits free-text health information. Groq LLaMA 3.3 extracts structured medical entities (symptoms, medications, conditions, vitals, allergies). Those entities are stored as nodes and relationships in a Neo4j knowledge graph. The original text is embedded via HuggingFace `all-MiniLM-L6-v2` (384-dim) and stored in Qdrant. An audit log entry is written to MongoDB.

**Flow 2 — Consent-Gated Doctor RAG Chat**
A doctor submits a clinical query about a patient. The system first checks MongoDB for an active, approved consent record. If consent exists, it runs a parallel search — Neo4j graph traversal and Qdrant vector search simultaneously. Results are merged using a hybrid ranker (Graph×0.5 + Vector×0.3 + Recency×0.2), passed as context to Groq LLM, and returned with citations.

**Flow 3 — FHIR R4 Bundle Exchange**
A doctor requests a full patient record. After consent validation, data is retrieved from Neo4j and Qdrant. Groq generates a clinical summary. `fhir.resources` builds a standards-compliant FHIR R4 Bundle (Patient, Condition, MedicationStatement, DocumentReference). The bundle is stored in MongoDB and returned to the doctor.

---

## 2. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.12.x | venv at `./venv/` |
| Node.js | 22.x | |
| npm | 11.x | |
| Docker Desktop | 29.x | WSL2 required on Windows |
| Groq API Key | — | Free tier at console.groq.com |

---

## 3. Environment Setup

### 3.1 Copy and configure `.env`

```bash
cp .env.example .env
```

Edit `.env` and fill in your `GROQ_API_KEY` and a strong `JWT_SECRET_KEY`. All other defaults work out of the box with Docker.

Key variables:

```env
GROQ_API_KEY=gsk_...              # Required — get from console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=medgraph

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=medgraph123

QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=patient_memories

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384

JWT_SECRET_KEY=change_this_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

GRAPH_WEIGHT=0.5
VECTOR_WEIGHT=0.3
RECENCY_WEIGHT=0.2
TOP_K=10
```

> The `.env` file lives at the project root. `config.py` resolves it as three levels up from `backend/app/config.py`. Do not move it.

### 3.2 Python virtual environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

pip install -r backend/requirements.txt
```

> The first time `EmbeddingService` initializes, it downloads `all-MiniLM-L6-v2` (~90 MB) from HuggingFace. It caches to `~/.cache/huggingface/` after that.

### 3.3 Frontend dependencies

```bash
cd frontend
npm install
```

---

## 4. Running the Project

### Option A — Local development (recommended)

**Step 1: Start the databases**

```bash
docker compose up -d mongodb neo4j qdrant
```

This starts:
- `medgraph-mongodb` on port `27017`
- `medgraph-neo4j` on ports `7474` (browser UI) and `7687` (Bolt)
- `medgraph-qdrant` on port `6333`

Wait ~15 seconds for Neo4j to finish initializing. You can check with:

```bash
docker compose ps
```

**Step 2: Initialize database schemas (first time only)**

```bash
# With venv active, from project root
venv\Scripts\python.exe scripts/init_neo4j.py
venv\Scripts\python.exe scripts/init_qdrant.py
```

`init_neo4j.py` creates uniqueness constraints and `patient_id` indexes on all node labels.
`init_qdrant.py` creates the `patient_memories` collection (384-dim, Cosine) and payload indexes.

**Step 3: Start the backend**

```bash
# Must run from the backend/ directory
cd backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

Backend: `http://localhost:8000`
Interactive API docs: `http://localhost:8000/docs`

**Step 4: Start the frontend**

```bash
cd frontend
npm run dev
```

Frontend: `http://localhost:5173`

---

### Option B — Full Docker deployment

```bash
docker compose up --build
```

This builds and runs all five services (MongoDB, Neo4j, Qdrant, backend, frontend).

- Frontend: `http://localhost:80`
- Backend API: `http://localhost:8000`

> Docker Compose overrides `MONGODB_URL`, `NEO4J_URI`, and `QDRANT_HOST` to use internal service names automatically.

---

### Health check

```bash
curl http://localhost:8000/health
# {"status":"healthy","services":{"mongodb":true,"neo4j":true,"qdrant":true}}
```

---

## 5. Project Structure

```
MED_GRAPH/
├── .env                          # Secrets and config (never commit)
├── .env.example                  # Template
├── docker-compose.yml            # All five services
│
├── backend/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── app/
│       ├── main.py               # FastAPI app factory, lifespan, CORS, routers
│       ├── config.py             # Pydantic settings loaded from .env
│       ├── dependencies.py       # get_db(), get_current_user(), require_role()
│       │
│       ├── models/
│       │   ├── user.py           # UserRole, UserCreate, UserInDB, UserResponse, TokenResponse
│       │   ├── consent.py        # ConsentScope, ConsentStatus, ConsentRequest, ConsentRecord, ConsentGrant, ConsentCheckResult
│       │   └── medical.py        # MemoryIngestRequest/Response, ChatRequest/Response, FHIRExchangeRequest/Response
│       │
│       ├── routers/
│       │   ├── auth.py           # /auth/register, /auth/login, /auth/me
│       │   ├── memory.py         # /memory/ingest, /memory/history/{patient_id}
│       │   ├── chat.py           # /chat/
│       │   ├── consent.py        # /consent/request, /consent/grant, /consent/active/{id}, /consent/{id}
│       │   └── fhir.py           # /fhir/exchange, /fhir/bundle/{bundle_id}
│       │
│       ├── services/
│       │   ├── groq_service.py       # LLM calls with retry (tenacity, 3 attempts)
│       │   ├── embedding_service.py  # HuggingFace local embeddings, singleton
│       │   ├── neo4j_service.py      # Graph CRUD: store_entities, search, create_event_node, get_patient_summary
│       │   ├── qdrant_service.py     # Vector CRUD: index, search, delete_patient_data
│       │   ├── mongo_service.py      # ping_mongodb() health check
│       │   ├── consent_service.py    # create_request, process_grant, check_access, revoke
│       │   ├── fhir_service.py       # build_fhir_bundle, store_bundle
│       │   └── audit_service.py      # log_phi_access() → MongoDB audit_logs
│       │
│       ├── pipelines/
│       │   ├── ingestion_pipeline.py  # LangGraph 6-node state machine
│       │   └── retrieval_pipeline.py  # LangGraph 7-node state machine
│       │
│       ├── prompts/
│       │   ├── entity_extraction.py   # System prompt + build_extraction_prompt()
│       │   └── clinical_summary.py    # System prompt + build_chat_prompt() + build_fhir_summary_prompt()
│       │
│       └── utils/
│           ├── hybrid_ranker.py   # HybridRanker.rank() — weighted merge + recency decay
│           └── jwt_handler.py     # create_access_token, decode_access_token, hash/verify password
│
├── frontend/
│   ├── .env                      # VITE_API_URL=http://localhost:8000
│   ├── vite.config.js
│   ├── tailwind.config.js        # Custom brand/surface color palettes
│   └── src/
│       ├── App.jsx               # All routes
│       ├── index.css             # Tailwind + custom @layer components
│       ├── services/api.js       # Axios instance + all API modules
│       ├── store/authStore.js    # Zustand: user, token, login(), logout()
│       ├── components/
│       │   ├── layout/           # AppLayout, Sidebar, ProtectedRoute
│       │   └── ui/               # Spinner, EmptyState, StatusDot
│       └── pages/
│           ├── Landing.jsx
│           ├── Login.jsx
│           ├── Register.jsx
│           ├── patient/          # HealthRecords, PatientChat, PatientConsents
│           └── doctor/           # PatientLookup, ClinicalQuery, DoctorConsents, FHIRExchange
│
├── scripts/
│   ├── init_neo4j.py    # Creates constraints + indexes
│   └── init_qdrant.py   # Creates collection + payload indexes
│
└── tests/
    ├── conftest.py       # Adds backend/ to sys.path
    ├── unit/
    │   ├── test_consent_service.py
    │   ├── test_hybrid_ranker.py
    │   └── test_jwt_handler.py
    └── integration/
        └── test_ingestion_flow.py
```

---

## 6. Architecture Overview

### Request lifecycle — Doctor RAG chat

```
Doctor browser
  → POST /chat/  (Bearer token)
  → dependencies.py: decode JWT, fetch user from MongoDB
  → require_role("doctor") check
  → consent_service.check_access() → MongoDB consents collection
      → if no active consent: 403
  → RetrievalPipeline.run()
      1. validate_scope       — log consent scope
      2. generate_query_embedding — HuggingFace embed(query)
      3. parallel_search      — asyncio.gather(neo4j.search(), qdrant.search())
      4. hybrid_rank          — HybridRanker.rank(graph, vector, weights)
      5. build_context        — format top 8 results as context string
      6. invoke_llm           — Groq LLaMA 3.3 with clinical summary prompt
      7. attach_citations     — build citation objects from top 5 results
  → audit_service.log_phi_access() → MongoDB audit_logs
  → return ChatResponse {response, citations, timing metrics}
```

### Request lifecycle — Patient ingestion

```
Patient browser
  → POST /memory/ingest  (Bearer token)
  → IngestionPipeline.run()
      1. validate_input       — text ≥ 10 chars, patient_id present
      2. extract_entities     — Groq LLM → JSON {symptoms, medications, conditions, vitals, allergies}
      3. store_neo4j          — MERGE nodes + relationships per entity type
      4. generate_embedding   — HuggingFace embed(text), normalize to unit length
      5. store_qdrant         — upsert point with full payload
      6. create_event         — Event node in Neo4j
  → audit_service.log_phi_access()
  → return MemoryIngestResponse {entities, graph_nodes_created, vector_entry_id, ...}
```

---

## 7. Backend Deep Dive

### Config (`backend/app/config.py`)

Uses `pydantic-settings`. The `.env` file path is resolved at import time as:

```python
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
```

This means the backend **must** be started from the `backend/` directory, or the path resolution will fail. `get_settings()` is `@lru_cache`-decorated — settings are loaded once per process.

### Dependencies (`backend/app/dependencies.py`)

Three FastAPI dependencies used across all routers:

- `get_db()` — returns a `motor` `AsyncIOMotorDatabase`. The underlying `AsyncIOMotorClient` is a singleton via `@lru_cache`.
- `get_current_user()` — reads the `Authorization: Bearer <token>` header, decodes the JWT, and fetches the user document from MongoDB. Raises `401` on any failure.
- `require_role(*roles)` — factory that returns a dependency checking `current_user["role"]` is in the allowed set. Raises `403` otherwise.

### LangGraph Pipelines

Both pipelines use `StateGraph` from LangGraph. Each node is an `async` method that receives the full state dict and returns an updated copy. Errors in any node are caught, appended to `state["errors"]`, and execution continues (partial success is acceptable).

**Ingestion pipeline nodes** (`ingestion_pipeline.py`):

| Node | What it does |
|---|---|
| `validate_input` | Checks text length ≥ 10 and patient_id is present |
| `extract_entities` | Groq LLM call, strips markdown fences, parses JSON |
| `store_neo4j` | MERGE nodes for each entity type, create relationships |
| `generate_embedding` | HuggingFace embed + normalize |
| `store_qdrant` | Upsert vector point with payload |
| `create_event` | Create Event node in Neo4j |

**Retrieval pipeline nodes** (`retrieval_pipeline.py`):

| Node | What it does |
|---|---|
| `validate_scope` | Logs consent scope |
| `generate_query_embedding` | Embed the query text |
| `parallel_search` | `asyncio.gather(neo4j.search(), qdrant.search())` |
| `hybrid_rank` | `HybridRanker.rank()` with configurable weights |
| `build_context` | Format top 8 results into a context string |
| `invoke_llm` | Groq with clinical summary system prompt |
| `attach_citations` | Build citation objects from top 5 ranked results |

### Hybrid Ranker (`backend/app/utils/hybrid_ranker.py`)

```
final_score = graph_score × 0.5 + vector_score × 0.3 + recency_score × 0.2

recency_score = exp(-0.01 × days_old)
  → today        ≈ 1.0
  → 1 year ago   ≈ 0.026
  → unknown date = 0.5
```

Scores from each source are min-max normalized before merging. Results with the same ID in both graph and vector results are deduplicated — the vector score is added to the graph entry.

### Consent Scopes

| Scope | Behavior |
|---|---|
| `full` | All patient data |
| `medication_only` | Only medication nodes and vectors |
| `disease_specific` | Filter by disease names list (`disease_filter` field) |
| `time_bound` | Filter by date range (`date_range_start` / `date_range_end`) |

### JWT Auth

- Algorithm: HS256
- Payload: `{ sub: user_id, role, email, exp }`
- Expiry: 60 minutes (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)
- Header: `Authorization: Bearer <token>`

### Groq Service (`backend/app/services/groq_service.py`)

Wraps the Groq Python SDK. Uses `tenacity` for retry: 3 attempts, exponential backoff 2–10 seconds. All calls are logged with `structlog` including latency in milliseconds. Temperature is always `0.0` for deterministic clinical output.

### FHIR R4 Bundle Structure

```
Bundle (type: transaction)
├── Patient resource          — patient_id as identifier
├── Condition × N             — one per condition, with ICD-10 code
├── MedicationStatement × N   — one per medication, with dosage text
└── DocumentReference         — LLM clinical summary, base64 encoded, contentType: text/plain
```

---

## 8. Frontend Deep Dive

### Routing (`src/App.jsx`)

```
/              → RootRedirect (→ /patient or /doctor based on role, or /landing if not authed)
/landing       → Landing (public)
/login         → Login (public)
/register      → Register (public)

/patient       → ProtectedRoute(role=patient) → AppLayout
  /patient           → HealthRecords
  /patient/chat      → PatientChat
  /patient/consents  → PatientConsents

/doctor        → ProtectedRoute(role=doctor) → AppLayout
  /doctor            → PatientLookup
  /doctor/chat       → ClinicalQuery
  /doctor/consents   → DoctorConsents
  /doctor/fhir       → FHIRExchange
```

### State Management (`src/store/authStore.js`)

Zustand store with three persisted keys in `localStorage`:
- `mg_token` — JWT access token
- `mg_user` — full user profile object

Actions: `login(email, password)`, `register(userData)`, `logout()`, `clearError()`.

On login, the store calls `/auth/login` to get the token, then immediately calls `/auth/me` to fetch the full profile.

### API Layer (`src/services/api.js`)

Axios instance with `baseURL = VITE_API_URL` (defaults to `http://localhost:8000`).

- **Request interceptor** — auto-attaches `Authorization: Bearer <token>` from `localStorage`.
- **Response interceptor** — on `401`, clears auth state and redirects to `/login`.

Exported API modules: `authAPI`, `memoryAPI`, `chatAPI`, `consentAPI`, `fhirAPI`, `healthAPI`.

### Design System

Custom Tailwind utility classes defined in `src/index.css` via `@layer components`:

| Class | Description |
|---|---|
| `.btn-primary` | Blue filled button |
| `.btn-secondary` | White bordered button |
| `.btn-danger` | Red filled button |
| `.btn-ghost` | Transparent hover button |
| `.card` | White rounded border shadow |
| `.card-hover` | Card with hover shadow transition |
| `.input` | Styled form input |
| `.badge`, `.badge-blue/green/yellow/red/gray` | Status badges |
| `.section-title`, `.page-title` | Typography helpers |

Custom Tailwind color palettes in `tailwind.config.js`:
- `brand-*` (50–900) — blue palette for primary actions
- `surface-*` (50–900) — slate palette for backgrounds and text

---

## 9. Database Schemas

### MongoDB Collections

**`users`**
```json
{
  "user_id": "uuid",
  "email": "string",
  "hashed_password": "bcrypt hash",
  "full_name": "string",
  "role": "patient | doctor",
  "specialization": "string | null",
  "created_at": "datetime"
}
```

**`consents`**
```json
{
  "consent_id": "uuid",
  "doctor_id": "uuid",
  "patient_id": "uuid",
  "purpose": "string",
  "requested_scope": "full | medication_only | disease_specific | time_bound",
  "disease_filter": ["string"] | null,
  "date_range_start": "datetime | null",
  "date_range_end": "datetime | null",
  "duration_hours": 24,
  "status": "pending | approved | denied | revoked",
  "created_at": "datetime",
  "valid_until": "datetime | null",
  "granted_at": "datetime | null"
}
```

**`audit_logs`**
```json
{
  "event_id": "uuid",
  "timestamp": "datetime",
  "action": "string",
  "patient_id": "uuid",
  "accessor_id": "uuid",
  "accessor_role": "string",
  "consent_id": "uuid | null",
  "details": {}
}
```

**`fhir_bundles`**
```json
{
  "bundle_id": "uuid",
  "bundle": { /* FHIR R4 Bundle JSON */ },
  "created_at": "datetime"
}
```

### Neo4j Graph Schema

```
Nodes:
  Patient    { patient_id, created_at }
  Symptom    { node_id, name, severity, duration, patient_id, timestamp, source }
  Medication { node_id, name, dosage, frequency, patient_id, timestamp, source }
  Condition  { node_id, name, icd10, status, patient_id, timestamp }
  Vital      { node_id, type, value, unit, status, patient_id, timestamp }
  Allergy    { node_id, substance, reaction, severity, patient_id, timestamp }
  Event      { event_id, patient_id, source, encounter_date, request_id }

Relationships:
  (Patient)-[:HAS_SYMPTOM]      → (Symptom)
  (Patient)-[:TAKES_MEDICATION] → (Medication)
  (Patient)-[:HAS_CONDITION]    → (Condition)
  (Patient)-[:HAS_VITAL]        → (Vital)
  (Patient)-[:HAS_ALLERGY]      → (Allergy)
  (Event)-[:PART_OF_EVENT]      → (Patient)
```

All entity `node_id` values are UUID5 derived from `patient_id + entity_type + entity_name`, ensuring MERGE idempotency.

### Qdrant Collection: `patient_memories`

- Vector: 384-dim, Cosine distance
- Payload fields:

| Field | Type | Purpose |
|---|---|---|
| `patient_id` | keyword | Data isolation per patient |
| `text` | string | Original ingested text |
| `source` | string | Origin of the record |
| `encounter_date` | datetime | For recency scoring |
| `has_medications` | bool | Filtered search |
| `has_conditions` | bool | Filtered search |
| `has_symptoms` | bool | Filtered search |
| `medication_names` | list | Scope filtering |
| `condition_names` | list | Scope filtering |
| `symptom_names` | list | Scope filtering |

---

## 10. API Reference

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/health` | None | Public | Service health check |
| POST | `/auth/register` | None | Public | Create patient or doctor account |
| POST | `/auth/login` | None | Public | Returns JWT token |
| GET | `/auth/me` | Bearer | Any | Current user profile |
| POST | `/memory/ingest` | Bearer | patient, doctor | Ingest health text → graph + vector |
| GET | `/memory/history/{patient_id}` | Bearer | patient, doctor | Last 20 audit events |
| POST | `/chat/` | Bearer | patient, doctor | Consent-gated RAG query |
| POST | `/consent/request` | Bearer | doctor | Request access to patient data |
| POST | `/consent/grant` | Bearer | patient | Approve or deny a consent request |
| GET | `/consent/active/{patient_id}` | Bearer | patient, doctor | List active consents |
| DELETE | `/consent/{consent_id}` | Bearer | patient | Revoke a consent |
| POST | `/fhir/exchange` | Bearer | doctor | Generate FHIR R4 bundle |
| GET | `/fhir/bundle/{bundle_id}` | Bearer | doctor | Retrieve a stored bundle |

Full interactive docs at `http://localhost:8000/docs`.

### Quick end-to-end test (curl)

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Register a patient
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@test.com","password":"test1234","full_name":"John Patient","role":"patient"}'

# 3. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@test.com","password":"test1234"}'
# → copy access_token

# 4. Ingest health data
curl -X POST http://localhost:8000/memory/ingest \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"<USER_ID>","text":"Patient has Type 2 Diabetes (E11.9). Taking Metformin 500mg twice daily. Allergic to penicillin.","source":"patient_input"}'
```

For the full consent → chat → FHIR flow, use the frontend at `http://localhost:5173`.

---

## 11. Testing

### Unit tests (no Docker required)

```bash
# From project root, with venv active
venv\Scripts\python.exe -m pytest tests/unit/ -v
```

Current unit test coverage:
- `test_hybrid_ranker.py` — empty inputs, deduplication, recency scoring, weight dominance, normalization
- `test_consent_service.py` — self-access, doctor access with various consent scopes, grant/deny/revoke flows
- `test_jwt_handler.py` — token creation, decoding, password hashing

### Integration tests (requires Docker services running)

```bash
venv\Scripts\python.exe -m pytest tests/integration/ -v -s -m integration
```

### pytest configuration

`pytest.ini` at the project root. `tests/conftest.py` inserts `backend/` into `sys.path` so all `app.*` imports resolve correctly without installing the package.

---

## 12. Known Issues

**Qdrant Docker healthcheck shows "unhealthy"**
The Qdrant image does not include `curl`, so the Docker healthcheck fails. The service itself works correctly on port 6333. Ignore the Docker status indicator.

**Backend must run from `backend/` directory**
`config.py` resolves `.env` relative to its own file path. If you start uvicorn from the project root, the path resolution breaks. Always `cd backend` first, or use the full path command shown in section 4.

**Login endpoint sends extra fields**
The `/auth/login` endpoint currently reuses the `UserCreate` model, which requires `full_name` and `role`. The frontend sends empty strings for these. It works but is a minor design smell — a dedicated `LoginRequest` model would be cleaner.

**Embedding model cold start**
The first request after starting the backend triggers the HuggingFace model download (~90 MB) if not cached. Subsequent starts use the local cache at `~/.cache/huggingface/`.

**Singleton pipelines**
`IngestionPipeline` and `RetrievalPipeline` are instantiated once at module load time (global `_pipeline` variable in each router). The embedding model stays in memory for the lifetime of the process — this is intentional for performance.

---

## 13. Tech Stack Summary

| Layer | Technology | Version |
|---|---|---|
| LLM | Groq Cloud — llama-3.3-70b-versatile | — |
| Embeddings | HuggingFace all-MiniLM-L6-v2 (local) | 384-dim |
| Orchestration | LangGraph + LangChain | 0.1.19 / 0.2.6 |
| FHIR | fhir.resources | 7.1.0 |
| Graph DB | Neo4j 5.18 (Docker) | driver 5.20.0 |
| Vector DB | Qdrant (Docker) | client 1.9.1 |
| Primary DB | MongoDB 7.0 (Docker) | motor 3.4.0 |
| Backend | FastAPI | 0.111.0 |
| Auth | JWT (python-jose) + bcrypt (passlib) | 3.3.0 / 4.1.3 |
| Frontend | React 19 + Vite | — |
| Styling | TailwindCSS | 3.4.4 |
| State | Zustand | 5.x |
| HTTP client | Axios | 1.x |
| Icons | lucide-react | — |
| Toasts | react-hot-toast | — |
| Router | react-router-dom | v6 |

---

*MedGraph AI v1.0 — TLE_Eliminators — Cognizant Technoverse 2026*
