# MedGraph AI — API Reference

> Base URL: `http://localhost:8000`  
> Auth: All endpoints (except `/auth/register`, `/auth/login`, `/health`, `/legal/*`) require `Authorization: Bearer <token>`

---

## Health Check

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Service health status |

**Response:**
```json
{
  "status": "healthy",
  "services": { "dynamodb": true, "neo4j": true, "bedrock": true, "opensearch": true }
}
```

---

## Auth

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/auth/register` | None | — | Patient self-registration |
| POST | `/auth/login` | None | — | Login (returns JWT) |
| GET | `/auth/me` | Bearer | — | Get current user profile |

### POST `/auth/register`

Only patients can self-register. Staff accounts are created by Hospital Admins.

**Request:**
```json
{
  "email": "patient@example.com",
  "password": "securepass123",
  "full_name": "Ravi Patil",
  "role": "patient",
  "phone": "+919876543210",
  "abha_id": "ABHA-1234-5678",
  "blood_group": "O+",
  "date_of_birth": "1990-05-15",
  "gender": "male"
}
```

**Response (201):**
```json
{
  "user_id": "uuid",
  "email": "patient@example.com",
  "full_name": "Ravi Patil",
  "role": "patient",
  "mrn": "MED-2026-00001",
  "permissions": ["patient:read_own", "patient:write_own", "consent:grant", "consent:view_own", "memory:ingest"]
}
```

### POST `/auth/login`

**Request:**
```json
{ "email": "patient@example.com", "password": "securepass123" }
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": "uuid",
  "role": "patient"
}
```

### GET `/auth/me`

**Response:**
```json
{
  "user_id": "uuid",
  "email": "patient@example.com",
  "full_name": "Ravi Patil",
  "role": "patient",
  "permissions": ["patient:read_own", "..."],
  "is_active": true
}
```

---

## Memory (Health Record Ingestion)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/memory/ingest` | Bearer | `memory:ingest` | Ingest patient health text |

### POST `/memory/ingest`

Runs the full ingestion pipeline: PHI redaction → entity extraction → Neo4j graph → vector embedding → OpenSearch.

**Request:**
```json
{
  "patient_id": "uuid",
  "text": "Patient reports persistent headache for 3 days, taking Paracetamol 500mg twice daily. BP 140/90.",
  "source": "patient_input",
  "encounter_date": "2026-05-01"
}
```

**Response (201):**
```json
{
  "request_id": "uuid",
  "status": "completed",
  "entities": {
    "symptoms": [{"name": "headache", "severity": "moderate", "duration": "3 days"}],
    "medications": [{"name": "Paracetamol", "dosage": "500mg", "frequency": "twice daily"}],
    "vitals": [{"type": "blood_pressure", "value": "140/90", "unit": "mmHg"}]
  },
  "graph_nodes_created": 4,
  "vector_entry_id": "uuid",
  "processing_time_ms": 2340
}
```

---

## Chat (Clinical RAG Query)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/chat/` | Bearer | `chat:query` | Send clinical query (consent-gated) |
| GET | `/chat/sessions` | Bearer | — | List user's chat sessions |
| POST | `/chat/sessions` | Bearer | — | Create new session |
| GET | `/chat/sessions/{id}` | Bearer | — | Get session message history |
| DELETE | `/chat/sessions/{id}` | Bearer | — | Close/archive session |
| GET | `/chat/cache/stats` | Bearer | Admin | Cache health stats |

### POST `/chat/`

Consent-gated. Doctors need active patient consent. Patients always have access to their own data.

**Request:**
```json
{
  "patient_id": "uuid",
  "query": "What medications is this patient currently taking?",
  "requester_id": "doctor-uuid",
  "requester_role": "doctor",
  "session_id": "optional-session-uuid"
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "session_id": "uuid",
  "response": "Based on the patient's records, they are currently taking Paracetamol 500mg...",
  "citations": [
    { "source": "patient_input", "date": "2026-05-01", "text": "..." }
  ],
  "graph_nodes_used": 3,
  "vector_entries_used": 5,
  "retrieval_time_ms": 450,
  "llm_time_ms": 1200,
  "total_time_ms": 1680,
  "cache_hit": false,
  "history_turns": 0,
  "guardrail_action": "NONE"
}
```

**Error (403 — No Consent):**
```json
{
  "detail": {
    "error": "CONSENT_DENIED",
    "reason": "No active consent found",
    "patient_id": "uuid"
  }
}
```

---

