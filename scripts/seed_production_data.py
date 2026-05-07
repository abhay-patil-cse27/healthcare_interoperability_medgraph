"""
MedGraph AI — Production Seed Script
======================================
Injects realistic data into DynamoDB + Neo4j Aura for 4 Maharashtra hospitals.

Creates:
  - 4 Hospitals (AIIMS Nagpur, KEM Mumbai, Sassoon Pune, GMC Aurangabad)
  - 1 Super Admin
  - 4 Hospital Admins (one per hospital)
  - 8 Doctors (2 per hospital)
  - 4 Nurses (1 per hospital)
  - 4 HITL Validators (1 per hospital)
  - 8 Patients (2 per hospital)
  - Sample consents, clinical data in Neo4j

Run: .\venv\Scripts\python.exe scripts/seed_production_data.py
"""
import sys
import os
import uuid
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.config import get_settings
from app.services.dynamo_service import get_dynamodb
from app.services.neo4j_service import Neo4jService
from app.utils.jwt_handler import get_password_hash
from app.models.rbac import UserRole, ROLE_PERMISSIONS


# ═══════════════════════════════════════════════════════════════════════════════
# DATA DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

HOSPITALS = [
    {
        "hospital_id": "hosp-aiims-nagpur-001",
        "name": "AIIMS Nagpur",
        "registration_number": "MH-NGP-AIIMS-2024-001",
        "address": {"city": "Nagpur", "state": "Maharashtra", "pincode": "441108", "street": "Plot No. 2, Sector 20, MIHAN"},
        "contact_email": "admin@aiimsnagpur.edu.in",
        "contact_phone": "+912712234567",
        "departments": ["General Medicine", "Cardiology", "Orthopedics", "Pathology"],
        "empanelment": {"pm_jay": True, "mpjay": True, "cghs": True},
        "is_active": True,
    },
    {
        "hospital_id": "hosp-kem-mumbai-001",
        "name": "KEM Hospital Mumbai",
        "registration_number": "MH-MUM-KEM-1926-001",
        "address": {"city": "Mumbai", "state": "Maharashtra", "pincode": "400012", "street": "Acharya Donde Marg, Parel"},
        "contact_email": "admin@kemhospital.org",
        "contact_phone": "+912224136051",
        "departments": ["General Medicine", "Surgery", "Neurology", "Oncology"],
        "empanelment": {"pm_jay": True, "mpjay": True, "cghs": True},
        "is_active": True,
    },
    {
        "hospital_id": "hosp-sassoon-pune-001",
        "name": "Sassoon General Hospital Pune",
        "registration_number": "MH-PUN-SGH-1868-001",
        "address": {"city": "Pune", "state": "Maharashtra", "pincode": "411001", "street": "Near Pune Railway Station, Bund Garden Road"},
        "contact_email": "admin@sassoonhospital.org",
        "contact_phone": "+912026128000",
        "departments": ["General Medicine", "Pediatrics", "Gynecology", "Emergency"],
        "empanelment": {"pm_jay": True, "mpjay": True},
        "is_active": True,
    },
    {
        "hospital_id": "hosp-gmc-aurangabad-001",
        "name": "Government Medical College Chhatrapati Sambhajinagar",
        "registration_number": "MH-AUR-GMC-1956-001",
        "address": {"city": "Chhatrapati Sambhajinagar", "state": "Maharashtra", "pincode": "431001", "street": "Panchakki Road"},
        "contact_email": "admin@gmcaurangabad.org",
        "contact_phone": "+912402331234",
        "departments": ["General Medicine", "Dermatology", "ENT", "Ophthalmology"],
        "empanelment": {"pm_jay": True, "mpjay": True},
        "is_active": True,
    },
]

# All users use password: Test@1234
DEFAULT_PASSWORD = get_password_hash("Test@1234")

