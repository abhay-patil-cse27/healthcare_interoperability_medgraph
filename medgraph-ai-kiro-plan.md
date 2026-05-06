# MedGraph AI — Kiro Implementation Plan
**Healthcare Interoperability Platform | Cognizant Technoverse 2026**
**Team: TLE_Eliminators | KIT's College of Engineering, Kolhapur**

---

## Document Conventions
- 🔵 = Flow 1 — Patient Memory Ingestion
- 🟢 = Flow 2 — Consent-Gated RAG Chat
- 🟠 = Flow 3 — FHIR Bundle Generation & Exchange
- 📁 = File to create
- 🤖 = Kiro agent instruction
- ✅ = Validation checkpoint

---

## Project Understanding

**Problem Statement:** Enable secure, consent-based sharing of patient records across providers and payers using FHIR standards.

**What we're building:**
A full-stack healthcare interoperability platform where:
- Patients own and control their health data
- Doctors request access via explicit consent mechanism
- Data is stored as a knowledge graph (Neo4j) + semantic vectors (Qdrant)
- All queries are consent-scoped — doctors only see what patients approve
- Output is a standards-compliant FHIR R4 bundle shareable across any provider

**Three Core Flows:**

```
🔵 FLOW 1 — INGEST
Patient submits health text
  → Groq LLM extracts medical entities (symptoms, meds, conditions, vitals)
  → Entities stored as Neo4j graph nodes + relationships
  → Text embedded via HuggingFace all-MiniLM-L6-v2
  → Embedding stored in Qdrant vector index
  → Metadata stored in MongoDB

🟢 FLOW 2 — CHAT
Doctor submits query about patient
  → Consent check: is there an active approved consent? (MongoDB)
  → If yes: parallel search — Neo4j graph traversal + Qdrant vector search
  → Hybrid ranking: Graph×0.5 + Vector×0.3 + Recency×0.2
  → Top results → context → Groq LLM → clinical response
  → Citations attached, audit log written

🟠 FLOW 3 — FHIR EXCHANGE
Doctor requests full patient record
  → Consent validated + scope enforced
  → Neo4j + Qdrant data retrieved
  → Groq LLM generates clinical summary
  → fhir.resources builds FHIR R4 Bundle
  → Bundle stored in MongoDB + returned to doctor
```

---

## Finalized Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| LLM | Groq Cloud (llama-3.3-70b-versatile) | Fast inference, free tier |
| Embeddings | all-MiniLM-L6-v2 (HuggingFace local) | 384-dim, no API cost |
| Orchestration | LangGraph + LangChain | Agentic state machines |
| FHIR | fhir.resources (Python lib) | R4 compliance |
| Graph DB | Neo4j 5.x (Docker) | Patient entity relationships |
| Vector DB | Qdrant (Docker) | Semantic search |
| Primary DB | MongoDB (Docker) | Users, consents, audit logs, FHIR docs |
| Backend | FastAPI (Python 3.11) | Async, fast |
| Auth | JWT (python-jose + bcrypt) | Role-based: patient / doctor / admin |
| Frontend | React + Vite + TailwindCSS | |
| Infra | Docker Compose | Single command startup |

---

## Repository Structure

```
medgraph-ai/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── memory.py
│   │   │   ├── chat.py
│   │   │   ├── consent.py
│   │   │   └── fhir.py
│   │   ├── services/
│   │   │   ├── groq_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── neo4j_service.py
│   │   │   ├── qdrant_service.py
│   │   │   ├── mongo_service.py
│   │   │   ├── consent_service.py
│   │   │   ├── fhir_service.py
│   │   │   └── audit_service.py
│   │   ├── pipelines/
│   │   │   ├── ingestion_pipeline.py
│   │   │   └── retrieval_pipeline.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── consent.py
│   │   │   └── medical.py
│   │   ├── prompts/
│   │   │   ├── entity_extraction.py
│   │   │   └── clinical_summary.py
│   │   ├── middleware/
│   │   │   └── auth_middleware.py
│   │   └── utils/
│   │       ├── hybrid_ranker.py
│   │       └── jwt_handler.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PatientPortal/
│   │   │   ├── DoctorDashboard/
│   │   │   └── ConsentManager/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── store/
│   ├── package.json
│   └── Dockerfile
└── scripts/
    ├── init_neo4j.py
    └── init_qdrant.py
```

---

# PHASE 1: Project Foundation

## Objective
Set up the complete project scaffold, Docker infrastructure, environment configuration, and verify all services are healthy before writing any application code.

---

### Step 1.1 — Initialize Repository

🤖 **Kiro Prompt:**
```
Create the full medgraph-ai project directory structure exactly as shown in the repository structure above. Create all directories and empty __init__.py files where needed. Run these commands:

mkdir medgraph-ai && cd medgraph-ai
git init
git checkout -b main
mkdir -p backend/app/{routers,services,pipelines,models,prompts,middleware,utils}
mkdir -p backend/app/routers backend/app/services backend/app/pipelines
mkdir -p backend/app/models backend/app/prompts backend/app/middleware backend/app/utils
mkdir -p frontend/src/{components/{PatientPortal,DoctorDashboard,ConsentManager},pages,hooks,services,store}
mkdir -p scripts
touch backend/app/__init__.py
touch backend/app/routers/__init__.py backend/app/services/__init__.py
touch backend/app/pipelines/__init__.py backend/app/models/__init__.py
touch backend/app/prompts/__init__.py backend/app/middleware/__init__.py backend/app/utils/__init__.py
```

---

### Step 1.2 — Docker Compose

📁 **File:** `docker-compose.yml`

🤖 **Kiro Prompt:**
```
Create docker-compose.yml with the following services:

1. mongodb: mongo:7.0, port 27017, volume mongo_data, env MONGO_INITDB_DATABASE=medgraph
2. neo4j: neo4j:5.18, ports 7474 and 7687, env NEO4J_AUTH=neo4j/medgraph123, NEO4J_PLUGINS=["apoc"], volume neo4j_data
3. qdrant: qdrant/qdrant:latest, port 6333, volume qdrant_data

All services on a custom network called medgraph-network.
Include named volumes for all three.
Add healthchecks for each service.
```

```yaml
version: "3.9"

services:
  mongodb:
    image: mongo:7.0
    container_name: medgraph-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: medgraph
    volumes:
      - mongo_data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - medgraph-network

  neo4j:
    image: neo4j:5.18
    container_name: medgraph-neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/medgraph123
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_dbms_security_procedures_unrestricted: apoc.*
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "medgraph123", "RETURN 1"]
      interval: 15s
      timeout: 10s
      retries: 10
    networks:
      - medgraph-network

  qdrant:
    image: qdrant/qdrant:latest
    container_name: medgraph-qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - medgraph-network

volumes:
  mongo_data:
  neo4j_data:
  qdrant_data:

networks:
  medgraph-network:
    driver: bridge
```

---

### Step 1.3 — Environment Configuration

📁 **File:** `.env.example`

🤖 **Kiro Prompt:**
```
Create .env.example with all required environment variables. Then create .env by copying .env.example and filling in the actual values (except secrets which user will fill).
```

```env
# ─── Groq ─────────────────────────────────────────────
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# ─── MongoDB ──────────────────────────────────────────
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=medgraph

# ─── Neo4j ────────────────────────────────────────────
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=medgraph123

# ─── Qdrant ───────────────────────────────────────────
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=patient_memories

# ─── Embedding ────────────────────────────────────────
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384

# ─── JWT ──────────────────────────────────────────────
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# ─── App ──────────────────────────────────────────────
APP_ENV=development
LOG_LEVEL=INFO

# ─── Hybrid Search Weights ────────────────────────────
GRAPH_WEIGHT=0.5
VECTOR_WEIGHT=0.3
RECENCY_WEIGHT=0.2
TOP_K=10
```

---

### Step 1.4 — Backend Requirements

📁 **File:** `backend/requirements.txt`

```txt
# Web Framework
fastapi==0.111.0
uvicorn[standard]==0.30.1

# AI / LLM
groq==0.9.0
langchain==0.2.6
langchain-community==0.2.6
langgraph==0.1.19
langchain-core==0.2.10
sentence-transformers==3.0.1

# Databases
motor==3.4.0
pymongo==4.7.3
neo4j==5.20.0
qdrant-client==1.9.1

# FHIR
fhir.resources==7.1.0

# Auth
python-jose[cryptography]==3.3.0
bcrypt==4.1.3
passlib[bcrypt]==1.7.4
python-multipart==0.0.9

# Data / Utils
pydantic==2.7.4
pydantic-settings==2.3.3
python-dotenv==1.0.1
structlog==24.2.0
tenacity==8.3.0
numpy==1.26.4
httpx==0.27.0

# Testing
pytest==8.2.2
pytest-asyncio==0.23.7
pytest-mock==3.14.0
```

---

### Step 1.5 — App Config

📁 **File:** `backend/app/config.py`

🤖 **Kiro Prompt:**
```
Create backend/app/config.py using pydantic-settings. Load all variables from .env file. Create a cached get_settings() function using lru_cache. Include all variables from .env.example mapped to proper Python types.
```

