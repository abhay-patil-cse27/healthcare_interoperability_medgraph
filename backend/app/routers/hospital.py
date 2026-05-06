from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.models.user import UserCreate, UserInDB
from app.models.rbac import UserRole, Permission, ROLE_PERMISSIONS
from app.utils.jwt_handler import get_password_hash
from app.dependencies import get_db, require_permission
import uuid
from datetime import datetime

router = APIRouter()

def _clean(doc: dict) -> dict:
    doc.pop("_id", None)
    doc.pop("hashed_password", None)
    return doc

@router.post("/departments", status_code=201)
async def create_department(
    dept: dict,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.HOSPITAL_MANAGE.value))
):
    hospital_id = current_user.get("hospital_id")
    if not hospital_id and current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Not assigned to a hospital")
    if "department_id" not in dept:
        dept["department_id"] = str(uuid.uuid4())
    if current_user["role"] != "super_admin":
        dept["hospital_id"] = hospital_id

    hospital = await db.hospitals.find_one({"hospital_id": dept.get("hospital_id")})
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    dept.setdefault("is_active", True)
    dept.setdefault("bed_count", 0)
    await db.departments.insert_one(dept)
    await db.hospitals.update_one(
        {"hospital_id": dept["hospital_id"]},
        {"$addToSet": {"departments": dept["department_id"]}}
    )
    dept.pop("_id", None)
    return dept

@router.get("/departments")
async def list_departments(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.HOSPITAL_MANAGE.value))
):
    hospital_id = current_user.get("hospital_id")
    query: dict = {} if current_user["role"] == "super_admin" else {"hospital_id": hospital_id}
    docs = await db.departments.find(query).to_list(200)
    return [_clean(d) for d in docs]

@router.post("/staff", status_code=201)
async def invite_staff(
    user_data: UserCreate,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.USER_CREATE_STAFF.value))
):
    if user_data.role in [UserRole.SUPER_ADMIN, UserRole.PATIENT, UserRole.GOVT_ADMIN]:
        raise HTTPException(status_code=403, detail=f"Cannot create role {user_data.role} via this endpoint")

    hospital_id = current_user.get("hospital_id")
    if not hospital_id and current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Not assigned to a hospital")

    if await db.users.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    perms = [p.value for p in ROLE_PERMISSIONS.get(user_data.role, [])]
    user  = UserInDB(
        user_id=str(uuid.uuid4()),
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        sub_role=user_data.sub_role,
        specialization=user_data.specialization,
        license_number=user_data.license_number,
        phone=user_data.phone,
        hospital_id=hospital_id,
        permissions=perms,
        created_by=current_user["user_id"],
        created_at=datetime.utcnow()
    )
    await db.users.insert_one(user.model_dump())
    d = user.model_dump()
    d.pop("hashed_password", None)
    return d

@router.get("/staff")
async def list_staff(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.AUDIT_READ_HOSPITAL.value))
):
    hospital_id = current_user.get("hospital_id")
    query: dict = {"role": {"$nin": ["patient"]}}
    if hospital_id:
        query["hospital_id"] = hospital_id
    docs = await db.users.find(query).to_list(500)
    safe = []
    for d in docs:
        d = _clean(d)
        d.setdefault("permissions", [])
        d.setdefault("is_active", True)
        safe.append(d)
    return safe

@router.get("/stats")
async def hospital_stats(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.AUDIT_READ_HOSPITAL.value))
):
    hospital_id = current_user.get("hospital_id")
    base = {"hospital_id": hospital_id} if hospital_id else {}
    total_staff   = await db.users.count_documents({**base, "role": {"$nin": ["patient"]}})
    total_depts   = await db.departments.count_documents(base)
    total_doctors = await db.users.count_documents({**base, "role": {"$in": ["doctor", "surgeon"]}})
    total_nurses  = await db.users.count_documents({**base, "role": {"$in": ["nurse", "ward_incharge"]}})
    hospital = await db.hospitals.find_one({"hospital_id": hospital_id})
    return {
        "total_staff":       total_staff,
        "total_departments": total_depts,
        "total_doctors":     total_doctors,
        "total_nurses":      total_nurses,
        "hospital_name":     hospital["name"] if hospital else "Your Hospital",
        "hospital_id":       hospital_id,
    }
