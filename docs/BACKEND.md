# MedGraph AI — Backend Architecture

---

## Overview

The backend is a **FastAPI** application running on **Uvicorn** (ASGI). It orchestrates AI pipelines via **LangGraph**, connects to three databases (DynamoDB, Neo4j Aura, OpenSearch Serverless), and uses **AWS Bedrock** for LLM inference and embeddings.

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory, router mounting, lifespan
│   ├── config.py            # Pydantic Settings (env vars)
│   ├── dependencies.py      # Auth guards, DB injection
│   ├── middleware/           # Custom middleware
│   ├── models/              # Pydantic request/response models
│   │   ├── user.py          # UserCreate, UserInDB, UserResponse, TokenResponse
│   │   ├── consent.py       # ConsentRequest, ConsentRecord, ConsentGrant
│   │   ├── medical.py       # ChatRequest/Response, MemoryIngest, FHIR models
│   │   ├── clinical.py      # Admission, VitalSign, Appointment
│   │   ├── hospital.py      # Hospital, Bed, Department
│   │   ├── rbac.py          # UserRole enum, Permission enum, ROLE_PERMISSIONS map
│   │   ├── screening.py     # Screening models (HITL workflow)
│   │   ├── finance_legal.py # Insurance, Scheme models
│   │   └── privacy.py       # Privacy policy text
│   ├── routers/             # 24 API router modules
│   ├── services/            # Business logic layer
│   │   ├── bedrock_service.py      # AWS Bedrock LLM (Claude + Guardrails)
│   │   ├── embedding_service.py    # Bedrock Titan embeddings
│   │   ├── dynamo_service.py       # DynamoDB abstraction
│   │   ├── neo4j_service.py        # Neo4j Aura graph operations
│   │   ├── opensearch_service.py   # OpenSearch vector operations
│   │   ├── document_service.py     # PDF processing + S3 storage
│   │   ├── consent_service.py      # Consent validation logic
│   │   ├── audit_service.py        # PHI access audit logging
│   │   ├── phi_redaction_service.py # HIPAA Safe Harbor redaction
│   │   ├── fhir_service.py         # FHIR R4 bundle builder
│   │   ├── screening_service.py    # Responsible AI screening
│   │   ├── chat_history_service.py # Session-based chat history
│   │   └── cache_service.py        # Response caching
│   ├── pipelines/           # LangGraph state machines
│   │   ├── ingestion_pipeline.py   # 7-stage ingestion
│   │   └── retrieval_pipeline.py   # 7-stage retrieval
│   ├── prompts/             # LLM prompt templates
│   │   ├── clinical_summary.py     # RAG + FHIR summary prompts
│   │   ├── entity_extraction.py    # Entity extraction prompt
│   │   └── responsible_ai.py       # Screening prompt
│   └── utils/
│       ├── jwt_handler.py   # JWT create/decode, password hash/verify
│       └── hybrid_ranker.py # Weighted hybrid ranking algorithm
├── scripts/                 # Seed data, setup scripts
└── requirements.txt
```

---

## Services

### Bedrock Service
- **Model:** `us.anthropic.claude-sonnet-4-6` (clinical RAG)
- **Guardrails:** HIPAA content filtering on input/output
- **Retry:** 3 attempts with exponential backoff (2-10s)
- **Features:** Multi-turn conversation, guardrail intervention detection

### Embedding Service
- **Model:** `amazon.titan-embed-text-v2:0`
- **Dimensions:** 1024
- **Usage:** Query embeddings + document embeddings

### DynamoDB Service
- Async-compatible via `run_in_executor`
- Handles Decimal ↔ float conversion
- Table prefix: `medgraph-*`

### Neo4j Service
- Async driver (`AsyncGraphDatabase`)
- Protocol: `neo4j+s://` (TLS, cloud)
- Operations: MERGE nodes, create relationships, patient summary queries

### OpenSearch Service
- AWS SigV4 authentication (no API keys)
- Collection type: VECTORSEARCH
- Index: `patient-memories` (1024-dim, cosine similarity)
- Payload: patient_id, text, source, encounter_date, medication/condition/symptom names

### Document Service
- PDF storage: S3 with AES256 encryption
- Text extraction: PyMuPDF
- Key structure: `patient-pdfs/{patient_id}/{document_id}/{filename}`
- Presigned URLs for patient download

---

## Pipelines

### Ingestion Pipeline (LangGraph)

