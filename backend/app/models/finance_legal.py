from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

# --- Insurance Models ---
class InsuranceClaim(BaseModel):
    claim_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admission_id: str
    patient_id: str
    hospital_id: str
    tpa_name: str
    claim_amount: float
    status: str = "initiated" # initiated, pre_auth_pending, approved, rejected, settled
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    settled_at: Optional[datetime] = None
    approved_amount: Optional[float] = None
    rejection_reason: Optional[str] = None

# --- Government Scheme Models ---
class SchemeEligibilityCheck(BaseModel):
    check_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    scheme_name: str # PM-JAY, MPJAY
    identity_type: str # ABHA, Aadhaar, Ration Card
    identity_value: str
    is_eligible: bool
    coverage_cap: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Medico-Legal Case (MLC) Models ---
class MLCRecord(BaseModel):
    mlc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admission_id: str
    patient_id: str
    doctor_id: str
    hospital_id: str
    case_type: str # assault, accident, poisoning, burn
    injury_description: str
    fir_number: Optional[str] = None
    police_station: Optional[str] = None
    is_locked: bool = False # Locked after 24h
    created_at: datetime = Field(default_factory=datetime.utcnow)
