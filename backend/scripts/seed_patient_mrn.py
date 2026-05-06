"""Seed MRN and patient demographics into existing seeded patients."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient

async def seed():
    s  = get_settings()
    db = AsyncIOMotorClient(s.mongodb_url)[s.mongodb_db]

    patients = [
        {
            "email": "patient.ramesh@gmail.com",
            "mrn": "AIIMS-2026-00001", "abha_id": "91-1234-5678-9012",
            "blood_group": "B+", "gender": "male",
            "date_of_birth": "1978-03-15", "phone": "+91-98765-43210",
            "address": "12 Gandhi Nagar, Bhopal, MP",
            "emergency_contact": "Sunita Yadav +91-98765-43211",
        },
        {
            "email": "patient.nisha@gmail.com",
            "mrn": "AIIMS-2026-00002", "abha_id": "91-9876-5432-1011",
            "blood_group": "A+", "gender": "female",
            "date_of_birth": "1992-07-22", "phone": "+91-87654-32109",
            "address": "45 Andheri West, Mumbai, MH",
            "emergency_contact": "Raj Kulkarni +91-87654-32110",
        },
        {
            "email": "patient.sanjay@gmail.com",
            "mrn": "AIIMS-2026-00003", "abha_id": "91-5678-1234-9087",
            "blood_group": "O+", "gender": "male",
            "date_of_birth": "1965-11-08", "phone": "+91-76543-21098",
            "address": "78 Camp Area, Pune, MH",
            "emergency_contact": "Meena Pawar +91-76543-21099",
        },
        {
            "email": "john.patient@example.com",
            "mrn": "AIIMS-2026-00004", "abha_id": None,
            "blood_group": "AB+", "gender": "male",
            "date_of_birth": "1985-06-14", "phone": "+91-65432-10987",
            "address": "Connaught Place, New Delhi", "emergency_contact": None,
        },
    ]

    for p in patients:
        email = p.pop("email")
        r = await db.users.update_one({"email": email}, {"$set": p})
        mrn = p.get("mrn")
        print(f"  {email:<38} MRN={mrn}  modified={r.modified_count}")

    # Init MRN counter
    await db.mrn_counters.update_one(
        {"_id": "national-2026"},
        {"$set": {"seq": 100}},
        upsert=True
    )
    await db.mrn_counters.update_one(
        {"_id": "hosp-aiims-delhi-001-2026"},
        {"$set": {"seq": 4}},
        upsert=True
    )
    print("MRN counters initialized")
    print("Done!")

asyncio.run(seed())
