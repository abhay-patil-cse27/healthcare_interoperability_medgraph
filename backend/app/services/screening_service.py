"""
Screening Service — Antigravity Agent v2
==========================================
Redesigned pipeline with HITL-gated doctor access:

  Patient → Consent Engine → AI Screening → HITL Validator → Doctor (time-bound consent)

Flow:
  1. Patient grants consent for data processing
  2. AI generates screening summary (grounded, no hallucination)
  3. HITL Validator reviews:
     a) EDIT: Corrects inaccuracies, forwards to doctor with time-bound consent
     b) ACCEPT: Confirms accuracy, forwards to doctor with time-bound consent
     c) REJECT: Returns for re-processing
     d) ESCALATE: Flags for admin (identity/record issues)
  4. Doctor can ONLY access the screening via time-bound consent issued by HITL forward

Key: Doctor NEVER sees raw AI output. Only HITL-validated/edited summaries reach them.
"""
import re
import uuid
import time
import structlog
from datetime import datetime, timedelta
from typing import List, Optional

from app.models.screening import (
    AbnormalityStatus,
    FlaggedAbnormality,
    ScreeningStage,
    ScreeningSummary,
    DoctorScreeningView,
)
from app.prompts.responsible_ai import (
    ANTIGRAVITY_SCREENING_SYSTEM_PROMPT,
    build_screening_prompt,
)
from app.services.groq_service import GroqService
from app.services.consent_service import ConsentService
from app.services.audit_service import log_phi_access
from app.config import get_settings

logger = structlog.get_logger()

SCREENING_COLLECTION = "screening_summaries"
DOCTOR_SCREENING_CONSENTS = "doctor_screening_consents"


# ── Reference ranges for programmatic abnormality detection ───────────────────
REFERENCE_RANGES = {
    "glucose_fasting": (70.0, 99.0, "mg/dL"),
    "hba1c": (0.0, 5.6, "%"),
    "bilirubin_total": (0.0, 1.2, "mg/dL"),
    "bilirubin_direct": (0.0, 0.3, "mg/dL"),
    "bilirubin_indirect": (0.1, 1.0, "mg/dL"),
    "total_protein": (6.4, 8.3, "gm/dL"),
    "albumin": (3.5, 5.2, "gm/dL"),
    "globulin": (1.8, 3.6, "gm/dL"),
    "ag_ratio": (1.1, 2.2, ""),
    "sgpt_alt": (0.0, 41.0, "U/L"),
    "sgot_ast": (0.0, 40.0, "U/L"),
    "creatinine": (0.90, 1.30, "mg/dL"),
    "bun": (6.0, 20.0, "mg/dL"),
    "uric_acid": (3.4, 7.0, "mg/dL"),
    "phosphorus": (2.5, 4.5, "mg/dL"),
    "calcium": (8.6, 10.0, "mg/dL"),
    "cholesterol_total": (0.0, 200.0, "mg/dL"),
    "triglycerides": (0.0, 150.0, "mg/dL"),
    "hdl": (40.0, 999.0, "mg/dL"),
    "ldl": (0.0, 100.0, "mg/dL"),
    "vldl": (6.0, 38.0, "mg/dL"),
    "sodium": (136.0, 145.0, "mmol/L"),
    "potassium": (3.5, 5.1, "mmol/L"),
    "chloride": (98.0, 107.0, "mmol/L"),
    "haemoglobin": (14.0, 18.0, "gm/dL"),
    "rbc_count": (4.4, 6.0, "mill/cu.mm"),
    "pcv": (42.0, 52.0, "%"),
    "wbc_count": (4300.0, 10300.0, "cells/cu.mm"),
    "platelet_count": (140.0, 440.0, "10^3/uL"),
    "eosinophils_percent": (1.0, 6.0, "%"),
    "eosinophils_absolute": (20.0, 500.0, "cells/cu.mm"),
    "basophils_absolute": (20.0, 100.0, "cells/cu.mm"),
    "esr": (0.0, 15.0, "mm/hr"),
    "tsh": (0.54, 5.3, "uIU/mL"),
    "ft3": (2.0, 4.4, "pg/mL"),
    "ft4": (0.93, 1.7, "ng/dL"),
    "vitamin_b12": (197.0, 771.0, "pg/mL"),
    "vitamin_d": (30.0, 100.0, "ng/mL"),
}


