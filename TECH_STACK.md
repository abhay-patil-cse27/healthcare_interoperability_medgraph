# MedGraph AI — Tech Stack & Architecture

> A HIPAA-compliant, AI-powered healthcare interoperability platform built on AWS.

---

## AWS Services

| Service | Purpose |
|---------|---------|
| **Bedrock (Claude Sonnet 4.6)** | Primary LLM — entity extraction, clinical Q&A, summarization |
| **Bedrock (Claude 3.7 Sonnet)** | Vaidya Guide Bot (patient-facing assistant) |
| **Bedrock (Titan Text Embeddings v2)** | 1024-dim vector embeddings for semantic search |
| **Bedrock Guardrails** | HIPAA content filtering — blocks PHI leakage, unsafe medical advice, hallucinations |
| **DynamoDB** | Primary NoSQL database — users, consents, audit logs, chat sessions, documents |
| **OpenSearch Serverless** | Vector database (VECTORSEARCH collection) — semantic search over patient records |
| **S3** | Encrypted PDF storage for patient documents (AES256 server-side encryption) |
| **IAM + SigV4** | Authentication for all AWS service calls — no API keys, uses CLI credentials |

---

## Databases

| Database | Type | Purpose |
|----------|------|---------|
| **DynamoDB** | NoSQL (Key-Value) | Users, consents, audit logs, chat history, document metadata, screening results, FHIR references |
| **Neo4j Aura** | Graph DB (Cloud) | Clinical entity relationships — Patient → Condition, Medication, Symptom, Vital, Allergy |
| **OpenSearch Serverless** | Vector DB | Cosine-similarity search over 1024-dim patient record embeddings |

### DynamoDB Tables
- `medgraph-users` — User accounts (GSI: email-index)
- `medgraph-consents` — Consent records (GSI: doctor-patient-index, patient-index)
- `medgraph-audit-logs` — PHI access audit trail
- `medgraph-patient-documents` — Document metadata
- `medgraph-document-raw-texts` — Extracted PDF text
- `medgraph-fhir-document-references` — FHIR DocumentReference resources
- `medgraph-chat-sessions` — Conversation history
- `medgraph-screening-results` — Responsible AI screening
- `medgraph-phi-redaction-maps` — Reversible PHI redaction mappings

### Neo4j Graph Schema
- **Nodes:** Patient, Symptom, Medication, Condition, Vital, Allergy, Event
- **Relationships:** HAS_SYMPTOM, TAKES_MEDICATION, HAS_CONDITION, HAS_VITAL, HAS_ALLERGY, PART_OF_EVENT

---

## Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | **FastAPI** | 0.111.0 |
| ASGI Server | **Uvicorn** | 0.30.1 |
| AI Orchestration | **LangGraph** | 0.1.19 |
| LLM Abstraction | **LangChain** | 0.2.6 |
| AWS SDK | **boto3** | ≥1.34.0 |
| Graph Driver | **neo4j** (async) | 5.20.0 |
| Vector Client | **opensearch-py** | ≥2.4.0 |
| FHIR Standard | **fhir.resources** | 7.1.0 |
| Data Validation | **Pydantic** | 2.7.4 |
| Config Management | **Pydantic Settings** | 2.3.3 |
| Auth (JWT) | **python-jose** | 3.3.0 |
| Password Hashing | **bcrypt** | 4.1.3 |
| PDF Processing | **PyMuPDF** | 1.24.5 |
| Structured Logging | **structlog** | 24.2.0 |
| Retry Logic | **tenacity** | 8.3.0 |
| HTTP Client | **httpx** | 0.27.0 |
| Testing | **pytest** + pytest-asyncio | 8.2.2 |

---

## Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| UI Library | **React** | 19.2.5 |
| Build Tool | **Vite** | 8.0.10 |
| Routing | **react-router-dom** | 6.30.3 |
| State Management | **Zustand** | 5.0.12 |
| HTTP Client | **Axios** | 1.16.0 |
| Styling | **TailwindCSS** | 3.4.4 |
| UI Components | **@headlessui/react** | 2.2.10 |
| Icons | **lucide-react** | 1.14.0 |
| Charts | **Recharts** | 3.8.1 |
| Markdown Rendering | **react-markdown** | 10.1.0 |
| Notifications | **react-hot-toast** | 2.6.0 |
| 3D Globe | **cobe** | 2.0.1 |
| Linting | **ESLint** | 10.2.1 |

---

## AI/ML Pipeline Architecture

### Ingestion Pipeline (LangGraph — 7 stages)

```
Input Text → PHI Redaction → Entity Extraction (Bedrock Claude)
  → Store in Neo4j → Generate Embedding (Bedrock Titan)
  → Store in OpenSearch → Create Audit Event
```