## Consent

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/consent/request` | Bearer | `consent:request` | Doctor requests consent |
| POST | `/consent/grant` | Bearer | `consent:grant` | Patient approves/denies |
| GET | `/consent/active/{patient_id}` | Bearer | varies | List active consents |
| DELETE | `/consent/{consent_id}` | Bearer | `consent:grant` | Patient revokes consent |

### POST `/consent/request`

**Request:**
```json
{
  "doctor_id": "auto-filled-from-token",
  "patient_id": "patient-uuid",
  "purpose": "Review medication history for follow-up consultation",
  "requested_scope": "full",
  "duration_hours": 24
}
```

**Scopes:** `full`, `medication_only`, `disease_specific`, `time_bound`

### POST `/consent/grant`

**Request:**
```json
{
  "consent_id": "uuid",
  "patient_id": "patient-uuid",
  "approved": true
}
```

---

## FHIR Exchange

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/fhir/exchange` | Bearer | `fhir:export` | Generate FHIR R4 Bundle |

### POST `/fhir/exchange`

Consent-gated. Generates a FHIR R4 Bundle with Patient, Condition, MedicationStatement, and DocumentReference resources.

**Request:**
```json
{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "consent_id": "uuid",
  "include_summary": true
}
```

**Response:**
```json
{
  "bundle_id": "uuid",
  "fhir_bundle": { "resourceType": "Bundle", "type": "collection", "entry": [...] },
  "clinical_summary": "Patient presents with...",
  "resource_count": 5
}
```

---

## Documents

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/documents/upload` | Bearer | `patient:write_own` | Upload PDF lab report |
| GET | `/documents/my-documents` | Bearer | — | Patient's document history |
| GET | `/documents/{id}` | Bearer | — | Document metadata |
| GET | `/documents/{id}/pdf` | Bearer | — | Download original PDF |
| GET | `/documents/{id}/fhir` | Bearer | — | FHIR DocumentReference |
| POST | `/documents/{id}/trigger-screening` | Bearer | `screening:validate` | HITL triggers screening |

### POST `/documents/upload`

Multipart form upload. PDF only, max 20MB.

**Form Fields:**
- `file` — PDF file (required)
- `patient_id` — Patient UUID (required)
- `report_date` — ISO date string (optional)

**Flow:**
1. PDF stored encrypted in S3
2. Text extracted via PyMuPDF
3. PHI redacted (HIPAA Safe Harbor)
4. Redacted text ingested into vector DB + Neo4j
5. FHIR DocumentReference created

---

## Screening (Responsible AI)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/screening/summarise` | Bearer | `screening:validate` | Generate AI screening |
| GET | `/screening/hitl/queue` | Bearer | `screening:view_pending` | HITL pending queue |
| GET | `/screening/hitl/{id}` | Bearer | `screening:validate` | View screening detail |
| POST | `/screening/hitl/edit-forward` | Bearer | `screening:edit` | Edit & forward to doctor |
| POST | `/screening/hitl/accept-forward` | Bearer | `screening:forward` | Accept & forward |
| POST | `/screening/hitl/reject` | Bearer | `screening:validate` | Reject screening |
| POST | `/screening/hitl/escalate` | Bearer | `screening:escalate` | Escalate issue |
| GET | `/screening/doctor/inbox` | Bearer | `clinical:read` | Doctor's forwarded screenings |
| GET | `/screening/doctor/{id}` | Bearer | `clinical:read` | View specific screening |

---

## Patient Search

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/patient/search?q=` | Bearer | `patient:read_assigned` | Search by name/MRN/ABHA/phone |
| GET | `/patient/{id}/card` | Bearer | `patient:read_assigned` | Lightweight patient card |

### GET `/patient/search`

**Query Params:** `q` (min 2 chars), `limit` (default 10, max 30)

Searches across: full_name, phone, MRN, ABHA ID, email.

---

## Profile

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/profile/me` | Bearer | — | Get own profile |
| PATCH | `/profile/me` | Bearer | — | Update own demographics |

### PATCH `/profile/me`

**Request:**
```json
{
  "full_name": "Updated Name",
  "phone": "+919876543210",
  "gender": "male",
  "date_of_birth": "1990-05-15",
  "address": "123 Main St, Pune",
  "blood_group": "O+",
  "emergency_contact": "+919876543211"
}
```

---

## Nursing

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/nurse/my-patients` | Bearer | `patient:read_assigned` | Doctor's patient list |
| GET | `/nurse/patient/{id}/full-history` | Bearer | `patient:read_assigned` | Full clinical history |
| POST | `/nurse/notes` | Bearer | `patient:read_assigned` | Add IPD note |
| POST | `/nurse/vitals` | Bearer | `vitals:write` | Log vitals (auto-alerts) |
| GET | `/nurse/patients/{id}/vitals` | Bearer | `vitals:read` | Get patient vitals |

### POST `/nurse/vitals`

Auto-generates critical alerts when: temp > 38.5°C or < 35°C, HR > 110 or < 50, SpO2 < 94%.

---

## Prescription (Pharmacy)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/prescription/` | Bearer | `prescription:write` | Create prescription |
| GET | `/prescription/patient/{id}` | Bearer | `prescription:read` | Patient prescriptions |
| GET | `/prescription/queue` | Bearer | `prescription:read` | Pharmacy pending queue |
| GET | `/prescription/stats` | Bearer | `prescription:read` | Pharmacy stats |
| POST | `/prescription/{id}/dispense` | Bearer | `prescription:dispense` | Mark as dispensed |