```
validate_input → redact_phi → extract_entities → store_neo4j
  → generate_embedding → store_vectors → create_event
```

| Stage | Purpose |
|-------|---------|
| validate_input | Text ≥ 10 chars, patient_id present |
| redact_phi | HIPAA Safe Harbor (18 identifier types) |
| extract_entities | Bedrock Claude → symptoms, meds, conditions, vitals, allergies |
| store_neo4j | MERGE graph nodes with relationships |
| generate_embedding | Bedrock Titan 1024-dim on redacted text |
| store_vectors | Upsert into OpenSearch with metadata |
| create_event | Audit event node for traceability |

### Retrieval Pipeline (LangGraph)

```
validate_scope → generate_query_embedding → graph_search
  → hybrid_rank → build_context → invoke_llm → attach_citations
```

| Stage | Purpose |
|-------|---------|
| validate_scope | Log consent scope |
| generate_query_embedding | Embed query (1024-dim) |
| graph_search | Parallel Neo4j + OpenSearch search |
| hybrid_rank | Graph×0.5 + Vector×0.3 + Recency×0.2 |
| build_context | Format top 8 results |
| invoke_llm | Bedrock Claude with clinical prompt |
| attach_citations | Build citation objects from top 5 |

---

## Database Schemas

### DynamoDB Tables

| Table | Partition Key | Sort Key | GSIs |
|-------|--------------|----------|------|
| `medgraph-users` | user_id | — | email-index |
| `medgraph-consents` | consent_id | — | doctor-patient-index, patient-index |
| `medgraph-audit-logs` | log_id | — | — |
| `medgraph-patient-documents` | document_id | — | patient-index |
| `medgraph-document-raw-texts` | document_id | — | — |
| `medgraph-fhir-document-references` | reference_id | — | — |
| `medgraph-chat-sessions` | session_id | — | user-index |
| `medgraph-screening-results` | screening_id | — | patient-index, status-index |
| `medgraph-phi-redaction-maps` | redaction_map_id | — | — |

### Neo4j Graph Schema

**Nodes:**
- `Patient` {patient_id, created_at}
- `Symptom` {node_id, name, severity, duration, patient_id, timestamp, source}
- `Medication` {node_id, name, dosage, frequency, route, patient_id, timestamp, source}
- `Condition` {node_id, name, icd10_code, status, patient_id, timestamp}
- `Vital` {node_id, type, value, unit, status, patient_id, timestamp}
- `Allergy` {node_id, substance, reaction, severity, patient_id, timestamp}
- `Event` {event_id, patient_id, source, encounter_date, request_id}

**Relationships:**
- `(Patient)-[:HAS_SYMPTOM]->(Symptom)`
- `(Patient)-[:TAKES_MEDICATION]->(Medication)`
- `(Patient)-[:HAS_CONDITION]->(Condition)`
- `(Patient)-[:HAS_VITAL]->(Vital)`
- `(Patient)-[:HAS_ALLERGY]->(Allergy)`
- `(Patient)-[:PART_OF_EVENT]->(Event)`

### OpenSearch Vector Index

**Index:** `patient-memories`

| Field | Type | Purpose |
|-------|------|---------|
| patient_id | keyword | Filter by patient |
| entry_id | keyword | Unique entry ID |
| text | text | PHI-redacted clinical text |
| embedding | knn_vector (1024, cosine) | Semantic search |
| source | keyword | Origin (patient_input, pdf_upload) |
| encounter_date | date | Recency scoring |
| medication_names | keyword[] | Metadata filter |
| condition_names | keyword[] | Metadata filter |
| symptom_names | keyword[] | Metadata filter |

---

## Authentication Flow

1. User calls `POST /auth/login` with email + password
2. Server verifies bcrypt hash, generates JWT (HS256, 60-min expiry)
3. JWT payload: `{sub: user_id, role, email, hospital_id, department_id, permissions[]}`
4. Client sends `Authorization: Bearer <token>` on all subsequent requests
5. `get_current_user` dependency decodes token, fetches user from DynamoDB
6. `require_permission` checks if user has the required permission string

---

## Startup Health Check

On startup, the app verifies connectivity to all downstream services:
- DynamoDB (describe table)
- Neo4j Aura (RETURN 1)
- AWS Bedrock (list foundation models)
- OpenSearch Serverless (index exists)

Status is exposed at `GET /health`.