```python
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Groq
    groq_api_key: str = Field(env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")

    # MongoDB
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_db: str = Field(default="medgraph", env="MONGODB_DB")

    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="medgraph123", env="NEO4J_PASSWORD")

    # Qdrant
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_collection: str = Field(default="patient_memories", env="QDRANT_COLLECTION")

    # Embedding
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=384, env="EMBEDDING_DIM")

    # JWT
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # App
    app_env: str = Field(default="development", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Hybrid search weights
    graph_weight: float = Field(default=0.5, env="GRAPH_WEIGHT")
    vector_weight: float = Field(default=0.3, env="VECTOR_WEIGHT")
    recency_weight: float = Field(default=0.2, env="RECENCY_WEIGHT")
    top_k: int = Field(default=10, env="TOP_K")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

✅ **Phase 1 Validation**

🤖 **Kiro Prompt:**
```
Run docker compose up -d and verify all three services are healthy:
- curl http://localhost:6333/healthz → should return OK
- curl http://localhost:27017 → mongo connection
- Open http://localhost:7474 in browser → Neo4j browser should load
Also run: pip install -r backend/requirements.txt and confirm no errors.
```

---

# PHASE 2: Auth System

## Objective
Implement JWT-based authentication with role-based access control. Roles: `patient`, `doctor`, `admin`. Users stored in MongoDB.

---

### Step 2.1 — User Model

📁 **File:** `backend/app/models/user.py`

🤖 **Kiro Prompt:**
```
Create backend/app/models/user.py with Pydantic models:
- UserRole enum: patient, doctor, admin
- UserCreate: email, password, full_name, role, optional specialization (for doctors)
- UserInDB: all above + hashed_password + user_id (str UUID) + created_at
- UserResponse: no password fields, just user_id, email, full_name, role
- TokenResponse: access_token, token_type="bearer", user_id, role
```

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import datetime
from enum import Enum
import uuid


class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole
    specialization: Optional[str] = None  # for doctors


class UserInDB(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    hashed_password: str
    full_name: str
    role: UserRole
    specialization: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: UserRole
    specialization: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: UserRole
```

---

### Step 2.2 — JWT Handler

📁 **File:** `backend/app/utils/jwt_handler.py`

🤖 **Kiro Prompt:**
```
Create backend/app/utils/jwt_handler.py with:
- create_access_token(data: dict) → str JWT with expiry
- decode_access_token(token: str) → dict claims or None
- get_password_hash(password) → bcrypt hash
- verify_password(plain, hashed) → bool
Use python-jose for JWT and passlib for bcrypt.
```

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

---

### Step 2.3 — Auth Router

📁 **File:** `backend/app/routers/auth.py`

🤖 **Kiro Prompt:**
```
Create backend/app/routers/auth.py with:
- POST /auth/register → creates user in MongoDB users collection, hashes password, returns UserResponse
- POST /auth/login → validates credentials, returns TokenResponse with JWT
- GET /auth/me → returns current user from JWT (protected route)
Use motor (async MongoDB driver) for all DB operations.
Check for duplicate emails on register.
```

```python
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import UserCreate, UserResponse, TokenResponse, UserInDB
from app.utils.jwt_handler import get_password_hash, verify_password, create_access_token
from app.dependencies import get_db, get_current_user
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate, db=Depends(get_db)):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = UserInDB(
        user_id=str(uuid.uuid4()),
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        specialization=user_data.specialization,
        created_at=datetime.utcnow(),
    )

    await db.users.insert_one(user.model_dump())
    return UserResponse(**user.model_dump())


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserCreate, db=Depends(get_db)):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user["user_id"],
        "role": user["role"],
        "email": user["email"],
    })
    return TokenResponse(access_token=token, user_id=user["user_id"], role=user["role"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return UserResponse(**current_user)
```

---

### Step 2.4 — Dependencies

📁 **File:** `backend/app/dependencies.py`

🤖 **Kiro Prompt:**
```
Create backend/app/dependencies.py with:
- get_db(): returns motor AsyncIOMotorDatabase instance (singleton)
- get_current_user(): FastAPI dependency that reads Bearer token from Authorization header, decodes JWT, fetches user from MongoDB, raises 401 if invalid
- require_role(*roles): dependency factory that checks current_user role is in allowed roles, raises 403 if not
```

```python
from fastapi import Depends, HTTPException, Header
from typing import Annotated, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from functools import lru_cache
from app.config import get_settings
from app.utils.jwt_handler import decode_access_token


@lru_cache()
def get_mongo_client() -> AsyncIOMotorClient:
    settings = get_settings()
    return AsyncIOMotorClient(settings.mongodb_url)


async def get_db() -> AsyncIOMotorDatabase:
    settings = get_settings()
    client = get_mongo_client()
    return client[settings.mongodb_db]


async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    db=Depends(get_db),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    claims = decode_access_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db.users.find_one({"user_id": claims["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def require_role(*roles: str):
    async def role_checker(current_user=Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail=f"Access denied. Required roles: {roles}")
        return current_user
    return role_checker
```

---

✅ **Phase 2 Validation**

🤖 **Kiro Prompt:**
```
Start the FastAPI server: uvicorn app.main:app --reload --port 8000
Test these endpoints:

1. POST http://localhost:8000/auth/register
   Body: {"email":"patient@test.com","password":"test1234","full_name":"John Patient","role":"patient"}
   Expected: 201 with user_id

2. POST http://localhost:8000/auth/login
   Body: {"email":"patient@test.com","password":"test1234"}
   Expected: 200 with access_token

3. GET http://localhost:8000/auth/me
   Header: Authorization: Bearer <token from step 2>
   Expected: user object with role=patient
```

---

# PHASE 3: AI Services

## Objective
Implement Groq LLM service, HuggingFace embedding service, and all three database service wrappers (Neo4j, Qdrant, MongoDB).

---

### Step 3.1 — Groq Service

📁 **File:** `backend/app/services/groq_service.py`

🤖 **Kiro Prompt:**
```
Create backend/app/services/groq_service.py with GroqService class:
- __init__: initialize Groq client with API key from settings
- async invoke(system_prompt, user_message, max_tokens=2048, temperature=0.0) → dict with {text, input_tokens, output_tokens}
- Add retry logic with tenacity: 3 attempts, exponential backoff 2-10s
- Log all invocations with structlog including latency_ms
```

```python
import time
import structlog
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings

logger = structlog.get_logger()


class GroqService:
    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def invoke(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> dict:
        start = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            latency_ms = int((time.time() - start) * 1000)
            text = response.choices[0].message.content

            logger.info("Groq invoked", latency_ms=latency_ms, model=self.model)
            return {
                "text": text,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "latency_ms": latency_ms,
            }
        except Exception as e:
            logger.error("Groq invocation failed", error=str(e))
            raise
```

---

### Step 3.2 — Embedding Service

📁 **File:** `backend/app/services/embedding_service.py`

🤖 **Kiro Prompt:**
```
Create backend/app/services/embedding_service.py with EmbeddingService class:
- Load sentence-transformers model on __init__ using SentenceTransformer
- async embed(text: str) → List[float] (384-dim vector)
- async embed_batch(texts: List[str]) → List[List[float]]
- Use lru_cache on the class instance so model loads once (singleton pattern)
- Normalize embeddings to unit length
```

```python
from functools import lru_cache
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
import structlog
from app.config import get_settings

logger = structlog.get_logger()


class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        logger.info("Loading embedding model", model=settings.embedding_model)
        self.model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded")

    async def embed(self, text: str) -> List[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
```

---

### Step 3.3 — Neo4j Service

📁 **File:** `backend/app/services/neo4j_service.py`

🤖 **Kiro Prompt:**
```
Create backend/app/services/neo4j_service.py with Neo4jService class using the official neo4j Python driver (async).

Graph Schema:
Nodes: Patient, Symptom, Medication, Condition, Vital, Allergy, Event
Relationships: HAS_SYMPTOM, TAKES_MEDICATION, HAS_CONDITION, HAS_VITAL, HAS_ALLERGY, PART_OF_EVENT

Methods needed:
- async store_entities(patient_id, entities, source, encounter_date) → int (nodes created)
- async search(patient_id, query, scope, filters, top_k) → List[dict]
- async create_event_node(patient_id, request_id, source, encounter_date) → str (event_id)
- async get_patient_summary(patient_id) → dict with conditions, medications, symptoms, allergies

All nodes must have patient_id property for data isolation.
Use MERGE not CREATE to avoid duplicates.
```

