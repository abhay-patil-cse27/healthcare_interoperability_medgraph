# -*- coding: utf-8 -*-
"""
Seed Users into DynamoDB (replaces MongoDB seed_test_users.py)
"""
import asyncio, sys, os, uuid
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.dynamo_service import get_dynamodb
from app.models.rbac import UserRole, ROLE_PERMISSIONS
from app.utils.jwt_handler import get_password_hash

HOSPITAL_ID = "hosp-aiims-delhi-001"

TEST_USERS = [
    {"full_name":"Rajesh Kumar IAS","email":"superadmin@mohfw.gov.in","password":"SuperAdmin@123","role":UserRole.SUPER_ADMIN,"hospital_id":None,"phone":"+91-9800000001"},
    {"full_name":"Ananya Singh IFS","email":"govtadmin@nha.gov.in","password":"GovtAdmin@123","role":UserRole.GOVT_ADMIN,"hospital_id":None,"phone":"+91-9800000002"},
    {"full_name":"Dr. Priya Mehta","email":"admin@aiims-delhi.gov.in","password":"HospAdmin@123","role":UserRole.HOSPITAL_ADMIN,"hospital_id":HOSPITAL_ID,"phone":"+91-9810000001"},
    {"full_name":"Dr. Arun Sharma","email":"dr.arun@aiims-delhi.gov.in","password":"Doctor@1234","role":UserRole.DOCTOR,"hospital_id":HOSPITAL_ID,"phone":"+91-9811000001","specialization":"Cardiology"},
    {"full_name":"Dr. Sneha Patel","email":"dr.sneha@aiims-delhi.gov.in","password":"Doctor@1234","role":UserRole.DOCTOR,"hospital_id":HOSPITAL_ID,"phone":"+91-9811000002","specialization":"Internal Medicine"},
    {"full_name":"Dr. Vikram Nair","email":"surgeon.vikram@aiims-delhi.gov.in","password":"Surgeon@1234","role":UserRole.SURGEON,"hospital_id":HOSPITAL_ID,"phone":"+91-9812000001","specialization":"Orthopedic Surgery"},
    {"full_name":"Kavita Desai","email":"nurse.kavita@aiims-delhi.gov.in","password":"Nurse@12345","role":UserRole.NURSE,"hospital_id":HOSPITAL_ID,"phone":"+91-9813000001"},
    {"full_name":"Rekha Sharma","email":"incharge.rekha@aiims-delhi.gov.in","password":"WardIncharge@1","role":UserRole.WARD_INCHARGE,"hospital_id":HOSPITAL_ID,"phone":"+91-9813000002"},
    {"full_name":"Suresh Gupta","email":"pharmacist.suresh@aiims-delhi.gov.in","password":"Pharma@12345","role":UserRole.PHARMACIST,"hospital_id":HOSPITAL_ID,"phone":"+91-9814000001"},
    {"full_name":"Mohan Rao","email":"opd.mohan@aiims-delhi.gov.in","password":"OpdStaff@123","role":UserRole.OPD_STAFF,"hospital_id":HOSPITAL_ID,"phone":"+91-9815000001"},
    {"full_name":"Sunita Joshi","email":"ipd.sunita@aiims-delhi.gov.in","password":"IpdStaff@1234","role":UserRole.IPD_STAFF,"hospital_id":HOSPITAL_ID,"phone":"+91-9815000002"},
    {"full_name":"Deepa Chaudhary","email":"insurance@starhealth.in","password":"Insure@12345","role":UserRole.INSURANCE_OFFICER,"hospital_id":HOSPITAL_ID,"phone":"+91-9816000001"},
    {"full_name":"Ravi Verma","email":"scheme.ravi@mpjay.gov.in","password":"Scheme@12345","role":UserRole.SCHEME_OFFICER,"hospital_id":None,"phone":"+91-9816000002"},
    {"full_name":"Inspector Arjun Singh","email":"insp.arjun@delhipolice.gov.in","password":"Police@12345","role":UserRole.POLICE_INTERFACE,"hospital_id":None,"phone":"+91-9817000001"},
    {"full_name":"Ramesh Yadav","email":"patient.ramesh@gmail.com","password":"Patient@123","role":UserRole.PATIENT,"hospital_id":None,"phone":"+91-9900000001","blood_group":"B+","gender":"male","date_of_birth":"1978-03-15","address":"42 MG Road, Pune, Maharashtra","abha_id":"91-1234-5678-9012","mrn":"AIIMS-2026-00001"},
    {"full_name":"Nisha Kulkarni","email":"patient.nisha@gmail.com","password":"Patient@123","role":UserRole.PATIENT,"hospital_id":None,"phone":"+91-9900000002","blood_group":"A+","gender":"female","date_of_birth":"1992-07-22","address":"15 FC Road, Pune, Maharashtra","abha_id":"91-2345-6789-0123","mrn":"AIIMS-2026-00002"},
    {"full_name":"Sanjay Pawar","email":"patient.sanjay@gmail.com","password":"Patient@123","role":UserRole.PATIENT,"hospital_id":None,"phone":"+91-9900000003","blood_group":"O+","gender":"male","date_of_birth":"1985-11-08","address":"78 Andheri West, Mumbai, Maharashtra","abha_id":"91-3456-7890-1234","mrn":"AIIMS-2026-00003"},
    {"full_name":"HITL Validator","email":"hitl@aiims-delhi.gov.in","password":"Hitl@12345","role":UserRole.HITL_VALIDATOR,"hospital_id":HOSPITAL_ID,"phone":"+91-9818000001"},
]


async def main():
    db = get_dynamodb()
    print(f"{'='*60}")
    print(f"  Seeding {len(TEST_USERS)} users into DynamoDB")
    print(f"{'='*60}\n")

    inserted = 0
    skipped = 0
    for u in TEST_USERS:
        existing = await db.users.find_one({"email": u["email"]})
        if existing:
            print(f"  [SKIP] {u['role'].value:<20} {u['email']}")
            skipped += 1
            continue

        role_enum = u["role"]
        permissions = [p.value for p in ROLE_PERMISSIONS.get(role_enum, [])]
        doc = {
            "user_id": str(uuid.uuid4()),
            "email": u["email"],
            "hashed_password": get_password_hash(u["password"]),
            "full_name": u["full_name"],
            "role": role_enum.value,
            "hospital_id": u.get("hospital_id"),
            "permissions": permissions,
            "specialization": u.get("specialization"),
            "phone": u.get("phone"),
            "blood_group": u.get("blood_group"),
            "gender": u.get("gender"),
            "date_of_birth": u.get("date_of_birth"),
            "address": u.get("address"),
            "abha_id": u.get("abha_id"),
            "mrn": u.get("mrn"),
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        await db.users.insert_one(doc)
        print(f"  [OK]   {role_enum.value:<20} {u['email']}")
        inserted += 1

    print(f"\n{'='*60}")
    print(f"  Done. Inserted: {inserted} | Skipped: {skipped}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
