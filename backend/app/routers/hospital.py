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
    # DynamoDB doesn't support $nin — fetch all and filter in-memory
    query = {"hospital_id": hospital_id} if hospital_id else {}
    docs = await db.users.find(query).to_list(500)
    safe = []
    for d in docs:
        # Exclude patients from staff list
        if d.get("role") == "patient":
            continue
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
    # Fetch all users for this hospital and count in-memory (DynamoDB doesn't support $nin/$in in count)
    query = {"hospital_id": hospital_id} if hospital_id else {}
    all_users = await db.users.find(query).to_list(1000)
    
    staff = [u for u in all_users if u.get("role") != "patient"]
    doctors = [u for u in staff if u.get("role") in ["doctor", "surgeon"]]
    nurses = [u for u in staff if u.get("role") in ["nurse", "ward_incharge"]]
    
    depts = await db.departments.find(query).to_list(200)
    
    hospital = await db.hospitals.find_one({"hospital_id": hospital_id}) if hospital_id else None
    return {
        "total_staff":       len(staff),
        "total_departments": len(depts),
        "total_doctors":     len(doctors),
        "total_nurses":      len(nurses),
        "hospital_name":     hospital["name"] if hospital else "Your Hospital",
        "hospital_id":       hospital_id,
    }


@router.patch("/staff/{user_id}")
async def update_staff_profile(
    user_id: str,
    updates: dict,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.USER_CREATE_STAFF.value))
):
    """Hospital Admin can update staff profiles — role, department, specialization, active status."""
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hospital admin can only manage staff in their hospital
    hospital_id = current_user.get("hospital_id")
    if hospital_id and user.get("hospital_id") != hospital_id:
        raise HTTPException(status_code=403, detail="Cannot manage staff from another hospital")
    
    # Cannot modify patients or super admins
    if user.get("role") in ["patient", "super_admin", "govt_admin"]:
        raise HTTPException(status_code=403, detail="Cannot modify this user type")
    
    # Allowed fields for hospital admin to update
    allowed_fields = {
        "full_name", "phone", "specialization", "license_number",
        "department_id", "sub_role", "is_active",
    }
    safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not safe_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # If changing role, update permissions too
    if "role" in updates and updates["role"] not in ["patient", "super_admin", "govt_admin"]:
        try:
            new_role = UserRole(updates["role"])
            safe_updates["role"] = new_role.value
            safe_updates["permissions"] = [p.value for p in ROLE_PERMISSIONS.get(new_role, [])]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
    
    await db.users.update_one({"user_id": user_id}, {"$set": safe_updates})
    
    updated = await db.users.find_one({"user_id": user_id})
    return _clean(updated)


@router.patch("/staff/{user_id}/deactivate")
async def deactivate_staff(
    user_id: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.USER_CREATE_STAFF.value))
):
    """Hospital Admin deactivates a staff account."""
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("role") in ["patient", "super_admin", "govt_admin"]:
        raise HTTPException(status_code=403, detail="Cannot deactivate this user type")
    
    hospital_id = current_user.get("hospital_id")
    if hospital_id and user.get("hospital_id") != hospital_id:
        raise HTTPException(status_code=403, detail="Cannot manage staff from another hospital")
    
    await db.users.update_one({"user_id": user_id}, {"$set": {"is_active": False}})
    return {"status": "deactivated", "user_id": user_id}


@router.patch("/staff/{user_id}/activate")
async def activate_staff(
    user_id: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.USER_CREATE_STAFF.value))
):
    """Hospital Admin reactivates a staff account."""
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hospital_id = current_user.get("hospital_id")
    if hospital_id and user.get("hospital_id") != hospital_id:
        raise HTTPException(status_code=403, detail="Cannot manage staff from another hospital")
    
    await db.users.update_one({"user_id": user_id}, {"$set": {"is_active": True}})
    return {"status": "activated", "user_id": user_id}
