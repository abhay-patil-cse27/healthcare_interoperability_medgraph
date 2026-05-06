# API Reference

> Base URL: `http://localhost:8000`  
> Auth: Bearer JWT token in `Authorization` header  
> Content-Type: `application/json` (except file uploads: `multipart/form-data`)

---

## Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | None | Patient self-registration |
| POST | `/auth/login` | None | Login (returns JWT) |
| GET | `/auth/me` | JWT | Get current user profile |

### POST `/auth/login`
```json
// Request
{ "email": "doctor@hospital.com", "password": "SecurePass123" }

// Response 200
{ "access_token": "eyJ...", "token_type": "bearer" }
```

---

## Chat (Clinical RAG)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/chat/` | JWT | Send message (consent-gated, session-aware) |
| GET | `/chat/sessions` | JWT | List user's chat sessions |
| POST | `/chat/sessions?patient_id={id}` | JWT | Create new session |
| GET | `/chat/sessions/{session_id}` | JWT | Get full message history |
| DELETE | `/chat/sessions/{session_id}` | JWT | Delete/archive session |

### POST `/chat/`
```json
// Request
{
  "patient_id": "uuid",
  "query": "What medications is this patient on?",
  "session_id": "uuid (optional — auto-creates if omitted)"
}

// Response 200
{
  "request_id": "uuid",
  "session_id": "uuid",
  "response": "Based on the patient records...",
  "citations": [
    { "source_type": "graph_node", "source_id": "uuid", "relevance_score": 0.92, "excerpt": "..." }
  ],
  "graph_nodes_used": 5,
  "vector_entries_used": 3,
  "retrieval_time_ms": 120,
  "llm_time_ms": 850,
  "total_time_ms": 1050,
  "cache_hit": false,
  "history_turns": 2
}
```

---

## Consent

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/consent/request` | JWT (doctor) | Request consent from patient |
| POST | `/consent/grant` | JWT (patient) | Grant/deny consent |
| GET | `/consent/active/{patient_id}` | JWT | List active consents |
| DELETE | `/consent/{consent_id}` | JWT (patient) | Revoke consent |

### POST `/consent/request`
```json
{
  "doctor_id": "uuid",
  "patient_id": "uuid",
  "purpose": "Review lab results for diabetes management",
  "requested_scope": "full | disease_specific | time_bound | medication_only",
  "disease_filter": ["diabetes"],
  "duration_hours": 24
}
```

---

## Documents (PDF Upload)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/documents/upload` | JWT | Upload PDF lab report |
| GET | `/documents/my-documents` | JWT (patient) | List patient's documents |
| GET | `/documents/{id}` | JWT | Get document metadata |
| GET | `/documents/{id}/pdf` | JWT | Download original PDF |
| GET | `/documents/{id}/fhir` | JWT | Get FHIR DocumentReference |
| POST | `/documents/{id}/trigger-screening` | JWT (HITL) | Trigger AI screening |

### POST `/documents/upload`
```
Content-Type: multipart/form-data
Fields: file (PDF), patient_id (string), report_date (optional string)
```
```json
// Response 200
{
  "document_id": "uuid",
  "total_pages": 10,
  "sections_found": 15,
  "high_priority_sections": 6,
  "privacy": {
    "phi_redacted": true,
    "redactions_applied": 8,
    "redacted_fields": ["patient_name", "phone", "address", "vid_number"],
    "hipaa_compliant": true
  },
  "storage": { "original_pdf_stored": true, "gridfs_stored": true },
  "fhir": { "document_reference_created": true, "loinc_code": "11502-2" },
  "ingestion": { "chunks_total": 12, "chunks_successful": 12 }
}
```

---

## Screening (Responsible AI)

### HITL Validator Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/screening/summarise` | JWT (HITL) | Generate AI screening |
| GET | `/screening/hitl/queue` | JWT (HITL) | Pending validation queue |
| GET | `/screening/hitl/{id}` | JWT (HITL) | Full screening detail |
| POST | `/screening/hitl/edit-forward` | JWT (HITL) | Edit & forward to doctor |
| POST | `/screening/hitl/accept-forward` | JWT (HITL) | Accept & forward to doctor |
| POST | `/screening/hitl/reject` | JWT (HITL) | Reject (data mismatch) |
| POST | `/screening/hitl/escalate` | JWT (HITL) | Escalate to admin |

### Doctor Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/screening/doctor/inbox` | JWT (doctor) | Forwarded screenings |
| GET | `/screening/doctor/{id}` | JWT (doctor) | View screening (consent-gated) |
| POST | `/screening/doctor/{id}/reviewed` | JWT (doctor) | Mark as reviewed |

