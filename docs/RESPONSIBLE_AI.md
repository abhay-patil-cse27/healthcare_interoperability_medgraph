# MedGraph AI — Responsible AI & Compliance

---

## Overview

MedGraph implements multiple layers of AI safety and healthcare compliance:

1. **PHI Redaction** — HIPAA Safe Harbor before any LLM processing
2. **Bedrock Guardrails** — Input/output content filtering
3. **HITL Validation** — Human review of AI-generated content
4. **Consent-Gated Access** — Patient controls who sees their data
5. **Audit Trail** — Every PHI access logged

---

## PHI Redaction (HIPAA Safe Harbor)

All patient text is de-identified **before** reaching the LLM or vector database.

### What Gets Redacted (18 HIPAA Identifiers)

| # | Identifier | Example | Replacement |
|---|-----------|---------|-------------|
| 1 | Names | "Ravi Patil" | `[REDACTED_NAME]` |
| 2 | Geographic data | "Pune, 411001" | `[REDACTED_ADDRESS]` |
| 3 | Dates (except year) | "15-May-1990" | `[REDACTED_DATE]` |
| 4 | Phone numbers | "+919876543210" | `[REDACTED_PHONE]` |
| 5 | Email addresses | "ravi@email.com" | `[REDACTED_EMAIL]` |
| 6 | SSN / Aadhaar | "1234-5678-9012" | `[REDACTED_ID]` |
| 7 | Medical record numbers | "AIIMS-2026-00042" | `[REDACTED_MRN]` |
| 8 | Health plan IDs | "ABHA-1234" | `[REDACTED_HEALTH_ID]` |
| 9 | Account numbers | — | `[REDACTED_ACCOUNT]` |
| 10 | License numbers | — | `[REDACTED_LICENSE]` |
| 11-18 | Vehicle, device, URLs, IPs, biometric, photos | — | `[REDACTED_*]` |

### What Gets Preserved

- Age, gender
- Clinical values (BP: 140/90, SpO2: 98%)
- Lab results (HbA1c: 7.2%)
- Medical terminology
- Drug names and dosages
- Symptoms and conditions

### Reversible Redaction

- Redaction maps stored in `medgraph-phi-redaction-maps` table
- Only HITL validators can access redaction maps for re-association
- Maps are never exposed to the LLM or vector database

---

## Bedrock Guardrails

Applied to both clinical RAG and Vaidya chatbot responses.

### Configuration

| Filter | Action |
|--------|--------|
| **Denied Topics** | Block: medical diagnosis, unauthorized PHI access |
| **Content Filters** | Block: hate speech, violence, sexual content, insults |
| **Sensitive Info** | Detect & block: PII/PHI in output |
| **Contextual Grounding** | Block: hallucinated content (threshold 0.7) |

### Behavior

When a guardrail intervenes:
1. Response `guardrail_action` = `"BLOCKED"`
2. Safe replacement message returned to user
3. Event logged with user ID, role, IP, query preview
4. Original blocked content never reaches the client

### Setup

```bash
python backend/scripts/setup_bedrock_guardrails.py
```

This creates the guardrail and outputs the `BEDROCK_GUARDRAIL_ID` for your `.env`.

---

## HITL (Human-in-the-Loop) Validation

AI-generated screening summaries are **never** sent directly to doctors. They pass through a human validator first.

### Workflow

```
1. Lab report uploaded → AI generates screening summary
2. Summary enters HITL queue (status: "pending_hitl")
3. HITL validator reviews:
   a. ACCEPT & FORWARD → Summary sent to doctor with time-bound consent
   b. EDIT & FORWARD → Validator corrects errors, then forwards
   c. REJECT → Data mismatch, nothing forwarded
   d. ESCALATE → Identity/record issues flagged to admin
4. Doctor receives forwarded screening with temporary access (1-8 hours)
5. Doctor marks as reviewed
```

### HITL Permissions

| Permission | Action |
|------------|--------|
| `screening:view_pending` | View the queue |
| `screening:validate` | Review individual screenings |
| `screening:edit` | Edit AI summary before forwarding |
| `screening:forward` | Accept and forward to doctor |
| `screening:escalate` | Flag issues to admin |

---

## Consent-Gated Access

### How Consent Works

1. **Doctor requests** consent for a specific patient with a stated purpose
2. **Patient receives** notification and reviews the request
3. **Patient grants or denies** — can specify scope restrictions
4. **If granted:** Doctor gets time-limited access (1-8760 hours)
5. **Patient can revoke** at any time — immediate effect

### Consent Scopes

| Scope | Access Level |
|-------|-------------|
| `full` | All patient records |
| `medication_only` | Only medication-related data |
| `disease_specific` | Only records matching specified conditions |
| `time_bound` | Only records within a date range |

### Enforcement Points

- `POST /chat/` — Consent checked before RAG query
- `POST /fhir/exchange` — Consent checked before bundle generation
- `GET /screening/doctor/{id}` — Consent checked before viewing

---

## Audit Trail

Every PHI access is logged to `medgraph-audit-logs`:

```json
{
  "log_id": "uuid",
  "action": "CHAT_QUERY",
  "patient_id": "patient-uuid",
  "accessor_id": "doctor-uuid",
  "accessor_role": "doctor",
  "resource_type": "ClinicalChat",
  "request_id": "uuid",
  "metadata": {
    "consent_id": "uuid",
    "consent_scope": "full",
    "query_preview": "What medications..."
  },
  "timestamp": "2026-05-07T10:30:00Z"
}
```

### Audited Actions

| Action | Trigger |
|--------|---------|
| `INGEST` | Patient health text ingested |
| `CHAT_QUERY` | Doctor queries patient records |
| `FHIR_EXCHANGE` | FHIR bundle generated |
| `CONSENT_REQUESTED` | Doctor requests consent |
| `CONSENT_GRANTED` | Patient approves |
| `CONSENT_DENIED` | Patient denies |
| `CONSENT_REVOKED` | Patient revokes |
| `DOCUMENT_UPLOADED` | PDF uploaded |
| `DOCUMENT_DOWNLOADED` | PDF accessed |
| `SCREENING_GENERATED` | AI screening created |
| `SCREENING_FORWARDED` | HITL forwards to doctor |

---

## Compliance Standards

| Standard | Implementation |
|----------|---------------|
| **HIPAA** | PHI redaction, encrypted storage, audit logs, access controls |
| **FHIR R4** | Standardized health data exchange bundles |
| **ABDM/ABHA** | India's Ayushman Bharat Digital Health Mission integration |
| **DPDP Act** | India's Digital Personal Data Protection compliance |

---

## Security Measures

| Layer | Protection |
|-------|-----------|
| Transport | HTTPS/TLS everywhere |
| Storage | S3 AES256, DynamoDB encryption at rest, Neo4j TLS |
| Auth | JWT with 60-min expiry, bcrypt password hashing |
| Input | PDF magic byte validation, file size limits, input sanitization |
| Output | Guardrail filtering, no raw PHI in responses |
| Access | Permission-based RBAC + consent-gated data access |
