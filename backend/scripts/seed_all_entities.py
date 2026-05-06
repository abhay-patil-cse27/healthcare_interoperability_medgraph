# -*- coding: utf-8 -*-
"""
Master Seed - All Entities for Every Role
==========================================
Drops and re-seeds: prescriptions, admissions, appointments,
insurance_claims, mlc_records, vitals, ipd_notes, scheme checks.

Usage:
    venv\Scripts\python.exe backend\scripts\seed_all_entities.py
"""
import asyncio, sys, os, uuid, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings
from datetime import datetime, timedelta

HOSPITAL_ID   = "hosp-aiims-delhi-001"
DEPT_OPD      = "dept-opd-cardio-001"
DEPT_OPD_GEN  = "dept-opd-general-002"
DEPT_IPD      = "dept-ipd-general-001"
DEPT_ICU      = "dept-icu-001"
DEPT_PHARMACY = "dept-pharmacy-001"
DEPT_SURGERY  = "dept-surgery-ot-001"

def uid():
    return str(uuid.uuid4())

def ago(hours=0, minutes=0, days=0):
    return datetime.utcnow() - timedelta(hours=hours, minutes=minutes, days=days)


async def seed():
    settings = get_settings()
    client   = AsyncIOMotorClient(settings.mongodb_url)
    db       = client[settings.mongodb_db]

    # Resolve user IDs from DB
    async def uid_for(email):
        u = await db.users.find_one({"email": email})
        return u["user_id"] if u else uid()

    print("\n[1] Resolving user IDs from DB...")
    RAMESH  = await uid_for("patient.ramesh@gmail.com")
    NISHA   = await uid_for("patient.nisha@gmail.com")
    SANJAY  = await uid_for("patient.sanjay@gmail.com")
    DR_ARUN = await uid_for("dr.arun@aiims-delhi.gov.in")
    DR_SNEHA= await uid_for("dr.sneha@aiims-delhi.gov.in")
    VIKRAM  = await uid_for("surgeon.vikram@aiims-delhi.gov.in")
    NURSE_K = await uid_for("nurse.kavita@aiims-delhi.gov.in")
    SURESH  = await uid_for("pharmacist.suresh@aiims-delhi.gov.in")
    DEEPA   = await uid_for("insurance@starhealth.in")
    RAVI    = await uid_for("scheme.ravi@mpjay.gov.in")
    ARJUN   = await uid_for("insp.arjun@delhipolice.gov.in")

    # Fixed IDs for cross-references
    ADM_RAMESH  = "adm-ramesh-001"
    ADM_NISHA   = "adm-nisha-002"
    ADM_SANJAY  = "adm-sanjay-ot-003"
    APT_RAMESH  = "apt-ramesh-cardio-001"
    APT_NISHA   = "apt-nisha-gen-001"
    CLM_RAMESH  = "clm-ramesh-pmjay-001"
    CLM_NISHA   = "clm-nisha-star-002"
    CLM_SANJAY  = "clm-sanjay-star-003"
    MLC_SANJAY  = "mlc-sanjay-acc-001"

    # =========================================================
    print("\n[2] Clearing old seed data...")
    for col in ["prescriptions","admissions","appointments","insurance_claims",
                "mlc_records","vitals","ipd_notes","scheme_checks"]:
        await db[col].delete_many({"_seed": True})

    # =========================================================
    print("[3] Seeding APPOINTMENTS (OPD Staff, Doctors)...")
    appointments = [
        {
            "_seed": True,
            "appointment_id": APT_RAMESH,
            "patient_id":   RAMESH,
            "patient_name": "Ramesh Yadav",
            "doctor_id":    DR_ARUN,
            "doctor_name":  "Dr. Arun Sharma",
            "hospital_id":  HOSPITAL_ID,
            "department_id":DEPT_OPD,
            "department_name":"Cardiology OPD",
            "scheduled_time": ago(hours=2),
            "status":       "completed",
            "reason_for_visit": "Follow-up for Type 2 Diabetes + Hypertension",
            "notes":        "BP 148/92. Adjust Metformin. Refer for lipid panel.",
            "created_at":   ago(days=1),
        },
        {
            "_seed": True,
            "appointment_id": APT_NISHA,
            "patient_id":   NISHA,
            "patient_name": "Nisha Kulkarni",
            "doctor_id":    DR_SNEHA,
            "doctor_name":  "Dr. Sneha Patel",
            "hospital_id":  HOSPITAL_ID,
            "department_id":DEPT_OPD_GEN,
            "department_name":"General OPD",
            "scheduled_time": ago(hours=1),
            "status":       "scheduled",
            "reason_for_visit": "Persistent cough + fever for 5 days",
            "notes":        None,
            "created_at":   ago(hours=3),
        },
        {
            "_seed": True,
            "appointment_id": uid(),
            "patient_id":   SANJAY,
            "patient_name": "Sanjay Pawar",
            "doctor_id":    VIKRAM,
            "doctor_name":  "Dr. Vikram Nair",
            "hospital_id":  HOSPITAL_ID,
            "department_id":DEPT_SURGERY,
            "department_name":"Orthopedic Surgery OT",
            "scheduled_time": ago(days=3),
            "status":       "completed",
            "reason_for_visit": "Pre-operative assessment — Right Knee Arthroplasty",
            "notes":        "Patient cleared for OT. Consent signed. PM-JAY pre-auth pending.",
            "created_at":   ago(days=4),
        },
    ]
    await db.appointments.insert_many(appointments)
    print(f"   Inserted {len(appointments)} appointments")

    # =========================================================
    print("[4] Seeding ADMISSIONS (IPD Staff, Doctors, Nurses)...")
    admissions = [
        {
            "_seed": True,
            "admission_id":    ADM_RAMESH,
            "patient_id":      RAMESH,
            "patient_name":    "Ramesh Yadav",
            "admitting_doctor_id": DR_ARUN,
            "doctor_name":     "Dr. Arun Sharma",
            "hospital_id":     HOSPITAL_ID,
            "department_id":   DEPT_IPD,
            "ward_id":         "ward-ipd-gen-a",
            "bed_id":          "bed-401-a",
            "bed_label":       "Bed 401-A",
            "admission_time":  ago(days=2),
            "status":          "admitted",
            "is_mlc":          False,
            "diagnosis":       "Type 2 DM with Hypertensive Crisis (E11.65 + I10)",
            "scheme_applied":  "PM-JAY",
            "created_at":      ago(days=2),
        },
        {
            "_seed": True,
            "admission_id":    ADM_NISHA,
            "patient_id":      NISHA,
            "patient_name":    "Nisha Kulkarni",
            "admitting_doctor_id": DR_SNEHA,
            "doctor_name":     "Dr. Sneha Patel",
            "hospital_id":     HOSPITAL_ID,
            "department_id":   DEPT_ICU,
            "ward_id":         "ward-icu-1",
            "bed_id":          "bed-icu-03",
            "bed_label":       "ICU Bed 03",
            "admission_time":  ago(hours=10),
            "status":          "admitted",
            "is_mlc":          False,
            "diagnosis":       "Severe Community Acquired Pneumonia (J18.9) — Oxygen support",
            "scheme_applied":  "Private",
            "created_at":      ago(hours=10),
        },
        {
            "_seed": True,
            "admission_id":    ADM_SANJAY,
            "patient_id":      SANJAY,
            "patient_name":    "Sanjay Pawar",
            "admitting_doctor_id": VIKRAM,
            "doctor_name":     "Dr. Vikram Nair",
            "hospital_id":     HOSPITAL_ID,
            "department_id":   DEPT_SURGERY,
            "ward_id":         "ward-ot-post-op",
            "bed_id":          "bed-post-op-02",
            "bed_label":       "Post-Op Bed 02",
            "admission_time":  ago(days=1),
            "status":          "admitted",
            "is_mlc":          True,
            "mlc_fir_number":  "FIR/2026/DL/04821",
            "diagnosis":       "Right Knee Arthroplasty — Post-Op Day 1 (Z96.651)",
            "scheme_applied":  "PM-JAY",
            "created_at":      ago(days=1),
        },
    ]
    await db.admissions.insert_many(admissions)
    print(f"   Inserted {len(admissions)} admissions")

    # =========================================================
    print("[5] Seeding PRESCRIPTIONS (Pharmacist, Doctors)...")
    prescriptions = [
        {
            "_seed": True,
            "prescription_id": "rx-ramesh-001",
            "patient_id":    RAMESH,
            "patient_name":  "Ramesh Yadav",
            "doctor_id":     DR_ARUN,
            "doctor_name":   "Dr. Arun Sharma",
            "hospital_id":   HOSPITAL_ID,
            "encounter_type":"ipd",
            "encounter_id":  ADM_RAMESH,
            "diagnosis":     "Type 2 DM with Hypertensive Crisis (E11.65 + I10)",
            "medications": [
                {"name":"Metformin",    "dosage":"1000mg","frequency":"Twice daily after meals","duration_days":30},
                {"name":"Amlodipine",   "dosage":"5mg",   "frequency":"Once daily morning","duration_days":30},
                {"name":"Atorvastatin", "dosage":"40mg",  "frequency":"Once at night","duration_days":30},
            ],
            "notes":   "Monitor BP twice daily. Low-salt, low-carb diet. HbA1c recheck in 3 months.",
            "status":  "pending",
            "created_at": ago(hours=3),
        },
        {
            "_seed": True,
            "prescription_id": "rx-nisha-001",
            "patient_id":    NISHA,
            "patient_name":  "Nisha Kulkarni",
            "doctor_id":     DR_SNEHA,
            "doctor_name":   "Dr. Sneha Patel",
            "hospital_id":   HOSPITAL_ID,
            "encounter_type":"ipd",
            "encounter_id":  ADM_NISHA,
            "diagnosis":     "Severe CAP (J18.9) — ICU",
            "medications": [
                {"name":"Ceftriaxone",    "dosage":"2g IV","frequency":"Once daily","duration_days":7},
                {"name":"Azithromycin",   "dosage":"500mg","frequency":"Once daily","duration_days":5},
                {"name":"Dexamethasone",  "dosage":"8mg IV","frequency":"Every 8 hours","duration_days":3},
                {"name":"Paracetamol",    "dosage":"1g IV","frequency":"Every 6 hours PRN","duration_days":5},
            ],
            "notes":   "Oxygen support — maintain SpO2 > 94%. IV fluids 1L/day. Daily CBC.",
            "status":  "pending",
            "created_at": ago(hours=5),
        },
        {
            "_seed": True,
            "prescription_id": "rx-sanjay-postop",
            "patient_id":    SANJAY,
            "patient_name":  "Sanjay Pawar",
            "doctor_id":     VIKRAM,
            "doctor_name":   "Dr. Vikram Nair",
            "hospital_id":   HOSPITAL_ID,
            "encounter_type":"ipd",
            "encounter_id":  ADM_SANJAY,
            "diagnosis":     "Post-Op Knee Arthroplasty (Z96.651)",
            "medications": [
                {"name":"Tramadol",    "dosage":"50mg","frequency":"Every 8h post-op","duration_days":5},
                {"name":"Enoxaparin", "dosage":"40mg SC","frequency":"Once daily","duration_days":14},
                {"name":"Cefuroxime", "dosage":"500mg","frequency":"Twice daily","duration_days":7},
                {"name":"Pantoprazole","dosage":"40mg","frequency":"Once before breakfast","duration_days":14},
            ],
            "notes":   "Physiotherapy Day 2. Ice PRN. DVT prophylaxis critical.",
            "status":  "dispensed",
            "created_at": ago(days=1, hours=2),
        },
    ]
    await db.prescriptions.insert_many(prescriptions)
    print(f"   Inserted {len(prescriptions)} prescriptions")

    # =========================================================
    print("[6] Seeding VITALS (Nurses, Ward Bot)...")
    vitals = []
    # Ramesh — 3 readings over 2 days
    for i, (h, temp, hr, spo2, sysbp, diabp) in enumerate([
        (48, 37.8, 92, 97, 148, 94),
        (24, 37.4, 84, 98, 138, 88),
        (2,  37.1, 78, 99, 128, 82),
    ]):
        vitals.append({
            "_seed": True,
            "vital_id":    uid(),
            "patient_id":  RAMESH,
            "admission_id":ADM_RAMESH,
            "recorded_by": NURSE_K,
            "recorder_name":"Nurse Kavita Desai",
            "recorded_at": ago(hours=h),
            "temperature_c":temp, "heart_rate":hr, "sp02":spo2,
            "blood_pressure_sys":sysbp, "blood_pressure_dia":diabp,
            "respiratory_rate": 16,
            "is_alert": sysbp > 140,
        })
    # Nisha — ICU vitals every 4h, some alerts
    for i, (h, temp, hr, spo2, sysbp, diabp) in enumerate([
        (10, 38.9, 108, 91, 110, 72),
        (6,  38.5, 98,  93, 108, 70),
        (2,  38.1, 92,  95, 112, 74),
    ]):
        vitals.append({
            "_seed": True,
            "vital_id":    uid(),
            "patient_id":  NISHA,
            "admission_id":ADM_NISHA,
            "recorded_by": "ward_bot",
            "recorder_name":"Ward Bot IoT",
            "recorded_at": ago(hours=h),
            "temperature_c":temp, "heart_rate":hr, "sp02":spo2,
            "blood_pressure_sys":sysbp, "blood_pressure_dia":diabp,
            "respiratory_rate": 24,
            "is_alert": spo2 < 94 or temp > 38.5,
        })
    # Sanjay — post-op stable
    vitals.append({
        "_seed": True,
        "vital_id":    uid(),
        "patient_id":  SANJAY,
        "admission_id":ADM_SANJAY,
        "recorded_by": NURSE_K,
        "recorder_name":"Nurse Kavita Desai",
        "recorded_at": ago(hours=4),
        "temperature_c":37.2, "heart_rate":76, "sp02":98,
        "blood_pressure_sys":122, "blood_pressure_dia":80,
        "respiratory_rate":16, "is_alert": False,
    })
    await db.vitals.insert_many(vitals)
    print(f"   Inserted {len(vitals)} vital readings")

    # =========================================================
    print("[7] Seeding IPD NOTES (Doctors, Nurses)...")
    ipd_notes = [
        {
            "_seed": True,
            "note_id":      uid(),
            "admission_id": ADM_RAMESH,
            "patient_id":   RAMESH,
            "author_id":    DR_ARUN,
            "author_name":  "Dr. Arun Sharma",
            "author_role":  "doctor",
            "note_type":    "morning_round",
            "content":      "Patient conscious, oriented. BP remains elevated at 138/88. Continue IV Labetolol. Oral medications to start at lunch. Dietician consult requested. No chest pain or SOB.",
            "timestamp":    ago(hours=6),
            "is_flagged":   False,
        },
        {
            "_seed": True,
            "note_id":      uid(),
            "admission_id": ADM_RAMESH,
            "patient_id":   RAMESH,
            "author_id":    NURSE_K,
            "author_name":  "Nurse Kavita Desai",
            "author_role":  "nurse",
            "note_type":    "nursing_shift",
            "content":      "Evening shift handover. Patient ate 70% of dinner. IV line patent. Urine output 1200ml in 8h (adequate). Sleeping comfortably. BP 128/82 at 22:00.",
            "timestamp":    ago(hours=2),
            "is_flagged":   False,
        },
        {
            "_seed": True,
            "note_id":      uid(),
            "admission_id": ADM_NISHA,
            "patient_id":   NISHA,
            "author_id":    DR_SNEHA,
            "author_name":  "Dr. Sneha Patel",
            "author_role":  "doctor",
            "note_type":    "morning_round",
            "content":      "CRITICAL: SpO2 dropped to 91% overnight. Increased O2 flow to 8L/min via venturi mask. Chest X-ray ordered STAT. CRP pending. Consider CT chest if no improvement in 6h.",
            "timestamp":    ago(hours=8),
            "is_flagged":   True,
        },
        {
            "_seed": True,
            "note_id":      uid(),
            "admission_id": ADM_SANJAY,
            "patient_id":   SANJAY,
            "author_id":    VIKRAM,
            "author_name":  "Dr. Vikram Nair",
            "author_role":  "surgeon",
            "note_type":    "morning_round",
            "content":      "Post-Op Day 1. Wound site clean — no bleeding. ROM exercises started. Physiotherapy team to visit 14:00. DVT stockings in place. Pain score 4/10, managed with Tramadol. Discharge planned Day 4 if stable.",
            "timestamp":    ago(hours=5),
            "is_flagged":   False,
        },
    ]
    await db.ipd_notes.insert_many(ipd_notes)
    print(f"   Inserted {len(ipd_notes)} IPD notes")

    # =========================================================
    print("[8] Seeding INSURANCE CLAIMS (Insurance Officer)...")
    claims = [
        {
            "_seed": True,
            "claim_id":       CLM_RAMESH,
            "admission_id":   ADM_RAMESH,
            "patient_id":     RAMESH,
            "patient_name":   "Ramesh Yadav",
            "hospital_id":    HOSPITAL_ID,
            "tpa_name":       "Star Health TPA",
            "scheme":         "PM-JAY",
            "diagnosis_code": "E11.65",
            "claim_amount":   85000.0,
            "approved_amount":None,
            "status":         "pre_auth_pending",
            "submitted_by":   DEEPA,
            "submitted_at":   ago(hours=4),
            "settled_at":     None,
            "notes":          "IPD admission — DM with Hypertensive Crisis. 3-day stay anticipated.",
        },
        {
            "_seed": True,
            "claim_id":       CLM_NISHA,
            "admission_id":   ADM_NISHA,
            "patient_id":     NISHA,
            "patient_name":   "Nisha Kulkarni",
            "hospital_id":    HOSPITAL_ID,
            "tpa_name":       "Star Health TPA",
            "scheme":         "Private Insurance",
            "diagnosis_code": "J18.9",
            "claim_amount":   145000.0,
            "approved_amount":None,
            "status":         "initiated",
            "submitted_by":   DEEPA,
            "submitted_at":   ago(hours=8),
            "settled_at":     None,
            "notes":          "ICU admission — Severe CAP. Requires pre-auth for ICU charges.",
        },
        {
            "_seed": True,
            "claim_id":       CLM_SANJAY,
            "admission_id":   ADM_SANJAY,
            "patient_id":     SANJAY,
            "patient_name":   "Sanjay Pawar",
            "hospital_id":    HOSPITAL_ID,
            "tpa_name":       "Star Health TPA",
            "scheme":         "PM-JAY",
            "diagnosis_code": "Z96.651",
            "claim_amount":   420000.0,
            "approved_amount":420000.0,
            "status":         "approved",
            "submitted_by":   DEEPA,
            "submitted_at":   ago(days=2),
            "settled_at":     None,
            "notes":          "Right Knee Arthroplasty — PM-JAY Package H20022. Pre-auth approved Rs 4.2L.",
        },
    ]
    await db.insurance_claims.insert_many(claims)
    print(f"   Inserted {len(claims)} insurance claims")

    # =========================================================
    print("[9] Seeding SCHEME ELIGIBILITY CHECKS (Scheme Officer)...")
    scheme_checks = [
        {
            "_seed": True,
            "check_id":       uid(),
            "patient_id":     RAMESH,
            "patient_name":   "Ramesh Yadav",
            "scheme_name":    "PM-JAY",
            "identity_type":  "ABHA",
            "identity_value": "91-1234-5678-9012",
            "is_eligible":    True,
            "coverage_cap":   500000.0,
            "family_id":      "PMJAY-FAM-MH-098234",
            "checked_by":     RAVI,
            "timestamp":      ago(days=3),
        },
        {
            "_seed": True,
            "check_id":       uid(),
            "patient_id":     SANJAY,
            "patient_name":   "Sanjay Pawar",
            "scheme_name":    "PM-JAY",
            "identity_type":  "Aadhaar",
            "identity_value": "XXXX-XXXX-4821",
            "is_eligible":    True,
            "coverage_cap":   500000.0,
            "family_id":      "PMJAY-FAM-MH-112984",
            "checked_by":     RAVI,
            "timestamp":      ago(days=4),
        },
        {
            "_seed": True,
            "check_id":       uid(),
            "patient_id":     NISHA,
            "patient_name":   "Nisha Kulkarni",
            "scheme_name":    "MPJAY",
            "identity_type":  "Ration Card",
            "identity_value": "MH/2021/RC/094821",
            "is_eligible":    False,
            "coverage_cap":   None,
            "family_id":      None,
            "checked_by":     RAVI,
            "notes":          "Above income threshold. Referred to private insurance.",
            "timestamp":      ago(days=5),
        },
    ]
    await db.scheme_checks.insert_many(scheme_checks)
    print(f"   Inserted {len(scheme_checks)} scheme checks")

    # =========================================================
    print("[10] Seeding MLC RECORDS (Police, Doctors)...")
    mlc_records = [
        {
            "_seed": True,
            "mlc_id":              MLC_SANJAY,
            "admission_id":        ADM_SANJAY,
            "patient_id":          SANJAY,
            "patient_name":        "Sanjay Pawar",
            "doctor_id":           VIKRAM,
            "doctor_name":         "Dr. Vikram Nair",
            "hospital_id":         HOSPITAL_ID,
            "case_type":           "accident",
            "injury_description":  "RTA — Right knee crush injury from road traffic accident on NH-48. Patient brought by ambulance. No LOC. Right lower limb trauma with fracture confirmed on X-ray.",
            "fir_number":          "FIR/2026/DL/04821",
            "police_station":      "IGI Traffic Police Station, New Delhi",
            "referred_by":         "Emergency triage nurse",
            "is_locked":           False,
            "created_at":          ago(days=1, hours=6),
        },
    ]
    await db.mlc_records.insert_many(mlc_records)
    print(f"   Inserted {len(mlc_records)} MLC records")

    print(f"\n{'='*60}")
    print("  Master seed complete!")
    print(f"{'='*60}")
    print("  Collections seeded:")
    for col in ["prescriptions","admissions","appointments","insurance_claims","mlc_records","vitals","ipd_notes","scheme_checks"]:
        count = await db[col].count_documents({"_seed": True})
        print(f"    {col:<22} {count} seeded documents")
    print(f"{'='*60}\n")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