USERS = [
    # Super Admin
    {"user_id": str(uuid.uuid4()), "email": "superadmin@medgraph.ai", "full_name": "Dr. Rajesh Sharma", "role": "super_admin", "hospital_id": None},

    # Hospital Admins
    {"user_id": str(uuid.uuid4()), "email": "admin@aiimsnagpur.edu.in", "full_name": "Dr. Priya Deshmukh", "role": "hospital_admin", "hospital_id": "hosp-aiims-nagpur-001"},
    {"user_id": str(uuid.uuid4()), "email": "admin@kemhospital.org", "full_name": "Dr. Suresh Patil", "role": "hospital_admin", "hospital_id": "hosp-kem-mumbai-001"},
    {"user_id": str(uuid.uuid4()), "email": "admin@sassoonhospital.org", "full_name": "Dr. Anita Kulkarni", "role": "hospital_admin", "hospital_id": "hosp-sassoon-pune-001"},
    {"user_id": str(uuid.uuid4()), "email": "admin@gmcaurangabad.org", "full_name": "Dr. Vikram Jadhav", "role": "hospital_admin", "hospital_id": "hosp-gmc-aurangabad-001"},

    # Doctors (2 per hospital)
    {"user_id": str(uuid.uuid4()), "email": "dr.mehta@aiimsnagpur.edu.in", "full_name": "Dr. Anil Mehta", "role": "doctor", "hospital_id": "hosp-aiims-nagpur-001", "specialization": "Cardiology"},
    {"user_id": str(uuid.uuid4()), "email": "dr.joshi@aiimsnagpur.edu.in", "full_name": "Dr. Sneha Joshi", "role": "doctor", "hospital_id": "hosp-aiims-nagpur-001", "specialization": "General Medicine"},
    {"user_id": str(uuid.uuid4()), "email": "dr.shah@kemhospital.org", "full_name": "Dr. Rohan Shah", "role": "doctor", "hospital_id": "hosp-kem-mumbai-001", "specialization": "Neurology"},
    {"user_id": str(uuid.uuid4()), "email": "dr.patel@kemhospital.org", "full_name": "Dr. Kavita Patel", "role": "doctor", "hospital_id": "hosp-kem-mumbai-001", "specialization": "Oncology"},
    {"user_id": str(uuid.uuid4()), "email": "dr.deshpande@sassoon.org", "full_name": "Dr. Manoj Deshpande", "role": "doctor", "hospital_id": "hosp-sassoon-pune-001", "specialization": "Pediatrics"},
    {"user_id": str(uuid.uuid4()), "email": "dr.bhosale@sassoon.org", "full_name": "Dr. Sunita Bhosale", "role": "doctor", "hospital_id": "hosp-sassoon-pune-001", "specialization": "Gynecology"},
    {"user_id": str(uuid.uuid4()), "email": "dr.kale@gmcaur.org", "full_name": "Dr. Ashok Kale", "role": "doctor", "hospital_id": "hosp-gmc-aurangabad-001", "specialization": "Dermatology"},
    {"user_id": str(uuid.uuid4()), "email": "dr.more@gmcaur.org", "full_name": "Dr. Pooja More", "role": "doctor", "hospital_id": "hosp-gmc-aurangabad-001", "specialization": "ENT"},

    # Nurses (1 per hospital)
    {"user_id": str(uuid.uuid4()), "email": "nurse.kamble@aiimsnagpur.edu.in", "full_name": "Smt. Rekha Kamble", "role": "nurse", "hospital_id": "hosp-aiims-nagpur-001"},
    {"user_id": str(uuid.uuid4()), "email": "nurse.sawant@kemhospital.org", "full_name": "Smt. Meena Sawant", "role": "nurse", "hospital_id": "hosp-kem-mumbai-001"},
    {"user_id": str(uuid.uuid4()), "email": "nurse.gaikwad@sassoon.org", "full_name": "Smt. Asha Gaikwad", "role": "nurse", "hospital_id": "hosp-sassoon-pune-001"},
    {"user_id": str(uuid.uuid4()), "email": "nurse.pawar@gmcaur.org", "full_name": "Smt. Lata Pawar", "role": "nurse", "hospital_id": "hosp-gmc-aurangabad-001"},

    # HITL Validators (1 per hospital)
    {"user_id": str(uuid.uuid4()), "email": "hitl.nagpur@medgraph.ai", "full_name": "Shri. Ganesh Wagh", "role": "hitl_validator", "hospital_id": "hosp-aiims-nagpur-001"},
    {"user_id": str(uuid.uuid4()), "email": "hitl.mumbai@medgraph.ai", "full_name": "Smt. Deepa Naik", "role": "hitl_validator", "hospital_id": "hosp-kem-mumbai-001"},
    {"user_id": str(uuid.uuid4()), "email": "hitl.pune@medgraph.ai", "full_name": "Shri. Rahul Shinde", "role": "hitl_validator", "hospital_id": "hosp-sassoon-pune-001"},
    {"user_id": str(uuid.uuid4()), "email": "hitl.aurangabad@medgraph.ai", "full_name": "Smt. Vaishali Chavan", "role": "hitl_validator", "hospital_id": "hosp-gmc-aurangabad-001"},

    # Patients (2 per hospital)
    {"user_id": str(uuid.uuid4()), "email": "ramesh.patil@gmail.com", "full_name": "Ramesh Patil", "role": "patient", "hospital_id": "hosp-aiims-nagpur-001", "gender": "male", "date_of_birth": "1965-03-15", "blood_group": "B+", "phone": "+919876543210"},
    {"user_id": str(uuid.uuid4()), "email": "sunita.desai@gmail.com", "full_name": "Sunita Desai", "role": "patient", "hospital_id": "hosp-aiims-nagpur-001", "gender": "female", "date_of_birth": "1978-07-22", "blood_group": "A+", "phone": "+919876543211"},
    {"user_id": str(uuid.uuid4()), "email": "vijay.thakur@gmail.com", "full_name": "Vijay Thakur", "role": "patient", "hospital_id": "hosp-kem-mumbai-001", "gender": "male", "date_of_birth": "1955-11-08", "blood_group": "O+", "phone": "+919876543212"},
    {"user_id": str(uuid.uuid4()), "email": "meera.kulkarni@gmail.com", "full_name": "Meera Kulkarni", "role": "patient", "hospital_id": "hosp-kem-mumbai-001", "gender": "female", "date_of_birth": "1982-01-30", "blood_group": "AB+", "phone": "+919876543213"},
    {"user_id": str(uuid.uuid4()), "email": "prakash.jagtap@gmail.com", "full_name": "Prakash Jagtap", "role": "patient", "hospital_id": "hosp-sassoon-pune-001", "gender": "male", "date_of_birth": "1970-09-12", "blood_group": "B-", "phone": "+919876543214"},
    {"user_id": str(uuid.uuid4()), "email": "anjali.mane@gmail.com", "full_name": "Anjali Mane", "role": "patient", "hospital_id": "hosp-sassoon-pune-001", "gender": "female", "date_of_birth": "1990-04-05", "blood_group": "O-", "phone": "+919876543215"},
    {"user_id": str(uuid.uuid4()), "email": "sunil.gawande@gmail.com", "full_name": "Sunil Gawande", "role": "patient", "hospital_id": "hosp-gmc-aurangabad-001", "gender": "male", "date_of_birth": "1960-12-20", "blood_group": "A-", "phone": "+919876543216"},
    {"user_id": str(uuid.uuid4()), "email": "priya.shinde@gmail.com", "full_name": "Priya Shinde", "role": "patient", "hospital_id": "hosp-gmc-aurangabad-001", "gender": "female", "date_of_birth": "1985-06-18", "blood_group": "B+", "phone": "+919876543217"},
]

