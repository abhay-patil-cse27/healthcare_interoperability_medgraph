# -*- coding: utf-8 -*-
"""
Seed Script - MedGraph Platform Entities
=========================================
Seeds hospitals, departments, and prescriptions.
Run AFTER seed_test_users.py.

Usage:
    venv\Scripts\python.exe backend\scripts\seed_entities.py
"""
import asyncio
import sys
import os
import uuid
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings
from datetime import datetime, timedelta

HOSPITAL_ID   = "hosp-aiims-delhi-001"
HOSPITAL_ID_2 = "hosp-kims-pune-002"
DEPT_OPD      = "dept-opd-cardio-001"
DEPT_OPD_GEN  = "dept-opd-general-002"
DEPT_IPD      = "dept-ipd-general-001"
DEPT_ICU      = "dept-icu-001"
DEPT_PHARMACY = "dept-pharmacy-001"
DEPT_SURGERY  = "dept-surgery-ot-001"
DEPT_EMERGENCY= "dept-emergency-001"

HOSPITALS = [
    {
        "hospital_id": HOSPITAL_ID,
        "name": "AIIMS New Delhi",
        "registration_number": "DL-MOHFW-2001-0001",
        "address": {"city": "New Delhi", "state": "Delhi", "pincode": "110029"},
        "contact_email": "admin@aiims-delhi.gov.in",
        "contact_phone": "011-26588500",
        "admin_user_id": "admin-aiims-001",
        "departments": [DEPT_OPD, DEPT_OPD_GEN, DEPT_IPD, DEPT_ICU, DEPT_PHARMACY, DEPT_SURGERY, DEPT_EMERGENCY],
        "empanelment": {
            "pm_jay": True, "mpjay": False, "abha_linked": True,
            "approved_by": "GoI-MoHFW", "approval_date": "2020-04-01",
            "specialties": ["cardiology","neurology","orthopedics","oncology","emergency"],
            "max_claim_per_case": 500000
        },
        "bed_inventory": {
            "general": {"total": 800, "available": 142},
            "special": {"total": 200, "available": 31},
            "icu":     {"total": 60,  "available": 8},
            "ot":      {"total": 12,  "available": 3}
        },
        "is_active": True,
        "created_by": "seed_script",
        "created_at": datetime.utcnow(),
    },
    {
        "hospital_id": HOSPITAL_ID_2,
        "name": "KIMS Multispecialty Hospital",
        "registration_number": "MH-MOHFW-2015-0042",
        "address": {"city": "Pune", "state": "Maharashtra", "pincode": "411001"},
        "contact_email": "admin@kims-pune.gov.in",
        "contact_phone": "020-27034000",
        "admin_user_id": "admin-kims-001",
        "departments": [],
        "empanelment": {
            "pm_jay": True, "mpjay": True, "abha_linked": True,
            "approved_by": "GoI-MoHFW", "approval_date": "2021-06-15",
            "specialties": ["cardiology","surgery","general medicine"],
            "max_claim_per_case": 300000
        },
        "bed_inventory": {
            "general": {"total": 300, "available": 67},
            "special": {"total": 80,  "available": 12},
            "icu":     {"total": 20,  "available": 3},
            "ot":      {"total": 6,   "available": 1}
        },
        "is_active": True,
        "created_by": "seed_script",
        "created_at": datetime.utcnow(),
    },
]

DEPARTMENTS = [
    {"department_id": DEPT_OPD,       "hospital_id": HOSPITAL_ID, "name": "Cardiology OPD",    "type": "opd",       "sub_type": None,            "bed_count": 0,  "is_active": True},
    {"department_id": DEPT_OPD_GEN,   "hospital_id": HOSPITAL_ID, "name": "General OPD",        "type": "opd",       "sub_type": None,            "bed_count": 0,  "is_active": True},
    {"department_id": DEPT_IPD,       "hospital_id": HOSPITAL_ID, "name": "General IPD Ward",   "type": "ipd",       "sub_type": "non_surgical",  "bed_count": 80, "is_active": True},
    {"department_id": DEPT_ICU,       "hospital_id": HOSPITAL_ID, "name": "Medical ICU",         "type": "icu",       "sub_type": None,            "bed_count": 20, "is_active": True},
    {"department_id": DEPT_PHARMACY,  "hospital_id": HOSPITAL_ID, "name": "Central Pharmacy",   "type": "pharmacy",  "sub_type": None,            "bed_count": 0,  "is_active": True},
    {"department_id": DEPT_SURGERY,   "hospital_id": HOSPITAL_ID, "name": "Orthopedic Surgery OT","type": "ot",      "sub_type": "surgical",      "bed_count": 0,  "is_active": True},
    {"department_id": DEPT_EMERGENCY, "hospital_id": HOSPITAL_ID, "name": "Emergency & Trauma",  "type": "emergency", "sub_type": None,           "bed_count": 15, "is_active": True},
]