```python
import uuid
import structlog
from datetime import datetime
from typing import Optional, List
from neo4j import AsyncGraphDatabase
from app.config import get_settings

logger = structlog.get_logger()


class Neo4jService:
    def __init__(self):
        settings = get_settings()
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    async def close(self):
        await self.driver.close()

    async def store_entities(
        self,
        patient_id: str,
        entities: dict,
        source: str,
        encounter_date: str,
    ) -> int:
        nodes_created = 0
        timestamp = encounter_date or datetime.utcnow().isoformat()

        async with self.driver.session() as session:
            # Merge Patient node
            await session.run(
                "MERGE (p:Patient {patient_id: $pid}) ON CREATE SET p.created_at = $now",
                pid=patient_id, now=datetime.utcnow().isoformat()
            )

            # Symptoms
            for s in entities.get("symptoms", []):
                node_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{patient_id}:symptom:{s['name']}"))
                await session.run("""
                    MERGE (n:Symptom {node_id: $nid})
                    ON CREATE SET n.name=$name, n.severity=$sev, n.duration=$dur,
                                  n.patient_id=$pid, n.timestamp=$ts, n.source=$src
                    WITH n
                    MATCH (p:Patient {patient_id: $pid})
                    MERGE (p)-[:HAS_SYMPTOM]->(n)
                """, nid=node_id, name=s["name"].lower(), sev=s.get("severity","unknown"),
                     dur=s.get("duration",""), pid=patient_id, ts=timestamp, src=source)
                nodes_created += 1

            # Medications
            for m in entities.get("medications", []):
                node_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{patient_id}:med:{m['name']}"))
                await session.run("""
                    MERGE (n:Medication {node_id: $nid})
                    ON CREATE SET n.name=$name, n.dosage=$dos, n.frequency=$freq,
                                  n.patient_id=$pid, n.timestamp=$ts, n.source=$src
                    WITH n
                    MATCH (p:Patient {patient_id: $pid})
                    MERGE (p)-[:TAKES_MEDICATION]->(n)
                """, nid=node_id, name=m["name"].lower(), dos=m.get("dosage",""),
                     freq=m.get("frequency",""), pid=patient_id, ts=timestamp, src=source)
                nodes_created += 1

            # Conditions
            for c in entities.get("conditions", []):
                node_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{patient_id}:cond:{c['name']}"))
                await session.run("""
                    MERGE (n:Condition {node_id: $nid})
                    ON CREATE SET n.name=$name, n.icd10=$icd, n.status=$stat,
                                  n.patient_id=$pid, n.timestamp=$ts
                    WITH n
                    MATCH (p:Patient {patient_id: $pid})
                    MERGE (p)-[:HAS_CONDITION]->(n)
                """, nid=node_id, name=c["name"].lower(), icd=c.get("icd10_code",""),
                     stat=c.get("status","active"), pid=patient_id, ts=timestamp)
                nodes_created += 1

            # Vitals
            for v in entities.get("vitals", []):
                node_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{patient_id}:vital:{v['type']}:{timestamp}"))
                await session.run("""
                    MERGE (n:Vital {node_id: $nid})
                    ON CREATE SET n.type=$type, n.value=$val, n.unit=$unit,
                                  n.status=$stat, n.patient_id=$pid, n.timestamp=$ts
                    WITH n
                    MATCH (p:Patient {patient_id: $pid})
                    MERGE (p)-[:HAS_VITAL]->(n)
                """, nid=node_id, type=v.get("type",""), val=v.get("value",""),
                     unit=v.get("unit",""), stat=v.get("status","normal"), pid=patient_id, ts=timestamp)
                nodes_created += 1

            # Allergies
            for a in entities.get("allergies", []):
                node_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{patient_id}:allergy:{a['substance']}"))
                await session.run("""
                    MERGE (n:Allergy {node_id: $nid})
                    ON CREATE SET n.substance=$sub, n.reaction=$react, n.severity=$sev,
                                  n.patient_id=$pid, n.timestamp=$ts
                    WITH n
                    MATCH (p:Patient {patient_id: $pid})
                    MERGE (p)-[:HAS_ALLERGY]->(n)
                """, nid=node_id, sub=a.get("substance",""), react=a.get("reaction",""),
                     sev=a.get("severity",""), pid=patient_id, ts=timestamp)
                nodes_created += 1

        logger.info("Neo4j entities stored", patient_id=patient_id, nodes=nodes_created)
        return nodes_created

    async def search(
        self,
        patient_id: str,
        query: str,
        scope: str,
        filters: dict,
        top_k: int = 10,
    ) -> List[dict]:
        results = []

        async with self.driver.session() as session:
            if scope == "medication_only":
                cypher = """
                    MATCH (p:Patient {patient_id: $pid})-[:TAKES_MEDICATION]->(n:Medication)
                    RETURN n, 'Medication' as label LIMIT $k
                """
                records = await session.run(cypher, pid=patient_id, k=top_k)

            elif scope == "disease_specific":
                diseases = filters.get("diseases", [])
                cypher = """
                    MATCH (p:Patient {patient_id: $pid})-[:HAS_CONDITION]->(n:Condition)
                    WHERE n.name IN $diseases OR $diseases = []
                    RETURN n, 'Condition' as label LIMIT $k
                """
                records = await session.run(cypher, pid=patient_id, diseases=[d.lower() for d in diseases], k=top_k)

            elif scope == "time_bound":
                date_start = filters.get("date_start", "")
                date_end = filters.get("date_end", datetime.utcnow().isoformat())
                cypher = """
                    MATCH (p:Patient {patient_id: $pid})-[]->(n)
                    WHERE n.timestamp >= $ds AND n.timestamp <= $de
                    RETURN n, labels(n)[0] as label LIMIT $k
                """
                records = await session.run(cypher, pid=patient_id, ds=date_start, de=date_end, k=top_k)

            else:  # full
                cypher = """
                    MATCH (p:Patient {patient_id: $pid})-[]->(n)
                    RETURN n, labels(n)[0] as label LIMIT $k
                """
                records = await session.run(cypher, pid=patient_id, k=top_k)

            async for record in records:
                node = dict(record["n"])
                label = record["label"]
                content = self._node_to_text(node, label)
                results.append({
                    "id": node.get("node_id", str(uuid.uuid4())),
                    "type": "graph_node",
                    "vertex_label": label,
                    "content": content,
                    "score": 1.0,
                    "date": node.get("timestamp", ""),
                })

        return results

    async def get_patient_summary(self, patient_id: str) -> dict:
        summary = {"conditions": [], "medications": [], "symptoms": [], "allergies": [], "vitals": []}
        async with self.driver.session() as session:
            for rel, key in [("HAS_CONDITION","conditions"), ("TAKES_MEDICATION","medications"),
                              ("HAS_SYMPTOM","symptoms"), ("HAS_ALLERGY","allergies"), ("HAS_VITAL","vitals")]:
                records = await session.run(
                    f"MATCH (p:Patient {{patient_id: $pid}})-[:{rel}]->(n) RETURN n",
                    pid=patient_id
                )
                async for r in records:
                    summary[key].append(dict(r["n"]))
        return summary

    async def create_event_node(self, patient_id, request_id, source, encounter_date) -> str:
        event_id = str(uuid.uuid4())
        async with self.driver.session() as session:
            await session.run("""
                CREATE (e:Event {event_id: $eid, patient_id: $pid, request_id: $rid,
                                 source: $src, timestamp: $ts})
                WITH e
                MATCH (p:Patient {patient_id: $pid})
                CREATE (e)-[:PART_OF_EVENT]->(p)
            """, eid=event_id, pid=patient_id, rid=request_id,
                 src=source, ts=encounter_date or datetime.utcnow().isoformat())
        return event_id

    def _node_to_text(self, node: dict, label: str) -> str:
        parts = [f"[{label}]"]
        skip = {"node_id", "patient_id"}
        for k, v in node.items():
            if k not in skip and v:
                parts.append(f"{k}: {v}")
        return " | ".join(parts)
```

---

### Step 3.4 — Qdrant Service

📁 **File:** `backend/app/services/qdrant_service.py`

🤖 **Kiro Prompt:**
```
Create backend/app/services/qdrant_service.py with QdrantService class:
- __init__: connect to Qdrant, create collection if not exists (384 dims, Cosine distance)
- async index(patient_id, entry_id, text, embedding, source, encounter_date, entities) → str
- async search(patient_id, query_embedding, scope, filters, top_k) → List[dict]
  - CRITICAL: always filter by patient_id to prevent cross-patient leakage
  - scope=medication_only → filter has_medications=True
  - scope=disease_specific → filter condition_names contains disease
  - scope=time_bound → filter encounter_date range
- async delete_patient_data(patient_id) → int (deleted count)
```

