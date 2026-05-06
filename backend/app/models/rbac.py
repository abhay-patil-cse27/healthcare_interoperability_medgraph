from enum import Enum
from typing import List, Dict

class Permission(str, Enum):
    # System & Global Admin
    SYSTEM_MANAGE = "system:manage"
    HOSPITAL_CREATE = "hospital:create"
    HOSPITAL_MANAGE = "hospital:manage"
    HOSPITAL_NETWORK_REGISTRY = "hospital:network_registry"
    GOVT_AUDIT_READ = "govt:audit_read"
    USER_CREATE_STAFF = "user:create_staff"
    USER_READ_ALL = "user:read_all"
    AUDIT_READ_GLOBAL = "audit:read_global"
    AUDIT_READ_HOSPITAL = "audit:read_hospital"

    # Patient Data & Consent
    PATIENT_READ_OWN = "patient:read_own"
    PATIENT_READ_CONSENTED = "patient:read_consented"
    PATIENT_READ_ASSIGNED = "patient:read_assigned"
    PATIENT_REGISTER = "patient:register"
    PATIENT_WRITE_OWN = "patient:write_own"
    CONSENT_REQUEST = "consent:request"
    CONSENT_GRANT = "consent:grant"
    CONSENT_VIEW_OWN = "consent:view_own"
    MEMORY_INGEST = "memory:ingest"

    # HITL Validator (Responsible AI)
    SCREENING_VALIDATE = "screening:validate"
    SCREENING_EDIT = "screening:edit"
    SCREENING_FORWARD = "screening:forward"
    SCREENING_ESCALATE = "screening:escalate"
    SCREENING_VIEW_PENDING = "screening:view_pending"

    # Clinical
    VITALS_READ = "vitals:read"
    VITALS_WRITE = "vitals:write"
    PRESCRIPTION_WRITE = "prescription:write"
    PRESCRIPTION_READ = "prescription:read"
    PRESCRIPTION_DISPENSE = "prescription:dispense"
    DRUG_INTERACTION_CHECK = "drug_interaction:check"
    CHAT_QUERY = "chat:query"

    # FHIR & Interoperability
    FHIR_EXPORT = "fhir:export"
    FHIR_READ = "fhir:read"
    ABHA_LINK = "abha:link"
    ABHA_PUSH_RECORD = "abha:push_record"

    # OPD & IPD Operations
    ADMISSION_CREATE = "admission:create"
    ADMISSION_DISCHARGE = "admission:discharge"
    BED_MANAGE = "bed:manage"
    WARD_MANAGE = "ward:manage"
    APPOINTMENT_CREATE = "appointment:create"
    APPOINTMENT_READ = "appointment:read"

    # Surgical / OT
    OT_SCHEDULE = "ot:schedule"
    OT_RECORD_INTRAOP = "ot:record_intraop"

    # MLC & Police
    MLC_CREATE = "mlc:create"
    MLC_READ = "mlc:read"
    MLC_POLICE_SHARE = "mlc:police_share"

    # Insurance & Schemes
    INSURANCE_CLAIM_CREATE = "insurance:claim_create"
    INSURANCE_CLAIM_READ = "insurance:claim_read"
    INSURANCE_PREAUTH = "insurance:preauth"
    SCHEME_ELIGIBILITY_CHECK = "scheme:eligibility_check"
    SCHEME_DISBURSE = "scheme:disburse"

    # Bot specific
    WARD_BOT_WRITE_VITALS = "ward_bot:write_vitals"
    WARD_BOT_SEND_ALERT = "ward_bot:send_alert"


class UserRole(str, Enum):
    GOVT_ADMIN = "govt_admin"
    SUPER_ADMIN = "super_admin"
    HOSPITAL_ADMIN = "hospital_admin"
    DOCTOR = "doctor"
    SURGEON = "surgeon"
    NURSE = "nurse"
    WARD_INCHARGE = "ward_incharge"
    WARD_BOT = "ward_bot"
    PHARMACIST = "pharmacist"
    OPD_STAFF = "opd_staff"
    IPD_STAFF = "ipd_staff"
    RECEPTIONIST = "receptionist"
    INSURANCE_OFFICER = "insurance_officer"
    SCHEME_OFFICER = "scheme_officer"
    POLICE_INTERFACE = "police_interface"
    HITL_VALIDATOR = "hitl_validator"
    PATIENT = "patient"