# Clinical data for Neo4j (per patient)
PATIENT_CLINICAL_DATA = {
    "ramesh.patil@gmail.com": {
        "conditions": [{"name": "type 2 diabetes mellitus", "icd10_code": "E11.9", "status": "active"}, {"name": "essential hypertension", "icd10_code": "I10", "status": "active"}],
        "medications": [{"name": "metformin", "dosage": "500mg", "frequency": "twice daily"}, {"name": "amlodipine", "dosage": "5mg", "frequency": "once daily"}],
        "allergies": [{"substance": "sulfonamides", "reaction": "skin rash", "severity": "moderate"}],
        "vitals": [{"type": "blood_pressure", "value": "148/92", "unit": "mmHg", "status": "high"}],
        "symptoms": [],
    },
    "sunita.desai@gmail.com": {
        "conditions": [{"name": "hypothyroidism", "icd10_code": "E03.9", "status": "active"}],
        "medications": [{"name": "levothyroxine", "dosage": "50mcg", "frequency": "once daily morning"}],
        "allergies": [],
        "vitals": [{"type": "tsh", "value": "6.8", "unit": "mIU/L", "status": "high"}],
        "symptoms": [{"name": "fatigue", "severity": "moderate", "duration": "3 months"}],
    },
    "vijay.thakur@gmail.com": {
        "conditions": [{"name": "coronary artery disease", "icd10_code": "I25.1", "status": "active"}, {"name": "hyperlipidemia", "icd10_code": "E78.5", "status": "active"}],
        "medications": [{"name": "atorvastatin", "dosage": "40mg", "frequency": "once daily night"}, {"name": "aspirin", "dosage": "75mg", "frequency": "once daily"}, {"name": "metoprolol", "dosage": "25mg", "frequency": "twice daily"}],
        "allergies": [{"substance": "penicillin", "reaction": "anaphylaxis", "severity": "severe"}],
        "vitals": [{"type": "cholesterol_total", "value": "242", "unit": "mg/dL", "status": "high"}],
        "symptoms": [{"name": "chest pain on exertion", "severity": "moderate", "duration": "2 weeks"}],
    },
    "meera.kulkarni@gmail.com": {
        "conditions": [{"name": "iron deficiency anemia", "icd10_code": "D50.9", "status": "active"}],
        "medications": [{"name": "ferrous sulfate", "dosage": "200mg", "frequency": "twice daily"}],
        "allergies": [],
        "vitals": [{"type": "haemoglobin", "value": "9.2", "unit": "g/dL", "status": "low"}],
        "symptoms": [{"name": "weakness", "severity": "moderate", "duration": "1 month"}, {"name": "pallor", "severity": "mild", "duration": "1 month"}],
    },
}


