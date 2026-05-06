from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

# --- OPD Models ---
class Appointment(BaseModel):
    appointment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    hospital_id: str
    department_id: str
    scheduled_time: datetime
    status: str = "scheduled" # scheduled, completed, cancelled, no_show
    reason_for_visit: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- IPD Models ---
class Admission(BaseModel):
    admission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    admitting_doctor_id: str
    hospital_id: str
    department_id: str
    ward_id: str
    bed_id: str
    admission_time: datetime = Field(default_factory=datetime.utcnow)
    discharge_time: Optional[datetime] = None
    status: str = "admitted" # admitted, discharged, transferred, deceased
    is_mlc: bool = False # Medico-Legal Case
    mlc_fir_number: Optional[str] = None
    diagnosis: str
    scheme_applied: Optional[str] = None # PM-JAY, MPJAY, Private
    created_at: datetime = Field(default_factory=datetime.utcnow)

class IPDNote(BaseModel):
    note_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admission_id: str
    patient_id: str
    author_id: str # Doctor, Nurse, Ward Incharge
    author_role: str
    note_type: str # morning_round, evening_round, nursing_shift, emergency
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_flagged: bool = False # Flagged for review by Ward Incharge or Doctor

class VitalSign(BaseModel):
    vital_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    admission_id: Optional[str] = None # Null if taken in OPD
    recorded_by: str # user_id or "ward_bot"
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    temperature_c: Optional[float] = None
    blood_pressure_sys: Optional[int] = None
    blood_pressure_dia: Optional[int] = None
    heart_rate: Optional[int] = None
    sp02: Optional[int] = None
    respiratory_rate: Optional[int] = None
    is_alert: bool = False # Set by Ward Bot if out of normal ranges

# --- Prescription Models ---
class PrescriptionItem(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    instructions: Optional[str] = None

class Prescription(BaseModel):
    prescription_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    encounter_type: str # opd, ipd
    encounter_id: str # appointment_id or admission_id
    medications: List[PrescriptionItem]
    status: str = "active" # active, dispensed, discontinued
    created_at: datetime = Field(default_factory=datetime.utcnow)