1. **validate_input** — Check text length, patient_id
2. **redact_phi** — HIPAA Safe Harbor de-identification (18 identifier types)
3. **extract_entities** — Bedrock Claude extracts symptoms, medications, conditions, vitals, allergies
4. **store_neo4j** — MERGE entities as graph nodes with relationships
5. **generate_embedding** — Bedrock Titan (1024-dim) on redacted text
6. **store_vectors** — Upsert into OpenSearch with metadata payload
7. **create_event** — Audit event node for traceability

### Retrieval Pipeline (LangGraph — 7 stages)

```
Query → Embed → Parallel Search (Neo4j + OpenSearch)
  → Hybrid Rank → Build Context → LLM Response → Citations
```

1. **validate_scope** — Verify consent scope
2. **generate_query_embedding** — Embed the query
3. **parallel_search** — Simultaneous Neo4j graph + OpenSearch vector search
4. **hybrid_rank** — Weighted scoring: Graph (0.5) + Vector (0.3) + Recency (0.2)
5. **build_context** — Format top 8 results
6. **invoke_llm** — Bedrock Claude with clinical prompt
7. **attach_citations** — Build citation objects from ranked results

---

## Authentication & Authorization

| Mechanism | Details |
|-----------|---------|
| **JWT Tokens** | HS256, 60-min expiry, payload: user_id, role, email |
| **Password Hashing** | bcrypt via passlib |
| **RBAC** | 16 roles: patient, doctor, surgeon, nurse, pharmacist, admin, etc. |
| **Consent-Gated Access** | Doctors need active patient consent to access records |
| **Consent Scopes** | full, medication_only, disease_specific, time_bound |

---

## Compliance & Security

| Feature | Implementation |
|---------|---------------|
| **HIPAA Safe Harbor** | PHI redaction before any LLM processing (18 identifier types) |
| **Bedrock Guardrails** | Input/output filtering for PHI leakage, unsafe advice, hallucinations |
| **Audit Logging** | Every PHI access logged to DynamoDB with structured metadata |
| **Encrypted Storage** | S3 AES256 server-side encryption for patient documents |
| **FHIR R4** | Standardized health data exchange (Patient, Condition, MedicationStatement, DocumentReference) |
| **HITL Validation** | Human-in-the-Loop dashboard for AI output review |
| **Reversible Redaction** | PHI redaction maps stored separately for authorized re-association |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend (Vite + TailwindCSS + Zustand)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Axios + JWT Bearer Token
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI Backend (Uvicorn)                                       │
│                                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────────┐ │
│  │ Auth     │  │ Consent      │  │ Ingestion Pipeline        │ │
│  │ Router   │  │ Router       │  │ (LangGraph)               │ │
│  └────┬─────┘  └──────┬───────┘  │  PHI Redact → Extract    │ │
│       │               │          │  → Neo4j → Embed → AOSS  │ │
│       ▼               ▼          └───────────────────────────┘ │
│  ┌─────────┐   ┌──────────┐   ┌───────────────────────────┐   │
│  │DynamoDB │   │DynamoDB  │   │ Retrieval Pipeline        │   │
│  │(users)  │   │(consents)│   │ (LangGraph)               │   │
│  └─────────┘   └──────────┘   │  Neo4j + AOSS → Rank     │   │
│                                │  → Bedrock LLM → Cite    │   │
│  ┌──────────────────────┐     └───────────────────────────┘   │
│  │ Document Service     │                                      │
│  │  S3 (PDFs) + DynamoDB│                                      │
│  └──────────────────────┘                                      │
└─────────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌────────────┐  ┌─────────────┐  ┌────────────┐
   │ AWS Bedrock│  │ Neo4j Aura  │  │ OpenSearch │
   │ Claude +   │  │ (Graph DB)  │  │ Serverless │
   │ Titan +    │  │             │  │ (Vector DB)│
   │ Guardrails │  │             │  │            │
   └────────────┘  └─────────────┘  └────────────┘
```

---

## User Roles & Dashboards

| Role | Dashboard |
|------|-----------|
| Patient | Health records, chat, consents, document upload |
| Doctor / Surgeon | Patient lookup, clinical query, FHIR exchange, screening inbox |
| Nurse / Ward Incharge | Nurse station |
| Pharmacist | Pharmacist console |
| OPD / IPD Staff | OPD/IPD dashboards |
| Insurance / Scheme Officer | Finance dashboards |
| Police Interface | MLC (Medico-Legal Case) dashboard |
| HITL Validator | AI output review dashboard |
| Hospital Admin | Hospital management |
| Super Admin / Govt Admin | System-wide administration |

---

## Development & Tooling

| Tool | Purpose |
|------|---------|
| **Python 3.11+** | Backend runtime |
| **Node.js** | Frontend build |
| **Vite** | Dev server + HMR + production builds |
| **ESLint** | Frontend code quality |
| **pytest** | Backend testing (async support) |
| **structlog** | Structured JSON logging |
| **pydantic-settings** | Type-safe environment config |
