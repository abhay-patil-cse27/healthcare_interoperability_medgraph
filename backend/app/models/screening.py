"""
Screening Models — Responsible AI Pipeline
=============================================
Pydantic models for the Antigravity Agent clinical screening pipeline.

Architecture Flow:
  Patient → Consent Engine → AI Screening → HITL Validator → Doctor (time-bound consent)

HITL Validator actions:
  1. EDIT: Modify AI summary to correct inaccuracies, then forward to doctor
  2. ACCEPT: Confirm AI summary matches source data, forward to doctor
  3. REJECT: Flag as inaccurate, return for re-processing
  4. ESCALATE: Flag for admin review (identity mismatch, inconsistent records)

Doctor access is ONLY granted via time-bound consent created by the HITL forward action.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AbnormalityStatus(str, Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    LOW = "LOW"
    CRITICAL = "CRITICAL"


class ScreeningStage(str, Enum):
    """Tracks where the screening is in the pipeline."""
    AI_GENERATED = "ai_generated"           # AI has produced summary, awaiting HITL
    HITL_IN_REVIEW = "hitl_in_review"       # HITL operator is actively reviewing
    HITL_EDITED = "hitl_edited"             # HITL edited and forwarded to doctor
    HITL_ACCEPTED = "hitl_accepted"         # HITL accepted as-is and forwarded to doctor
    HITL_REJECTED = "hitl_rejected"         # HITL rejected — needs re-processing
    HITL_ESCALATED = "hitl_escalated"       # Escalated to admin
    DOCTOR_CONSENT_ACTIVE = "doctor_consent_active"  # Time-bound consent issued to doctor
    DOCTOR_REVIEWED = "doctor_reviewed"     # Doctor has reviewed the summary
    CONSENT_EXPIRED = "consent_expired"     # Doctor's time-bound access expired


class FlaggedAbnormality(BaseModel):
    """A single flagged lab parameter with its clinical context."""
    parameter: str
    observed_value: str
    unit: str
    reference_range: str
    status: AbnormalityStatus
    ai_note: Optional[str] = Field(
        None,
        description="AI-generated observation — explicitly not a diagnosis",
    )
    source_section: str = Field(
        ..., description="Which section of the report this came from"
    )


# ── Request Models ────────────────────────────────────────────────────────────

class ScreeningRequest(BaseModel):
    """Request body for the /screening/summarise endpoint."""
    patient_id: str
    lab_report_text: str = Field(
        ..., description="Raw lab report text to be screened"
    )
    source_document_id: Optional[str] = Field(
        None, description="ID of the source document in the system"
    )
    patient_name: Optional[str] = None
    patient_age: Optional[str] = None
    patient_gender: Optional[str] = None
    known_conditions: Optional[List[str]] = Field(default_factory=list)
    report_date: Optional[str] = None


class HITLEditAndForward(BaseModel):
    """HITL operator edits the AI summary and forwards to doctor."""
    screening_id: str
    edited_summary: str = Field(
        ..., description="The corrected/edited version of the AI summary"
    )
    edit_reason: str = Field(
        ..., description="Why the HITL operator edited the summary"
    )
    target_doctor_id: str = Field(
        ..., description="Doctor who should receive this screening"
    )
    consent_duration_hours: int = Field(
        default=24, ge=1, le=168,
        description="How long the doctor can access this screening (1-168 hours)"
    )
    notes: Optional[str] = None


class HITLAcceptAndForward(BaseModel):
    """HITL operator accepts AI summary as accurate and forwards to doctor."""
    screening_id: str
    target_doctor_id: str = Field(
        ..., description="Doctor who should receive this screening"
    )
    consent_duration_hours: int = Field(
        default=24, ge=1, le=168,
        description="How long the doctor can access this screening (1-168 hours)"
    )
    validation_notes: Optional[str] = Field(
        None, description="Optional notes confirming data accuracy"
    )


class HITLReject(BaseModel):
    """HITL operator rejects the screening — data doesn't match source."""
    screening_id: str
    rejection_reason: str
    discrepancies: Optional[List[str]] = Field(
        default_factory=list,
        description="List of specific data points that don't match"
    )


class HITLEscalate(BaseModel):
    """HITL operator escalates — identity/record issues."""
    screening_id: str
    escalation_reason: str
    escalation_type: str = Field(
        ..., description="identity_mismatch | inconsistent_records | hitl_unavailable | other"
    )


# ── Response Models ───────────────────────────────────────────────────────────

class ScreeningSummary(BaseModel):
    """Structured output from the Antigravity Agent screening pipeline."""
    screening_id: str
    patient_id: str
    consent_status: str
    summary_date: str
    source_document_id: Optional[str] = None

    # AI-generated structured summary
    ai_summary: str = Field(
        ..., description="Full AI-generated screening summary in markdown format"
    )

    # HITL-edited version (if edited)
    hitl_edited_summary: Optional[str] = Field(
        None, description="HITL-edited version of the summary (if modified)"
    )
    edit_reason: Optional[str] = None

    # The final summary that goes to the doctor
    final_summary: Optional[str] = Field(
        None, description="The version forwarded to doctor (edited or original)"
    )

    # Parsed abnormalities for programmatic use
    flagged_abnormalities: List[FlaggedAbnormality] = Field(default_factory=list)
    abnormality_count: int = 0
    critical_count: int = 0

    # Pipeline stage tracking
    stage: ScreeningStage = ScreeningStage.AI_GENERATED

    # HITL verification state
    hitl_operator_id: Optional[str] = None
    hitl_action_at: Optional[datetime] = None
    hitl_notes: Optional[str] = None

    # Doctor access (time-bound consent)
    target_doctor_id: Optional[str] = None
    doctor_consent_id: Optional[str] = None
    doctor_consent_expires: Optional[datetime] = None
    doctor_reviewed: bool = False
    doctor_reviewed_at: Optional[datetime] = None

    # Metadata
    responsible_ai_version: str = "2.0.0"
    model_used: str = Field(default="", alias="model_used")
    processing_time_ms: int = 0
    grounding_sources: List[str] = Field(
        default_factory=list,
        description="List of source document IDs that ground this summary",
    )

    model_config = {"protected_namespaces": ()}


class DoctorScreeningView(BaseModel):
    """What the doctor sees — only after HITL validation + time-bound consent."""
    screening_id: str
    patient_id: str
    patient_name: Optional[str] = None
    summary_date: str

    # Doctor sees the final (possibly edited) summary
    clinical_summary: str
    flagged_abnormalities: List[FlaggedAbnormality]
    abnormality_count: int
    critical_count: int

    # Transparency markers
    was_edited_by_hitl: bool = False
    ai_generated_label: str = "This summary was AI-generated and verified by a HITL operator. It is not a clinical diagnosis."

    # Consent info
    consent_expires_at: Optional[datetime] = None
    source_document_id: Optional[str] = None


class ScreeningListItem(BaseModel):
    """Lightweight item for listing screenings."""
    screening_id: str
    patient_id: str
    patient_name: Optional[str] = None
    summary_date: str
    abnormality_count: int
    critical_count: int
    stage: ScreeningStage
    consent_status: str
    target_doctor_id: Optional[str] = None