def _classify_value(value: float, lower: float, upper: float) -> AbnormalityStatus:
    """Classify a lab value against its reference range."""
    if lower <= value <= upper:
        return AbnormalityStatus.NORMAL
    if value > upper:
        deviation = (value - upper) / (upper - lower) if (upper - lower) > 0 else 1
        return AbnormalityStatus.CRITICAL if deviation > 2.0 else AbnormalityStatus.HIGH
    # value < lower
    deviation = (lower - value) / (upper - lower) if (upper - lower) > 0 else 1
    return AbnormalityStatus.CRITICAL if deviation > 2.0 else AbnormalityStatus.LOW


def parse_lab_abnormalities(lab_text: str) -> List[FlaggedAbnormality]:
    """
    Deterministic regex-based abnormality detection.
    Runs BEFORE the LLM — provides structured flags independent of AI output.
    """
    flagged: List[FlaggedAbnormality] = []

    extraction_patterns = [
        ("glucose_fasting", r"Glucose\s+Fasting[^0-9]*?([\d.]+)\s*mg/dL", "Glucose Fasting"),
        ("hba1c", r"HbA1C[^0-9]*?([\d.]+)\s*%", "HbA1c"),
        ("bilirubin_total", r"Bilirubin\s+Total[^0-9]*?([\d.]+)\s*mg/dL", "Bilirubin Total"),
        ("bilirubin_direct", r"Bilirubin\s+Direct[^0-9]*?([\d.]+)\s*mg/dL", "Bilirubin Direct"),
        ("sgpt_alt", r"SGPT\s*\(ALT\)[^0-9]*?([\d.]+)\s*U/L", "SGPT (ALT)"),
        ("sgot_ast", r"SGOT\s*\(AST\)[^0-9]*?([\d.]+)\s*U/L", "SGOT (AST)"),
        ("creatinine", r"Creatinine,?\s*Serum[^0-9]*?([\d.]+)\s*mg/dL", "Creatinine"),
        ("bun", r"BUN,?\s*Serum[^0-9]*?([\d.]+)\s*mg/dL", "BUN"),
        ("uric_acid", r"Uric\s+Acid,?\s*Serum[^0-9]*?([\d.]+)\s*mg/dL", "Uric Acid"),
        ("cholesterol_total", r"Cholesterol\s+Total,?\s*Serum[^0-9]*?(\d+)\s*mg/dL", "Cholesterol Total"),
        ("triglycerides", r"Triglycerides,?\s*Serum[^0-9]*?(\d+)\s*mg/dL", "Triglycerides"),
        ("hdl", r"HDL\s+Cholesterol\s+Direct[^0-9]*?([\d.]+)\s*mg/dL", "HDL Cholesterol"),
        ("ldl", r"LDL\s+Cholesterol\s*\(Calculated\)[^0-9]*?([\d.]+)\s*mg/dL", "LDL Cholesterol"),
        ("sodium", r"Sodium,?\s*Serum\s*([\d.]+)\s*mmol/L", "Sodium"),
        ("potassium", r"Potassium,?\s*Serum\s*([\d.]+)\s*mmol/L", "Potassium"),
        ("chloride", r"Chloride,?\s*Serum\s*([\d.]+)\s*mmol/L", "Chloride"),
        ("haemoglobin", r"Haemoglobin\s*\(Hb\)\s*([\d.]+)\s*gm/dL", "Haemoglobin"),
        ("rbc_count", r"Erythrocyte\s*\(RBC\)\s*Count\s*([\d.]+)\s*mill/cu\.mm", "RBC Count"),
        ("pcv", r"PCV[^0-9]*?([\d.]+)\s*%", "PCV"),
        ("wbc_count", r"Total\s+Leucocytes\s*\(WBC\)\s*Count\s*([\d,]+)\s*cells/cu\.mm", "WBC Count"),
        ("platelet_count", r"Platelet\s+count\s*(\d+)\s*10\^3", "Platelet Count"),
        ("eosinophils_percent", r"Eosinophils\s+(\d+)\s*%", "Eosinophils %"),
        ("eosinophils_absolute", r"Absolute\s+Eosinophil\s+Count\s*(\d+)\s*cells/cu\.mm", "Absolute Eosinophil Count"),
        ("basophils_absolute", r"Absolute\s+Basophil\s+Count\s*(\d+)\s*cells/cu\.mm", "Absolute Basophil Count"),
        ("esr", r"ESR[^0-9]*?(\d+)\s*mm/hr", "ESR"),
        ("tsh", r"TSH[^0-9]*?([\d.]+)\s*(?:µ|u)IU/mL", "TSH"),
        ("ft3", r"FT3[^0-9]*?([\d.]+)\s*pg/mL", "FT3"),
        ("ft4", r"FT4[^0-9]*?([\d.]+)\s*ng/dL", "FT4"),
        ("vitamin_b12", r"Vitamin\s+B12[^0-9]*?(\d+)\s*pg/mL", "Vitamin B12"),
        ("vitamin_d", r"Vitamin\s+D\s+Total[^0-9]*?([\d.]+)\s*ng/mL", "Vitamin D"),
        ("phosphorus", r"Phosphorus,?\s*Serum[^0-9]*?([\d.]+)\s*mg/dL", "Phosphorus"),
        ("calcium", r"Calcium,?\s*Serum[^0-9]*?([\d.]+)\s*mg/dL", "Calcium"),
    ]

    for key, pattern, display_name in extraction_patterns:
        match = re.search(pattern, lab_text, re.IGNORECASE)
        if match:
            raw_value = match.group(1).replace(",", "")
            try:
                value = float(raw_value)
            except ValueError:
                continue

            ref = REFERENCE_RANGES.get(key)
            if not ref:
                continue

            lower, upper, unit = ref
            status = _classify_value(value, lower, upper)

            if status != AbnormalityStatus.NORMAL:
                flagged.append(FlaggedAbnormality(
                    parameter=display_name,
                    observed_value=raw_value,
                    unit=unit,
                    reference_range=f"{lower}-{upper}",
                    status=status,
                    ai_note=None,
                    source_section="Lab Report",
                ))

    return flagged


