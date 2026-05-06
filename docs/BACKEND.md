# Backend Architecture

> FastAPI · Python 3.11 · LangGraph · Groq LLM · MongoDB · Neo4j · Qdrant

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app factory, middleware, router registration
│   ├── config.py                  # Pydantic Settings (env-based configuration)
│   ├── dependencies.py            # DI: get_db, get_current_user, require_permission
│   ├── __init__.py
│   │
│   ├── models/                    # Pydantic models & enums
│   │   ├── rbac.py                # 17 roles, 50+ permissions, ROLE_PERMISSIONS map
│   │   ├── user.py                # User registration/login models
│   │   ├── medical.py             # ChatRequest, ChatResponse, MemoryIngest models
│   │   ├── consent.py             # ConsentRequest, ConsentRecord, ConsentGrant
│   │   ├── screening.py           # ScreeningSummary, HITL models, DoctorScreeningView
│   │   ├── clinical.py            # Clinical data models
│   │   ├── hospital.py            # Hospital, Department, Bed models
│   │   ├── finance_legal.py       # Insurance claims, MLC records
│   │   └── privacy.py            # HIPAA/DPDP compliance models
│   │
│   ├── routers/                   # API endpoint handlers (22 routers)
│   │   ├── auth.py                # POST /auth/register, /auth/login, GET /auth/me
│   │   ├── chat.py                # POST /chat/, session CRUD, cache stats
│   │   ├── consent.py             # Consent request/grant/revoke/check
│   │   ├── screening.py           # Responsible AI: HITL queue, edit/accept/reject/escalate
│   │   ├── documents.py           # PDF upload, viewing, FHIR, trigger screening
│   │   ├── memory.py              # Health text ingestion
│   │   ├── fhir.py                # FHIR R4 bundle generation
│   │   ├── admin.py               # Super admin: hospitals, users, stats
│   │   ├── hospital.py            # Hospital admin: departments, staff
│   │   ├── patient.py             # Patient search (name/MRN/phone/ABHA)
│   │   ├── profile.py             # Self-service profile management
│   │   ├── nurse.py               # Vitals logging, ward management
│   │   ├── prescription.py        # Prescription CRUD, dispensing
│   │   ├── opd.py                 # OPD appointments, queue management
│   │   ├── ipd.py                 # IPD admissions, discharge, beds
│   │   ├── insurance.py           # Insurance claims lifecycle
│   │   ├── scheme.py              # PM-JAY/MPJAY eligibility, disbursement
│   │   ├── mlc.py                 # Medico-legal case records
│   │   ├── legal.py               # Privacy policy, compliance
│   │   ├── ward_bot.py            # IoT ward bot automations
│   │   ├── notifications.py       # Push notifications
│   │   └── activity_log.py        # Activity/audit log viewer
│   │
│   ├── services/                  # Business logic layer
│   │   ├── groq_service.py        # LLM invocation (Groq SDK, retry, multi-turn)
│   │   ├── embedding_service.py   # Sentence-transformers embedding (MiniLM-L6-v2)
│   │   ├── neo4j_service.py       # Graph DB: entity storage, search, patient summary
│   │   ├── qdrant_service.py      # Vector DB: index, search, delete
│   │   ├── mongo_service.py       # MongoDB utilities
│   │   ├── consent_service.py     # Consent check, grant, revoke logic
│   │   ├── chat_history_service.py# Session + message persistence
│   │   ├── cache_service.py       # Response caching (MongoDB-backed)
│   │   ├── audit_service.py       # PHI access audit logging
│   │   ├── fhir_service.py        # FHIR R4 bundle builder
│   │   ├── screening_service.py   # Antigravity Agent pipeline orchestration
│   │   ├── document_service.py    # PDF parse, GridFS storage, FHIR DocumentReference
│   │   └── phi_redaction_service.py # HIPAA Safe Harbor PHI de-identification
│   │
│   ├── pipelines/                 # LangGraph-based AI pipelines
│   │   ├── ingestion_pipeline.py  # PHI redact → extract → Neo4j + Qdrant
│   │   └── retrieval_pipeline.py  # Embed → parallel search → rank → LLM
│   │
│   ├── prompts/                   # LLM system prompts
│   │   ├── clinical_summary.py    # Chat + FHIR summary prompts
│   │   ├── entity_extraction.py   # PII-free entity extraction prompt
│   │   └── responsible_ai.py      # Antigravity Agent (strictly word-bounded)
│   │
│   ├── utils/
│   │   ├── jwt_handler.py         # JWT encode/decode
│   │   └── hybrid_ranker.py       # Graph + vector score fusion
│   │
│   └── middleware/
│       └── __init__.py
│
├── scripts/                       # Database seeding scripts
│   ├── seed_super_admin.py
│   ├── seed_test_users.py
│   ├── seed_entities.py
│   ├── seed_all_entities.py
│   ├── seed_patient_mrn.py
│   └── fix_permissions.py
│
├── Dockerfile
└── requirements.txt
```

---

## Core Services

### 1. Groq LLM Service (`groq_service.py`)
- Wraps Groq SDK with retry (exponential backoff, 3 attempts)
- Supports multi-turn conversation history
- Temperature control (0.0 for clinical, 0.3 for conversational)
- Structured logging with latency, token counts

### 2. Ingestion Pipeline (`ingestion_pipeline.py`)
LangGraph state machine:
```
validate → PHI_REDACT → extract_entities → store_neo4j → embed → store_qdrant → create_event
```
- **PHI Redaction** runs FIRST — LLM never sees raw PII
- Post-extraction PII scrub (defense-in-depth)
- Entities stored in Neo4j, embeddings in Qdrant
- Event node created for audit linkage

### 3. Retrieval Pipeline (`retrieval_pipeline.py`)
LangGraph state machine:
```
validate_scope → embed_query → parallel_search(Neo4j + Qdrant) → hybrid_rank → build_context → invoke_llm → attach_citations
```
- Hybrid ranking: graph_weight (0.5) + vector_weight (0.3) + recency_weight (0.2)
- Top-K configurable (default 10)
- Citations only attached for sources the LLM actually referenced

### 4. Screening Service (`screening_service.py`)
Full Responsible AI pipeline:
```
consent_gate → parse_abnormalities → LLM_screening → persist → audit
```
- Deterministic regex-based abnormality detection (30+ lab parameters)
- LLM generates strictly word-bounded summary
- HITL validation workflow (edit/accept/reject/escalate)
- Time-bound consent for doctor access

### 5. Document Service (`document_service.py`)
- PDF text extraction (PyMuPDF)
- Section-priority parser (HIGH: interpretations/notes, MEDIUM: lab values, LOW: demographics)
- GridFS storage for original PDFs
- FHIR R4 DocumentReference creation
- Section-aware chunking (never splits high-priority sections)

### 6. PHI Redaction Service (`phi_redaction_service.py`)
HIPAA Safe Harbor de-identification:
- Patient name → `[PATIENT]`
- DOB → `[DOB_REDACTED]`
- Phone → `[PHONE_REDACTED]`
- Address → `[ADDRESS_REDACTED]`
- Pin code → `[PINCODE_REDACTED]`
- VID/PID → `[LAB_ID_REDACTED]`
- Doctor name → `[DOCTOR_REDACTED]`
- Reg number → `[REG_REDACTED]`
- Lab/Hospital → `[LAB_REDACTED]`
- Email, URLs, IPs → redacted

**Preserved**: Age, gender, all clinical values, medical terminology

### 7. Consent Service (`consent_service.py`)
- Scoped consent: full, disease_specific, time_bound, medication_only
- Time-limited access (configurable hours)
- Patient self-access always allowed
- Consent check on every data access

### 8. Chat History Service (`chat_history_service.py`)
- Session-based conversations (MongoDB)
- Windowed history for LLM context (last 6 turns)
- Full thread retrieval for UI display
- Session close/archive (soft delete)

---

## Configuration

All configuration via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Groq API key (required) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection |
| `MONGODB_DB` | `medgraph` | Database name |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `medgraph123` | Neo4j password |
| `QDRANT_HOST` | `localhost` | Qdrant host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `QDRANT_COLLECTION` | `patient_memories` | Vector collection name |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `EMBEDDING_DIM` | `384` | Embedding dimensions |
| `JWT_SECRET_KEY` | — | JWT signing secret (required) |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token TTL |
| `GRAPH_WEIGHT` | `0.5` | Hybrid search: graph weight |
| `VECTOR_WEIGHT` | `0.3` | Hybrid search: vector weight |
| `RECENCY_WEIGHT` | `0.2` | Hybrid search: recency weight |
| `TOP_K` | `10` | Search results limit |

---

## Database Collections (MongoDB)

| Collection | Purpose |
|-----------|---------|
| `users` | All platform users (patients, doctors, admins, etc.) |
| `consents` | Consent records (request, grant, revoke) |
| `chat_sessions` | Chat session metadata |
| `chat_messages` | Individual chat messages |
| `response_cache` | LLM response cache |
| `audit_logs` | PHI access audit trail |
| `screening_summaries` | AI screening results + HITL status |
| `doctor_screening_consents` | Time-bound consent for doctor screening access |
| `patient_documents` | Document metadata (uploaded PDFs) |
| `document_raw_texts` | Extracted text + priority sections |
| `phi_redaction_maps` | Reversible PHI redaction mappings |
| `fhir_bundles` | Generated FHIR R4 bundles |
| `fhir_document_references` | FHIR DocumentReference resources |
| `insurance_claims` | Insurance claim lifecycle |
| `mrn_counters` | MRN sequence counters per hospital |
| `notifications` | User notifications |
| `hospitals` | Hospital registry |

---

## Neo4j Graph Schema

```
(:Patient {patient_id, created_at})
  -[:HAS_SYMPTOM]->   (:Symptom {name, severity, duration, timestamp})
  -[:TAKES_MEDICATION]->(:Medication {name, dosage, frequency, timestamp})
  -[:HAS_CONDITION]->  (:Condition {name, icd10, status, timestamp})
  -[:HAS_VITAL]->      (:Vital {type, value, unit, status, timestamp})
  -[:HAS_ALLERGY]->    (:Allergy {substance, reaction, severity, timestamp})

(:Event {event_id, request_id, source, timestamp})
  -[:PART_OF_EVENT]->  (:Patient)
```

**Note**: No PII stored in graph nodes. Only clinical entities + pseudonymized patient_id (UUID).

---

## Qdrant Vector Schema

```json
{
  "patient_id": "uuid",
  "entry_id": "uuid",
  "text": "PHI-redacted clinical text",
  "source": "pdf_upload:doc_id:section_id",
  "encounter_date": "ISO datetime",
  "has_medications": true,
  "has_conditions": false,
  "medication_names": ["metformin"],
  "condition_names": ["diabetes"],
  "symptom_names": []
}
```

**Note**: The `text` field contains only PHI-redacted content. No PII in the vector store.
