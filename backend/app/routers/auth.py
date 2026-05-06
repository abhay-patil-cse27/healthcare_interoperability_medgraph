import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import UserCreate, UserResponse, TokenResponse, UserInDB, LoginRequest
from app.models.rbac import UserRole, ROLE_PERMISSIONS
from app.utils.jwt_handler import get_password_hash, verify_password, create_access_token
from app.dependencies import get_db, get_current_user
from app.routers.patient import generate_mrn

router = APIRouter()

@router.post("/register", status_code=201)
async def register(user_data: UserCreate, db=Depends(get_db)):
    # Public registration is ONLY for patients
    if user_data.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=403,
            detail="Staff accounts are created by Hospital Admins. Only patients can self-register."
        )

    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    default_permissions = [p.value for p in ROLE_PERMISSIONS.get(user_data.role, [])]

    # Generate MRN for patients — human-readable, hospital-scoped
    # Patients don't have a hospital_id yet, use a national MRN pool
    mrn = await generate_mrn("national", db)

    user = UserInDB(
        user_id=str(uuid.uuid4()),
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        phone=getattr(user_data, 'phone', None),
        mrn=mrn,
        abha_id=getattr(user_data, 'abha_id', None),
        blood_group=getattr(user_data, 'blood_group', None),
        date_of_birth=getattr(user_data, 'date_of_birth', None),
        gender=getattr(user_data, 'gender', None),
        permissions=default_permissions,
        created_at=datetime.utcnow(),
    )

    await db.users.insert_one(user.model_dump())
    d = user.model_dump()
    d.pop("hashed_password", None)
    return d

@router.post("/login", response_model=TokenResponse)
async def login(user_data: LoginRequest, db=Depends(get_db)):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User account is disabled")

    # Ensure permissions exist (migration for older records)
    permissions = user.get("permissions", [])
    if not permissions:
        try:
            role_enum = UserRole(user["role"])
            permissions = [p.value for p in ROLE_PERMISSIONS.get(role_enum, [])]
            # Optionally update DB here in background
        except ValueError:
            permissions = []

    token = create_access_token(
        {
            "sub": user["user_id"],
            "role": user["role"],
            "email": user["email"],
            "hospital_id": user.get("hospital_id"),
            "department_id": user.get("department_id"),
            "permissions": permissions,
        }
    )
    return TokenResponse(
        access_token=token, user_id=user["user_id"], role=user["role"]
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    # Re-evaluate permissions for older DB users who might not have it saved
    if "permissions" not in current_user or not current_user["permissions"]:
        try:
            role_enum = UserRole(current_user["role"])
            current_user["permissions"] = [p.value for p in ROLE_PERMISSIONS.get(role_enum, [])]
        except ValueError:
            current_user["permissions"] = []
            
    # Default is_active to True for older records
    if "is_active" not in current_user:
        current_user["is_active"] = True
        
    return UserResponse(**current_user)
