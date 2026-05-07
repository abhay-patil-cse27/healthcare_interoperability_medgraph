# -*- coding: utf-8 -*-
"""
MedGraph Demo Seed — Full Hackathon Data
==========================================
Seeds comprehensive demo data using EXISTING users only.
Covers: consents, assignments, Neo4j graph entities,
scheme eligibility (Maharashtra), screening summaries, notifications.

Usage:
    cd backend
    venv\\Scripts\\python.exe -m scripts.seed_demo_data
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.dynamo_service import get_dynamodb
from app.services.neo4j_service import Neo4jService

HOSPITAL_ID = "hosp-aiims-delhi-001"


def uid():
    return str(uuid.uuid4())


def ago(days=0, hours=0):
    return (datetime.utcnow() - timedelta(days=days, hours=hours)).isoformat()


def future(hours=0, days=0):
    return (datetime.utcnow() + timedelta(days=days, hours=hours)).isoformat()


async def resolve_users(db):
    """Resolve existing user IDs by email."""
    mapping = {}
    emails = [
        "patient.ramesh@gmail.com",
        "patient.nisha@gmail.com",
        "patient.sanjay@gmail.com",
        "dr.arun@aiims-delhi.gov.in",
        "dr.sneha@aiims-delhi.gov.in",
        "surgeon.vikram@aiims-delhi.gov.in",
        "nurse.kavita@aiims-delhi.gov.in",
        "pharmacist.suresh@aiims-delhi.gov.in",
        "insurance@starhealth.in",
        "scheme.ravi@mpjay.gov.in",
        "insp.arjun@delhipolice.gov.in",
        "admin@aiims-delhi.gov.in",
    ]
    for email in emails:
        user = await db.users.find_one({"email": email})
        if user:
            mapping[email] = user["user_id"]
            print(f"  [OK] {email} -> {user['user_id'][:12]}...")
        else:
            mapping[email] = uid()
            print(f"  [!!] {email} NOT FOUND - using random ID")
    return mapping


async def seed_consents(db, u):
    """Create active consents linking patients to doctors."""
    print("\n[2] Seeding CONSENTS (patient->doctor assignments)...")
    consents = [
        {
            "consent_id": uid(),
            "patient_id": u["patient.ramesh@gmail.com"],
            "doctor_id": u["dr.arun@aiims-delhi.gov.in"],
            "scope": "full",
            "status": "approved",
            "duration_hours": 720,
            "valid_until": future(days=30),
            "granted_at": ago(days=5),
            "created_at": ago(days=5),
            "filters": {},
        },
        {
            "consent_id": uid(),
            "patient_id": u["patient.nisha@gmail.com"],
            "doctor_id": u["dr.sneha@aiims-delhi.gov.in"],
            "scope": "full",
            "status": "approved",
            "duration_hours": 720,
            "valid_until": future(days=30),
            "granted_at": ago(days=3),
            "created_at": ago(days=3),
            "filters": {},
        },
        {
            "consent_id": uid(),
            "patient_id": u["patient.sanjay@gmail.com"],
            "doctor_id": u["surgeon.vikram@aiims-delhi.gov.in"],
            "scope": "full",
            "status": "approved",
            "duration_hours": 720,
            "valid_until": future(days=30),
            "granted_at": ago(days=2),
            "created_at": ago(days=2),
            "filters": {},
        },
        {
            "consent_id": uid(),
            "patient_id": u["patient.ramesh@gmail.com"],
            "doctor_id": u["dr.sneha@aiims-delhi.gov.in"],
            "scope": "medication_only",
            "status": "approved",
            "duration_hours": 168,
            "valid_until": future(days=7),
            "granted_at": ago(days=1),
            "created_at": ago(days=1),
            "filters": {},
        },
    ]
    for c in consents:
        await db.consents.insert_one(c)
    print(f"   Inserted {len(consents)} consents")


async def seed_scheme_eligibility(db, u):
    """Maharashtra scheme eligibility data."""
    print("\n[3] Seeding SCHEME ELIGIBILITY (Maharashtra focus)...")
    checks = [
        {
            "id": uid(),
            "check_id": uid(),
            "patient_id": u["patient.ramesh@gmail.com"],
            "patient_name": "Ramesh Yadav",
            "scheme_name": "PM-JAY (Ayushman Bharat)",
            "identity_type": "Ayushman Card",
            "identity_value": "PMJAY-MH-2024-098234",
            "is_eligible": True,
            "coverage_cap": 500000.0,
            "family_id": "PMJAY-FAM-MH-098234",
            "ration_card": "MH/APL/2021/094821",
            "ration_card_type": "APL (Orange)",
            "district": "Pune",
            "taluka": "Haveli",
            "checked_by": u["scheme.ravi@mpjay.gov.in"],
            "timestamp": ago(days=3),
            "additional_schemes_eligible": [
                "Mahatma Jyotiba Phule Jan Arogya Yojana (MJPJAY)",
            ],
            "notes": "Patient has valid Ayushman card + APL ration card. Eligible for MJPJAY up to Rs 1.5L + PM-JAY up to Rs 5L.",
        },
        {
            "id": uid(),
            "check_id": uid(),
            "patient_id": u["patient.ramesh@gmail.com"],
            "patient_name": "Ramesh Yadav",
            "scheme_name": "Mahatma Jyotiba Phule Jan Arogya Yojana (MJPJAY)",
            "identity_type": "Ration Card (Orange/Yellow)",
            "identity_value": "MH/APL/2021/094821",
            "is_eligible": True,
            "coverage_cap": 150000.0,
            "family_id": "MJPJAY-FAM-MH-094821",
            "district": "Pune",
            "taluka": "Haveli",
            "checked_by": u["scheme.ravi@mpjay.gov.in"],
            "timestamp": ago(days=3),
            "eligibility_criteria_met": [
                "Valid Maharashtra domicile",
                "Orange/Yellow ration card holder",
                "Annual family income below Rs 1.5L",
            ],
            "covered_procedures": [
                "Cardiac surgery (up to Rs 1.5L)",
                "Knee replacement (up to Rs 1.5L)",
                "Cancer treatment (up to Rs 1.5L)",
                "Renal transplant",
            ],
            "notes": "MJPJAY covers 971 procedures across 30 specialties in empanelled hospitals.",
        },
        {
            "id": uid(),
            "check_id": uid(),
            "patient_id": u["patient.sanjay@gmail.com"],
            "patient_name": "Sanjay Pawar",
            "scheme_name": "PM-JAY (Ayushman Bharat)",
            "identity_type": "Ayushman Card",
            "identity_value": "PMJAY-MH-2024-112984",
            "is_eligible": True,
            "coverage_cap": 500000.0,
            "family_id": "PMJAY-FAM-MH-112984",
            "ration_card": "MH/BPL/2020/112984",
            "ration_card_type": "BPL (Yellow)",
            "district": "Mumbai Suburban",
            "taluka": "Andheri",
            "checked_by": u["scheme.ravi@mpjay.gov.in"],
            "timestamp": ago(days=4),
            "additional_schemes_eligible": [
                "Mahatma Jyotiba Phule Jan Arogya Yojana (MJPJAY)",
                "Rajiv Gandhi Jeevandayee Arogya Yojana (legacy)",
            ],
            "notes": "BPL card holder. Knee arthroplasty covered under PM-JAY package H20022 (Rs 4.2L). Also eligible for MJPJAY.",
        },
        {
            "id": uid(),
            "check_id": uid(),
            "patient_id": u["patient.nisha@gmail.com"],
            "patient_name": "Nisha Kulkarni",
            "scheme_name": "PM-JAY (Ayushman Bharat)",
            "identity_type": "Aadhaar",
            "identity_value": "XXXX-XXXX-7823",
            "is_eligible": False,
            "coverage_cap": None,
            "family_id": None,
            "ration_card": None,
            "ration_card_type": None,
            "district": "Pune",
            "checked_by": u["scheme.ravi@mpjay.gov.in"],
            "timestamp": ago(days=5),
            "notes": "Not in SECC database. Annual income above Rs 5L threshold. Private insurance recommended.",
        },
        {
            "id": uid(),
            "check_id": uid(),
            "patient_id": u["patient.nisha@gmail.com"],
            "patient_name": "Nisha Kulkarni",
            "scheme_name": "MJPJAY",
            "identity_type": "Ration Card",
            "identity_value": "N/A",
            "is_eligible": False,
            "coverage_cap": None,
            "checked_by": u["scheme.ravi@mpjay.gov.in"],
            "timestamp": ago(days=5),
            "notes": "No valid Orange/Yellow ration card. Above income threshold for MJPJAY.",
        },
    ]
    for c in checks:
        await db.scheme_checks.insert_one(c)
    print(f"   Inserted {len(checks)} scheme eligibility checks")


async def seed_notifications(db, u):
    """Seed notifications for various roles."""
    print("\n[4] Seeding NOTIFICATIONS...")
    notifs = [
        {
            "id": uid(),
            "notification_id": uid(),
            "user_id": u["dr.arun@aiims-delhi.gov.in"],
            "type": "consent_granted",
            "priority": "normal",
            "title": "New consent from Ramesh Yadav",
            "message": "Patient Ramesh Yadav has granted you full access to their health records for 30 days.",
            "patient_id": u["patient.ramesh@gmail.com"],
            "for_roles": ["doctor"],
            "hospital_id": HOSPITAL_ID,
            "read_by": [],
            "created_at": ago(days=5),
        },
        {
            "id": uid(),
            "notification_id": uid(),
            "user_id": u["nurse.kavita@aiims-delhi.gov.in"],
            "type": "vitals_alert",
            "priority": "high",
            "title": "Critical Vitals — Nisha Kulkarni (ICU Bed 03)",
            "message": "SpO2 dropped to 91%. Temperature 38.9C. Immediate review required.",
            "patient_id": u["patient.nisha@gmail.com"],
            "for_roles": ["nurse", "doctor", "ward_incharge"],
            "hospital_id": HOSPITAL_ID,
            "read_by": [],
            "created_at": ago(hours=10),
        },
        {
            "id": uid(),
            "notification_id": uid(),
            "user_id": u["insurance@starhealth.in"],
            "type": "claim_update",
            "priority": "normal",
            "title": "PM-JAY Pre-Auth Approved — Sanjay Pawar",
            "message": "Knee arthroplasty claim Rs 4.2L approved under PM-JAY package H20022.",
            "patient_id": u["patient.sanjay@gmail.com"],
            "for_roles": ["insurance_officer"],
            "hospital_id": HOSPITAL_ID,
            "read_by": [],
            "created_at": ago(days=2),
        },
        {
            "id": uid(),
            "notification_id": uid(),
            "user_id": u["dr.sneha@aiims-delhi.gov.in"],
            "type": "screening_ready",
            "priority": "normal",
            "title": "AI Screening Ready — Nisha Kulkarni",
            "message": "Lab report screening completed by HITL validator. Review available in your inbox.",
            "patient_id": u["patient.nisha@gmail.com"],
            "for_roles": ["doctor"],
            "hospital_id": HOSPITAL_ID,
            "read_by": [],
            "created_at": ago(hours=6),
        },
    ]
    for n in notifs:
        await db.notifications.insert_one(n)
    print(f"   Inserted {len(notifs)} notifications")


async def seed_neo4j_graph(u):
    """Seed rich clinical entities into Neo4j for all 3 patients."""
    print("\n[5] Seeding NEO4J GRAPH (clinical entities + relationships)...")
    neo4j = Neo4jService()

    # Ramesh — Diabetic + Hypertensive
    n1 = await neo4j.store_entities(
        patient_id=u["patient.ramesh@gmail.com"],
        entities={
            "conditions": [
                {"name": "Type 2 Diabetes Mellitus", "icd10_code": "E11.65", "status": "active"},
                {"name": "Essential Hypertension", "icd10_code": "I10", "status": "active"},
                {"name": "Hyperlipidemia", "icd10_code": "E78.5", "status": "active"},
            ],
            "medications": [
                {"name": "Metformin", "dosage": "1000mg", "frequency": "Twice daily"},
                {"name": "Amlodipine", "dosage": "5mg", "frequency": "Once daily"},
                {"name": "Atorvastatin", "dosage": "40mg", "frequency": "Once at night"},
                {"name": "Aspirin", "dosage": "75mg", "frequency": "Once daily"},
            ],
            "vitals": [
                {"type": "Blood Pressure", "value": "148/92", "unit": "mmHg", "status": "high"},
                {"type": "HbA1c", "value": "8.2", "unit": "%", "status": "high"},
                {"type": "Fasting Glucose", "value": "186", "unit": "mg/dL", "status": "high"},
                {"type": "LDL Cholesterol", "value": "162", "unit": "mg/dL", "status": "high"},
                {"type": "BMI", "value": "28.4", "unit": "kg/m2", "status": "high"},
            ],
            "symptoms": [
                {"name": "headache", "severity": "moderate", "duration": "2 weeks"},
                {"name": "fatigue", "severity": "mild", "duration": "1 month"},
                {"name": "blurred vision", "severity": "mild", "duration": "3 days"},
            ],
            "allergies": [
                {"substance": "Sulfonamides", "reaction": "Skin rash", "severity": "moderate"},
            ],
        },
        source="seed_demo",
        encounter_date=ago(days=2),
    )
    print(f"   Ramesh: {n1} nodes")

    # Nisha — Pneumonia ICU
    n2 = await neo4j.store_entities(
        patient_id=u["patient.nisha@gmail.com"],
        entities={
            "conditions": [
                {"name": "Severe Community Acquired Pneumonia", "icd10_code": "J18.9", "status": "active"},
                {"name": "Acute Respiratory Distress", "icd10_code": "J80", "status": "active"},
                {"name": "Iron Deficiency Anemia", "icd10_code": "D50.9", "status": "chronic"},
            ],
            "medications": [
                {"name": "Ceftriaxone", "dosage": "2g IV", "frequency": "Once daily"},
                {"name": "Azithromycin", "dosage": "500mg", "frequency": "Once daily"},
                {"name": "Dexamethasone", "dosage": "8mg IV", "frequency": "Every 8 hours"},
                {"name": "Paracetamol", "dosage": "1g IV", "frequency": "Every 6h PRN"},
                {"name": "Ferrous Sulfate", "dosage": "200mg", "frequency": "Once daily"},
            ],
            "vitals": [
                {"type": "SpO2", "value": "91", "unit": "%", "status": "critical"},
                {"type": "Temperature", "value": "38.9", "unit": "C", "status": "high"},
                {"type": "Heart Rate", "value": "108", "unit": "bpm", "status": "high"},
                {"type": "Respiratory Rate", "value": "28", "unit": "/min", "status": "high"},
                {"type": "CRP", "value": "142", "unit": "mg/L", "status": "critical"},
            ],
            "symptoms": [
                {"name": "productive cough", "severity": "severe", "duration": "5 days"},
                {"name": "high fever", "severity": "severe", "duration": "5 days"},
                {"name": "dyspnea", "severity": "severe", "duration": "3 days"},
                {"name": "chest pain on breathing", "severity": "moderate", "duration": "2 days"},
            ],
            "allergies": [
                {"substance": "Penicillin", "reaction": "Anaphylaxis", "severity": "severe"},
            ],
        },
        source="seed_demo",
        encounter_date=ago(hours=10),
    )
    print(f"   Nisha: {n2} nodes")

    # Sanjay — Post-op knee
    n3 = await neo4j.store_entities(
        patient_id=u["patient.sanjay@gmail.com"],
        entities={
            "conditions": [
                {"name": "Osteoarthritis Right Knee", "icd10_code": "M17.11", "status": "treated"},
                {"name": "Post Knee Arthroplasty", "icd10_code": "Z96.651", "status": "active"},
                {"name": "Road Traffic Accident", "icd10_code": "V89.2", "status": "resolved"},
            ],
            "medications": [
                {"name": "Tramadol", "dosage": "50mg", "frequency": "Every 8h"},
                {"name": "Enoxaparin", "dosage": "40mg SC", "frequency": "Once daily"},
                {"name": "Cefuroxime", "dosage": "500mg", "frequency": "Twice daily"},
                {"name": "Pantoprazole", "dosage": "40mg", "frequency": "Once before breakfast"},
            ],
            "vitals": [
                {"type": "Blood Pressure", "value": "122/80", "unit": "mmHg", "status": "normal"},
                {"type": "Heart Rate", "value": "76", "unit": "bpm", "status": "normal"},
                {"type": "Temperature", "value": "37.2", "unit": "C", "status": "normal"},
                {"type": "Pain Score", "value": "4", "unit": "/10", "status": "moderate"},
            ],
            "symptoms": [
                {"name": "post-operative pain", "severity": "moderate", "duration": "1 day"},
                {"name": "knee swelling", "severity": "mild", "duration": "1 day"},
            ],
            "allergies": [],
        },
        source="seed_demo",
        encounter_date=ago(days=1),
    )
    print(f"   Sanjay: {n3} nodes")

    await neo4j.close()
    print(f"   Total graph nodes created: {n1 + n2 + n3}")


async def seed_screening_summaries(db, u):
    """Seed AI screening summaries for HITL demo."""
    print("\n[6] Seeding SCREENING SUMMARIES (HITL pipeline demo)...")
    screenings = [
        {
            "screening_id": uid(),
            "patient_id": u["patient.ramesh@gmail.com"],
            "consent_status": "VERIFIED",
            "summary_date": ago(days=1),
            "source_document_id": "doc-ramesh-lab-001",
            "ai_summary": """## Lab Report Screening — Ramesh Yadav

