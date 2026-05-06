# MedGraph AI — Complete Codebase Handoff Document

> **Project:** Healthcare Interoperability Platform  
> **Team:** TLE_Eliminators | KIT's College of Engineering, Kolhapur  
> **Hackathon:** Cognizant Technoverse 2026  
> **Stack:** Groq + LangGraph + Neo4j + Qdrant + MongoDB + FastAPI + React  
> **Status:** Backend fully implemented & running. Frontend fully implemented & running.

---

## 1. What This Project Does

MedGraph AI is a full-stack healthcare interoperability platform with three core flows:

```
FLOW 1 — PATIENT INGEST
  Patient submits free-text health info
  → Groq LLaMA 3.3 extracts structured medical entities (symptoms, meds, conditions, vitals, allergies)
  → Entities stored as Neo4j graph nodes + relationships
  → Full text embedded via HuggingFace all-MiniLM-L6-v2 (384-dim)
  → Embedding stored in Qdrant vector index
  → Audit log written to MongoDB

FLOW 2 — DOCTOR RAG CHAT
  Doctor submits clinical query about a patient
  → Consent check: is there an active approved consent? (MongoDB)
  → If yes: parallel search — Neo4j graph traversal + Qdrant vector search
  → Hybrid ranking: Graph×0.5 + Vector×0.3 + Recency×0.2
  → Top results → context → Groq LLM → clinical response with citations

FLOW 3 — FHIR EXCHANGE
  Doctor requests full patient record
  → Consent validated + scope enforced
  → Neo4j + Qdrant data retrieved
  → Groq LLM generates clinical summary
  → fhir.resources builds FHIR R4 Bundle (Patient, Condition, MedicationStatement, DocumentReference)
  → Bundle stored in MongoDB + returned to doctor
```

---

## 2. Environment & Prerequisites

| Requirement | Version | Status |
|---|---|---|
| Python | 3.12.7 | ✅ venv at `./venv/` |
| Node.js | 22.x | ✅ |
| npm | 11.x | ✅ |
| Docker Desktop | 29.x | ✅ Running |
| WSL2 | — | ✅ Enabled |

### Environment Variables (`.env` in project root)

```env
GROQ_API_KEY=<your-groq-api-key>
GROQ_MODEL=llama-3.3-70b-versatile
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=medgraph
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-neo4j-password>
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=patient_memories
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384
JWT_SECRET_KEY=<your-jwt-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
APP_ENV=development
LOG_LEVEL=INFO
GRAPH_WEIGHT=0.5
VECTOR_WEIGHT=0.3
RECENCY_WEIGHT=0.2
TOP_K=10
```

---

## 3. How to Start Everything

### Step 1 — Start Docker databases
```bash
# From project root: C:\Users\ravip\OneDrive\Desktop\MED_GRAPH
docker compose up -d
```
This starts:
- `medgraph-mongodb` on port 27017
- `medgraph-neo4j` on ports 7474 (browser) + 7687 (bolt)
- `medgraph-qdrant` on port 6333

### Step 2 — Activate virtual environment
```bash
venv\Scripts\activate
# Prompt should show (venv)
```

### Step 3 — Start FastAPI backend
```bash
# From project root
C:\Users\ravip\OneDrive\Desktop\MED_GRAPH\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
# Must run from: C:\Users\ravip\OneDrive\Desktop\MED_GRAPH\backend
```
Backend runs at: `http://localhost:8000`  
API docs at: `http://localhost:8000/docs`

### Step 4 — Start React frontend
```bash
cd frontend
npm run dev
```
Frontend runs at: `http://localhost:5173`

### Step 5 — Initialize DB schemas (first time only)
```bash
# With venv active, from project root
venv\Scripts\python.exe scripts/init_neo4j.py
venv\Scripts\python.exe scripts/init_qdrant.py
```

---

## 4. Project Directory Structure

