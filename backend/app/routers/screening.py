"""
Screening Router — Responsible AI Pipeline v2
================================================
Architecture:
  Patient → Consent Engine → AI Screening → HITL Validator → Doctor (time-bound consent)

Endpoints grouped by actor:

  HITL Validator:
    POST /screening/summarise          — Trigger AI screening (consent-gated)
    GET  /screening/hitl/queue         — View pending screenings
    GET  /screening/hitl/{id}          — View full screening detail
    POST /screening/hitl/edit-forward  — Edit summary & forward to doctor
    POST /screening/hitl/accept-forward — Accept & forward to doctor
    POST /screening/hitl/reject        — Reject (data mismatch)
    POST /screening/hitl/escalate      — Escalate (identity/record issues)

  Doctor:
    GET  /screening/doctor/inbox       — View forwarded screenings (time-bound)
    GET  /screening/doctor/{id}        — View specific screening (consent-gated)
    POST /screening/doctor/{id}/reviewed — Mark as reviewed
"""
import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_db, get_current_user, require_permission, require_any_permission
from app.models.screening import (
    ScreeningRequest,
    ScreeningSummary,
    DoctorScreeningView,
    ScreeningListItem,
    HITLEditAndForward,
    HITLAcceptAndForward,
    HITLReject,
    HITLEscalate,
)
from app.services.screening_service import ScreeningService

logger = structlog.get_logger()
router = APIRouter()