class ScreeningService:
    """
    Orchestrates the Responsible AI screening pipeline.

    Architecture:
      Patient → Consent Engine → AI Screening → HITL Validator → Doctor (time-bound)

    The doctor NEVER receives raw AI output. All summaries pass through HITL first.
    HITL forward action creates a time-bound consent record for the target doctor.
    """

    def __init__(self):
        self.groq = GroqService()
        self.consent_service = ConsentService()
        self.settings = get_settings()

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 1: AI Screening (consent-gated)
    # ══════════════════════════════════════════════════════════════════════════

    async def generate_screening(
        self,
        patient_id: str,
        lab_report_text: str,
        requester_id: str,
        requester_role: str,
        request_id: str,
        db,
        patient_name: Optional[str] = None,
        patient_age: Optional[str] = None,
        patient_gender: Optional[str] = None,
        known_conditions: Optional[List[str]] = None,
        source_document_id: Optional[str] = None,
        high_priority_text: Optional[str] = None,
        source_language: str = "English",
    ) -> ScreeningSummary:
        """
        Generate AI screening summary. Consent-gated.
        Output goes to HITL queue — NOT directly to any doctor.

        Args:
            high_priority_text: Pre-extracted high-priority sections (Interpretation,
                Note, Remark, etc.) for strict verbatim reproduction by the LLM.
            source_language: Detected language of the source document.
        """
        screening_id = str(uuid.uuid4())
        start_time = time.time()

        # ── Consent Gate ──────────────────────────────────────────────────────
        consent_result = await self.consent_service.check_access(
            requester_id=requester_id,
            requester_role=requester_role,
            patient_id=patient_id,
            db=db,
        )

        if not consent_result.allowed:
            logger.warning(
                "screening_blocked_no_consent",
                patient_id=patient_id[:8] + "...",
                requester_id=requester_id,
                request_id=request_id,
            )
            return ScreeningSummary(
                screening_id=screening_id,
                patient_id=patient_id,
                consent_status="NOT_VERIFIED",
                summary_date=datetime.utcnow().isoformat(),
                ai_summary="Cannot generate summary — patient consent not verified.",
                flagged_abnormalities=[],
                abnormality_count=0,
                critical_count=0,
                stage=ScreeningStage.AI_GENERATED,
                responsible_ai_version="2.0.0",
                model_used="none",
                processing_time_ms=0,
                grounding_sources=[],
            )

        # ── Deterministic Abnormality Parsing ─────────────────────────────────
        flagged = parse_lab_abnormalities(lab_report_text)
        critical_count = sum(1 for f in flagged if f.status == AbnormalityStatus.CRITICAL)

        # ── LLM Screening Summary ────────────────────────────────────────────
        patient_context = {
            "patient_id": patient_id,
            "name": patient_name or "Not provided",
            "age": patient_age or "Not provided",
            "gender": patient_gender or "Not provided",
            "known_conditions": ", ".join(known_conditions) if known_conditions else "None on record",
            "report_date": "See source document",
            "referred_by": "See source document",
            "visit_history": "See graph database",
        }

        user_prompt = build_screening_prompt(
            patient_context=patient_context,
            lab_data=lab_report_text,
            consent_status="VERIFIED",
            source_document_id=source_document_id or screening_id,
            high_priority_sections=high_priority_text or "",
            source_language=source_language,
        )

        llm_result = await self.groq.invoke(
            system_prompt=ANTIGRAVITY_SCREENING_SYSTEM_PROMPT,
            user_message=user_prompt,
            max_tokens=4096,
            temperature=0.0,
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # ── Build & Persist Summary ───────────────────────────────────────────
        summary = ScreeningSummary(
            screening_id=screening_id,
            patient_id=patient_id,
            consent_status="VERIFIED",
            summary_date=datetime.utcnow().isoformat(),
            source_document_id=source_document_id,
            ai_summary=llm_result["text"],
            hitl_edited_summary=None,
            final_summary=None,  # Only set after HITL forwards
            flagged_abnormalities=flagged,
            abnormality_count=len(flagged),
            critical_count=critical_count,
            stage=ScreeningStage.AI_GENERATED,
            responsible_ai_version="2.0.0",
            model_used=self.settings.groq_model,
            processing_time_ms=processing_time_ms,
            grounding_sources=[source_document_id] if source_document_id else [screening_id],
        )

        await db[SCREENING_COLLECTION].insert_one(summary.model_dump())

        # ── Audit Log ─────────────────────────────────────────────────────────
        await log_phi_access(
            action="screening_generated",
            patient_id=patient_id,
            accessor_id=requester_id,
            accessor_role=requester_role,
            resource_type="lab_report_screening",
            request_id=request_id,
            db=db,
            metadata={
                "screening_id": screening_id,
                "abnormality_count": len(flagged),
                "critical_count": critical_count,
                "consent_id": consent_result.consent_id,
                "stage": ScreeningStage.AI_GENERATED.value,
            },
        )

        logger.info(
            "screening_generated",
            screening_id=screening_id,
            patient_id=patient_id[:8] + "...",
            abnormalities=len(flagged),
            criticals=critical_count,
            processing_ms=processing_time_ms,
        )

        return summary

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2: HITL Validator Actions
    # ══════════════════════════════════════════════════════════════════════════

    async def hitl_edit_and_forward(
        self,
        screening_id: str,
        operator_id: str,
        edited_summary: str,
        edit_reason: str,
        target_doctor_id: str,
        consent_duration_hours: int,
        request_id: str,
        db,
        notes: Optional[str] = None,
    ) -> Optional[ScreeningSummary]:
        """
        HITL edits the AI summary and forwards to doctor with time-bound consent.
        The edited version becomes the final_summary seen by the doctor.
        """
        doc = await db[SCREENING_COLLECTION].find_one({"screening_id": screening_id})
        if not doc:
            return None

        # Create time-bound consent for doctor to access this screening
        consent_id, consent_expires = await self._create_doctor_screening_consent(
            screening_id=screening_id,
            patient_id=doc["patient_id"],
            doctor_id=target_doctor_id,
            duration_hours=consent_duration_hours,
            granted_by=operator_id,
            db=db,
        )

        update = {
            "stage": ScreeningStage.HITL_EDITED.value,
            "hitl_edited_summary": edited_summary,
            "edit_reason": edit_reason,
            "final_summary": edited_summary,  # Edited version goes to doctor
            "hitl_operator_id": operator_id,
            "hitl_action_at": datetime.utcnow(),
            "hitl_notes": notes,
            "target_doctor_id": target_doctor_id,
            "doctor_consent_id": consent_id,
            "doctor_consent_expires": consent_expires,
        }

        await db[SCREENING_COLLECTION].update_one(
            {"screening_id": screening_id}, {"$set": update}
        )

        await log_phi_access(
            action="screening_hitl_edited_forwarded",
            patient_id=doc["patient_id"],
            accessor_id=operator_id,
            accessor_role="hitl_validator",
            resource_type="screening_summary",
            request_id=request_id,
            db=db,
            metadata={
                "screening_id": screening_id,
                "target_doctor_id": target_doctor_id,
                "consent_duration_hours": consent_duration_hours,
                "edit_reason": edit_reason,
            },
        )

        doc.update(update)
        doc.pop("_id", None)
        return ScreeningSummary(**doc)

    async def hitl_accept_and_forward(
        self,
        screening_id: str,
        operator_id: str,
        target_doctor_id: str,
        consent_duration_hours: int,
        request_id: str,
        db,
        validation_notes: Optional[str] = None,
    ) -> Optional[ScreeningSummary]:
        """
        HITL accepts AI summary as accurate and forwards to doctor with time-bound consent.
        The original AI summary becomes the final_summary.
        """
        doc = await db[SCREENING_COLLECTION].find_one({"screening_id": screening_id})
        if not doc:
            return None

        # Create time-bound consent for doctor
        consent_id, consent_expires = await self._create_doctor_screening_consent(
            screening_id=screening_id,
            patient_id=doc["patient_id"],
            doctor_id=target_doctor_id,
            duration_hours=consent_duration_hours,
            granted_by=operator_id,
            db=db,
        )

        update = {
            "stage": ScreeningStage.HITL_ACCEPTED.value,
            "final_summary": doc["ai_summary"],  # Original AI summary goes to doctor
            "hitl_operator_id": operator_id,
            "hitl_action_at": datetime.utcnow(),
            "hitl_notes": validation_notes,
            "target_doctor_id": target_doctor_id,
            "doctor_consent_id": consent_id,
            "doctor_consent_expires": consent_expires,
        }

        await db[SCREENING_COLLECTION].update_one(
            {"screening_id": screening_id}, {"$set": update}
        )

        await log_phi_access(
            action="screening_hitl_accepted_forwarded",
            patient_id=doc["patient_id"],
            accessor_id=operator_id,
            accessor_role="hitl_validator",
            resource_type="screening_summary",
            request_id=request_id,
            db=db,
            metadata={
                "screening_id": screening_id,
                "target_doctor_id": target_doctor_id,
                "consent_duration_hours": consent_duration_hours,
            },
        )

        doc.update(update)
        doc.pop("_id", None)
        return ScreeningSummary(**doc)

    async def hitl_reject(
        self,
        screening_id: str,
        operator_id: str,
        rejection_reason: str,
        discrepancies: List[str],
        request_id: str,
        db,
    ) -> Optional[ScreeningSummary]:
        """HITL rejects — data doesn't match source. No forwarding to doctor."""
        doc = await db[SCREENING_COLLECTION].find_one({"screening_id": screening_id})
        if not doc:
            return None

        update = {
            "stage": ScreeningStage.HITL_REJECTED.value,
            "hitl_operator_id": operator_id,
            "hitl_action_at": datetime.utcnow(),
            "hitl_notes": f"REJECTED: {rejection_reason}. Discrepancies: {discrepancies}",
        }

        await db[SCREENING_COLLECTION].update_one(
            {"screening_id": screening_id}, {"$set": update}
        )

        await log_phi_access(
            action="screening_hitl_rejected",
            patient_id=doc["patient_id"],
            accessor_id=operator_id,
            accessor_role="hitl_validator",
            resource_type="screening_summary",
            request_id=request_id,
            db=db,
            metadata={
                "screening_id": screening_id,
                "rejection_reason": rejection_reason,
                "discrepancies": discrepancies,
            },
        )

        doc.update(update)
        doc.pop("_id", None)
        return ScreeningSummary(**doc)

    async def hitl_escalate(
        self,
        screening_id: str,
        operator_id: str,
        escalation_reason: str,
        escalation_type: str,
        request_id: str,
        db,
    ) -> Optional[ScreeningSummary]:
        """HITL escalates — identity/record issues. No forwarding to doctor."""
        doc = await db[SCREENING_COLLECTION].find_one({"screening_id": screening_id})
        if not doc:
            return None

        update = {
            "stage": ScreeningStage.HITL_ESCALATED.value,
            "hitl_operator_id": operator_id,
            "hitl_action_at": datetime.utcnow(),
            "hitl_notes": f"ESCALATED ({escalation_type}): {escalation_reason}",
        }

        await db[SCREENING_COLLECTION].update_one(
            {"screening_id": screening_id}, {"$set": update}
        )

        await log_phi_access(
            action="screening_hitl_escalated",
            patient_id=doc["patient_id"],
            accessor_id=operator_id,
            accessor_role="hitl_validator",
            resource_type="screening_summary",
            request_id=request_id,
            db=db,
            metadata={
                "screening_id": screening_id,
                "escalation_reason": escalation_reason,
                "escalation_type": escalation_type,
            },
        )

        doc.update(update)
        doc.pop("_id", None)
        return ScreeningSummary(**doc)

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 3: Doctor Access (time-bound consent gated)
    # ══════════════════════════════════════════════════════════════════════════

    async def get_doctor_screening(
        self,
        screening_id: str,
        doctor_id: str,
        request_id: str,
        db,
    ) -> Optional[DoctorScreeningView]:
        """
        Doctor retrieves a screening — ONLY if:
        1. They are the target_doctor_id
        2. Time-bound consent has not expired
        3. Screening has been forwarded by HITL (stage = edited or accepted)
        """
        doc = await db[SCREENING_COLLECTION].find_one({"screening_id": screening_id})
        if not doc:
            return None

        # Gate 1: Must be the target doctor
        if doc.get("target_doctor_id") != doctor_id:
            logger.warning(
                "doctor_screening_access_denied_wrong_doctor",
                screening_id=screening_id,
                doctor_id=doctor_id,
            )
            return None

        # Gate 2: Must be in a forwarded stage
        valid_stages = [
            ScreeningStage.HITL_EDITED.value,
            ScreeningStage.HITL_ACCEPTED.value,
            ScreeningStage.DOCTOR_CONSENT_ACTIVE.value,
            ScreeningStage.DOCTOR_REVIEWED.value,
        ]
        if doc.get("stage") not in valid_stages:
            logger.warning(
                "doctor_screening_access_denied_not_forwarded",
                screening_id=screening_id,
                stage=doc.get("stage"),
            )
            return None

        # Gate 3: Time-bound consent must not be expired
        consent_expires = doc.get("doctor_consent_expires")
        if consent_expires:
            if isinstance(consent_expires, str):
                consent_expires = datetime.fromisoformat(consent_expires)
            if datetime.utcnow() > consent_expires:
                # Mark as expired
                await db[SCREENING_COLLECTION].update_one(
                    {"screening_id": screening_id},
                    {"$set": {"stage": ScreeningStage.CONSENT_EXPIRED.value}},
                )
                logger.warning(
                    "doctor_screening_consent_expired",
                    screening_id=screening_id,
                    doctor_id=doctor_id,
                )
                return None

        # All gates passed — return doctor view
        await log_phi_access(
            action="doctor_viewed_screening",
            patient_id=doc["patient_id"],
            accessor_id=doctor_id,
            accessor_role="doctor",
            resource_type="screening_summary",
            request_id=request_id,
            db=db,
            metadata={"screening_id": screening_id},
        )

        return DoctorScreeningView(
            screening_id=doc["screening_id"],
            patient_id=doc["patient_id"],
            summary_date=doc["summary_date"],
            clinical_summary=doc.get("final_summary") or doc.get("ai_summary", ""),
            flagged_abnormalities=[
                FlaggedAbnormality(**f) for f in doc.get("flagged_abnormalities", [])
            ],
            abnormality_count=doc.get("abnormality_count", 0),
            critical_count=doc.get("critical_count", 0),
            was_edited_by_hitl=doc.get("stage") == ScreeningStage.HITL_EDITED.value,
            consent_expires_at=doc.get("doctor_consent_expires"),
            source_document_id=doc.get("source_document_id"),
        )

    async def doctor_mark_reviewed(
        self,
        screening_id: str,
        doctor_id: str,
        request_id: str,
        db,
    ) -> bool:
        """Doctor marks a screening as reviewed."""
        doc = await db[SCREENING_COLLECTION].find_one({
            "screening_id": screening_id,
            "target_doctor_id": doctor_id,
        })
        if not doc:
            return False

        await db[SCREENING_COLLECTION].update_one(
            {"screening_id": screening_id},
            {"$set": {
                "stage": ScreeningStage.DOCTOR_REVIEWED.value,
                "doctor_reviewed": True,
                "doctor_reviewed_at": datetime.utcnow(),
            }},
        )

        await log_phi_access(
            action="doctor_reviewed_screening",
            patient_id=doc["patient_id"],
            accessor_id=doctor_id,
            accessor_role="doctor",
            resource_type="screening_summary",
            request_id=request_id,
            db=db,
            metadata={"screening_id": screening_id},
        )

        return True

    # ══════════════════════════════════════════════════════════════════════════
    # Query helpers
    # ══════════════════════════════════════════════════════════════════════════

    async def get_hitl_queue(self, db, limit: int = 50) -> List[dict]:
        """Get screenings awaiting HITL review."""
        cursor = db[SCREENING_COLLECTION].find(
            {"stage": ScreeningStage.AI_GENERATED.value}
        ).sort("summary_date", -1).limit(limit)

        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append({
                "screening_id": doc["screening_id"],
                "patient_id": doc["patient_id"],
                "summary_date": doc["summary_date"],
                "abnormality_count": doc.get("abnormality_count", 0),
                "critical_count": doc.get("critical_count", 0),
                "stage": doc.get("stage"),
                "consent_status": doc.get("consent_status", "unknown"),
            })
        return results

    async def get_doctor_inbox(self, doctor_id: str, db, limit: int = 50) -> List[dict]:
        """Get screenings forwarded to a specific doctor (active consent only)."""
        cursor = db[SCREENING_COLLECTION].find({
            "target_doctor_id": doctor_id,
            "stage": {"$in": [
                ScreeningStage.HITL_EDITED.value,
                ScreeningStage.HITL_ACCEPTED.value,
                ScreeningStage.DOCTOR_CONSENT_ACTIVE.value,
            ]},
            "doctor_consent_expires": {"$gt": datetime.utcnow()},
        }).sort("summary_date", -1).limit(limit)

        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append({
                "screening_id": doc["screening_id"],
                "patient_id": doc["patient_id"],
                "summary_date": doc["summary_date"],
                "abnormality_count": doc.get("abnormality_count", 0),
                "critical_count": doc.get("critical_count", 0),
                "stage": doc.get("stage"),
                "was_edited": doc.get("stage") == ScreeningStage.HITL_EDITED.value,
                "consent_expires": doc.get("doctor_consent_expires"),
            })
        return results

    async def get_screening_by_id(self, screening_id: str, db) -> Optional[ScreeningSummary]:
        """Retrieve a specific screening (for HITL operators and admins)."""
        doc = await db[SCREENING_COLLECTION].find_one({"screening_id": screening_id})
        if not doc:
            return None
        doc.pop("_id", None)
        return ScreeningSummary(**doc)

    # ══════════════════════════════════════════════════════════════════════════
    # Internal: Time-bound consent creation
    # ══════════════════════════════════════════════════════════════════════════

    async def _create_doctor_screening_consent(
        self,
        screening_id: str,
        patient_id: str,
        doctor_id: str,
        duration_hours: int,
        granted_by: str,
        db,
    ) -> tuple:
        """
        Create a time-bound consent record allowing a doctor to view a screening.
        This is separate from the patient→doctor consent — it's the HITL→doctor gate.
        """
        consent_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)

        consent_record = {
            "consent_id": consent_id,
            "screening_id": screening_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "granted_by_hitl": granted_by,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "duration_hours": duration_hours,
            "active": True,
        }

        await db[DOCTOR_SCREENING_CONSENTS].insert_one(consent_record)

        logger.info(
            "doctor_screening_consent_created",
            consent_id=consent_id,
            screening_id=screening_id,
            doctor_id=doctor_id,
            expires_at=expires_at.isoformat(),
        )

        return consent_id, expires_at
