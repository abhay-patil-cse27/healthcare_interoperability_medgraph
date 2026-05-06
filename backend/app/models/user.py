from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
from app.models.rbac import UserRole, Permission

class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole
    sub_role: Optional[str] = None # e.g. "surgical", "general"
    specialization: Optional[str] = None  # for doctors
    license_number: Optional[str] = None  # for doctors/pharmacists
    phone: Optional[str] = None

class UserInDB(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    hashed_password: str
    full_name: str
    role: UserRole
    sub_role: Optional[str] = None
    hospital_id: Optional[str] = None
    department_id: Optional[str] = None
    permissions: List[Permission] = Field(default_factory=list)
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    profile_photo_url: Optional[str] = None
    is_active: bool = True
    # Patient-specific identifiers (safe to store for all roles, null for staff)
    mrn: Optional[str] = None            # Medical Record Number — e.g. AIIMS-2026-04821
    abha_id: Optional[str] = None        # India ABHA Health ID
    blood_group: Optional[str] = None    # A+, B-, O+, etc.
    date_of_birth: Optional[str] = None  # YYYY-MM-DD
    gender: Optional[str] = None         # male / female / other
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: UserRole
    sub_role: Optional[str] = None
    hospital_id: Optional[str] = None
    department_id: Optional[str] = None
    permissions: List[Permission]
    specialization: Optional[str] = None
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: UserRole