_screening_service = ScreeningService()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1: AI Screening Generation
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/summarise", response_model=ScreeningSummary)
async def generate_screening(
    body: ScreeningRequest,
    request: Request,
    current_user=Depends(require_any_permission([
        "screening:validate", "screening:forward", "clinical:read"
    ])),
    db=Depends(get_db),
):
    """
    Generate an AI screening summary from a lab report.

    Requires patient consent. Output goes to HITL queue — NOT directly to doctor.
    Only HITL validators and admins can trigger this.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    summary = await _screening_service.generate_screening(
        patient_id=body.patient_id,
        lab_report_text=body.lab_report_text,
        requester_id=current_user["user_id"],
        requester_role=current_user["role"],
        request_id=request_id,
        db=db,
        patient_name=body.patient_name,
        patient_age=body.patient_age,
        patient_gender=body.patient_gender,
        known_conditions=body.known_conditions,
        source_document_id=body.source_document_id,
    )

    return summary


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2: HITL Validator Endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/hitl/queue", response_model=list[ScreeningListItem])
async def get_hitl_queue(
    current_user=Depends(require_permission("screening:view_pending")),
    db=Depends(get_db),
):
    """Get all screenings awaiting HITL validation."""
    return await _screening_service.get_hitl_queue(db=db)


@router.get("/hitl/{screening_id}", response_model=ScreeningSummary)
async def get_screening_for_hitl(
    screening_id: str,
    current_user=Depends(require_permission("screening:validate")),
    db=Depends(get_db),
):
    """HITL operator views full screening detail for validation."""
    result = await _screening_service.get_screening_by_id(screening_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Screening not found")
    return result


@router.post("/hitl/edit-forward", response_model=ScreeningSummary)
async def hitl_edit_and_forward(
    body: HITLEditAndForward,
    request: Request,
    current_user=Depends(require_permission("screening:edit")),
    db=Depends(get_db),
):
    """
    HITL edits the AI summary and forwards to doctor.

    Creates a time-bound consent for the target doctor.
    The edited version becomes what the doctor sees.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    result = await _screening_service.hitl_edit_and_forward(
        screening_id=body.screening_id,
        operator_id=current_user["user_id"],
        edited_summary=body.edited_summary,
        edit_reason=body.edit_reason,
        target_doctor_id=body.target_doctor_id,
        consent_duration_hours=body.consent_duration_hours,
        request_id=request_id,
        db=db,
        notes=body.notes,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Screening not found")

    logger.info(
        "hitl_edit_forwarded",
        screening_id=body.screening_id,
        operator=current_user["user_id"],
        target_doctor=body.target_doctor_id,
    )
    return result


@router.post("/hitl/accept-forward", response_model=ScreeningSummary)
async def hitl_accept_and_forward(
    body: HITLAcceptAndForward,
    request: Request,
    current_user=Depends(require_permission("screening:forward")),
    db=Depends(get_db),
):
    """
    HITL accepts AI summary as accurate and forwards to doctor.

    Creates a time-bound consent for the target doctor.
    The original AI summary becomes what the doctor sees.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    result = await _screening_service.hitl_accept_and_forward(
        screening_id=body.screening_id,
        operator_id=current_user["user_id"],
        target_doctor_id=body.target_doctor_id,
        consent_duration_hours=body.consent_duration_hours,
        request_id=request_id,
        db=db,
        validation_notes=body.validation_notes,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Screening not found")

    logger.info(
        "hitl_accepted_forwarded",
        screening_id=body.screening_id,
        operator=current_user["user_id"],
        target_doctor=body.target_doctor_id,
    )
    return result


@router.post("/hitl/reject", response_model=ScreeningSummary)
async def hitl_reject(
    body: HITLReject,
    request: Request,
    current_user=Depends(require_permission("screening:validate")),
    db=Depends(get_db),
):
    """
    HITL rejects the screening — data doesn't match source document.
    Nothing is forwarded to any doctor.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    result = await _screening_service.hitl_reject(
        screening_id=body.screening_id,
        operator_id=current_user["user_id"],
        rejection_reason=body.rejection_reason,
        discrepancies=body.discrepancies or [],
        request_id=request_id,
        db=db,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Screening not found")
    return result


@router.post("/hitl/escalate", response_model=ScreeningSummary)
async def hitl_escalate(
    body: HITLEscalate,
    request: Request,
    current_user=Depends(require_permission("screening:escalate")),
    db=Depends(get_db),
):
    """
    HITL escalates — patient identity cannot be confirmed or records are inconsistent.
    Nothing is forwarded to any doctor. Admin review required.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    result = await _screening_service.hitl_escalate(
        screening_id=body.screening_id,
        operator_id=current_user["user_id"],
        escalation_reason=body.escalation_reason,
        escalation_type=body.escalation_type,
        request_id=request_id,
        db=db,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Screening not found")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3: Doctor Endpoints (time-bound consent gated)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/doctor/inbox")
async def get_doctor_inbox(
    current_user=Depends(require_permission("patient:read_consented")),
    db=Depends(get_db),
):
    """
    Doctor's inbox — screenings forwarded by HITL with active time-bound consent.
    Only shows screenings where consent hasn't expired.
    """
    try:
        return await _screening_service.get_doctor_inbox(
            doctor_id=current_user["user_id"], db=db
        )
    except Exception as e:
        logger.error("doctor_inbox_error", error=str(e), doctor_id=current_user["user_id"])
        raise HTTPException(status_code=500, detail=f"Failed to load screening inbox: {str(e)}")


@router.get("/doctor/{screening_id}", response_model=DoctorScreeningView)
async def get_doctor_screening(
    screening_id: str,
    request: Request,
    current_user=Depends(require_permission("patient:read_consented")),
    db=Depends(get_db),
):
    """
    Doctor views a specific screening.

    Access is ONLY granted if:
    1. Doctor is the target_doctor_id set by HITL
    2. Time-bound consent has not expired
    3. Screening was forwarded (edited or accepted) by HITL

    Returns the final_summary (edited by HITL or original AI summary).
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    result = await _screening_service.get_doctor_screening(
        screening_id=screening_id,
        doctor_id=current_user["user_id"],
        request_id=request_id,
        db=db,
    )

    if not result:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Either consent expired, screening not forwarded to you, or screening not found.",
        )
    return result


@router.post("/doctor/{screening_id}/reviewed")
async def doctor_mark_reviewed(
    screening_id: str,
    request: Request,
    current_user=Depends(require_permission("patient:read_consented")),
    db=Depends(get_db),
):
    """Doctor marks a screening as reviewed — completes the pipeline."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    success = await _screening_service.doctor_mark_reviewed(
        screening_id=screening_id,
        doctor_id=current_user["user_id"],
        request_id=request_id,
        db=db,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Screening not found or not assigned to you")

    return {"status": "reviewed", "screening_id": screening_id}