```
MED_GRAPH/
├── .env                          # All secrets and config (DO NOT COMMIT)
├── .env.example                  # Template for .env
├── .gitignore
├── docker-compose.yml            # MongoDB + Neo4j + Qdrant containers
├── CODEBASE_HANDOFF.md           # This file
├── medgraph-ai-kiro-plan.md      # Original hackathon plan
│
├── backend/
│   ├── requirements.txt          # All Python dependencies
│   └── app/
│       ├── main.py               # FastAPI app factory, lifespan, routers
│       ├── config.py             # Pydantic settings, reads .env
│       ├── dependencies.py       # get_db(), get_current_user(), require_role()
│       │
│       ├── models/
│       │   ├── user.py           # UserRole, UserCreate, UserInDB, UserResponse, TokenResponse
│       │   ├── consent.py        # ConsentScope, ConsentStatus, ConsentRequest, ConsentRecord, ConsentGrant, ConsentCheckResult
│       │   └── medical.py        # MemoryIngestRequest/Response, ChatRequest/Response, FHIRExchangeRequest/Response
│       │
│       ├── routers/
│       │   ├── auth.py           # POST /auth/register, POST /auth/login, GET /auth/me
│       │   ├── memory.py         # POST /memory/ingest, GET /memory/history/{patient_id}
│       │   ├── chat.py           # POST /chat/
│       │   ├── consent.py        # POST /consent/request, POST /consent/grant, GET /consent/active/{id}, DELETE /consent/{id}
│       │   └── fhir.py           # POST /fhir/exchange, GET /fhir/bundle/{bundle_id}
│       │
│       ├── services/
│       │   ├── groq_service.py       # GroqService.invoke() — LLM calls with retry
│       │   ├── embedding_service.py  # EmbeddingService.embed/embed_batch() — HuggingFace local
│       │   ├── neo4j_service.py      # Neo4jService — store_entities, search, get_patient_summary, create_event_node
│       │   ├── qdrant_service.py     # QdrantService — index, search, delete_patient_data
│       │   ├── mongo_service.py      # ping_mongodb() health check
│       │   ├── consent_service.py    # ConsentService — create_request, process_grant, check_access, get_patient_consents, revoke
│       │   ├── fhir_service.py       # FHIRService — build_fhir_bundle, store_bundle
│       │   └── audit_service.py      # log_phi_access() — writes to MongoDB audit_logs collection
│       │
│       ├── pipelines/
│       │   ├── ingestion_pipeline.py  # LangGraph 6-node pipeline: validate→extract→neo4j→embed→qdrant→event
│       │   └── retrieval_pipeline.py  # LangGraph 7-node pipeline: validate→embed→parallel_search→rank→context→llm→citations
│       │
│       ├── prompts/
│       │   ├── entity_extraction.py   # ENTITY_EXTRACTION_SYSTEM_PROMPT + build_extraction_prompt()
│       │   └── clinical_summary.py    # CLINICAL_SUMMARY_SYSTEM_PROMPT + build_chat_prompt() + build_fhir_summary_prompt()
│       │
│       └── utils/
│           ├── hybrid_ranker.py   # HybridRanker.rank() — min-max normalize + merge + recency decay
│           └── jwt_handler.py     # create_access_token, decode_access_token, get_password_hash, verify_password
│
├── frontend/
│   ├── .env                      # VITE_API_URL=http://localhost:8000
│   ├── index.html                # Google Fonts (Inter + JetBrains Mono)
│   ├── vite.config.js            # Vite + React plugin + /api proxy
│   ├── tailwind.config.js        # Custom colors (brand, surface), animations, shadows
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx              # ReactDOM.createRoot + BrowserRouter + Toaster
│       ├── App.jsx               # All routes defined here
│       ├── index.css             # Tailwind + custom @layer components (btn-primary, card, input, badge, etc.)
│       │
│       ├── services/
│       │   └── api.js            # Axios instance + authAPI, memoryAPI, chatAPI, consentAPI, fhirAPI, healthAPI
│       │
│       ├── store/
│       │   └── authStore.js      # Zustand store: user, token, isAuthenticated, login(), register(), logout()
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── AppLayout.jsx      # Sidebar + <Outlet /> wrapper
│       │   │   ├── Sidebar.jsx        # Dark sidebar, role-aware nav, user pill
│       │   │   └── ProtectedRoute.jsx # Auth + role guard
│       │   └── ui/
│       │       ├── Spinner.jsx        # Animated SVG spinner (sm/md/lg/xl)
│       │       ├── EmptyState.jsx     # Empty state with icon, title, description, action
│       │       └── StatusDot.jsx      # Colored dot with optional pulse animation
│       │
│       └── pages/
│           ├── Landing.jsx            # Public hero page
│           ├── Login.jsx              # Dark glassmorphism login form
│           ├── Register.jsx           # Role selector (Patient/Doctor) + registration form
│           ├── patient/
│           │   ├── HealthRecords.jsx  # Text ingestion form + entity extraction results + history
│           │   ├── PatientChat.jsx    # Chat UI with citations and timing metrics
│           │   └── PatientConsents.jsx # Approve/deny/revoke consent requests
│           └── doctor/
│               ├── PatientLookup.jsx  # Consent request form with scope selector
│               ├── ClinicalQuery.jsx  # Consent-verified clinical chat
│               ├── DoctorConsents.jsx # Track own consent requests by patient
│               └── FHIRExchange.jsx   # Generate + view + download FHIR R4 bundles
│
├── scripts/
│   ├── init_neo4j.py    # Creates uniqueness constraints + patient_id indexes
│   └── init_qdrant.py   # Creates collection + payload indexes (patient_id, has_medications, etc.)
│
└── tests/
    ├── unit/            # Empty — ready for tests
    └── integration/     # Empty — ready for tests
```

