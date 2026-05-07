# MedGraph AI — Infrastructure & Deployment

---

## AWS Services

| Service | Resource | Purpose |
|---------|----------|---------|
| **Bedrock** | Claude Sonnet 4.6 | Clinical RAG, entity extraction, summarization |
| **Bedrock** | Claude 3.7 Sonnet | Vaidya platform guide bot |
| **Bedrock** | Titan Text Embeddings v2 | 1024-dim vector embeddings |
| **Bedrock** | Guardrails | HIPAA content filtering, PHI leakage prevention |
| **DynamoDB** | 9 tables (medgraph-*) | Primary database for all structured data |
| **OpenSearch Serverless** | medgraph-vectors collection | Vector search (cosine similarity) |
| **S3** | medgraph-patient-documents bucket | Encrypted PDF storage (AES256) |
| **IAM** | SigV4 signing | Authentication for all AWS API calls |

---

## Environment Configuration

### Root `.env` (Backend)

```env
# AWS
AWS_REGION=us-east-1

# Bedrock LLM
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
VAIDYA_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
EMBEDDING_DIM=1024

# Bedrock Guardrails
BEDROCK_GUARDRAIL_ID=<your-guardrail-id>
BEDROCK_GUARDRAIL_VERSION=DRAFT

# DynamoDB
DYNAMODB_TABLE_PREFIX=medgraph

# OpenSearch Serverless
OPENSEARCH_ENDPOINT=<your-aoss-endpoint>.us-east-1.aoss.amazonaws.com
OPENSEARCH_INDEX=patient-memories

# S3
S3_DOCUMENTS_BUCKET=medgraph-patient-documents-<account-id>

# Neo4j Aura
NEO4J_URI=neo4j+s://<your-aura-instance>.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>
NEO4J_DATABASE=neo4j

# JWT
JWT_SECRET_KEY=<strong-random-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# App
APP_ENV=development
LOG_LEVEL=INFO

# Hybrid Search Weights
GRAPH_WEIGHT=0.5
VECTOR_WEIGHT=0.3
RECENCY_WEIGHT=0.2
TOP_K=10
```

### Frontend `.env`

```env
VITE_API_URL=http://localhost:8000
```

---

## Prerequisites

| Requirement | Purpose |
|-------------|---------|
| AWS CLI configured | boto3 uses CLI credentials (SigV4) |
| Python 3.11+ | Backend runtime |
| Node.js 18+ | Frontend build |
| Neo4j Aura account | Graph database (free tier available) |

---

## DynamoDB Tables

Create all tables with the `medgraph-` prefix:

| Table | Partition Key | Purpose |
|-------|--------------|---------|
| medgraph-users | user_id (S) | User accounts |
| medgraph-consents | consent_id (S) | Consent records |
| medgraph-audit-logs | log_id (S) | PHI access audit |
| medgraph-patient-documents | document_id (S) | Document metadata |
| medgraph-document-raw-texts | document_id (S) | Extracted PDF text |
| medgraph-fhir-document-references | reference_id (S) | FHIR references |
| medgraph-chat-sessions | session_id (S) | Chat history |
| medgraph-screening-results | screening_id (S) | AI screenings |
| medgraph-phi-redaction-maps | redaction_map_id (S) | Reversible redaction |

Use `backend/scripts/create_dynamodb_tables.py` to create all tables.

---

## OpenSearch Serverless Setup

1. Create a **VECTORSEARCH** collection named `medgraph-vectors`
2. Create index `patient-memories` with mapping:

```json
{
  "settings": {
    "index": { "knn": true }
  },
  "mappings": {
    "properties": {
      "embedding": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": { "name": "hnsw", "space_type": "cosinesimil", "engine": "nmslib" }
      },
      "patient_id": { "type": "keyword" },
      "text": { "type": "text" },
      "source": { "type": "keyword" },
      "encounter_date": { "type": "date" }
    }
  }
}
```

3. Configure data access policy to allow your IAM role/user.

---

## S3 Bucket Setup

```bash
aws s3 mb s3://medgraph-patient-documents-<account-id> --region us-east-1

# Enable default encryption
aws s3api put-bucket-encryption \
  --bucket medgraph-patient-documents-<account-id> \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket medgraph-patient-documents-<account-id> \
  --public-access-block-configuration '{
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
  }'
```

---

## Bedrock Guardrails Setup

Use `backend/scripts/setup_bedrock_guardrails.py` or create manually:

- **Denied Topics:** Medical diagnosis, unauthorized PHI access
- **Content Filters:** Hate, violence, sexual content, insults
- **Sensitive Info:** PII/PHI detection and blocking
- **Contextual Grounding:** Hallucination prevention (grounding threshold 0.7)

---

## Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Backend runs at `http://localhost:8000` (Swagger docs at `/docs`)  
Frontend runs at `http://localhost:5173`

---

## Seed Scripts

| Script | Purpose |
|--------|---------|
| `scripts/create_dynamodb_tables.py` | Create all DynamoDB tables |
| `scripts/seed_super_admin.py` | Create initial super admin user |
| `scripts/seed_test_users.py` | Create test users for all roles |
| `scripts/seed_demo_data.py` | Seed demo patient data |
| `scripts/seed_entities.py` | Seed Neo4j graph entities |
| `scripts/seed_patient_mrn.py` | Generate MRNs for existing patients |
| `scripts/setup_bedrock_guardrails.py` | Configure Bedrock Guardrails |

---

## Security

- **No API keys in code** — all AWS auth via IAM/SigV4
- **JWT tokens** — 60-minute expiry, HS256 signed
- **S3 encryption** — AES256 server-side
- **DynamoDB encryption** — AWS managed at rest
- **Neo4j Aura** — TLS encrypted (neo4j+s://)
- **OpenSearch Serverless** — TLS + SigV4 auth
- **CORS** — configured in FastAPI middleware
- **PHI never stored in graph/vector DB** — only redacted text