PRESCRIPTIONS = [
    {
        "prescription_id": "rx-" + str(uuid.uuid4())[:8],
        "patient_id":   "PATIENT-RAMESH-ID",  # will be updated after lookup
        "patient_name": "Ramesh Yadav",
        "doctor_id":    "DOCTOR-ARUN-ID",
        "doctor_name":  "Dr. Arun Sharma",
        "hospital_id":  HOSPITAL_ID,
        "medications": [
            {"name": "Metformin",    "dosage": "500mg", "frequency": "Twice daily", "duration_days": 30},
            {"name": "Atorvastatin", "dosage": "20mg",  "frequency": "Once at night","duration_days": 30},
        ],
        "diagnosis": "Type 2 Diabetes Mellitus (E11.9) + Dyslipidemia",
        "notes": "Monitor HbA1c after 3 months. Dietary counselling advised.",
        "status": "pending",
        "created_at": datetime.utcnow() - timedelta(minutes=25),
    },
    {
        "prescription_id": "rx-" + str(uuid.uuid4())[:8],
        "patient_id":   "PATIENT-NISHA-ID",
        "patient_name": "Nisha Kulkarni",
        "doctor_id":    "DOCTOR-SNEHA-ID",
        "doctor_name":  "Dr. Sneha Patel",
        "hospital_id":  HOSPITAL_ID,
        "medications": [
            {"name": "Amoxicillin",  "dosage": "500mg", "frequency": "Three times daily","duration_days": 7},
            {"name": "Paracetamol",  "dosage": "650mg", "frequency": "As needed (max 4x/day)","duration_days": 5},
        ],
        "diagnosis": "Community Acquired Pneumonia (J18.9)",
        "notes": "Return if fever persists beyond 3 days. Rest advised.",
        "status": "pending",
        "created_at": datetime.utcnow() - timedelta(minutes=60),
    },
    {
        "prescription_id": "rx-" + str(uuid.uuid4())[:8],
        "patient_id":   "PATIENT-SANJAY-ID",
        "patient_name": "Sanjay Pawar",
        "doctor_id":    "DOCTOR-VIKRAM-ID",
        "doctor_name":  "Dr. Vikram Nair",
        "hospital_id":  HOSPITAL_ID,
        "medications": [
            {"name": "Tramadol",     "dosage": "50mg",  "frequency": "Every 8h (post-op)","duration_days": 5},
            {"name": "Pantoprazole", "dosage": "40mg",  "frequency": "Once before breakfast","duration_days": 14},
            {"name": "Cefuroxime",   "dosage": "500mg", "frequency": "Twice daily","duration_days": 7},
        ],
        "diagnosis": "Post-Op Orthopedic Recovery — Right Knee Arthroplasty (Z96.651)",
        "notes": "Physiotherapy to start Day 2 post-op. Ice packs PRN.",
        "status": "dispensed",
        "created_at": datetime.utcnow() - timedelta(hours=4),
    },
]


async def seed():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]

    print(f"\n{'='*60}")
    print("  MedGraph Entity Seed")
    print(f"{'='*60}\n")

    # --- Hospitals ---
    print("HOSPITALS")
    for h in HOSPITALS:
        existing = await db.hospitals.find_one({"hospital_id": h["hospital_id"]})
        if existing:
            print(f"  [SKIP] {h['name']}")
        else:
            await db.hospitals.insert_one(h)
            print(f"  [OK]   {h['name']}")

    # --- Departments ---
    print("\nDEPARTMENTS")
    for d in DEPARTMENTS:
        existing = await db.departments.find_one({"department_id": d["department_id"]})
        if existing:
            print(f"  [SKIP] {d['name']}")
        else:
            await db.departments.insert_one(d)
            print(f"  [OK]   {d['name']}")

    # --- Prescriptions (resolve real patient/doctor IDs) ---
    print("\nPRESCRIPTIONS")
    patient_map = {}
    for email in ["patient.ramesh@gmail.com", "patient.nisha@gmail.com", "patient.sanjay@gmail.com"]:
        u = await db.users.find_one({"email": email})
        if u:
            patient_map[email] = u["user_id"]

    doctor_map = {}
    for email in ["dr.arun@aiims-delhi.gov.in", "dr.sneha@aiims-delhi.gov.in", "surgeon.vikram@aiims-delhi.gov.in"]:
        u = await db.users.find_one({"email": email})
        if u:
            doctor_map[email] = u["user_id"]

    # Update prescriptions with real IDs
    if patient_map.get("patient.ramesh@gmail.com"):
        PRESCRIPTIONS[0]["patient_id"] = patient_map["patient.ramesh@gmail.com"]
        PRESCRIPTIONS[0]["doctor_id"]  = doctor_map.get("dr.arun@aiims-delhi.gov.in", "unknown")
    if patient_map.get("patient.nisha@gmail.com"):
        PRESCRIPTIONS[1]["patient_id"] = patient_map["patient.nisha@gmail.com"]
        PRESCRIPTIONS[1]["doctor_id"]  = doctor_map.get("dr.sneha@aiims-delhi.gov.in", "unknown")
    if patient_map.get("patient.sanjay@gmail.com"):
        PRESCRIPTIONS[2]["patient_id"] = patient_map["patient.sanjay@gmail.com"]
        PRESCRIPTIONS[2]["doctor_id"]  = doctor_map.get("surgeon.vikram@aiims-delhi.gov.in", "unknown")

    for rx in PRESCRIPTIONS:
        existing = await db.prescriptions.find_one({"prescription_id": rx["prescription_id"]})
        if existing:
            print(f"  [SKIP] {rx['prescription_id']}")
        else:
            await db.prescriptions.insert_one(rx)
            print(f"  [OK]   {rx['prescription_id']} ({rx['patient_name']})")

    print(f"\n{'='*60}")
    print("  Done. Check MongoDB at http://localhost:8081")
    print(f"{'='*60}\n")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