---

## 5. API Endpoints Reference

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| POST | `/auth/register` | None | Public | Create patient or doctor account |
| POST | `/auth/login` | None | Public | Returns JWT token |
| GET | `/auth/me` | Bearer | Any | Get current user profile |
| POST | `/memory/ingest` | Bearer | patient, doctor | Ingest health text → graph + vector |
| GET | `/memory/history/{patient_id}` | Bearer | patient, doctor | Last 20 audit events |
| POST | `/chat/` | Bearer | patient, doctor | Consent-gated RAG query |
| POST | `/consent/request` | Bearer | doctor | Request access to patient data |
| POST | `/consent/grant` | Bearer | patient | Approve or deny consent |
| GET | `/consent/active/{patient_id}` | Bearer | patient, doctor | List consents |
| DELETE | `/consent/{consent_id}` | Bearer | patient | Revoke consent |
| POST | `/fhir/exchange` | Bearer | doctor | Generate FHIR R4 bundle |
| GET | `/fhir/bundle/{bundle_id}` | Bearer | doctor | Retrieve stored bundle |
| GET | `/health` | None | Public | Service health check |

---

## 6. Database Schemas

### MongoDB Collections
- `users` — user accounts (user_id, email, hashed_password, full_name, role, specialization)
- `consents` — consent records (consent_id, doctor_id, patient_id, status, requested_scope, valid_until, ...)
- `audit_logs` — PHI access log (event_id, timestamp, action, patient_id, accessor_id, accessor_role, ...)
- `fhir_bundles` — stored FHIR R4 bundles (bundle_id, bundle JSON, created_at)

### Neo4j Graph Schema
```
Nodes: Patient, Symptom, Medication, Condition, Vital, Allergy, Event

Relationships:
  (Patient)-[:HAS_SYMPTOM]->(Symptom)
  (Patient)-[:TAKES_MEDICATION]->(Medication)
  (Patient)-[:HAS_CONDITION]->(Condition)
  (Patient)-[:HAS_VITAL]->(Vital)
  (Patient)-[:HAS_ALLERGY]->(Allergy)
  (Event)-[:PART_OF_EVENT]->(Patient)

All nodes have: node_id (UUID5, unique), patient_id, timestamp, source
```