```python
import uuid
import structlog
from typing import List, Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition,
    MatchValue, MatchAny, Range, HasIdCondition
)
from app.config import get_settings

logger = structlog.get_logger()


class QdrantService:
    def __init__(self):
        settings = get_settings()
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection = settings.qdrant_collection
        self.dim = settings.embedding_dim
        self._ensure_collection()

    def _ensure_collection(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
            )
            logger.info("Qdrant collection created", collection=self.collection)

    async def index(
        self,
        patient_id: str,
        entry_id: str,
        text: str,
        embedding: List[float],
        source: str,
        encounter_date: Optional[str],
        entities: Optional[dict],
    ) -> str:
        entities = entities or {}
        payload = {
            "patient_id": patient_id,
            "entry_id": entry_id,
            "text": text,
            "source": source,
            "encounter_date": encounter_date or datetime.utcnow().isoformat(),
            "has_medications": bool(entities.get("medications")),
            "has_conditions": bool(entities.get("conditions")),
            "has_symptoms": bool(entities.get("symptoms")),
            "medication_names": [m["name"].lower() for m in entities.get("medications", [])],
            "condition_names": [c["name"].lower() for c in entities.get("conditions", [])],
            "symptom_names": [s["name"].lower() for s in entities.get("symptoms", [])],
        }

        self.client.upsert(
            collection_name=self.collection,
            points=[PointStruct(id=entry_id, vector=embedding, payload=payload)],
        )
        logger.info("Qdrant entry indexed", entry_id=entry_id)
        return entry_id

    async def search(
        self,
        patient_id: str,
        query_embedding: List[float],
        scope: str,
        filters: dict,
        top_k: int = 10,
    ) -> List[dict]:
        must_conditions = [FieldCondition(key="patient_id", match=MatchValue(value=patient_id))]

        if scope == "medication_only":
            must_conditions.append(FieldCondition(key="has_medications", match=MatchValue(value=True)))
        elif scope == "disease_specific":
            diseases = [d.lower() for d in filters.get("diseases", [])]
            if diseases:
                must_conditions.append(FieldCondition(key="condition_names", match=MatchAny(any=diseases)))
        elif scope == "time_bound":
            date_start = filters.get("date_start")
            date_end = filters.get("date_end", datetime.utcnow().isoformat())
            if date_start:
                must_conditions.append(FieldCondition(
                    key="encounter_date",
                    range=Range(gte=date_start, lte=date_end)
                ))

        search_filter = Filter(must=must_conditions)
        hits = self.client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
        )

        return [{
            "id": str(hit.id),
            "type": "vector_entry",
            "content": hit.payload.get("text", ""),
            "score": hit.score,
            "date": hit.payload.get("encounter_date", ""),
            "medication_names": hit.payload.get("medication_names", []),
            "condition_names": hit.payload.get("condition_names", []),
        } for hit in hits]

    async def delete_patient_data(self, patient_id: str) -> int:
        result = self.client.delete(
            collection_name=self.collection,
            points_selector=Filter(must=[
                FieldCondition(key="patient_id", match=MatchValue(value=patient_id))
            ]),
        )
        return result.result if result else 0
```

---

✅ **Phase 3 Validation**

🤖 **Kiro Prompt:**
```
Write and run a quick test script tests/test_services.py:
1. Test GroqService.invoke() with a simple "Say hello" prompt → should return text
2. Test EmbeddingService.embed("diabetes medication") → should return list of 384 floats
3. Test Neo4jService stores a patient node and retrieves it
4. Test QdrantService indexes a point and searches it back

Run: python -m pytest tests/test_services.py -v
```

---

# PHASE 4: Prompts & Entity Extraction

## Objective
Define all LLM prompts for medical entity extraction and clinical summary generation.

---

### Step 4.1 — Entity Extraction Prompt

📁 **File:** `backend/app/prompts/entity_extraction.py`

🤖 **Kiro Prompt:**
```
Create backend/app/prompts/entity_extraction.py with:
- ENTITY_EXTRACTION_SYSTEM_PROMPT: instructs LLM to extract structured JSON with keys:
  symptoms, medications, conditions, vitals, allergies
  Each with appropriate sub-fields (name, severity, dosage, icd10_code, etc.)
  Must return ONLY valid JSON, no markdown, no preamble
- build_extraction_prompt(text) → formatted user message
```

```python
ENTITY_EXTRACTION_SYSTEM_PROMPT = """You are a medical entity extraction engine for a HIPAA-compliant healthcare platform.

Extract structured medical information from unstructured patient health text.
Respond with ONLY a valid JSON object. No markdown. No explanation. No preamble.

JSON structure:
{
  "symptoms": [{"name": str, "severity": "mild|moderate|severe", "duration": str}],
  "medications": [{"name": str, "dosage": str, "frequency": str, "route": str}],
  "conditions": [{"name": str, "icd10_code": str, "status": "active|resolved|chronic"}],
  "vitals": [{"type": str, "value": str, "unit": str, "status": "normal|elevated|critical"}],
  "allergies": [{"substance": str, "reaction": str, "severity": str}]
}

Rules:
- Only extract information explicitly present in the text
- Never infer or fabricate information
- Use ICD-10 codes where recognizable
- Normalize medication names to generic form
- Return empty arrays [] for categories with no data"""


def build_extraction_prompt(text: str) -> str:
    return f"""Extract all medical entities from this patient health text:

<health_text>
{text}
</health_text>

Return ONLY the JSON object."""
```

---

### Step 4.2 — Clinical Summary Prompt

📁 **File:** `backend/app/prompts/clinical_summary.py`

🤖 **Kiro Prompt:**
```
Create backend/app/prompts/clinical_summary.py with:
- CLINICAL_SUMMARY_SYSTEM_PROMPT: instructs LLM to generate doctor-ready SOAP-format summaries
- build_chat_prompt(query, context, patient_id) → formats retrieved context + doctor query
- build_fhir_summary_prompt(graph_data, vector_context) → formats full patient data for FHIR summary generation
```

```python
CLINICAL_SUMMARY_SYSTEM_PROMPT = """You are a clinical summarization assistant for licensed healthcare providers.

Generate concise, accurate, doctor-ready summaries from structured patient health data.
Follow clinical documentation standards. Be factual and precise.

Format your response with clear sections:
- Current Medications (with dosages)
- Active Conditions (with ICD codes if available)
- Recent Symptoms
- Known Allergies
- Vitals (if available)
- Clinical Alerts (drug interactions, critical values)

Rules:
- Be factual. Only report what the data shows.
- Note drug interaction risks explicitly.
- Highlight urgent findings first.
- State clearly if data is unavailable for any section."""


def build_chat_prompt(query: str, context: str, patient_id: str) -> str:
    return f"""Patient Health Query

Patient ID: {patient_id}
Clinician Query: {query}

Retrieved Patient Health Context:
{context}

Answer the clinician's query strictly based on the provided health context.
Cite specific data points in your answer.
If the information is not available in the context, state that clearly.
Do not hallucinate medical facts."""


def build_fhir_summary_prompt(graph_data: dict, vector_context: str) -> str:
    return f"""Generate a comprehensive clinical summary for FHIR export.

Patient Graph Data:
- Conditions: {graph_data.get('conditions', [])}
- Medications: {graph_data.get('medications', [])}
- Symptoms: {graph_data.get('symptoms', [])}
- Allergies: {graph_data.get('allergies', [])}
- Vitals: {graph_data.get('vitals', [])}

Additional Context from Records:
{vector_context}

Generate a complete clinical summary following the SOAP format suitable for inclusion in a FHIR DocumentReference resource."""
```

---

# PHASE 5: LangGraph Pipelines

## Objective
Build the ingestion pipeline (Flow 1) and retrieval pipeline (Flow 2) as LangGraph state machines.

---

### Step 5.1 — Ingestion Pipeline

📁 **File:** `backend/app/pipelines/ingestion_pipeline.py`

🤖 **Kiro Prompt:**
```
Create backend/app/pipelines/ingestion_pipeline.py implementing the ingestion LangGraph state machine.

Nodes in order:
1. validate_input → check text length, patient_id present
2. extract_entities → call GroqService with entity extraction prompt, parse JSON response
3. store_in_neo4j → call Neo4jService.store_entities()
4. generate_embedding → call EmbeddingService.embed()
5. store_in_qdrant → call QdrantService.index()
6. create_event_node → call Neo4jService.create_event_node()

State: IngestionState TypedDict with all intermediate values
Each node receives and returns state.
On error in any node: set error field, continue to next node (partial success OK).
Final run() method returns result dict.
```