---

## OPD (Outpatient)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/opd/appointments` | Bearer | `appointment:create` | Book appointment |
| GET | `/opd/appointments` | Bearer | `appointment:read` | List appointments |
| GET | `/opd/appointments/queue` | Bearer | `appointment:read` | Today's OPD queue |
| PATCH | `/opd/appointments/{id}/status` | Bearer | `appointment:create` | Update status |
| GET | `/opd/stats` | Bearer | `appointment:read` | OPD statistics |

---

## IPD (Inpatient)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/ipd/admissions` | Bearer | `admission:create` | Admit patient |
| POST | `/ipd/admissions/{id}/discharge` | Bearer | `admission:discharge` | Discharge patient |
| GET | `/ipd/wards/{ward_id}/beds` | Bearer | `bed:manage` | List ward beds |

---

## Insurance

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/insurance/claims` | Bearer | `insurance:claim_create` | Create claim |
| GET | `/insurance/claims` | Bearer | `insurance:claim_read` | List claims |
| GET | `/insurance/claims/stats` | Bearer | `insurance:claim_read` | Claim statistics |
| PATCH | `/insurance/claims/{id}/status` | Bearer | `insurance:preauth` | Update claim status |

---

## Government Schemes

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/scheme/eligibility/check` | Bearer | `scheme:eligibility_check` | Check PM-JAY/MPJAY eligibility |
| POST | `/scheme/disburse/{claim_id}` | Bearer | `scheme:disburse` | Disburse funds |

---

## MLC (Medico-Legal Case)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/mlc/records` | Bearer | `mlc:create` | Flag MLC case |
| GET | `/mlc/records` | Bearer | `mlc:read` | List MLC records |
| GET | `/mlc/records/{id}` | Bearer | `mlc:read` | Get MLC detail |
| GET | `/mlc/stats` | Bearer | `mlc:read` | MLC statistics |

---

## Hospital Admin

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/hospital/departments` | Bearer | `hospital:manage` | Create department |
| GET | `/hospital/departments` | Bearer | `hospital:manage` | List departments |
| POST | `/hospital/staff` | Bearer | `user:create_staff` | Invite staff member |
| GET | `/hospital/staff` | Bearer | `audit:read_hospital` | List hospital staff |
| GET | `/hospital/stats` | Bearer | `audit:read_hospital` | Hospital statistics |

---

## Super Admin

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/admin/hospitals` | Bearer | `hospital:create` | Create hospital |
| GET | `/admin/hospitals` | Bearer | `system:manage` | List all hospitals |
| POST | `/admin/users` | Bearer | `user:create_staff` | Create any user |
| GET | `/admin/users` | Bearer | `user:read_all` | List all users |
| GET | `/admin/stats` | Bearer | `system:manage` | System-wide stats |

---

## Notifications

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/notifications/` | Bearer | — | Get notifications |
| POST | `/notifications/{id}/read` | Bearer | — | Mark as read |
| POST | `/notifications/mark-all-read` | Bearer | — | Mark all read |
| GET | `/notifications/count` | Bearer | — | Unread count |

---

## Activity Logs

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/logs/` | Bearer | `audit:read_hospital` | Hospital audit logs |
| GET | `/logs/my` | Bearer | — | Personal activity log |

---

## Ward Bot (IoT)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/ward-bot/iot-vitals` | Bearer | `ward_bot:write_vitals` | Receive IoT vitals |
| POST | `/ward-bot/alerts/escalate` | Bearer | `ward_bot:send_alert` | Escalate alert |

---

## Vaidya Guide Bot

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/vaidya/chat` | Bearer | — | Platform guide chatbot |

### POST `/vaidya/chat`

Any authenticated user. No PHI access. Uses separate Bedrock model (Claude 3.7 Sonnet).

**Request:**
```json
{
  "message": "How do I view my health records?",
  "history": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hi! I'm Vaidya..." }
  ],
  "user_role": "patient"
}
```

**Response:**
```json
{
  "reply": "To view your health records, navigate to...",
  "latency_ms": 890,
  "guardrail_action": "NONE"
}
```

---

## Legal & Compliance

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/legal/privacy-policy` | None | — | HIPAA & DPDP privacy policy |
| GET | `/legal/compliance` | None | — | Compliance status flags |

---

## Error Responses

All errors follow this format:

```json
{ "detail": "Error message" }
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or invalid token |
| 403 | Insufficient permissions or consent denied |
| 404 | Resource not found |
| 422 | Unprocessable entity |
| 500 | Internal server error |
| 503 | Service unavailable |

---

## Authentication Header

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

JWT payload contains: `sub` (user_id), `role`, `email`, `hospital_id`, `department_id`, `permissions[]`