### Qdrant Collection: `patient_memories`
- Vector: 384-dim, Cosine distance
- Payload fields: patient_id (keyword), text, source, encounter_date (datetime), has_medications (bool), has_conditions (bool), has_symptoms (bool), medication_names (list), condition_names (list), symptom_names (list)

---

## 7. Key Implementation Details

### LangGraph Ingestion Pipeline (`ingestion_pipeline.py`)
6 nodes in sequence:
1. `validate_input` — check text length ≥ 10, patient_id present
2. `extract_entities` — Groq LLM call, parse JSON response, strip markdown fences
3. `store_neo4j` — MERGE nodes for each entity type, create relationships
4. `generate_embedding` — HuggingFace all-MiniLM-L6-v2, normalize to unit length
5. `store_qdrant` — upsert point with full payload
6. `create_event` — create Event node in Neo4j

On any node error: sets error field, continues (partial success OK).

### LangGraph Retrieval Pipeline (`retrieval_pipeline.py`)
7 nodes in sequence:
1. `validate_scope` — log consent scope
2. `generate_query_embedding` — embed the query
3. `parallel_search` — `asyncio.gather(neo4j.search(), qdrant.search())` simultaneously
4. `hybrid_rank` — HybridRanker.rank() with configurable weights
5. `build_context` — format top 8 results into context string
6. `invoke_llm` — Groq with clinical summary prompt
7. `attach_citations` — build citation objects from top 5 ranked results

### Hybrid Ranker (`hybrid_ranker.py`)
```
score = graph_score × 0.5 + vector_score × 0.3 + recency_score × 0.2

recency_score = exp(-0.01 × days_old)
  → today = ~1.0
  → 1 year ago = ~0.026
  → unknown date = 0.5

Scores are min-max normalized within each source before merging.
Duplicate IDs across graph + vector results are deduplicated (vector score added to graph entry).
```

### Consent Scopes
- `full` — all patient data
- `medication_only` — only medication nodes/vectors
- `disease_specific` — filter by disease names list
- `time_bound` — filter by date range

### FHIR R4 Bundle Structure
```
Bundle (type: transaction)
├── Patient resource (patient_id as identifier)
├── Condition resource × N (one per condition, with ICD-10 code)
├── MedicationStatement resource × N (one per medication, with dosage text)
└── DocumentReference (LLM clinical summary, base64 encoded, contentType: text/plain)
```

### JWT Auth
- Algorithm: HS256
- Payload: `{ sub: user_id, role, email, exp }`
- Expiry: 60 minutes
- Header: `Authorization: Bearer <token>`

---

## 8. Frontend Architecture

### State Management
- **Zustand** (`authStore.js`) — user, token, isAuthenticated
- Token persisted to `localStorage` as `mg_token`
- User profile persisted as `mg_user`

### API Layer (`api.js`)
- Axios instance with `baseURL = VITE_API_URL`
- Request interceptor: auto-attach Bearer token
- Response interceptor: on 401 → clear auth + redirect to `/login`

### Routing (`App.jsx`)
```
/              → RootRedirect (→ /patient or /doctor based on role)
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

### Design System (Tailwind `@layer components`)
Custom utility classes defined in `index.css`:
- `.btn-primary` — blue filled button
- `.btn-secondary` — white bordered button
- `.btn-danger` — red filled button
- `.btn-ghost` — transparent hover button
- `.card` — white rounded border shadow
- `.card-hover` — card with hover shadow transition
- `.input` — styled form input
- `.label` — form label
- `.badge`, `.badge-blue`, `.badge-green`, `.badge-yellow`, `.badge-red`, `.badge-gray`
- `.section-title`, `.page-title`

Custom Tailwind colors:
- `brand-*` (50–900) — blue palette for primary actions
- `surface-*` (50–900) — slate palette for backgrounds/text

---

## 9. Known Issues & Notes

1. **Qdrant healthcheck shows "unhealthy"** — This is a Docker healthcheck false alarm. The Qdrant image doesn't have `curl`. The service itself responds correctly on port 6333. Ignore the Docker status.

2. **Backend must run from `backend/` directory** — The `config.py` resolves `.env` as `../../../.env` relative to `backend/app/config.py`, which points to the project root. If you move files, update the `_ENV_FILE` path in `config.py`.

3. **Embedding model downloads on first run** — `all-MiniLM-L6-v2` (~90MB) downloads from HuggingFace on first `EmbeddingService()` instantiation. Cached in `~/.cache/huggingface/` after that.

4. **Singleton pipelines** — `IngestionPipeline` and `RetrievalPipeline` are instantiated once per router module load (global `_pipeline` variable). This means the embedding model loads once and stays in memory.

5. **Login endpoint quirk** — The `/auth/login` endpoint uses the `UserCreate` model which requires `full_name` and `role` fields. The frontend sends empty strings for these. This is a minor design issue — a dedicated `LoginRequest` model would be cleaner.

6. **No tests written yet** — `tests/unit/` and `tests/integration/` directories exist but are empty. The plan includes test specs in Phase 13.

7. **Frontend `.env`** — `frontend/.env` has `VITE_API_URL=http://localhost:8000`. For production, change this to your deployed backend URL.

