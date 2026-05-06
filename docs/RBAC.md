# Role-Based Access Control (RBAC)

> 17 Roles · 50+ Permissions · JWT-Embedded · Consent-Gated

---

## Roles

| # | Role | Login Path | Description |
|---|------|-----------|-------------|
| 1 | `super_admin` | `/admin` | Full system control, hospital onboarding |
| 2 | `govt_admin` | `/admin` | MoHFW oversight, national audit |
| 3 | `hospital_admin` | `/hospital` | Staff management, departments (is a doctor/employee) |
| 4 | `doctor` | `/doctor` | OPD/IPD physician, clinical RAG, prescriptions |
| 5 | `surgeon` | `/doctor` | OT scheduling, surgical care |
| 6 | `nurse` | `/nurse` | Ward bedside care, vitals logging |
| 7 | `ward_incharge` | `/nurse` | Shift supervisor, ward management |
| 8 | `ward_bot` | `/nurse` | IoT autonomous monitoring |
| 9 | `pharmacist` | `/pharmacist` | Prescription dispensing, drug interactions |
| 10 | `opd_staff` | `/opd` | Appointments, patient registration |
| 11 | `ipd_staff` | `/ipd` | Admissions, bed management, discharge |
| 12 | `receptionist` | `/opd` | Front desk, appointment booking |
| 13 | `insurance_officer` | `/finance` | Claims, TPA, pre-authorization |
| 14 | `scheme_officer` | `/scheme` | PM-JAY/MPJAY eligibility, disbursement |
| 15 | `police_interface` | `/mlc` | MLC records (read-only, 72h TTL) |
| 16 | `hitl_validator` | `/hitl` | AI screening validation, edit/forward/reject |
| 17 | `patient` | `/patient` | Own records, consent, ABHA linking |

---

## Permission Categories

### System & Admin
| Permission | Roles |
|-----------|-------|
| `system:manage` | super_admin |
| `hospital:create` | super_admin |
| `hospital:manage` | super_admin, hospital_admin |
| `hospital:network_registry` | super_admin |
| `govt:audit_read` | govt_admin, hospital_admin |
| `user:create_staff` | super_admin, hospital_admin |
| `user:read_all` | super_admin, hospital_admin |
| `audit:read_global` | super_admin |
| `audit:read_hospital` | hospital_admin, doctor, surgeon, hitl_validator |

### Patient Data & Consent
| Permission | Roles |
|-----------|-------|
| `patient:read_own` | patient |
| `patient:read_consented` | doctor, surgeon |
| `patient:read_assigned` | doctor, surgeon, nurse, ward_incharge, ipd_staff, hitl_validator |
| `patient:register` | hospital_admin, opd_staff |
| `patient:write_own` | patient |
| `consent:request` | doctor, surgeon |
| `consent:grant` | patient |
| `consent:view_own` | patient, hitl_validator |
| `memory:ingest` | doctor, surgeon, patient |

### HITL / Screening
| Permission | Roles |
|-----------|-------|
| `screening:validate` | hitl_validator |
| `screening:edit` | hitl_validator |
| `screening:forward` | hitl_validator |
| `screening:escalate` | hitl_validator |
| `screening:view_pending` | hitl_validator |

### Clinical
| Permission | Roles |
|-----------|-------|
| `vitals:read` | doctor, surgeon, nurse, ward_incharge, hitl_validator |
| `vitals:write` | doctor, surgeon, nurse, ward_incharge |
| `prescription:write` | doctor, surgeon |
| `prescription:read` | doctor, surgeon, nurse, ward_incharge, pharmacist |
| `prescription:dispense` | pharmacist |
| `drug_interaction:check` | doctor, surgeon, nurse, ward_incharge, pharmacist |
| `chat:query` | doctor, surgeon |

### FHIR & Interoperability
| Permission | Roles |
|-----------|-------|
| `fhir:export` | doctor, surgeon |
| `fhir:read` | doctor, surgeon, patient |
| `abha:link` | doctor, surgeon, opd_staff, ipd_staff, patient |
| `abha:push_record` | doctor, surgeon |

### Operations
| Permission | Roles |
|-----------|-------|
| `admission:create` | doctor, surgeon, ipd_staff |
| `admission:discharge` | doctor, surgeon, ipd_staff |
| `bed:manage` | ipd_staff |
| `ward:manage` | ward_incharge |
| `appointment:create` | doctor, surgeon, opd_staff, receptionist |
| `appointment:read` | doctor, surgeon, nurse, ward_incharge, opd_staff, receptionist, patient |
| `ot:schedule` | surgeon |
| `ot:record_intraop` | surgeon |

### MLC & Legal
| Permission | Roles |
|-----------|-------|
| `mlc:create` | doctor, surgeon |
| `mlc:read` | doctor, surgeon, nurse, ward_incharge, police_interface |
| `mlc:police_share` | doctor, surgeon |

### Insurance & Schemes
| Permission | Roles |
|-----------|-------|
| `insurance:claim_create` | insurance_officer |
| `insurance:claim_read` | insurance_officer, doctor, surgeon |
| `insurance:preauth` | insurance_officer |
| `scheme:eligibility_check` | scheme_officer, doctor, surgeon |
| `scheme:disburse` | scheme_officer |

---

## Consent Architecture

### Consent Scopes
| Scope | Description |
|-------|-------------|
| `full` | Complete access to all patient data |
| `disease_specific` | Only records matching specified diseases |
| `time_bound` | Only records within a date range |
| `medication_only` | Only medication-related records |

### Consent Lifecycle
```
Doctor requests → Patient receives notification → Patient approves/denies
                                                        ↓
                                              Consent active (time-limited)
                                                        ↓
                                              Auto-expires after duration_hours
```

### Self-Access Rule
Patients ALWAYS have full access to their own data — no consent needed.

### HITL Screening Consent
Separate from patient→doctor consent. When HITL forwards a screening:
- Creates a `doctor_screening_consent` record
- Time-bound (1–168 hours, configurable)
- Doctor can ONLY view the screening while consent is active
- Auto-expires, access revoked

---

## JWT Token Structure

```json
{
  "sub": "user_id (UUID)",
  "role": "doctor",
  "permissions": ["patient:read_consented", "chat:query", ...],
  "hospital_id": "hosp-aiims-delhi-001",
  "exp": 1717200000,
  "iat": 1717196400
}
```

---

## User Onboarding

| User Type | How They're Created |
|-----------|-------------------|
| Patient | Self-registration via `/auth/register` |
| Hospital Admin | Super Admin assigns via `/admin/users` |
| All other staff | Hospital Admin invites via `/hospital/staff` |
| HITL Validator | Super Admin creates via `/admin/users` |

**Staff can NEVER self-register.** Only patients can self-register.