# Pre-defined permission bundles for roles
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.GOVT_ADMIN: [
        Permission.SYSTEM_MANAGE, Permission.HOSPITAL_CREATE, Permission.HOSPITAL_NETWORK_REGISTRY,
        Permission.GOVT_AUDIT_READ, Permission.USER_READ_ALL, Permission.AUDIT_READ_GLOBAL
    ],
    UserRole.SUPER_ADMIN: [
        Permission.SYSTEM_MANAGE, Permission.HOSPITAL_CREATE, Permission.HOSPITAL_MANAGE,
        Permission.USER_CREATE_STAFF, Permission.USER_READ_ALL, Permission.AUDIT_READ_GLOBAL
    ],
    UserRole.HOSPITAL_ADMIN: [
        Permission.HOSPITAL_MANAGE, Permission.USER_CREATE_STAFF, Permission.USER_READ_ALL,
        Permission.AUDIT_READ_HOSPITAL, Permission.PATIENT_REGISTER, Permission.GOVT_AUDIT_READ
    ],
    UserRole.DOCTOR: [
        Permission.PATIENT_READ_CONSENTED, Permission.PATIENT_READ_ASSIGNED,
        Permission.VITALS_READ, Permission.VITALS_WRITE,
        Permission.PRESCRIPTION_WRITE, Permission.PRESCRIPTION_READ, Permission.DRUG_INTERACTION_CHECK,
        Permission.CONSENT_REQUEST, Permission.FHIR_EXPORT, Permission.FHIR_READ,
        Permission.ADMISSION_CREATE, Permission.ADMISSION_DISCHARGE, Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_READ, Permission.MEMORY_INGEST, Permission.CHAT_QUERY,
        Permission.MLC_CREATE, Permission.MLC_READ, Permission.MLC_POLICE_SHARE,
        Permission.INSURANCE_CLAIM_READ, Permission.SCHEME_ELIGIBILITY_CHECK, Permission.ABHA_LINK,
        Permission.ABHA_PUSH_RECORD, Permission.AUDIT_READ_HOSPITAL
    ],
    UserRole.SURGEON: [
        Permission.PATIENT_READ_CONSENTED, Permission.PATIENT_READ_ASSIGNED,
        Permission.VITALS_READ, Permission.VITALS_WRITE,
        Permission.PRESCRIPTION_WRITE, Permission.PRESCRIPTION_READ, Permission.DRUG_INTERACTION_CHECK,
        Permission.CONSENT_REQUEST, Permission.FHIR_EXPORT, Permission.FHIR_READ,
        Permission.ADMISSION_CREATE, Permission.ADMISSION_DISCHARGE, Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_READ, Permission.MEMORY_INGEST, Permission.CHAT_QUERY,
        Permission.MLC_CREATE, Permission.MLC_READ, Permission.MLC_POLICE_SHARE,
        Permission.INSURANCE_CLAIM_READ, Permission.SCHEME_ELIGIBILITY_CHECK,
        Permission.OT_SCHEDULE, Permission.OT_RECORD_INTRAOP, Permission.ABHA_PUSH_RECORD, Permission.AUDIT_READ_HOSPITAL
    ],
    UserRole.NURSE: [
        Permission.PATIENT_READ_ASSIGNED, Permission.VITALS_READ, Permission.VITALS_WRITE,
        Permission.PRESCRIPTION_READ, Permission.DRUG_INTERACTION_CHECK, Permission.APPOINTMENT_READ,
        Permission.MLC_READ
    ],
    UserRole.WARD_INCHARGE: [
        Permission.PATIENT_READ_ASSIGNED, Permission.VITALS_READ, Permission.VITALS_WRITE,
        Permission.PRESCRIPTION_READ, Permission.DRUG_INTERACTION_CHECK, Permission.APPOINTMENT_READ,
        Permission.MLC_READ, Permission.WARD_MANAGE
    ],
    UserRole.WARD_BOT: [
        Permission.WARD_BOT_WRITE_VITALS, Permission.WARD_BOT_SEND_ALERT
    ],
    UserRole.PHARMACIST: [
        Permission.PRESCRIPTION_READ, Permission.PRESCRIPTION_DISPENSE, Permission.DRUG_INTERACTION_CHECK
    ],
    UserRole.OPD_STAFF: [
        Permission.PATIENT_REGISTER, Permission.APPOINTMENT_CREATE, Permission.APPOINTMENT_READ,
        Permission.ABHA_LINK
    ],
    UserRole.IPD_STAFF: [
        Permission.PATIENT_READ_ASSIGNED, Permission.ADMISSION_CREATE, Permission.ADMISSION_DISCHARGE,
        Permission.BED_MANAGE, Permission.APPOINTMENT_READ, Permission.ABHA_LINK
    ],
    UserRole.RECEPTIONIST: [
        Permission.PATIENT_REGISTER, Permission.APPOINTMENT_CREATE, Permission.APPOINTMENT_READ
    ],
    UserRole.INSURANCE_OFFICER: [
        Permission.INSURANCE_CLAIM_CREATE, Permission.INSURANCE_CLAIM_READ, Permission.INSURANCE_PREAUTH
    ],
    UserRole.SCHEME_OFFICER: [
        Permission.SCHEME_ELIGIBILITY_CHECK, Permission.SCHEME_DISBURSE
    ],
    UserRole.POLICE_INTERFACE: [
        Permission.MLC_READ
    ],
    UserRole.HITL_VALIDATOR: [
        Permission.SCREENING_VALIDATE, Permission.SCREENING_EDIT,
        Permission.SCREENING_FORWARD, Permission.SCREENING_ESCALATE,
        Permission.SCREENING_VIEW_PENDING, Permission.PATIENT_READ_ASSIGNED,
        Permission.VITALS_READ, Permission.CONSENT_VIEW_OWN,
        Permission.AUDIT_READ_HOSPITAL,
    ],
    UserRole.PATIENT: [
        Permission.PATIENT_READ_OWN, Permission.PATIENT_WRITE_OWN, Permission.CONSENT_GRANT,
        Permission.CONSENT_VIEW_OWN, Permission.FHIR_READ, Permission.APPOINTMENT_READ,
        Permission.MEMORY_INGEST, Permission.ABHA_LINK
    ],
}