### Flagged Abnormalities:
1. **HbA1c: 8.2%** (Reference: <7.0%) — POORLY CONTROLLED diabetes
2. **Fasting Glucose: 186 mg/dL** (Reference: 70-100) — HIGH
3. **LDL Cholesterol: 162 mg/dL** (Reference: <100) — HIGH cardiovascular risk
4. **Blood Pressure: 148/92 mmHg** — Stage 2 Hypertension
5. **Serum Creatinine: 1.4 mg/dL** (Reference: 0.7-1.3) — BORDERLINE elevated

### Clinical Observation (AI-generated, not a diagnosis):
Patient shows signs of poorly controlled Type 2 DM with emerging nephropathy risk. Cardiovascular risk profile is elevated. Current medication regimen may need intensification.

### Recommended Actions:
- Consider adding GLP-1 agonist or SGLT2 inhibitor
- Lipid panel recheck in 4 weeks
- Urine albumin-to-creatinine ratio (UACR) test
- Ophthalmology referral for diabetic retinopathy screening""",
            "flagged_abnormalities": [
                {"parameter": "HbA1c", "observed_value": "8.2", "unit": "%", "reference_range": "<7.0", "status": "HIGH", "source_section": "Biochemistry"},
                {"parameter": "Fasting Glucose", "observed_value": "186", "unit": "mg/dL", "reference_range": "70-100", "status": "HIGH", "source_section": "Biochemistry"},
                {"parameter": "LDL Cholesterol", "observed_value": "162", "unit": "mg/dL", "reference_range": "<100", "status": "HIGH", "source_section": "Lipid Profile"},
                {"parameter": "Serum Creatinine", "observed_value": "1.4", "unit": "mg/dL", "reference_range": "0.7-1.3", "status": "HIGH", "source_section": "Renal Function"},
            ],
            "abnormality_count": 4,
            "critical_count": 0,
            "stage": "ai_generated",
            "responsible_ai_version": "2.0.0",
            "model_used": "us.anthropic.claude-sonnet-4-6",
        },
        {
            "screening_id": uid(),
            "patient_id": u["patient.nisha@gmail.com"],
            "consent_status": "VERIFIED",
            "summary_date": ago(hours=8),
            "source_document_id": "doc-nisha-lab-001",
            "ai_summary": """## Lab Report Screening — Nisha Kulkarni

