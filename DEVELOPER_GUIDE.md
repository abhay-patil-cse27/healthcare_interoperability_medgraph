# MedGraph AI — Developer Guide

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| AWS CLI | v2 | Configured with valid credentials |
| Neo4j Aura | — | Free tier at aura.neo4j.io |

---

## Environment Setup

### 1. Configure `.env`

```bash
cp .env.example .env
```

Fill in the required values:

```env
# AWS (uses CLI credentials — no access keys needed in .env)
AWS_REGION=us-east-1

# Bedrock
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
VAIDYA_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
EMBEDDING_DIM=1024
BEDROCK_GUARDRAIL_ID=           # Optional — run setup_bedrock_guardrails.py
BEDROCK_GUARDRAIL_VERSION=DRAFT

# DynamoDB
DYNAMODB_TABLE_PREFIX=medgraph

# OpenSearch Serverless
OPENSEARCH_ENDPOINT=<your-endpoint>.us-east-1.aoss.amazonaws.com
OPENSEARCH_INDEX=patient-memories

# S3
S3_DOCUMENTS_BUCKET=medgraph-patient-documents-<account-id>

# Neo4j Aura
NEO4J_URI=neo4j+s://<instance>.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-password>
NEO4J_DATABASE=neo4j

# JWT
JWT_SECRET_KEY=<generate-a-strong-random-string>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# App
APP_ENV=development
LOG_LEVEL=INFO
GRAPH_WEIGHT=0.5
VECTOR_WEIGHT=0.3
RECENCY_WEIGHT=0.2
TOP_K=10
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 3. Create AWS Resources

```bash
# DynamoDB tables
python scripts/create_dynamodb_tables.py

# Bedrock Guardrails (optional but recommended)
python scripts/setup_bedrock_guardrails.py

# Seed super admin
python scripts/seed_super_admin.py

# Seed test users (all roles)
python scripts/seed_test_users.py
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

---

## Running the Project

### Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Frontend

```bash
cd frontend
npm run dev
```

- App: http://localhost:5173

---

## Project Structure

```
MedGraph/
├── .env                    # Root environment config
├── .env.example            # Template
├── backend/
│   ├── app/
│   │   ├── main.py         # App factory
│   │   ├── config.py       # Settings (pydantic-settings)
│   │   ├── dependencies.py # Auth guards
│   │   ├── models/         # Pydantic schemas
│   │   ├── routers/        # 24 API modules
│   │   ├── services/       # Business logic
│   │   ├── pipelines/      # LangGraph pipelines
│   │   ├── prompts/        # LLM prompts
│   │   └── utils/          # JWT, hybrid ranker
│   ├── scripts/            # Setup & seed scripts
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Routes
│   │   ├── pages/          # Role-based pages
│   │   ├── components/     # Shared components
│   │   └── store/          # Zustand state
│   └── package.json
├── docs/                   # Documentation
├── TECH_STACK.md           # Technology inventory
└── ARCHITECTURE_DIAGRAM.mmd # Mermaid diagram
```

---

## Adding a New Feature

### New API Endpoint

1. Create/update model in `backend/app/models/`
2. Create router in `backend/app/routers/your_feature.py`
3. Register in `backend/app/main.py`:
   ```python
   from app.routers import your_feature
   app.include_router(your_feature.router, prefix="/your-feature", tags=["Your Feature"])
   ```
4. Add permission to `backend/app/models/rbac.py` if needed
5. Map permission to roles in `ROLE_PERMISSIONS`

### New Frontend Page

1. Create page in `frontend/src/pages/your-role/YourPage.jsx`
2. Add route in `frontend/src/App.jsx`
3. Add to role redirect map in `RootRedirect()`

---

## Testing

```bash
cd backend
pytest                          # Run all tests
pytest -x                       # Stop on first failure
pytest tests/test_auth.py       # Specific file
pytest -k "test_login"          # Specific test
```

---

## Common Tasks

### Create a new user role

1. Add to `UserRole` enum in `backend/app/models/rbac.py`
2. Define permissions in `ROLE_PERMISSIONS` dict
3. Add route mapping in `frontend/src/App.jsx` `RootRedirect()`
4. Create dashboard page

### Add a new DynamoDB table

1. Add table creation to `backend/scripts/create_dynamodb_tables.py`
2. Add collection accessor to `backend/app/services/dynamo_service.py`
3. Run the script: `python scripts/create_dynamodb_tables.py`

### Modify LLM prompts

Prompts live in `backend/app/prompts/`:
- `entity_extraction.py` — What entities to extract from health text
- `clinical_summary.py` — How to answer clinical queries
- `responsible_ai.py` — Screening summary generation

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `bedrock_unhealthy` on startup | Check AWS CLI credentials: `aws sts get-caller-identity` |
| `neo4j_aura_unhealthy` | Verify NEO4J_URI and password in .env |
| `opensearch_unhealthy` | Check OPENSEARCH_ENDPOINT and IAM permissions |
| 401 on API calls | Token expired (60 min) — re-login |
| 403 on API calls | Missing permission — check RBAC docs |
| CORS errors in browser | Backend CORS is `allow_origins=["*"]` — check if backend is running |
| PDF upload fails | Check S3 bucket exists and IAM has PutObject permission |

---

## Useful Commands

```bash
# Check AWS identity
aws sts get-caller-identity

# List DynamoDB tables
aws dynamodb list-tables

# Check Bedrock model access
aws bedrock list-foundation-models --by-output-modality TEXT --query "modelSummaries[].modelId"

# Neo4j browser (Aura)
# Use the Aura console at https://console.neo4j.io

# OpenSearch dashboard
# Use the AWS Console → OpenSearch Serverless → Collections
```
