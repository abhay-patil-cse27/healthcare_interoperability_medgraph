# MedGraph AI — Role-Based Access Control (RBAC)

---

## Overview

MedGraph uses a **permission-based** access control system. Each user has a `role` that maps to a set of granular `permissions`. API endpoints check for specific permissions, not roles directly.

---

## Roles (17)

| Role | Description | Default Route |
|------|-------------|---------------|
| `patient` | End user, manages own health records | `/patient` |
| `doctor` | Clinician, queries patient records (consent-gated) | `/doctor` |
| `surgeon` | Surgical specialist, same as doctor + OT access | `/doctor` |
| `nurse` | Ward nurse, logs vitals and notes | `/nurse` |
| `ward_incharge` | Senior nurse, manages ward operations | `/nurse` |
| `ward_bot` | IoT service account for automated vitals | `/nurse` |
| `pharmacist` | Dispenses prescriptions | `/pharmacist` |
| `opd_staff` | Manages outpatient appointments | `/opd` |
| `receptionist` | Front desk, books appointments | `/opd` |
| `ipd_staff` | Manages inpatient admissions/discharge | `/ipd` |
| `insurance_officer` | Creates and manages insurance claims | `/finance` |
| `scheme_officer` | Govt scheme eligibility and disbursals | `/scheme` |
| `police_interface` | Read-only MLC access | `/mlc` |
| `hitl_validator` | Reviews AI-generated screenings | `/hitl` |
| `hospital_admin` | Manages hospital departments and staff | `/hospital` |
| `govt_admin` | Government-level oversight | `/admin` |
| `super_admin` | Full system access | `/admin` |

---

## Permissions (50+)

### System & Admin

| Permission | Description |
|------------|-------------|
| `system:manage` | Full system control |
| `hospital:create` | Create new hospitals |
| `hospital:manage` | Manage departments, settings |
| `hospital:network_registry` | Network-level hospital registry |
| `govt:audit_read` | Government audit access |
| `user:create_staff` | Create staff accounts |
| `user:read_all` | View all users |
| `audit:read_global` | Global audit logs |
| `audit:read_hospital` | Hospital-scoped audit logs |

### Patient Data & Consent

| Permission | Description |
|------------|-------------|
| `patient:read_own` | Read own health data |
| `patient:read_consented` | Read consented patient data |
| `patient:read_assigned` | Read assigned patients |
| `patient:register` | Register new patients |
| `patient:write_own` | Write own health data |
| `consent:request` | Request patient consent |
| `consent:grant` | Grant/revoke consent |
| `consent:view_own` | View own consents |
| `memory:ingest` | Ingest health records |

### HITL / Responsible AI

| Permission | Description |
|------------|-------------|
| `screening:validate` | Validate AI screenings |
| `screening:edit` | Edit AI summaries |
| `screening:forward` | Forward to doctor |
| `screening:escalate` | Escalate issues |
| `screening:view_pending` | View pending queue |

### Clinical

| Permission | Description |
|------------|-------------|
| `vitals:read` | Read patient vitals |
| `vitals:write` | Log vitals |
| `prescription:write` | Write prescriptions |
| `prescription:read` | Read prescriptions |
| `prescription:dispense` | Dispense medications |
| `drug_interaction:check` | Check drug interactions |
| `chat:query` | Clinical RAG queries |

### FHIR & Interoperability

| Permission | Description |
|------------|-------------|
| `fhir:export` | Export FHIR bundles |
| `fhir:read` | Read FHIR resources |
| `abha:link` | Link ABHA ID |
| `abha:push_record` | Push to ABDM |

### Operations

| Permission | Description |
|------------|-------------|
| `admission:create` | Create IPD admissions |
| `admission:discharge` | Discharge patients |
| `bed:manage` | Manage beds/wards |
| `ward:manage` | Ward operations |
| `appointment:create` | Book OPD appointments |
| `appointment:read` | View appointments |
| `ot:schedule` | Schedule OT |
| `ot:record_intraop` | Record intra-op notes |

### MLC & Legal

| Permission | Description |
|------------|-------------|
| `mlc:create` | Create MLC records |
| `mlc:read` | Read MLC records |
| `mlc:police_share` | Share with police |

### Finance

| Permission | Description |
|------------|-------------|
| `insurance:claim_create` | Create insurance claims |
| `insurance:claim_read` | Read claims |
| `insurance:preauth` | Pre-authorization |
| `scheme:eligibility_check` | Check scheme eligibility |
| `scheme:disburse` | Disburse funds |

### Ward Bot

| Permission | Description |
|------------|-------------|
| `ward_bot:write_vitals` | IoT vitals ingestion |
| `ward_bot:send_alert` | Send escalation alerts |

---

## Role → Permission Mapping

### Patient
```
patient:read_own, patient:write_own, consent:grant, consent:view_own, memory:ingest
```

### Doctor
```
patient:read_consented, patient:read_assigned, consent:request, chat:query,
fhir:export, fhir:read, prescription:write, prescription:read,
drug_interaction:check, vitals:read, mlc:create, mlc:read,
admission:create, appointment:read
```

### Nurse
```
patient:read_assigned, vitals:read, vitals:write, prescription:read,
admission:create, bed:manage
```

### Pharmacist
```
prescription:read, prescription:dispense, drug_interaction:check
```

### Hospital Admin
```
hospital:manage, user:create_staff, audit:read_hospital,
patient:register, appointment:read, bed:manage, ward:manage
```

### Super Admin
```
system:manage, hospital:create, hospital:manage, user:create_staff,
user:read_all, audit:read_global, patient:register
```

### HITL Validator
```
screening:validate, screening:edit, screening:forward,
screening:escalate, screening:view_pending
```

---

## How It Works

### Endpoint Protection

```python
# Single permission required
@router.post("/ingest")
async def ingest(current_user=Depends(require_permission("memory:ingest"))):
    ...

# Any of multiple permissions
@router.post("/upload")
async def upload(current_user=Depends(require_any_permission(["patient:write_own", "memory:ingest"]))):
    ...
```

### Permission Resolution

1. Check JWT token `permissions[]` claim (zero-latency)
2. Fallback to DynamoDB user record permissions (for newly granted perms)
3. If neither contains the required permission → 403

### Consent Layer

Permissions alone don't grant access to patient data. Doctors also need:
- An **active, approved consent** from the patient
- Consent must not be expired or revoked
- Consent scope determines what data is accessible

---

## Staff Account Creation

- **Patients** self-register via `POST /auth/register`
- **Staff** are created by Hospital Admins via `POST /hospital/staff`
- **System users** are created by Super Admins via `POST /admin/users`
- Staff cannot self-register (403 if attempted)
