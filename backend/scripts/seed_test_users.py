# -*- coding: utf-8 -*-
"""
Seed Script - MedGraph Platform Test Users
==========================================
Inserts one realistic user for every RBAC role.
Safe to re-run - skips existing emails.

Usage (from project root with venv active):
    cd backend
    python scripts/seed_test_users.py
"""

import asyncio
import sys
import os
import uuid
import warnings
warnings.filterwarnings("ignore")  # suppress bcrypt version warning
import os; os.environ["PYTHONIOENCODING"] = "utf-8"
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from app.models.rbac import UserRole, ROLE_PERMISSIONS
from app.utils.jwt_handler import get_password_hash
from app.config import get_settings

# ── Shared hospital/dept IDs so users are linked realistically ──────────────
HOSPITAL_ID    = "hosp-aiims-delhi-001"
DEPT_OPD       = "dept-opd-cardio-001"
DEPT_IPD       = "dept-ipd-general-001"
DEPT_ICU       = "dept-icu-001"
DEPT_PHARMACY  = "dept-pharmacy-001"
DEPT_FINANCE   = "dept-finance-001"

# ── Test users ───────────────────────────────────────────────────────────────
TEST_USERS = [
    # ── Government tier ──────────────────────────────────────────────────────
    {
        "full_name": "Rajesh Kumar IAS",
        "email": "superadmin@mohfw.gov.in",
        "password": "SuperAdmin@123",
        "role": UserRole.SUPER_ADMIN,
        "hospital_id": None,
        "department_id": None,
        "phone": "+91-9800000001",
    },
    {
        "full_name": "Ananya Singh IFS",
        "email": "govtadmin@nha.gov.in",
        "password": "GovtAdmin@123",
        "role": UserRole.GOVT_ADMIN,
        "hospital_id": None,
        "department_id": None,
        "phone": "+91-9800000002",
    },

    # ── Hospital administration ───────────────────────────────────────────────
    {
        "full_name": "Dr. Priya Mehta",
        "email": "admin@aiims-delhi.gov.in",
        "password": "HospAdmin@123",
        "role": UserRole.HOSPITAL_ADMIN,
        "hospital_id": HOSPITAL_ID,
        "department_id": None,
        "phone": "+91-9810000001",
    },

    # ── Clinical — Doctor ─────────────────────────────────────────────────────
    {
        "full_name": "Dr. Arun Sharma",
        "email": "dr.arun@aiims-delhi.gov.in",
        "password": "Doctor@1234",
        "role": UserRole.DOCTOR,
        "sub_role": "general",
        "specialization": "Cardiology",
        "license_number": "MCI-DL-2019-04821",
        "hospital_id": HOSPITAL_ID,
        "department_id": DEPT_OPD,
        "phone": "+91-9811000001",
    },
    {
        "full_name": "Dr. Sneha Patel",
        "email": "dr.sneha@aiims-delhi.gov.in",
        "password": "Doctor@1234",
        "role": UserRole.DOCTOR,
        "sub_role": "general",
        "specialization": "Internal Medicine",
        "license_number": "MCI-MH-2020-09134",
        "hospital_id": HOSPITAL_ID,
        "department_id": DEPT_OPD,
        "phone": "+91-9811000002",
    },

    # ── Clinical — Surgeon ────────────────────────────────────────────────────
    {
        "full_name": "Dr. Vikram Nair",
        "email": "surgeon.vikram@aiims-delhi.gov.in",
        "password": "Surgeon@1234",
        "role": UserRole.SURGEON,
        "sub_role": "surgical",
        "specialization": "Orthopedic Surgery",
        "license_number": "MCI-DL-2015-00234",
        "hospital_id": HOSPITAL_ID,
        "department_id": DEPT_IPD,
        "phone": "+91-9812000001",
    },

    # ── Nursing ───────────────────────────────────────────────────────────────
    {
        "full_name": "Kavita Desai",
        "email": "nurse.kavita@aiims-delhi.gov.in",
        "password": "Nurse@12345",
        "role": UserRole.NURSE,
        "hospital_id": HOSPITAL_ID,
        "department_id": DEPT_IPD,
        "phone": "+91-9813000001",
    },
    {
        "full_name": "Rekha Sharma",
        "email": "incharge.rekha@aiims-delhi.gov.in",
        "password": "WardIncharge@1",
        "role": UserRole.WARD_INCHARGE,
        "hospital_id": HOSPITAL_ID,
        "department_id": DEPT_ICU,
        "phone": "+91-9813000002",
    },

    # ── Pharmacy ──────────────────────────────────────────────────────────────
    {
        "full_name": "Suresh Gupta",
        "email": "pharmacist.suresh@aiims-delhi.gov.in",
        "password": "Pharma@12345",
        "role": UserRole.PHARMACIST,
        "license_number": "PCI-DL-2018-00881",
        "hospital_id": HOSPITAL_ID,
        "department_id": DEPT_PHARMACY,
        "phone": "+91-9814000001",
    },

    # ── OPD & IPD Staff ───────────────────────────────────────────────────────
    {
        "full_name": "Mohan Rao",
        "email": "opd.mohan@aiims-delhi.gov.in",
        "password": "OpdStaff@123",
        "role": UserRole.OPD_STAFF,
        "sub_role": "non_surgical",
        "hospital_id": HOSPITAL_ID,
        "department_id": DEPT_OPD,
        "phone": "+91-9815000001",
    },
    {
        "full_name": "Sunita Joshi",
        "email": "ipd.sunita@aiims-delhi.gov.in",
        "password": "IpdStaff@1234",
        "role": UserRole.IPD_STAFF,
        "sub_role": "surgical",
        "hospital_id": HOSPITAL_ID,
        "department_id": DEPT_IPD,
        "phone": "+91-9815000002",
    },
    {
        "full_name": "Amit Pandey",
        "email": "reception.amit@aiims-delhi.gov.in",
        "password": "Recept@12345",
        "role": UserRole.RECEPTIONIST,
        "hospital_id": HOSPITAL_ID,
        "department_id": None,
        "phone": "+91-9815000003",
    },

    # ── Finance & Legal ───────────────────────────────────────────────────────
    {
        "full_name": "Deepa Chaudhary",
        "email": "insurance@starhealth.in",
        "password": "Insure@12345",
        "role": UserRole.INSURANCE_OFFICER,
        "hospital_id": HOSPITAL_ID,
        "department_id": DEPT_FINANCE,
        "phone": "+91-9816000001",
    },
    {
        "full_name": "Ravi Verma",
        "email": "scheme.ravi@mpjay.gov.in",
        "password": "Scheme@12345",
        "role": UserRole.SCHEME_OFFICER,
        "hospital_id": None,
        "department_id": None,
        "phone": "+91-9816000002",
    },
    {
        "full_name": "Inspector Arjun Singh",
        "email": "insp.arjun@delhipolice.gov.in",
        "password": "Police@12345",
        "role": UserRole.POLICE_INTERFACE,
        "hospital_id": None,
        "department_id": None,
        "phone": "+91-9817000001",
    },

    # ── Patients ──────────────────────────────────────────────────────────────
    {
        "full_name": "Ramesh Yadav",
        "email": "patient.ramesh@gmail.com",
        "password": "Patient@123",
        "role": UserRole.PATIENT,
        "hospital_id": None,
        "department_id": None,
        "phone": "+91-9900000001",
    },
    {
        "full_name": "Nisha Kulkarni",
        "email": "patient.nisha@gmail.com",
        "password": "Patient@123",
        "role": UserRole.PATIENT,
        "hospital_id": None,
        "department_id": None,
        "phone": "+91-9900000002",
    },
    {
        "full_name": "Sanjay Pawar",
        "email": "patient.sanjay@gmail.com",
        "password": "Patient@123",
        "role": UserRole.PATIENT,
        "hospital_id": None,
        "department_id": None,
        "phone": "+91-9900000003",
    },
]