### Flagged Abnormalities:
1. **CRP: 142 mg/L** (Reference: <5) — CRITICAL inflammatory marker
2. **WBC: 18,200/uL** (Reference: 4000-11000) — HIGH leukocytosis
3. **Procalcitonin: 4.8 ng/mL** (Reference: <0.5) — CRITICAL bacterial infection marker
4. **SpO2: 91%** (Reference: >95%) — CRITICAL hypoxemia
5. **Hemoglobin: 9.2 g/dL** (Reference: 12-16) — LOW anemia

### Clinical Observation (AI-generated, not a diagnosis):
Severe systemic inflammatory response consistent with bacterial pneumonia. Critical hypoxemia requiring oxygen support. Pre-existing anemia may complicate recovery.

### Recommended Actions:
- Blood culture sensitivity STAT
- CT chest if no improvement in 6h
- Consider ICU escalation protocol
- Transfusion if Hb drops below 8 g/dL""",
            "flagged_abnormalities": [
                {"parameter": "CRP", "observed_value": "142", "unit": "mg/L", "reference_range": "<5", "status": "CRITICAL", "source_section": "Inflammatory Markers"},
                {"parameter": "WBC", "observed_value": "18200", "unit": "/uL", "reference_range": "4000-11000", "status": "HIGH", "source_section": "CBC"},
                {"parameter": "Procalcitonin", "observed_value": "4.8", "unit": "ng/mL", "reference_range": "<0.5", "status": "CRITICAL", "source_section": "Inflammatory Markers"},
                {"parameter": "Hemoglobin", "observed_value": "9.2", "unit": "g/dL", "reference_range": "12-16", "status": "LOW", "source_section": "CBC"},
            ],
            "abnormality_count": 4,
            "critical_count": 2,
            "stage": "ai_generated",
            "responsible_ai_version": "2.0.0",
            "model_used": "us.anthropic.claude-sonnet-4-6",
        },
    ]
    for s in screenings:
        await db.screening_summaries.insert_one(s)
    print(f"   Inserted {len(screenings)} screening summaries")


async def seed_audit_logs(db, u):
    """Seed audit trail entries."""
    print("\n[7] Seeding AUDIT LOGS...")
    logs = [
        {
            "patient_id": u["patient.ramesh@gmail.com"],
            "sort_key": f"audit#{ago(days=5)}#{uid()[:8]}",
            "log_id": uid(),
            "action": "consent_granted",
            "user_id": u["patient.ramesh@gmail.com"],
            "accessor_role": "patient",
            "resource_type": "consent",
            "timestamp": ago(days=5),
            "metadata": {"doctor_id": u["dr.arun@aiims-delhi.gov.in"], "scope": "full"},
        },
        {
            "patient_id": u["patient.ramesh@gmail.com"],
            "sort_key": f"audit#{ago(days=4)}#{uid()[:8]}",
            "log_id": uid(),
            "action": "clinical_query",
            "user_id": u["dr.arun@aiims-delhi.gov.in"],
            "accessor_role": "doctor",
            "resource_type": "PatientQuery",
            "timestamp": ago(days=4),
            "metadata": {"query_preview": "What medications is this patient on?", "consent_scope": "full"},
        },
        {
            "patient_id": u["patient.ramesh@gmail.com"],
            "sort_key": f"audit#{ago(days=1)}#{uid()[:8]}",
            "log_id": uid(),
            "action": "document_uploaded_hipaa_compliant",
            "user_id": u["patient.ramesh@gmail.com"],
            "accessor_role": "patient",
            "resource_type": "pdf_lab_report",
            "timestamp": ago(days=1),
            "metadata": {"filename": "ramesh_blood_report_may2026.pdf", "pages": 3, "phi_redactions": 12},
        },
        {
            "patient_id": u["patient.nisha@gmail.com"],
            "sort_key": f"audit#{ago(hours=10)}#{uid()[:8]}",
            "log_id": uid(),
            "action": "vitals_recorded",
            "user_id": u["nurse.kavita@aiims-delhi.gov.in"],
            "accessor_role": "nurse",
            "resource_type": "vitals",
            "timestamp": ago(hours=10),
            "metadata": {"is_alert": True, "spo2": 91, "temperature": 38.9},
        },
    ]
    for l in logs:
        await db.audit_logs.insert_one(l)
    print(f"   Inserted {len(logs)} audit logs")


async def main():
    print("=" * 60)
    print("  MedGraph — Full Demo Data Seed")
    print("=" * 60)

    db = get_dynamodb()

    print("\n[1] Resolving existing users...")
    u = await resolve_users(db)

    await seed_consents(db, u)
    await seed_scheme_eligibility(db, u)
    await seed_notifications(db, u)
    await seed_neo4j_graph(u)
    await seed_screening_summaries(db, u)
    await seed_audit_logs(db, u)

    print("\n" + "=" * 60)
    print("  DEMO SEED COMPLETE!")
    print("=" * 60)
    print("\n  What was seeded:")
    print("    - 4 active consents (patient->doctor assignments)")
    print("    - 5 scheme eligibility checks (PM-JAY + MJPJAY Maharashtra)")
    print("    - 4 notifications (alerts, consents, claims)")
    print("    - 40+ Neo4j graph nodes with relationships")
    print("    - 2 AI screening summaries (HITL queue)")
    print("    - 4 audit log entries")
    print("\n  Demo credentials:")
    print("    Patient:  patient.ramesh@gmail.com / Patient@123")
    print("    Doctor:   dr.arun@aiims-delhi.gov.in / Doctor@1234")
    print("    Nurse:    nurse.kavita@aiims-delhi.gov.in / Nurse@12345")
    print("    Admin:    admin@aiims-delhi.gov.in / HospAdmin@123")
    print("    Scheme:   scheme.ravi@mpjay.gov.in / Scheme@12345")
    print("    Insurance:insurance@starhealth.in / Insure@12345")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
