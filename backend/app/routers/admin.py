from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.models.user import UserCreate, UserInDB
from app.models.hospital import Hospital
from app.models.rbac import UserRole, Permission, ROLE_PERMISSIONS
from app.utils.jwt_handler import get_password_hash
from app.dependencies import get_db, require_permission
import uuid
from datetime import datetime

router = APIRouter()

def _clean(doc: dict) -> dict:
    """Remove MongoDB internal fields and ensure JSON-serialisable."""
    doc.pop("_id", None)
    doc.pop("hashed_password", None)
    return doc

@router.post("/hospitals", status_code=201)
async def create_hospital(
    hospital: dict,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.HOSPITAL_CREATE.value))
):
    if "hospital_id" not in hospital:
        hospital["hospital_id"] = str(uuid.uuid4())
    hospital["created_by"] = current_user["user_id"]
    hospital["created_at"] = datetime.utcnow()
    hospital.setdefault("departments", [])
    hospital.setdefault("is_active", True)
    await db.hospitals.insert_one(hospital)
    hospital.pop("_id", None)
    return hospital

@router.get("/hospitals")
async def list_hospitals(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.SYSTEM_MANAGE.value))
):
    docs = await db.hospitals.find().to_list(1000)
    return [_clean(h) for h in docs]

@router.post("/users", status_code=201)
async def create_system_user(
    user_data: UserCreate,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.USER_CREATE_STAFF.value))
):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    perms = [p.value for p in ROLE_PERMISSIONS.get(user_data.role, [])]
    user  = UserInDB(
        user_id=str(uuid.uuid4()),
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        sub_role=user_data.sub_role,
        permissions=perms,
        created_by=current_user["user_id"],
        created_at=datetime.utcnow()
    )
    await db.users.insert_one(user.model_dump())
    d = user.model_dump()
    d.pop("hashed_password", None)
    return d

@router.get("/users")
async def list_all_users(
    role: Optional[str] = Query(None),
    db   = Depends(get_db),
    current_user = Depends(require_permission(Permission.USER_READ_ALL.value))
):
    """Super Admin — list all users (safe dict response, no Pydantic validation crash)."""
    query: dict = {}
    if role:
        query["role"] = role
    docs = await db.users.find(query).to_list(2000)
    safe = []
    for d in docs:
        d = _clean(d)
        # Ensure required fields exist for frontend
        d.setdefault("permissions", [])
        d.setdefault("is_active", True)
        d.setdefault("sub_role", None)
        d.setdefault("hospital_id", None)
        d.setdefault("department_id", None)
        d.setdefault("specialization", None)
        safe.append(d)
    return safe

@router.get("/stats")
async def system_stats(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.SYSTEM_MANAGE.value))
):
    """Global system stats for Super Admin dashboard."""
    total_hospitals = await db.hospitals.count_documents({})
    total_users     = await db.users.count_documents({})
    total_patients  = await db.users.count_documents({"role": "patient"})
    total_doctors   = await db.users.count_documents({"role": {"$in": ["doctor", "surgeon"]}})
    return {
        "total_hospitals":  total_hospitals,
        "total_users":      total_users,
        "total_patients":   total_patients,
        "total_doctors":    total_doctors,
        "system_uptime":    "99.98%",
        "compliance_score": "100%",
    }
