from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import uuid


class ConsentScope(str, Enum):
    FULL = "full"
    DISEASE_SPECIFIC = "disease_specific"
    TIME_BOUND = "time_bound"
    MEDICATION_ONLY = "medication_only"


class ConsentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ConsentRequest(BaseModel):
    doctor_id: str
    patient_id: str
    purpose: str = Field(max_length=500)
    requested_scope: ConsentScope
    disease_filter: Optional[List[str]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    duration_hours: int = Field(default=24, ge=1, le=8760)


class ConsentRecord(BaseModel):
    consent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doctor_id: str
    patient_id: str
    purpose: str
    requested_scope: ConsentScope
    disease_filter: Optional[List[str]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    duration_hours: int = 24
    status: ConsentStatus = ConsentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    granted_at: Optional[datetime] = None


class ConsentGrant(BaseModel):
    consent_id: str
    patient_id: str
    approved: bool
    scope: Optional[ConsentScope] = None


@dataclass
class ConsentCheckResult:
    allowed: bool
    reason: str
    scope: Optional[str] = None
    filters: Optional[dict] = None
    consent_id: Optional[str] = None