### POST `/screening/hitl/edit-forward`
```json
{
  "screening_id": "uuid",
  "edited_summary": "Corrected markdown summary...",
  "edit_reason": "Fixed glucose value transcription error",
  "target_doctor_id": "uuid",
  "consent_duration_hours": 24
}
```

---

## Memory (Health Data Ingestion)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/memory/ingest` | JWT | Ingest health text (PHI-redacted before storage) |
| GET | `/memory/history/{patient_id}` | JWT | Get ingestion history |

### POST `/memory/ingest`
```json
{
  "patient_id": "uuid",
  "text": "Lab report text content...",
  "source": "lab_result | prescription | discharge_note | patient_input",
  "encounter_date": "2026-03-03T09:08:00Z"
}
```

---

## FHIR

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/fhir/exchange` | JWT (doctor) | Generate FHIR R4 bundle |
| GET | `/fhir/bundle/{bundle_id}` | JWT | Retrieve stored bundle |

---

## Admin

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/admin/hospitals` | JWT (super_admin) | Onboard new hospital |
| GET | `/admin/hospitals` | JWT (super_admin) | List all hospitals |
| POST | `/admin/users` | JWT (super_admin) | Create system user |
| GET | `/admin/users` | JWT (super_admin) | List all users |
| GET | `/admin/stats` | JWT (super_admin) | System-wide statistics |

---

## Hospital Admin

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/hospital/departments` | JWT (hospital_admin) | Create department |
| GET | `/hospital/departments` | JWT (hospital_admin) | List departments |
| POST | `/hospital/staff` | JWT (hospital_admin) | Invite staff member |
| GET | `/hospital/staff` | JWT (hospital_admin) | List staff |
| GET | `/hospital/stats` | JWT (hospital_admin) | Hospital statistics |

---

## Clinical (Nurse/Doctor)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/nurse/vitals` | JWT (nurse) | Log patient vitals |
| GET | `/nurse/patients/{id}/vitals` | JWT | Get vitals history |
| GET | `/nurse/my-patients` | JWT (nurse/doctor) | Get assigned patients |
| GET | `/nurse/patient/{id}/full-history` | JWT | Full patient history |
| POST | `/nurse/notes` | JWT (nurse) | Add clinical note |

---

## Pharmacy

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/prescription/` | JWT (doctor) | Create prescription |
| GET | `/prescription/patient/{id}` | JWT | Get patient prescriptions |
| GET | `/prescription/queue` | JWT (pharmacist) | Dispensing queue |
| POST | `/prescription/{id}/dispense` | JWT (pharmacist) | Mark dispensed |
| GET | `/prescription/stats` | JWT | Prescription statistics |

---

## OPD

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/opd/appointments` | JWT | Book appointment |
| GET | `/opd/appointments` | JWT | List appointments |
| GET | `/opd/appointments/queue` | JWT | Get OPD queue |
| PATCH | `/opd/appointments/{id}/status` | JWT | Update status |
| GET | `/opd/stats` | JWT | OPD statistics |

---

## IPD

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/ipd/admissions` | JWT | Create admission |
| POST | `/ipd/admissions/{id}/discharge` | JWT | Discharge patient |
| GET | `/ipd/wards/{ward_id}/beds` | JWT | Get bed availability |

---

## Insurance

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/insurance/claims` | JWT | Create claim |
| GET | `/insurance/claims` | JWT | List claims (filterable) |
| PATCH | `/insurance/claims/{id}/status` | JWT | Update claim status |
| GET | `/insurance/claims/stats` | JWT | Claim statistics |

---

## Scheme (PM-JAY / MPJAY)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/scheme/eligibility/check` | JWT | Check scheme eligibility |
| POST | `/scheme/disburse/{claim_id}` | JWT | Disburse benefit |

---

## MLC (Medico-Legal)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/mlc/records` | JWT (doctor) | Create MLC record |
| GET | `/mlc/records` | JWT | List MLC records |
| GET | `/mlc/records/{id}` | JWT | Get specific record |
| GET | `/mlc/stats` | JWT | MLC statistics |

---

## Patient Search

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/patient/search?q={query}` | JWT | Search by name/MRN/phone/ABHA |
| GET | `/patient/{id}/card` | JWT | Get patient identity card |

---

## Profile

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/profile/me` | JWT | Get own profile |
| PATCH | `/profile/me` | JWT | Update own profile |

---

## Notifications

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/notifications/` | JWT | Get notifications |
| POST | `/notifications/{id}/read` | JWT | Mark as read |
| POST | `/notifications/mark-all-read` | JWT | Mark all read |
| GET | `/notifications/count` | JWT | Unread count |

---

## Health Check

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | None | Service health status |

```json
// Response
{
  "status": "healthy | degraded",
  "services": { "mongodb": true, "neo4j": true, "qdrant": true }
}
```