```python
import json
import uuid
import time
import structlog
from typing import TypedDict, Optional, List
from datetime import datetime
from langgraph.graph import StateGraph, END

from app.services.groq_service import GroqService
from app.services.embedding_service import get_embedding_service
from app.services.neo4j_service import Neo4jService
from app.services.qdrant_service import QdrantService
from app.prompts.entity_extraction import ENTITY_EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt

logger = structlog.get_logger()


class IngestionState(TypedDict):
    patient_id: str
    text: str
    source: str
    encounter_date: Optional[str]
    request_id: str
    extracted_entities: Optional[dict]
    graph_nodes_created: int
    embedding: Optional[List[float]]
    vector_entry_id: Optional[str]
    event_node_id: Optional[str]
    errors: List[str]
    status: str


class IngestionPipeline:
    def __init__(self):
        self.groq = GroqService()
        self.embedding_svc = get_embedding_service()
        self.neo4j = Neo4jService()
        self.qdrant = QdrantService()
        self.graph = self._build_graph()

    def _build_graph(self):
        g = StateGraph(IngestionState)
        g.add_node("validate_input", self._validate_input)
        g.add_node("extract_entities", self._extract_entities)
        g.add_node("store_neo4j", self._store_neo4j)
        g.add_node("generate_embedding", self._generate_embedding)
        g.add_node("store_qdrant", self._store_qdrant)
        g.add_node("create_event", self._create_event)
        g.set_entry_point("validate_input")
        g.add_edge("validate_input", "extract_entities")
        g.add_edge("extract_entities", "store_neo4j")
        g.add_edge("store_neo4j", "generate_embedding")
        g.add_edge("generate_embedding", "store_qdrant")
        g.add_edge("store_qdrant", "create_event")
        g.add_edge("create_event", END)
        return g.compile()

    async def run(self, patient_id, text, source, encounter_date=None, request_id=None) -> dict:
        initial: IngestionState = {
            "patient_id": patient_id,
            "text": text,
            "source": source,
            "encounter_date": encounter_date or datetime.utcnow().isoformat(),
            "request_id": request_id or str(uuid.uuid4()),
            "extracted_entities": None,
            "graph_nodes_created": 0,
            "embedding": None,
            "vector_entry_id": None,
            "event_node_id": None,
            "errors": [],
            "status": "processing",
        }
        final = await self.graph.ainvoke(initial)
        return {
            "entities": final["extracted_entities"] or {},
            "graph_nodes_created": final["graph_nodes_created"],
            "vector_entry_id": final["vector_entry_id"],
            "event_node_id": final["event_node_id"],
            "status": final["status"],
            "errors": final["errors"],
        }

    async def _validate_input(self, state: IngestionState) -> dict:
        if len(state["text"]) < 10:
            return {**state, "status": "failed", "errors": ["Text too short"]}
        if not state["patient_id"]:
            return {**state, "status": "failed", "errors": ["Missing patient_id"]}
        return state

    async def _extract_entities(self, state: IngestionState) -> dict:
        try:
            result = await self.groq.invoke(
                system_prompt=ENTITY_EXTRACTION_SYSTEM_PROMPT,
                user_message=build_extraction_prompt(state["text"]),
                temperature=0.0,
            )
            text = result["text"].strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            entities = json.loads(text.strip())
            return {**state, "extracted_entities": entities}
        except Exception as e:
            logger.error("Entity extraction failed", error=str(e))
            return {**state, "errors": state["errors"] + [str(e)], "extracted_entities": {}, "status": "partial"}

    async def _store_neo4j(self, state: IngestionState) -> dict:
        try:
            nodes = await self.neo4j.store_entities(
                patient_id=state["patient_id"],
                entities=state["extracted_entities"] or {},
                source=state["source"],
                encounter_date=state["encounter_date"],
            )
            return {**state, "graph_nodes_created": nodes}
        except Exception as e:
            logger.error("Neo4j store failed", error=str(e))
            return {**state, "errors": state["errors"] + [str(e)]}

    async def _generate_embedding(self, state: IngestionState) -> dict:
        try:
            embedding = await self.embedding_svc.embed(state["text"])
            return {**state, "embedding": embedding}
        except Exception as e:
            return {**state, "errors": state["errors"] + [str(e)]}

    async def _store_qdrant(self, state: IngestionState) -> dict:
        if not state["embedding"]:
            return state
        try:
            entry_id = str(uuid.uuid4())
            await self.qdrant.index(
                patient_id=state["patient_id"],
                entry_id=entry_id,
                text=state["text"],
                embedding=state["embedding"],
                source=state["source"],
                encounter_date=state["encounter_date"],
                entities=state["extracted_entities"],
            )
            return {**state, "vector_entry_id": entry_id}
        except Exception as e:
            return {**state, "errors": state["errors"] + [str(e)]}

    async def _create_event(self, state: IngestionState) -> dict:
        try:
            event_id = await self.neo4j.create_event_node(
                patient_id=state["patient_id"],
                request_id=state["request_id"],
                source=state["source"],
                encounter_date=state["encounter_date"],
            )
            return {**state, "event_node_id": event_id, "status": "success"}
        except Exception as e:
            return {**state, "event_node_id": state["request_id"], "status": "partial",
                    "errors": state["errors"] + [str(e)]}
```

---

### Step 5.2 — Retrieval Pipeline

📁 **File:** `backend/app/pipelines/retrieval_pipeline.py`

🤖 **Kiro Prompt:**
```
Create backend/app/pipelines/retrieval_pipeline.py with the RAG retrieval LangGraph pipeline.

Nodes in order:
1. validate_scope → confirm consent scope is set
2. generate_query_embedding → embed the query text
3. parallel_search → asyncio.gather(neo4j.search(), qdrant.search()) simultaneously
4. hybrid_rank → call HybridRanker.rank() with graph×0.5 + vector×0.3 + recency×0.2
5. build_context → format top 8 results into context string for LLM
6. invoke_llm → call GroqService with clinical summary prompt + context
7. attach_citations → build citation objects from top 5 ranked results

Return: response, citations, timing metrics, node counts used
```

```python
import asyncio
import time
import structlog
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END

from app.services.groq_service import GroqService
from app.services.embedding_service import get_embedding_service
from app.services.neo4j_service import Neo4jService
from app.services.qdrant_service import QdrantService
from app.utils.hybrid_ranker import HybridRanker
from app.prompts.clinical_summary import CLINICAL_SUMMARY_SYSTEM_PROMPT, build_chat_prompt
from app.config import get_settings

logger = structlog.get_logger()


class RetrievalState(TypedDict):
    patient_id: str
    query: str
    consent_scope: str
    consent_filters: dict
    request_id: str
    query_embedding: Optional[List[float]]
    graph_results: List[dict]
    vector_results: List[dict]
    ranked_results: List[dict]
    context_pack: Optional[str]
    citations: List[dict]
    llm_response: Optional[str]
    retrieval_start_ms: int
    retrieval_end_ms: int
    llm_start_ms: int
    llm_end_ms: int


class RetrievalPipeline:
    def __init__(self):
        self.groq = GroqService()
        self.embedding_svc = get_embedding_service()
        self.neo4j = Neo4jService()
        self.qdrant = QdrantService()
        self.ranker = HybridRanker()
        self.settings = get_settings()
        self.graph = self._build_graph()

    def _build_graph(self):
        g = StateGraph(RetrievalState)
        g.add_node("validate_scope", self._validate_scope)
        g.add_node("generate_query_embedding", self._generate_query_embedding)
        g.add_node("parallel_search", self._parallel_search)
        g.add_node("hybrid_rank", self._hybrid_rank)
        g.add_node("build_context", self._build_context)
        g.add_node("invoke_llm", self._invoke_llm)
        g.add_node("attach_citations", self._attach_citations)
        g.set_entry_point("validate_scope")
        g.add_edge("validate_scope", "generate_query_embedding")
        g.add_edge("generate_query_embedding", "parallel_search")
        g.add_edge("parallel_search", "hybrid_rank")
        g.add_edge("hybrid_rank", "build_context")
        g.add_edge("build_context", "invoke_llm")
        g.add_edge("invoke_llm", "attach_citations")
        g.add_edge("attach_citations", END)
        return g.compile()

    async def run(self, patient_id, query, consent_scope, consent_filters, request_id) -> dict:
        initial: RetrievalState = {
            "patient_id": patient_id, "query": query,
            "consent_scope": consent_scope, "consent_filters": consent_filters,
            "request_id": request_id, "query_embedding": None,
            "graph_results": [], "vector_results": [], "ranked_results": [],
            "context_pack": None, "citations": [], "llm_response": None,
            "retrieval_start_ms": int(time.time() * 1000),
            "retrieval_end_ms": 0, "llm_start_ms": 0, "llm_end_ms": 0,
        }
        final = await self.graph.ainvoke(initial)
        return {
            "response": final["llm_response"] or "No data available for this query.",
            "citations": final["citations"],
            "graph_nodes_used": len(final["graph_results"]),
            "vector_entries_used": len(final["vector_results"]),
            "retrieval_time_ms": max(final["retrieval_end_ms"] - final["retrieval_start_ms"], 0),
            "llm_time_ms": max(final["llm_end_ms"] - final["llm_start_ms"], 0),
        }

    async def _validate_scope(self, state: RetrievalState) -> dict:
        logger.info("Retrieval scope", scope=state["consent_scope"])
        return state

    async def _generate_query_embedding(self, state: RetrievalState) -> dict:
        embedding = await self.embedding_svc.embed(state["query"])
        return {**state, "query_embedding": embedding}

    async def _parallel_search(self, state: RetrievalState) -> dict:
        graph_task = self.neo4j.search(
            state["patient_id"], state["query"],
            state["consent_scope"], state["consent_filters"], self.settings.top_k
        )
        vector_task = self.qdrant.search(
            state["patient_id"], state["query_embedding"],
            state["consent_scope"], state["consent_filters"], self.settings.top_k
        )
        graph_results, vector_results = await asyncio.gather(graph_task, vector_task)
        return {**state, "graph_results": graph_results, "vector_results": vector_results,
                "retrieval_end_ms": int(time.time() * 1000)}

    async def _hybrid_rank(self, state: RetrievalState) -> dict:
        ranked = self.ranker.rank(
            state["graph_results"], state["vector_results"],
            self.settings.graph_weight, self.settings.vector_weight, self.settings.recency_weight
        )
        return {**state, "ranked_results": ranked}

    async def _build_context(self, state: RetrievalState) -> dict:
        parts = []
        for i, r in enumerate(state["ranked_results"][:8]):
            parts.append(f"[Source {i+1} | {r['type']} | Score: {r['score']:.3f} | Date: {r.get('date','unknown')}]\n{r['content']}")
        context = "\n\n---\n\n".join(parts)
        return {**state, "context_pack": context, "llm_start_ms": int(time.time() * 1000)}

    async def _invoke_llm(self, state: RetrievalState) -> dict:
        result = await self.groq.invoke(
            system_prompt=CLINICAL_SUMMARY_SYSTEM_PROMPT,
            user_message=build_chat_prompt(state["query"], state["context_pack"] or "No context", state["patient_id"]),
            temperature=0.0,
        )
        return {**state, "llm_response": result["text"], "llm_end_ms": int(time.time() * 1000)}

    async def _attach_citations(self, state: RetrievalState) -> dict:
        citations = [{
            "source_type": r["type"],
            "source_id": r["id"],
            "relevance_score": r["score"],
            "excerpt": r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"],
        } for r in state["ranked_results"][:5]]
        return {**state, "citations": citations}
```

