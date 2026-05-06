# Infrastructure & Deployment

> Docker Compose · MongoDB · Neo4j · Qdrant · AWS Migration Guide

---

## Local Development (Docker Compose)

```yaml
services:
  mongodb:    # MongoDB 7.0 — Document store, auth, sessions, audit
  neo4j:      # Neo4j 5.18 — Clinical knowledge graph
  qdrant:     # Qdrant latest — Vector search (patient memories)
  backend:    # FastAPI (Python 3.11)
  frontend:   # React SPA (Nginx)
```

### Quick Start
```bash
# Start all services
docker-compose up -d

# Verify health
curl http://localhost:8000/health

# Seed initial data
cd backend
python scripts/seed_super_admin.py
python scripts/seed_test_users.py
python scripts/seed_all_entities.py
```

### Ports
| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 80 | React SPA (Nginx) |
| Backend | 8000 | FastAPI REST API |
| MongoDB | 27017 | Document database |
| Neo4j Browser | 7474 | Graph DB web UI |
| Neo4j Bolt | 7687 | Graph DB protocol |
| Qdrant | 6333 | Vector DB REST API |

---

## Environment Variables

Create `.env` at project root:

```env
# Required
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
JWT_SECRET_KEY=your-256-bit-secret

# Optional (defaults shown)
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
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
APP_ENV=development
LOG_LEVEL=INFO
GRAPH_WEIGHT=0.5
VECTOR_WEIGHT=0.3
RECENCY_WEIGHT=0.2
TOP_K=10
```

Frontend `.env`:
```env
VITE_API_URL=http://localhost:8000
```

---

## AWS Migration Guide

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud                                  │
│                                                                   │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │ CloudFront   │────▶│ S3 (Static)  │     │ Route 53     │    │
│  │ (CDN)        │     │ React Build  │     │ (DNS)        │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐     ┌──────────────┐                          │
│  │ ALB          │────▶│ ECS Fargate  │                          │
│  │ (Load Bal.)  │     │ (Backend)    │                          │
│  └──────────────┘     └──────┬───────┘                          │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │ DocumentDB   │   │ Neptune      │   │ OpenSearch   │       │
│  │ (MongoDB)    │   │ (Neo4j alt)  │   │ (Vector alt) │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                                   │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │ Secrets Mgr  │   │ CloudWatch   │   │ WAF          │       │
│  │ (Env vars)   │   │ (Logging)    │   │ (Security)   │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Service Mapping

| Local Service | AWS Service | Notes |
|--------------|-------------|-------|
| MongoDB | Amazon DocumentDB | MongoDB-compatible, managed |
| Neo4j | Amazon Neptune | Graph DB (or self-hosted Neo4j on EC2) |
| Qdrant | Amazon OpenSearch Serverless (k-NN) | Or self-hosted Qdrant on ECS |
| FastAPI Backend | ECS Fargate | Containerized, auto-scaling |
| React Frontend | S3 + CloudFront | Static hosting with CDN |
| PDF Storage (GridFS) | S3 + DocumentDB metadata | S3 for blobs, DocumentDB for metadata |
| Groq LLM | Groq Cloud API | External API call (no AWS equivalent needed) |
| JWT Secrets | AWS Secrets Manager | Rotate secrets automatically |
| Logs | CloudWatch Logs | Structured logging |
| DNS | Route 53 | Custom domain |
| SSL | ACM (Certificate Manager) | Free SSL certificates |
| Firewall | WAF + Security Groups | DDoS protection, IP filtering |

### Migration Steps

1. **Frontend**: `npm run build` → upload `dist/` to S3 → CloudFront distribution
2. **Backend**: Build Docker image → push to ECR → deploy on ECS Fargate
3. **MongoDB → DocumentDB**: Use `mongodump`/`mongorestore` for data migration
4. **Neo4j → Neptune**: Export Cypher → convert to Gremlin (or run Neo4j on EC2)
5. **Qdrant**: Run as ECS service with EBS volume, or use OpenSearch k-NN
6. **Environment**: Store all secrets in AWS Secrets Manager
7. **Networking**: VPC with private subnets for databases, public subnet for ALB

### Cost Estimate (Production)

| Service | Estimated Monthly Cost |
|---------|----------------------|
| ECS Fargate (2 tasks, 1vCPU/2GB) | ~$70 |
| DocumentDB (db.t3.medium) | ~$120 |
| Neptune (db.t3.medium) | ~$150 |
| OpenSearch Serverless | ~$50 |
| S3 + CloudFront | ~$10 |
| ALB | ~$25 |
| Secrets Manager | ~$5 |
| CloudWatch | ~$20 |
| **Total** | **~$450/month** |

### Security Checklist for AWS

- [ ] VPC with private subnets for all databases
- [ ] Security groups: backend → databases only
- [ ] WAF rules on ALB (rate limiting, SQL injection protection)
- [ ] Encryption at rest (DocumentDB, Neptune, S3)
- [ ] Encryption in transit (TLS everywhere)
- [ ] IAM roles for ECS tasks (no hardcoded credentials)
- [ ] Secrets Manager for all sensitive config
- [ ] CloudTrail for API audit logging
- [ ] GuardDuty for threat detection
- [ ] Backup: DocumentDB automated snapshots, S3 versioning

---

## Docker Build

### Backend
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

---

## Monitoring & Observability

- **Structured Logging**: `structlog` with JSON output → CloudWatch Logs
- **Health Check**: `GET /health` returns service status for all 3 databases
- **Audit Trail**: Every PHI access logged to `audit_logs` collection
- **Request IDs**: `X-Request-ID` header propagated through all services
- **Metrics**: Token usage, latency, cache hit rate logged per LLM call
