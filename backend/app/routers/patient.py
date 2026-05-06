"""
Patient Search & MRN Utilities
================================
- generate_mrn(hospital_id, db) → e.g. "AIIMS-2026-04821"
- GET /patient/search?q=... → search by name, phone, MRN, ABHA ID
- GET /patient/{patient_id}/card → lightweight card for any lookup
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.rbac import Permission
from app.dependencies import get_db, require_permission
from datetime import datetime
import re

router = APIRouter()

# ── MRN generator ─────────────────────────────────────────────────────────
HOSPITAL_PREFIX = {
    "hosp-aiims-delhi-001": "AIIMS",
    "hosp-kims-pune-001":   "KIMS",
}

async def generate_mrn(hospital_id: str, db) -> str:
    """
    Generates a short, human-readable MRN.
    Format: <HOSPITAL_CODE>-<YEAR>-<5-digit-seq>
    Example: AIIMS-2026-00042
    """
    prefix = HOSPITAL_PREFIX.get(hospital_id, "MED")
    year   = datetime.utcnow().year
    # Use an atomic counter per hospital-year
    counter_id = f"{hospital_id}-{year}"
    result = await db.mrn_counters.find_one_and_update(
        {"_id": counter_id},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    seq = result.get("seq", 1)
    return f"{prefix}-{year}-{seq:05d}"

# ── Patient search ─────────────────────────────────────────────────────────
@router.get("/search")
async def search_patients(
    q: str = Query(..., min_length=2, description="Name, phone, MRN, or ABHA ID"),
    limit: int = Query(10, le=30),
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.PATIENT_READ_ASSIGNED.value))
):
    """
    Multi-field patient search. Supports:
    - Full or partial name (case-insensitive)
    - Phone number (partial)
    - MRN (e.g. AIIMS-2026-00042)
    - ABHA ID
    - Email (for admins)

    Returns patient cards — NO clinical data, just identity fields.
    """
    q = q.strip()
    regex = {"$regex": re.escape(q), "$options": "i"}

    pipeline = [
        {
            "$match": {
                "role": "patient",
                "$or": [
                    {"full_name":  regex},
                    {"phone":      regex},
                    {"mrn":        regex},
                    {"abha_id":    regex},
                    {"email":      regex},
                ]
            }
        },
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "hashed_password": 0,
                "permissions": 0,
            }
        }
    ]

    results = await db.users.aggregate(pipeline).to_list(limit)

    cards = []
    for u in results:
        cards.append({
            "user_id":           u.get("user_id"),
            "full_name":         u.get("full_name"),
            "mrn":               u.get("mrn"),
            "abha_id":           u.get("abha_id"),
            "phone":             u.get("phone"),
            "email":             u.get("email"),
            "blood_group":       u.get("blood_group"),
            "gender":            u.get("gender"),
            "date_of_birth":     u.get("date_of_birth"),
            "address":           u.get("address"),
            "emergency_contact": u.get("emergency_contact"),
            "is_active":         u.get("is_active", True),
        })
    return cards


@router.get("/{patient_id}/card")
async def get_patient_card(
    patient_id: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.PATIENT_READ_ASSIGNED.value))
):
    """Fetch a lightweight identity card for a patient by UUID or MRN."""
    user = await db.users.find_one({"user_id": patient_id, "role": "patient"})
    if not user:
        user = await db.users.find_one({"mrn": patient_id, "role": "patient"})
    if not user:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {
        "user_id":           user.get("user_id"),
        "full_name":         user.get("full_name"),
        "mrn":               user.get("mrn"),
        "abha_id":           user.get("abha_id"),
        "phone":             user.get("phone"),
        "email":             user.get("email"),
        "blood_group":       user.get("blood_group"),
        "gender":            user.get("gender"),
        "date_of_birth":     user.get("date_of_birth"),
        "address":           user.get("address"),
        "emergency_contact": user.get("emergency_contact"),
        "is_active":         user.get("is_active", True),
    }