async def seed():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]

    inserted = 0
    skipped  = 0

    print(f"\n{'='*60}")
    print(f"  MedGraph Seed — {len(TEST_USERS)} test users")
    print(f"  DB: {settings.mongodb_db}")
    print(f"{'='*60}\n")

    for u in TEST_USERS:
        existing = await db.users.find_one({"email": u["email"]})
        if existing:
            print(f"  [SKIP]  {u['role']:<20} {u['email']}")
            skipped += 1
            continue

        role_enum = u["role"]
        permissions = [p.value for p in ROLE_PERMISSIONS.get(role_enum, [])]

        doc = {
            "user_id":       str(uuid.uuid4()),
            "email":         u["email"],
            "hashed_password": get_password_hash(u["password"]),
            "full_name":     u["full_name"],
            "role":          role_enum.value,
            "sub_role":      u.get("sub_role"),
            "hospital_id":   u.get("hospital_id"),
            "department_id": u.get("department_id"),
            "permissions":   permissions,
            "specialization":u.get("specialization"),
            "license_number":u.get("license_number"),
            "phone":         u.get("phone"),
            "is_active":     True,
            "created_by":    "seed_script",
            "created_at":    datetime.utcnow(),
        }

        await db.users.insert_one(doc)
        print(f"  [OK]    {role_enum.value:<20} {u['email']}")
        inserted += 1

    print(f"\n{'='*60}")
    print(f"  Done. Inserted: {inserted}  |  Skipped: {skipped}")
    print(f"{'='*60}\n")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
