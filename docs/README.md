# MedGraph AI — Documentation Index

> National Healthcare Interoperability Platform  
> Ministry of Health & Family Welfare · Tier-1 Platform  
> Built for Cognizant Technoverse 2026

---

## Documentation Structure

| Document | Description |
|----------|-------------|
| [BACKEND.md](./BACKEND.md) | Backend architecture, services, pipelines, models, and configuration |
| [FRONTEND.md](./FRONTEND.md) | Frontend architecture, pages, components, routing, and state management |
| [API_REFERENCE.md](./API_REFERENCE.md) | Complete REST API reference with all endpoints, request/response schemas |
| [RESPONSIBLE_AI.md](./RESPONSIBLE_AI.md) | Antigravity Agent — Responsible AI pipeline, PHI redaction, HITL workflow |
| [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) | Docker, databases, deployment, and AWS migration guide |
| [RBAC.md](./RBAC.md) | Role-Based Access Control — 17 roles, permissions, and consent architecture |

---

## Quick Start

```bash
# Clone and start all services
git clone <repo-url>
cd MED_GRAPH
docker-compose up -d

# Backend (FastAPI)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (React + Vite)
cd frontend
npm install
npm run dev
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 19, Vite 8, Tailwind CSS 3, Zustand, Recharts | SPA with role-based dashboards |
| Backend | FastAPI, Python 3.11, LangGraph, Groq LLM | REST API + AI pipelines |
| Vector DB | Qdrant | Semantic search over patient records |
| Graph DB | Neo4j 5 | Entity relationships, clinical knowledge graph |
| Document DB | MongoDB 7 | Users, sessions, audit logs, documents |
| PDF Storage | MongoDB GridFS | Encrypted patient document storage |
| Auth | JWT (python-jose), bcrypt | Stateless authentication |
| Containerization | Docker Compose | Multi-service orchestration |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React SPA)                             │
│  Landing · Login · Patient Portal · Doctor Dashboard · Admin · HITL     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ REST API (JWT Auth)
┌────────────────────────────────────▼────────────────────────────────────┐
│                         BACKEND (FastAPI)                                 │
│  Routers → Services → Pipelines → LLM (Groq)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Auth     │  │ Chat     │  │ Screening│  │ Documents│               │
│  │ Consent  │  │ Memory   │  │ HITL     │  │ FHIR     │               │
│  │ Admin    │  │ Clinical │  │ PHI Redac│  │ Audit    │               │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘               │
└───────┬──────────────┬──────────────┬──────────────┬────────────────────┘
        │              │              │              │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │ MongoDB │   │  Neo4j  │   │ Qdrant  │   │  Groq   │
   │ (Docs)  │   │ (Graph) │   │(Vectors)│   │  (LLM)  │
   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

---

## Key Features

- **17-Role RBAC** with JWT-embedded permissions
- **Consent-gated data access** — patients own their data
- **AI Clinical RAG** — hybrid Neo4j + Qdrant retrieval with LLM synthesis
- **Responsible AI (Antigravity Agent)** — HITL-validated, strictly word-bounded screening
- **PHI Redaction** — HIPAA Safe Harbor de-identification before any LLM processing
- **PDF Upload + FHIR** — patient document management with EHR interoperability
- **Persistent Chat** — ChatGPT-style conversations with session management
- **Real-time Visualizations** — interactive vitals charts, activity sparklines
- **PM-JAY / MPJAY Integration** — government scheme eligibility and claims
- **MLC Interface** — medico-legal case management with police access

---

## License

Proprietary — Cognizant Technoverse 2026 Submission