async def seed():
    db = get_dynamodb()
    neo4j = Neo4jService()

    print("\n" + "=" * 60)
    print("  MedGraph AI — Production Data Seed")
    print("=" * 60)

    # ── Hospitals ─────────────────────────────────────────────────────────────
    print("\n[1/4] Seeding hospitals...")
    for h in HOSPITALS:
        h["created_by"] = "system"
        h["created_at"] = datetime.utcnow().isoformat()
        await db.hospitals.insert_one(h)
        print(f"  ✓ {h['name']}")

    # ── Users ─────────────────────────────────────────────────────────────────
    print("\n[2/4] Seeding users...")
    user_map = {}  # email → user_id
    for u in USERS:
        role_enum = UserRole(u["role"])
        permissions = [p.value for p in ROLE_PERMISSIONS.get(role_enum, [])]
        user_doc = {
            "user_id": u["user_id"],
            "email": u["email"],
            "hashed_password": DEFAULT_PASSWORD,
            "full_name": u["full_name"],
            "role": u["role"],
            "hospital_id": u.get("hospital_id", ""),
            "permissions": permissions,
            "specialization": u.get("specialization", ""),
            "phone": u.get("phone", ""),
            "gender": u.get("gender", ""),
            "date_of_birth": u.get("date_of_birth", ""),
            "blood_group": u.get("blood_group", ""),
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        await db.users.insert_one(user_doc)
        user_map[u["email"]] = u["user_id"]
        role_label = u["role"].replace("_", " ").title()
        print(f"  ✓ [{role_label}] {u['full_name']} ({u['email']})")

    # ── Neo4j Clinical Data ───────────────────────────────────────────────────
    print("\n[3/4] Seeding clinical data in Neo4j...")
    for email, clinical in PATIENT_CLINICAL_DATA.items():
        patient_id = user_map[email]
        nodes = await neo4j.store_entities(
            patient_id=patient_id,
            entities=clinical,
            source="seed_script",
            encounter_date=datetime.utcnow().isoformat(),
        )
        patient_name = next(u["full_name"] for u in USERS if u["email"] == email)
        print(f"  ✓ {patient_name}: {nodes} nodes")

    # ── Sample Consents ───────────────────────────────────────────────────────
    print("\n[4/4] Seeding sample consents...")
    # Doctor at AIIMS Nagpur requests consent for patient Ramesh Patil
    doctor_id = user_map["dr.mehta@aiimsnagpur.edu.in"]
    patient_id = user_map["ramesh.patil@gmail.com"]
    consent = {
        "consent_id": str(uuid.uuid4()),
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "purpose": "Cardiac evaluation and treatment planning",
        "requested_scope": "full",
        "duration_hours": 72,
        "status": "approved",
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "valid_until": (datetime.utcnow() + timedelta(hours=70)).isoformat(),
        "granted_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
    }
    await db.consents.insert_one(consent)
    print(f"  ✓ Dr. Mehta → Ramesh Patil (approved, full scope)")

    # Doctor at KEM requests consent for Vijay Thakur
    doctor_id2 = user_map["dr.shah@kemhospital.org"]
    patient_id2 = user_map["vijay.thakur@gmail.com"]
    consent2 = {
        "consent_id": str(uuid.uuid4()),
        "doctor_id": doctor_id2,
        "patient_id": patient_id2,
        "purpose": "Neurological assessment for chest pain differential",
        "requested_scope": "full",
        "duration_hours": 48,
        "status": "approved",
        "created_at": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
        "valid_until": (datetime.utcnow() + timedelta(hours=43)).isoformat(),
        "granted_at": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
    }
    await db.consents.insert_one(consent2)
    print(f"  ✓ Dr. Shah → Vijay Thakur (approved, full scope)")

    await neo4j.close()

    print("\n" + "=" * 60)
    print("  ✓ SEED COMPLETE")
    print("=" * 60)
    print(f"\n  Hospitals:       {len(HOSPITALS)}")
    print(f"  Users:           {len(USERS)}")
    print(f"  Clinical data:   {len(PATIENT_CLINICAL_DATA)} patients")
    print(f"  Consents:        2 (approved)")
    print(f"\n  Login credentials (all users): Test@1234")
    print(f"  Example: superadmin@medgraph.ai / Test@1234")
    print(f"           dr.mehta@aiimsnagpur.edu.in / Test@1234")
    print(f"           ramesh.patil@gmail.com / Test@1234")
    print(f"           hitl.nagpur@medgraph.ai / Test@1234")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(seed())
