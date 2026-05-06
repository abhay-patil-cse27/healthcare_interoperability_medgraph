"""
Self-service profile management.
PATCH /profile/me  — edit own demographics (name, phone, gender, dob, address, blood group, emergency contact)
GET  /profile/me   — own profile (safe subset, no hashed_password)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.dependencies import get_db, get_current_user

router = APIRouter()

# ── What users may edit about themselves ──────────────────────────────────
class ProfileUpdate(BaseModel):
    full_name:         Optional[str] = None
    phone:             Optional[str] = None
    gender:            Optional[str] = None          # male / female / other
    date_of_birth:     Optional[str] = None          # YYYY-MM-DD
    address:           Optional[str] = None
    emergency_contact: Optional[str] = None
    blood_group:       Optional[str] = None          # patients only (ignored silently for staff)
    abha_id:           Optional[str] = None          # patients linking their ABHA
    # Staff may update their specialization displayed in header chip
    specialization:    Optional[str] = None

SAFE_FIELDS = {
    "user_id", "email", "full_name", "role", "sub_role",
    "hospital_id", "department_id", "specialization", "license_number",
    "phone", "gender", "date_of_birth", "address", "emergency_contact",
    "blood_group", "abha_id", "mrn", "is_active", "profile_photo_url",
    "created_at",
}

@router.get("/me")
async def get_my_profile(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user = await db.users.find_one({"user_id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {k: v for k, v in user.items() if k in SAFE_FIELDS}


@router.patch("/me")
async def update_my_profile(
    payload: ProfileUpdate,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Prevent role escalation — users cannot change their own role
    updates.pop("role", None)
    updates.pop("permissions", None)
    updates.pop("hashed_password", None)
    updates.pop("user_id", None)

    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": updates}
    )
    # Return updated profile
    user = await db.users.find_one({"user_id": current_user["user_id"]})
    return {k: v for k, v in user.items() if k in SAFE_FIELDS}
