from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class Hospital(BaseModel):
    hospital_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    registration_number: str
    address: dict # e.g., {"city": "...", "state": "...", "pincode": "..."}
    contact_email: str
    contact_phone: Optional[str] = None
    admin_user_id: str
    departments: List[str] = Field(default_factory=list) # List of department_ids
    empanelment: dict = Field(default_factory=dict) # e.g., {"pm_jay": True, "mpjay": True, "approved_by": "GoI"}
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DepartmentType(str):
    OPD = "opd"
    IPD = "ipd"
    PHARMACY = "pharmacy"
    ICU = "icu"
    EMERGENCY = "emergency"
    LAB = "lab"
    OT = "ot"

class Department(BaseModel):
    department_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hospital_id: str
    name: str
    type: str # Use DepartmentType values
    sub_type: Optional[str] = None # e.g., "surgical", "non_surgical"
    head_doctor_id: Optional[str] = None
    bed_count: int = 0 # Applicable mainly for IPD/ICU
    is_active: bool = True

class Ward(BaseModel):
    ward_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department_id: str
    hospital_id: str
    name: str # e.g., "General Ward A", "ICU 1"
    ward_type: str # e.g., "general", "special", "icu"
    capacity: int
    is_active: bool = True

class Bed(BaseModel):
    bed_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ward_id: str
    hospital_id: str
    bed_number: str
    is_occupied: bool = False
    current_admission_id: Optional[str] = None