---

## 10. What's Left To Build

Based on the original plan (`medgraph-ai-kiro-plan.md`):

- [ ] **Phase 12** — Backend Dockerfile + add backend/frontend to docker-compose.yml
- [ ] **Phase 13** — Unit tests (hybrid ranker, consent service) + integration tests (full ingest flow)
- [ ] **Frontend Dockerfile** — containerize the React app
- [ ] **README.md** — user-facing setup guide

Everything else from Phases 1–11 is complete and working.

---

## 11. Quick Test Sequence (End-to-End)

```bash
# 1. Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy","services":{"mongodb":true,"neo4j":true,"qdrant":true}}

# 2. Register patient
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@test.com","password":"test1234","full_name":"John Patient","role":"patient"}'

# 3. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@test.com","password":"test1234","full_name":"","role":"patient"}'
# Save the access_token

# 4. Ingest health data
curl -X POST http://localhost:8000/memory/ingest \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"<USER_ID>","text":"Patient has Type 2 Diabetes (E11.9). Taking Metformin 500mg twice daily. Allergic to penicillin.","source":"patient_input"}'

# 5. Register doctor + login + request consent + patient approves + chat + FHIR
# (Use the frontend UI at http://localhost:5173 for the full flow)
```

---

## 12. Tech Stack Summary

| Layer         | Technology                           | Version        | Notes                        |
| ---------------| --------------------------------------| ----------------| ------------------------------|
| LLM           | Groq Cloud (llama-3.3-70b-versatile) | —              | Fast inference, free tier    |
| Embeddings    | all-MiniLM-L6-v2 (HuggingFace local) | —              | 384-dim, no API cost         |
| Orchestration | LangGraph + LangChain                | 0.1.19 / 0.2.6 | Agentic state machines       |
| FHIR          | fhir.resources                       | 7.1.0          | R4 compliance                |
| Graph DB      | Neo4j 5.18 (Docker)                  | 5.20.0 driver  | Patient entity relationships |
| Vector DB     | Qdrant (Docker)                      | 1.9.1 client   | Semantic search              |
| Primary DB    | MongoDB 7.0 (Docker)                 | motor 3.4.0    | Users, consents, audit, FHIR |
| Backend       | FastAPI                              | 0.111.0        | Async, Python 3.12           |
| Auth          | JWT (python-jose + bcrypt)           | 3.3.0 / 4.1.3  | Role-based: patient/doctor   |
| Frontend      | React + Vite                         | 19.x / 8.x     | JSX only, no TypeScript      |
| Styling       | TailwindCSS                          | 3.4.4          | Custom design system         |
| State         | Zustand                              | —              | Auth store                   |
| HTTP          | Axios                                | —              | With interceptors            |
| Icons         | lucide-react                         | —              |                              |
| Toasts        | react-hot-toast                      | —              |                              |
| Router        | react-router-dom                     | v6             |                              |

---

*Generated: May 4, 2026 | MedGraph AI v1.0 | TLE_Eliminators*