---

# PHASE 6: Consent Engine

## Objective
Full consent management: request, grant/deny, scope enforcement, expiry, audit logging. Stored in MongoDB.

---

### Step 6.1 — Consent Models

📁 **File:** `backend/app/models/consent.py`

🤖 **Kiro Prompt:**
```
Create backend/app/models/consent.py with:
- ConsentScope enum: full, disease_specific, time_bound, medication_only
- ConsentStatus enum: pending, approved, denied, revoked, expired
- ConsentRequest model: doctor_id, patient_id, purpose, requested_scope, disease_filter, date_range_start, date_range_end, duration_hours
- ConsentRecord (stored in MongoDB): all above + consent_id, status, created_at, valid_until, granted_at
- ConsentGrant: consent_id, patient_id, approved bool, scope, modifications
- ConsentCheckResult dataclass: allowed bool, reason, scope, filters, consent_id
```

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import uuid


class ConsentScope(str, Enum):
    FULL = "full"
    DISEASE_SPECIFIC = "disease_specific"
    TIME_BOUND = "time_bound"
    MEDICATION_ONLY = "medication_only"


class ConsentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ConsentRequest(BaseModel):
    doctor_id: str
    patient_id: str
    purpose: str = Field(max_length=500)
    requested_scope: ConsentScope
    disease_filter: Optional[List[str]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    duration_hours: int = Field(default=24, ge=1, le=8760)


class ConsentRecord(BaseModel):
    consent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doctor_id: str
    patient_id: str
    purpose: str
    requested_scope: ConsentScope
    disease_filter: Optional[List[str]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    duration_hours: int = 24
    status: ConsentStatus = ConsentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    granted_at: Optional[datetime] = None


class ConsentGrant(BaseModel):
    consent_id: str
    patient_id: str
    approved: bool
    scope: Optional[ConsentScope] = None


@dataclass
class ConsentCheckResult:
    allowed: bool
    reason: str
    scope: Optional[str] = None
    filters: Optional[dict] = None
    consent_id: Optional[str] = None
```

---

### Step 6.2 — Consent Service

📁 **File:** `backend/app/services/consent_service.py`

🤖 **Kiro Prompt:**
```
Create backend/app/services/consent_service.py with ConsentService class using motor (async MongoDB):

Methods:
- async create_request(request: ConsentRequest, db) → ConsentRecord
- async process_grant(grant: ConsentGrant, db) → ConsentRecord
- async check_access(requester_id, requester_role, patient_id, db) → ConsentCheckResult
  - patients always have full access to own data
  - doctors need active approved consent in MongoDB
  - look up by doctor_id + patient_id + status=approved + valid_until > now
- async get_patient_consents(patient_id, db) → List[ConsentRecord]
- async revoke(consent_id, patient_id, db) → bool

MongoDB collection: "consents"
```

```python
import structlog
from datetime import datetime, timedelta
from typing import List, Optional
from app.models.consent import ConsentRequest, ConsentRecord, ConsentGrant, ConsentCheckResult, ConsentScope, ConsentStatus

logger = structlog.get_logger()


class ConsentService:
    COLLECTION = "consents"

    async def create_request(self, request: ConsentRequest, db) -> ConsentRecord:
        record = ConsentRecord(
            doctor_id=request.doctor_id,
            patient_id=request.patient_id,
            purpose=request.purpose,
            requested_scope=request.requested_scope,
            disease_filter=request.disease_filter,
            date_range_start=request.date_range_start,
            date_range_end=request.date_range_end,
            duration_hours=request.duration_hours,
            status=ConsentStatus.PENDING,
        )
        await db[self.COLLECTION].insert_one(record.model_dump())
        logger.info("Consent request created", consent_id=record.consent_id)
        return record

    async def process_grant(self, grant: ConsentGrant, db) -> ConsentRecord:
        doc = await db[self.COLLECTION].find_one({"consent_id": grant.consent_id})
        if not doc:
            raise ValueError(f"Consent {grant.consent_id} not found")
        if doc["patient_id"] != grant.patient_id:
            raise ValueError("Patient ID mismatch")
        if doc["status"] != "pending":
            raise ValueError(f"Consent already {doc['status']}")

        new_status = ConsentStatus.APPROVED if grant.approved else ConsentStatus.DENIED
        valid_until = None
        if grant.approved:
            valid_until = datetime.utcnow() + timedelta(hours=doc["duration_hours"])

        await db[self.COLLECTION].update_one(
            {"consent_id": grant.consent_id},
            {"$set": {"status": new_status.value, "valid_until": valid_until,
                       "granted_at": datetime.utcnow()}}
        )

        doc.update({"status": new_status.value, "valid_until": valid_until})
        return ConsentRecord(**doc)

    async def check_access(self, requester_id: str, requester_role: str, patient_id: str, db) -> ConsentCheckResult:
        if requester_role == "patient" and requester_id == patient_id:
            return ConsentCheckResult(allowed=True, reason="Self-access", scope="full", filters={})

        consent = await db[self.COLLECTION].find_one({
            "doctor_id": requester_id,
            "patient_id": patient_id,
            "status": "approved",
            "valid_until": {"$gt": datetime.utcnow()}
        })

        if not consent:
            return ConsentCheckResult(allowed=False, reason="No active consent found")

        scope = consent["requested_scope"]
        filters = {}
        if scope == ConsentScope.DISEASE_SPECIFIC.value:
            filters["diseases"] = consent.get("disease_filter", [])
        elif scope == ConsentScope.TIME_BOUND.value:
            filters["date_start"] = consent.get("date_range_start", "")
            filters["date_end"] = consent.get("date_range_end", datetime.utcnow().isoformat())

        return ConsentCheckResult(allowed=True, reason="Active consent found",
                                   scope=scope, filters=filters, consent_id=consent["consent_id"])

    async def get_patient_consents(self, patient_id: str, db) -> List[ConsentRecord]:
        cursor = db[self.COLLECTION].find({"patient_id": patient_id})
        return [ConsentRecord(**doc) async for doc in cursor]

    async def revoke(self, consent_id: str, patient_id: str, db) -> bool:
        result = await db[self.COLLECTION].update_one(
            {"consent_id": consent_id, "patient_id": patient_id},
            {"$set": {"status": "revoked"}}
        )
        return result.modified_count > 0
```

---

# PHASE 7: Core API Routers

## Objective
Build all five FastAPI routers: memory ingestion, RAG chat, consent management, FHIR exchange. Wire up all services.

---

### Step 7.1 — Memory Router (Flow 1)

📁 **File:** `backend/app/routers/memory.py`

🤖 **Kiro Prompt:**
```
Create backend/app/routers/memory.py:
- POST /memory/ingest (patient or doctor role)
  - Request: {patient_id, text, source, encounter_date}
  - Auth: patients can only ingest own data (patient_id == current_user.user_id)
  - Calls IngestionPipeline.run()
  - Logs to audit collection in MongoDB via BackgroundTask
  - Response: {request_id, status, entities, graph_nodes_created, vector_entry_id, processing_time_ms}
- GET /memory/history/{patient_id} (patient or doctor with consent)
  - Returns last 20 event nodes from Neo4j
```

---

### Step 7.2 — Chat Router (Flow 2)

📁 **File:** `backend/app/routers/chat.py`

🤖 **Kiro Prompt:**
```
Create backend/app/routers/chat.py:
- POST /chat (doctor or patient role)
  - Request: {patient_id, query, requester_id, requester_role, session_id?}
  - FIRST: call ConsentService.check_access() — if denied, return 403 with CONSENT_DENIED error
  - THEN: call RetrievalPipeline.run() with consent scope + filters
  - Log to audit via BackgroundTask
  - Response: {request_id, response, citations, graph_nodes_used, vector_entries_used, retrieval_time_ms, llm_time_ms, total_time_ms}
```

---

### Step 7.3 — Consent Router (Flow 3 Part 1)

📁 **File:** `backend/app/routers/consent.py`

🤖 **Kiro Prompt:**
```
Create backend/app/routers/consent.py:
- POST /consent/request (doctor only) → ConsentService.create_request()
- POST /consent/grant (patient only, can only grant own consent) → ConsentService.process_grant()
- GET /consent/active/{patient_id} (patient sees own, doctor sees their requests)
- DELETE /consent/{consent_id} (patient only, revokes their consent)
All operations logged to audit.
```

---

### Step 7.4 — FHIR Router (Flow 3 Part 2)

📁 **File:** `backend/app/routers/fhir.py`

🤖 **Kiro Prompt:**
```
Create backend/app/routers/fhir.py:
- POST /fhir/exchange (doctor only)
  - Request: {patient_id, doctor_id, consent_id, include_summary: bool}
  - Validate consent
  - Get patient_summary from Neo4j
  - Search Qdrant for additional context
  - Generate LLM clinical summary via Groq
  - Build FHIR R4 bundle using fhir.resources library with:
    * Patient resource
    * Condition resources (one per condition)
    * MedicationStatement resources (one per medication)
    * DocumentReference (LLM summary as base64 text)
  - Store bundle in MongoDB fhir_bundles collection
  - Return {bundle_id, fhir_bundle, clinical_summary, resource_count}
- GET /fhir/bundle/{bundle_id} → retrieve stored bundle from MongoDB
```

---

# PHASE 8: FHIR Service

📁 **File:** `backend/app/services/fhir_service.py`

🤖 **Kiro Prompt:**
```
Create backend/app/services/fhir_service.py with FHIRService class.

Method: build_fhir_bundle(patient_id, graph_data, llm_summary, consent_scope, request_id) → dict

Build a FHIR R4 Transaction Bundle using fhir.resources library containing:
1. Patient resource with patient_id as identifier
2. Condition resource per condition (with ICD-10 code if available, clinicalStatus active/resolved)
3. MedicationStatement resource per medication (with dosage text)
4. DocumentReference resource with LLM summary (base64 encoded, contentType text/plain)
5. Bundle meta tags: consent-scope, request-id

Return the bundle as a Python dict (JSON-serializable).
Also write method store_bundle(bundle_dict, db) → str (bundle_id stored in MongoDB)
```

---

# PHASE 9: Hybrid Ranker + Audit Service

### Step 9.1 — Hybrid Ranker

📁 **File:** `backend/app/utils/hybrid_ranker.py`

🤖 **Kiro Prompt:**
```
Create backend/app/utils/hybrid_ranker.py with HybridRanker class.

rank(graph_results, vector_results, graph_weight=0.5, vector_weight=0.3, recency_weight=0.2) → List[dict]

Algorithm:
1. Min-max normalize scores within graph_results (to 0-1)
2. Min-max normalize scores within vector_results (to 0-1)
3. Merge by content key (id field), deduplicating overlapping results
4. For each merged result: score = graph_score×gw + vector_score×vw + recency_score×rw
5. Recency score: exponential decay math.exp(-0.01 × days_old), unknown date → 0.5
6. Sort descending by final score
7. Return sorted list

_compute_recency_score(date_str: str) → float (handle ISO8601, timezone-aware/naive)
_normalize_scores(results) → normalized list
_content_key(result) → dedup key
```

---

### Step 9.2 — Audit Service

📁 **File:** `backend/app/services/audit_service.py`

🤖 **Kiro Prompt:**
```
Create backend/app/services/audit_service.py.

async log_phi_access(action, patient_id, accessor_id, accessor_role, resource_type, request_id, db, metadata=None)

Writes to MongoDB "audit_logs" collection with:
{
  event_id: uuid4,
  timestamp: ISO8601,
  action: str (INGEST | CHAT_QUERY | CONSENT_REQUESTED | CONSENT_GRANTED | FHIR_EXCHANGE),
  patient_id: str,
  accessor_id: str,
  accessor_role: str,
  resource_type: str,
  request_id: str,
  metadata: dict,
}

Also log to structlog with patient_id partially masked (first 8 chars only).
```

---

# PHASE 10: FastAPI Main App

📁 **File:** `backend/app/main.py`

🤖 **Kiro Prompt:**
```
Create backend/app/main.py:
- FastAPI app with title "MedGraph AI", version "1.0.0"
- CORS middleware: allow all origins in dev, restrict in prod
- Include all routers with prefixes: /auth, /memory, /chat, /consent, /fhir
- Lifespan: on startup verify MongoDB, Neo4j, Qdrant connections are alive; log status
- GET /health → {"status":"healthy","services":{"mongodb":bool,"neo4j":bool,"qdrant":bool}}
- Global exception handler: return 500 with {detail, request_id}
- Add request_id middleware that injects X-Request-ID header on every response
```

---

# PHASE 11: Frontend

## Objective
Build three main UI sections: Patient Portal, Doctor Dashboard, Consent Manager.

---

### Step 11.1 — Project Setup

🤖 **Kiro Prompt:**
```
Inside the frontend/ directory:
npm create vite@latest . -- --template react
npm install tailwindcss postcss autoprefixer axios react-router-dom zustand
npx tailwindcss init -p

Configure tailwind.config.js for src/** files.
Set up React Router with routes:
- / → Landing page
- /login → Login page
- /register → Register page
- /patient → PatientPortal (protected, patient role)
- /doctor → DoctorDashboard (protected, doctor role)
- /consent → ConsentManager (protected, both roles)
```

---

### Step 11.2 — Auth Store & Service

🤖 **Kiro Prompt:**
```
Create frontend/src/store/authStore.js using Zustand:
- State: user (null), token (null), isAuthenticated (bool)
- Actions: login(email, password), register(userData), logout(), loadFromStorage()
- Persist token to localStorage

Create frontend/src/services/api.js:
- Axios instance with baseURL from env (VITE_API_URL)
- Request interceptor: attach Authorization: Bearer {token} from store
- Response interceptor: on 401 → logout + redirect to /login
- Export typed functions: register, login, ingestMemory, chat, requestConsent, grantConsent, fhirExchange
```

---

### Step 11.3 — Patient Portal

🤖 **Kiro Prompt:**
```
Create frontend/src/components/PatientPortal/index.jsx with:
1. Health Data Input section:
   - Textarea for health text input
   - Source selector (patient_input, lab_result, prescription)
   - Submit button → calls POST /memory/ingest
   - Show extracted entities in a card after submission

2. My Health Summary section:
   - Chat interface: input box + submit → calls POST /chat with requester_role=patient
   - Display response with citations
   - Conversation history (local state)

3. Active Consents section:
   - List all consents for current patient (GET /consent/active/{patient_id})
   - For each pending consent: Approve / Deny buttons → POST /consent/grant
   - For each approved consent: Revoke button → DELETE /consent/{id}
   - Show consent scope, doctor name, expiry

Use TailwindCSS. Keep it clean and medical-professional looking.
```

---

### Step 11.4 — Doctor Dashboard

🤖 **Kiro Prompt:**
```
Create frontend/src/components/DoctorDashboard/index.jsx with:
1. Patient Search section:
   - Input: patient_id or email
   - Fetch patient basic info

2. Request Consent section:
   - Form: purpose, scope selector (full/medication_only/disease_specific/time_bound)
   - Conditional fields: disease names for disease_specific, date range for time_bound
   - Duration selector (hours)
   - Submit → POST /consent/request

3. Patient Query section (only shows if active consent exists):
   - Query input textarea
   - Submit → POST /chat with requester_role=doctor
   - Display response with source citations
   - Show which consent scope is active

4. FHIR Export section (only if active consent):
   - Generate FHIR Bundle button → POST /fhir/exchange
   - Display bundle summary (resource count, clinical summary)
   - Download bundle as JSON button

Use TailwindCSS. Medical dashboard aesthetic.
```

---

# PHASE 12: Docker & Final Integration

### Step 12.1 — Backend Dockerfile

📁 **File:** `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Step 12.2 — Add Backend to Docker Compose

🤖 **Kiro Prompt:**
```
Update docker-compose.yml to add:
1. backend service: build from ./backend, port 8000:8000, env_file .env, depends_on mongodb+neo4j+qdrant, network medgraph-network
2. frontend service: build from ./frontend, port 5173:5173, env VITE_API_URL=http://localhost:8000, network medgraph-network

Update .env so all localhost references use Docker service names when running in Docker:
- MONGODB_URL=mongodb://mongodb:27017
- NEO4J_URI=bolt://neo4j:7687
- QDRANT_HOST=qdrant
```

---

### Step 12.3 — DB Initialization Scripts

📁 **File:** `scripts/init_neo4j.py`

🤖 **Kiro Prompt:**
```
Create scripts/init_neo4j.py:
- Connect to Neo4j using driver
- Create uniqueness constraints:
  CREATE CONSTRAINT IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE
  CREATE CONSTRAINT IF NOT EXISTS FOR (n:Symptom) REQUIRE n.node_id IS UNIQUE
  CREATE CONSTRAINT IF NOT EXISTS FOR (n:Medication) REQUIRE n.node_id IS UNIQUE
  CREATE CONSTRAINT IF NOT EXISTS FOR (n:Condition) REQUIRE n.node_id IS UNIQUE
  CREATE CONSTRAINT IF NOT EXISTS FOR (n:Vital) REQUIRE n.node_id IS UNIQUE
  CREATE CONSTRAINT IF NOT EXISTS FOR (n:Allergy) REQUIRE n.node_id IS UNIQUE
- Create indexes on patient_id for all node types
- Print success for each constraint
```

📁 **File:** `scripts/init_qdrant.py`

🤖 **Kiro Prompt:**
```
Create scripts/init_qdrant.py:
- Connect to Qdrant
- Create patient_memories collection if not exists (384 dims, Cosine)
- Create payload indexes: patient_id (keyword), has_medications (bool), has_conditions (bool), encounter_date (datetime)
- Print collection info after creation
```

---

# PHASE 13: Testing

🤖 **Kiro Prompt:**
```
Create the following test files and run them:

tests/unit/test_hybrid_ranker.py:
- test_rank_basic: graph + vector results merged and sorted correctly
- test_recency_today: today's date gets score > 0.99
- test_recency_old: date from 2020 gets score < 0.1
- test_empty_inputs: rank([], []) returns []
- test_deduplication: same id in both lists returns one result

tests/unit/test_consent_service.py:
- test_patient_self_access: patient accessing own data → allowed=True, scope=full
- test_doctor_no_consent: doctor with no consent → allowed=False
- test_doctor_valid_consent: mock active consent in DB → allowed=True with correct scope
- test_revoke_consent: status becomes revoked

tests/integration/test_ingestion_flow.py (with real Docker services running):
- test_full_ingest: submit health text → verify Neo4j nodes exist + Qdrant entry indexed
- test_entity_extraction: submit diabetes text → extracted_entities.conditions contains diabetes

Run: pytest tests/ -v --tb=short
Expected: All tests PASS
```

---

# MASTER VALIDATION CHECKLIST

## End-to-End Flow Tests

```bash
# 1. Start all services
docker compose up -d
# Wait ~30s for services to be healthy

# 2. Initialize DB schemas
python scripts/init_neo4j.py
python scripts/init_qdrant.py

# 3. Start backend
cd backend && uvicorn app.main:app --reload --port 8000

# ─── REGISTER USERS ──────────────────────────────────────
# Register patient
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@test.com","password":"test1234","full_name":"John Patient","role":"patient"}'

# Register doctor
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@test.com","password":"test1234","full_name":"Dr. Smith","role":"doctor","specialization":"Cardiology"}'

# ─── LOGIN ────────────────────────────────────────────────
# Get patient token
PATIENT_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@test.com","password":"test1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

PATIENT_ID=$(curl -s http://localhost:8000/auth/me \
  -H "Authorization: Bearer $PATIENT_TOKEN" | python -c "import sys,json; print(json.load(sys.stdin)['user_id'])")

DOCTOR_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@test.com","password":"test1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

DOCTOR_ID=$(curl -s http://localhost:8000/auth/me \
  -H "Authorization: Bearer $DOCTOR_TOKEN" | python -c "import sys,json; print(json.load(sys.stdin)['user_id'])")

# ─── FLOW 1: INGEST ──────────────────────────────────────
curl -X POST http://localhost:8000/memory/ingest \
  -H "Authorization: Bearer $PATIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"patient_id\":\"$PATIENT_ID\",\"text\":\"Patient has Type 2 Diabetes (E11.9). Taking Metformin 500mg twice daily. Blood pressure 145/92. Reports fatigue and frequent urination. Allergic to penicillin.\",\"source\":\"patient_input\"}"
# Expected: {"status":"success","graph_nodes_created":>=3,"vector_entry_id":"<uuid>"}

# ─── FLOW 2: CONSENT ─────────────────────────────────────
CONSENT_RESPONSE=$(curl -s -X POST http://localhost:8000/consent/request \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"doctor_id\":\"$DOCTOR_ID\",\"patient_id\":\"$PATIENT_ID\",\"purpose\":\"Annual cardiology review\",\"requested_scope\":\"full\",\"duration_hours\":24}")

CONSENT_ID=$(echo $CONSENT_RESPONSE | python -c "import sys,json; print(json.load(sys.stdin)['consent_id'])")

# Patient approves
curl -X POST http://localhost:8000/consent/grant \
  -H "Authorization: Bearer $PATIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"consent_id\":\"$CONSENT_ID\",\"patient_id\":\"$PATIENT_ID\",\"approved\":true}"
# Expected: {"status":"approved"}

# ─── FLOW 2: RAG CHAT ────────────────────────────────────
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"patient_id\":\"$PATIENT_ID\",\"query\":\"What medications is this patient on and are there any allergy concerns?\",\"requester_id\":\"$DOCTOR_ID\",\"requester_role\":\"doctor\"}"
# Expected: {"response":"...<clinical answer>...","citations":[...],"total_time_ms":<3000}

# ─── FLOW 3: FHIR EXCHANGE ───────────────────────────────
curl -X POST http://localhost:8000/fhir/exchange \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"patient_id\":\"$PATIENT_ID\",\"doctor_id\":\"$DOCTOR_ID\",\"consent_id\":\"$CONSENT_ID\",\"include_summary\":true}"
# Expected: {"fhir_bundle":{"resourceType":"Bundle","type":"transaction"},"resource_count":>=3,"clinical_summary":"..."}

# ─── HEALTH CHECK ─────────────────────────────────────────
curl http://localhost:8000/health
# Expected: {"status":"healthy","services":{"mongodb":true,"neo4j":true,"qdrant":true}}
```

## Performance Targets

| Endpoint | Target |
|---|---|
| POST /memory/ingest | < 4000ms |
| POST /chat | < 3000ms |
| POST /fhir/exchange | < 5000ms |
| GET /health | < 100ms |
| POST /auth/login | < 200ms |

## API Contract Summary

| Endpoint | Method | Role | Description |
|---|---|---|---|
| /auth/register | POST | public | Create patient or doctor account |
| /auth/login | POST | public | Get JWT token |
| /auth/me | GET | any | Get current user info |
| /memory/ingest | POST | patient, doctor | Ingest health text → graph + vector |
| /memory/history/{patient_id} | GET | patient, doctor | Get ingestion event history |
| /chat | POST | patient, doctor | Consent-gated RAG query |
| /consent/request | POST | doctor | Request access to patient data |
| /consent/grant | POST | patient | Approve or deny consent request |
| /consent/active/{patient_id} | GET | patient, doctor | List active consents |
| /consent/{consent_id} | DELETE | patient | Revoke consent |
| /fhir/exchange | POST | doctor | Generate FHIR R4 bundle |
| /fhir/bundle/{bundle_id} | GET | doctor | Retrieve stored bundle |
| /health | GET | public | Service health check |

---

## Data Flow Summary

```
🔵 FLOW 1 — PATIENT INGEST
POST /memory/ingest
  → JWT auth (patient role)
  → IngestionPipeline (LangGraph):
      Node 1: validate_input
      Node 2: extract_entities (Groq llama-3.3-70b)
      Node 3: store_neo4j (symptoms, meds, conditions, vitals, allergies)
      Node 4: generate_embedding (all-MiniLM-L6-v2, 384-dim)
      Node 5: store_qdrant (vector + payload)
      Node 6: create_event_node (Neo4j event node)
  → BackgroundTask: audit_log → MongoDB audit_logs
  → Response: entities + counts

🟢 FLOW 2 — DOCTOR RAG CHAT
POST /chat
  → JWT auth (doctor role)
  → ConsentService.check_access() → MongoDB consents
  → If denied: 403 CONSENT_DENIED
  → RetrievalPipeline (LangGraph):
      Node 1: validate_scope
      Node 2: generate_query_embedding
      Node 3: parallel_search (Neo4j + Qdrant simultaneously via asyncio.gather)
      Node 4: hybrid_rank (Graph×0.5 + Vector×0.3 + Recency×0.2)
      Node 5: build_context (top 8 results formatted)
      Node 6: invoke_llm (Groq with clinical summary prompt)
      Node 7: attach_citations
  → BackgroundTask: audit_log → MongoDB audit_logs
  → Response: clinical answer + citations + timing

🟠 FLOW 3 — FHIR EXCHANGE
POST /fhir/exchange
  → JWT auth (doctor role)
  → ConsentService.check_access()
  → Neo4jService.get_patient_summary() (scoped by consent)
  → QdrantService.search() (scoped by consent)
  → GroqService: clinical summary generation
  → FHIRService.build_fhir_bundle():
      Patient resource
      Condition resources (per condition)
      MedicationStatement resources (per medication)
      DocumentReference (LLM summary, base64)
  → MongoDB: store bundle in fhir_bundles collection
  → BackgroundTask: audit_log
  → Response: FHIR R4 Bundle JSON + clinical_summary
```

---

*End of MedGraph AI Kiro Implementation Plan — v2.0*
*Stack: Groq + HuggingFace + LangGraph + Neo4j + Qdrant + MongoDB + FastAPI + React*
*Team: TLE_Eliminators | KIT's College of Engineering, Kolhapur*
*Cognizant Technoverse 2026*
